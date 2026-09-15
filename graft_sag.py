"""Transplant named BANC SAG outputs onto FAFB cells by target type.

Default --receivers legacy preserves v7: both donors go to AN_SMP_2 only.
--receivers by-type maps each donor's fafb_cell_type to the same receiver type:
AN_SMP_2 -> AN_SMP_2 and AN_FLA_SMP_2 -> AN_FLA_SMP_2.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

ROOT = Path(__file__).parent
SIGN_CHOICE = ("CHOSEN: SAG sign +1 follows functional evidence that SAG activity promotes "
               "virgin receptivity and is silenced after mating by sex peptide acting on SPSN "
               "(Feng, Palfreyman, Hasemeyer, Talsma, Dickson 2014 Neuron 83:135), "
               "not the BANC dopamine transmitter prediction.")


def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def build(female=ROOT/'build/graph_female.npz', data_dir=ROOT/'data/banc',
          output=ROOT/'build/graph_female_sag.npz', report=ROOT/'build/sag_graft.json',
          receivers='legacy'):
    if receivers not in ('legacy', 'by-type'):
        raise ValueError('receivers must be legacy or by-type')
    female, data_dir, output, report = map(Path, (female, data_dir, output, report))
    sources = [female, data_dir/'banc_888_meta.feather', data_dir/'banc_888_edgelist_simple_v3.feather']
    for target in (output, report):
        if any(target.exists() and os.path.samefile(target, source) for source in sources):
            raise ValueError('output aliases a source file')
    with np.load(female, allow_pickle=False) as z:
        archive = dict(z)
    w = sp.csr_matrix((archive['data'], archive['indices'], archive['indptr']), shape=tuple(archive['shape']))
    sag = np.flatnonzero(np.isin(archive['types'], ['AN_SMP_2', 'AN_FLA_SMP_2'])
                        if receivers == 'by-type' else archive['types'] == 'AN_SMP_2')
    if not sag.size:
        raise ValueError('no FAFB SAG cells')
    if w[:, sag].nnz:
        raise ValueError('FAFB SAG cells already have outputs')
    meta = pd.read_feather(sources[1])
    edges = pd.read_feather(sources[2], columns=['pre', 'post', 'count'])
    meta['banc_888_id'] = meta.banc_888_id.astype(np.int64)
    edges = edges.astype({'pre': np.int64, 'post': np.int64})
    names = meta.fafb_cell_type.fillna('')
    # The calibration graft uses the cross-map FAFB names only. BANC-only
    # cell_type labels describe the full output census, not this transplant.
    lookup = pd.Series(names.to_numpy(), index=meta.banc_888_id)
    if not lookup.index.is_unique:
        raise ValueError('BANC ids must be unique')
    outgoing = edges[edges.pre.isin(meta.loc[meta.cell_type == 'ANXXX983', 'banc_888_id'])].copy()
    outgoing['target_type'] = outgoing.post.map(lookup).fillna('')
    if receivers == 'by-type':
        outgoing['receiver_type'] = outgoing.pre.map(lookup)
        for name in outgoing.receiver_type.unique():
            if name not in ('AN_SMP_2', 'AN_FLA_SMP_2') or not np.any(archive['types'] == name):
                raise ValueError(f'no matching FAFB receiver for donor type {name}')
    counts = outgoing.groupby('target_type')['count'].sum()
    unnamed = int(counts.get('', 0))
    table, rr, cc, values = [], [], [], []
    for name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        if not name:
            continue
        targets = np.flatnonzero(archive['types'] == name)
        count = int(count)
        table.append(dict(target_type=name, synapses=count, fafb_cells=int(targets.size),
                          placed=count if targets.size else 0, missing=0 if targets.size else count))
        if targets.size and receivers == 'legacy':
            rr.extend(np.repeat(targets, sag.size))
            cc.extend(np.tile(sag, targets.size))
            values.extend([count * .275 / (targets.size * sag.size)] * (targets.size * sag.size))
        elif targets.size:
            by_receiver = outgoing.loc[outgoing.target_type == name].groupby('receiver_type')['count'].sum()
            for receiver, subtotal in by_receiver.items():
                source_cells = np.flatnonzero(archive['types'] == receiver)
                rr.extend(np.repeat(targets, source_cells.size))
                cc.extend(np.tile(source_cells, targets.size))
                values.extend([int(subtotal)*.275/(targets.size*source_cells.size)] * (targets.size*source_cells.size))
    graft = dict(sources=[dict(file=p.name, sha256=sha256(p)) for p in sources],
                 sag_cells=int(sag.size), synapses_placed=sum(r['placed'] for r in table),
                 synapses_missing=sum(r['missing'] for r in table),
                 unnamed_synapses_excluded=unnamed, total_outgoing_synapses=int(outgoing['count'].sum()),
                 missing_types=[r['target_type'] for r in table if r['missing']],
                 sign_choice=SIGN_CHOICE, synapse_mv=.275,
                 mapping='fafb_cell_type only (cross-map names); no count threshold; even split over target cells and SAG cells')
    if receivers == 'by-type':
        graft.update(receivers='by-type', mapping='donor fafb_cell_type -> identical receiver type; even split within matching receiver and target types; no count threshold')
    w = (w + sp.csr_matrix((np.asarray(values, np.float32), (rr, cc)), shape=w.shape)).tocsr()
    archive.update(data=w.data, indices=w.indices, indptr=w.indptr,
                   graft=np.array([json.dumps(graft, sort_keys=True)]))
    output.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output, **archive)
    report.write_text(json.dumps(dict(**graft, per_type=table), indent=2) + '\n', encoding='utf-8')
    print(f"SAG cells: {sag.size}; female cells: {w.shape[0]}")
    print(f"Named synapses placed: {graft['synapses_placed']}; missing: {graft['synapses_missing']}; unnamed excluded: {unnamed}")
    print('Top missing types: ' + ', '.join(f"{r['target_type']}={r['missing']}" for r in table if r['missing']))
    print(SIGN_CHOICE)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--female', type=Path, default=ROOT/'build/graph_female.npz')
    parser.add_argument('--data-dir', type=Path, default=ROOT/'data/banc')
    parser.add_argument('--output', type=Path, default=ROOT/'build/graph_female_sag.npz')
    parser.add_argument('--report', type=Path, default=ROOT/'build/sag_graft.json')
    parser.add_argument('--receivers', choices=('legacy', 'by-type'), default='legacy')
    args = parser.parse_args()
    build(args.female, args.data_dir, args.output, args.report, args.receivers)
