"""Rebuild the male graph with two CHOSEN functional-sign overrides.

Pipeline mirrors build_graph.main (which exposes no reusable build function).
Only the per-cell sign differs; constants come from the original builder.
"""
import argparse
import json
import os
from pathlib import Path
import numpy as np
import pandas as pd
import scipy.sparse as sp
from build_graph import MIN_SYN, MV_PER_SYNAPSE, SIGN, DATA, BUILD
from backrooms_dictionary import resolve, DICTIONARY
from graft_sag import sha256

CITATION = 'Clowney et al. 2015 Neuron 87:1036-1049, https://doi.org/10.1016/j.neuron.2015.07.025'
OVERRIDES = (
    dict(group='vAB3', transmitter=None, sign=1., rationale='CHOSEN: functional excitation of P1; applied to all dictionary vAB3 outputs', citation=CITATION),
    dict(group='mAL', transmitter='unclear', sign=-1., rationale='CHOSEN: restore the known GABAergic group sign only for unclear cells', citation=CITATION),
)


def apply_overrides(types, nt, sign, bodies):
    result = sign.copy()
    records = []
    for spec in OVERRIDES:
        selected = resolve(types, DICTIONARY[spec['group']]['types'])
        if spec['transmitter'] is not None:
            selected = selected[np.asarray(nt)[selected] == spec['transmitter']]
        changed = selected[result[selected] != spec['sign']]
        records.append(dict(spec, selected_cells=len(selected), changed_cells=len(changed),
                            bodies=[int(b) for b in bodies[selected]], indices=selected.tolist()))
        result[selected] = spec['sign']
    return result, records


def build(data_dir=DATA, output=BUILD/'graph_male_fsign.npz', baseline=BUILD/'graph.npz', force=False):
    data_dir, output, baseline = map(Path, (data_dir, output, baseline))
    record_path = output.with_name('male_fsign.json')
    sources = [baseline, *[data_dir/name for name in ('connectome-weights.feather',
        'body-neurotransmitters.feather', 'body-annotations.feather')],
        Path(__file__), Path('build_graph.py'), Path('backrooms_dictionary.py')]
    for target in (output, record_path):
        if any(target.exists() and source.exists() and os.path.samefile(target, source) for source in sources):
            raise ValueError('output aliases a source file')
    if output.exists() and record_path.exists() and os.path.samefile(output, record_path):
        raise ValueError('graph and record alias each other')
    if not force and (output.exists() or record_path.exists()):
        raise FileExistsError('functional-sign output exists; use --force')
    output.parent.mkdir(parents=True, exist_ok=True)
    print(f"loading weights (keeping pairs with >= {MIN_SYN} synapses) ...")
    import pyarrow.feather as pf
    import pyarrow.compute as pc

    tbl = pf.read_table(data_dir / "connectome-weights.feather")
    print(f"  {tbl.num_rows:,} pre->post pairs on disk")
    tbl = tbl.filter(pc.greater_equal(tbl.column("weight"), MIN_SYN))
    pre_a = tbl.column("body_pre").to_numpy()
    post_a = tbl.column("body_post").to_numpy()
    wt_a = tbl.column("weight").to_numpy().astype(np.float32)
    del tbl
    print(f"  {len(wt_a):,} pairs kept, {int(wt_a.sum()):,} synapses")

    print("loading annotations ...")
    ann = pd.read_feather(data_dir / "body-annotations.feather")
    ann["t"] = ann["type"].fillna(ann["flywireType"]).fillna(ann["instance"]).fillna("")

    print("loading neurotransmitters ...")
    nt = pd.read_feather(data_dir / "body-neurotransmitters.feather")
    nt = nt[["body", "consensus_nt"]].dropna(subset=["body"])
    nt = nt.drop_duplicates(subset=["body"])

    # The weights table is keyed on every EM segment, including millions of
    # unproofread fragments. Only 'Traced' bodies are actual reconstructed
    # neurons (165,122 of them - the number in the paper's headline).
    neurons = ann.loc[(ann.status == "Traced") & (ann.statusLabel != "Glia"), "bodyId"]
    bodies = np.sort(neurons.unique())
    n = len(bodies)
    print(f"  {n:,} traced neurons (of {ann.bodyId.nunique():,} annotated bodies)")

    # keep only edges where both endpoints are real neurons
    valid = np.zeros(int(max(pre_a.max(), post_a.max())) + 1, dtype=bool)
    valid[bodies] = True
    edge_ok = valid[pre_a] & valid[post_a]
    pre_a, post_a, wt_a = pre_a[edge_ok], post_a[edge_ok], wt_a[edge_ok]
    print(f"  {len(wt_a):,} neuron->neuron edges, {int(wt_a.sum()):,} synapses")

    idx = pd.Series(np.arange(n, dtype=np.int32), index=bodies)

    # per-body sign
    ntmap = nt.set_index("body")["consensus_nt"]
    nt_str = ntmap.reindex(bodies).fillna("unknown").str.lower().to_numpy().astype("U24")
    sign = np.array([SIGN.get(s, 0.0) for s in nt_str], dtype=np.float32)

    # per-body metadata aligned to index
    ann_i = ann.drop_duplicates(subset=["bodyId"]).set_index("bodyId")
    types = ann_i["t"].reindex(bodies).fillna("").to_numpy().astype(str)
    superclass = ann_i["superclass"].reindex(bodies).fillna("").to_numpy().astype(str)
    subclass = ann_i["subclass"].reindex(bodies).fillna("").to_numpy().astype(str)
    receptor = ann_i["receptorType"].reindex(bodies).fillna("").to_numpy().astype(str)
    fru = ann_i["fruDsx"].reindex(bodies).fillna("").to_numpy().astype(str)

    original_sign = sign.copy()
    sign, overrides = apply_overrides(types, nt_str, sign, bodies)
    print("building sparse matrix ...")
    r = idx.loc[post_a].to_numpy()   # row = postsynaptic
    c = idx.loc[pre_a].to_numpy()    # col = presynaptic
    v = wt_a * MV_PER_SYNAPSE * sign[c]

    keep = v != 0.0
    W = sp.csr_matrix(
        (v[keep], (r[keep], c[keep])), shape=(n, n), dtype=np.float32
    )
    W.sum_duplicates()

    print(f"  W: {W.shape[0]:,} x {W.shape[1]:,}, {W.nnz:,} nonzero edges")
    print(f"  excitatory edges: {(W.data > 0).sum():,}")
    print(f"  inhibitory edges: {(W.data < 0).sum():,}")
    print(f"  dropped (modulatory/unknown NT): {(~keep).sum():,}")

    with np.load(baseline, allow_pickle=False) as z:
        if not np.array_equal(bodies, z['bodies']):
            raise ValueError('baseline body index differs')
        old = sp.csr_matrix((z['data'], z['indices'], z['indptr']), shape=tuple(z['shape']))
        np.testing.assert_array_equal(original_sign, z['sign'])
    delta = (W-old).tocsr()
    touched = np.flatnonzero(sign != original_sign)
    outside = delta.data[~np.isin(delta.indices, touched)]
    maximum = float(np.max(np.abs(outside))) if len(outside) else 0.
    if maximum != 0:
        raise ValueError(f'outside touched columns max abs diff = {maximum}')
    for record in overrides:
        mask = np.isin(c, record['indices'])
        record['edges'] = int(W[:, record['indices']].nnz)
        record['synapses'] = int(wt_a[mask].astype(np.int64).sum())
        record['action'] = 'flipped' if record['group'] == 'vAB3' else 'added'
        print(json.dumps(record), flush=True)
    vab = overrides[0]['indices']
    inputs = {g: int(wt_a[np.isin(c, vab) & np.isin(r, resolve(types, DICTIONARY[g]['types']))].astype(np.int64).sum()) for g in ('mAL', 'P1')}
    sources = [data_dir/name for name in ('connectome-weights.feather', 'body-neurotransmitters.feather', 'body-annotations.feather')]
    sources += [Path('build_graph.py'), Path('backrooms_dictionary.py'), Path(__file__), baseline]
    record = dict(overrides=overrides, source_sha256s={p.name: sha256(p) for p in sources},
        outside_columns_max_abs_diff=maximum, vab3_target_synapses=inputs,
        original_zero_sign_cells=int((original_sign == 0).sum()), cells=n,
        min_syn=MIN_SYN, mv_per_synapse=MV_PER_SYNAPSE)
    np.savez_compressed(output, data=W.data, indices=W.indices, indptr=W.indptr, shape=W.shape,
        bodies=bodies, sign=sign, types=types, superclass=superclass, subclass=subclass,
        receptor=receptor, fru=fru, nt=nt_str, fsign=np.array(json.dumps(record)))
    record_path.write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
    print(f'Outside touched columns max abs diff = {maximum}; vAB3 target synapses: {inputs}', flush=True)
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args(argv)
    build(force=args.force)


if __name__ == '__main__':
    main()
