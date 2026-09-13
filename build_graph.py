"""
Build a signed, sparse connectivity matrix from the FlyEM male CNS connectome v1.0.

Inputs (CC-BY, storage.googleapis.com/flyem-male-cns):
  data/connectome-weights.feather      pre -> post synapse counts
  data/body-neurotransmitters.feather  consensus neurotransmitter per body
  data/body-annotations.feather        cell type / superclass per body

Output:
  build/graph.npz   W (CSR, mV per presynaptic spike), body index, sign, type codes

Sign convention follows Shiu et al. 2024 (Nature): acetylcholine excitatory,
GABA and glutamate inhibitory. Monoamines are modulatory in reality; they are
given zero fast weight here rather than being faked as excitatory.
"""
import argparse
import numpy as np
import pandas as pd
import scipy.sparse as sp
from pathlib import Path

MV_PER_SYNAPSE = 0.275  # Shiu et al. 2024
MIN_SYN = 3  # drop 1-2 synapse pairs: dominated by reconstruction noise

SIGN = {
    "acetylcholine": +1.0,
    "gaba": -1.0,
    "glutamate": -1.0,
    "dopamine": 0.0,
    "octopamine": 0.0,
    "serotonin": 0.0,
    "histamine": -1.0,  # histamine is inhibitory at fly photoreceptor synapses
    "unclear": 0.0,
    "unknown": 0.0,
}

ROOT = Path(__file__).parent
DATA = ROOT / "data"
BUILD = ROOT / "build"


def select_neurons(ann, brain_only=False):
    traced = ann.loc[(ann.status == "Traced") & (ann.statusLabel != "Glia")]
    dropped = traced.iloc[:0]
    if brain_only:
        mask = traced.superclass.fillna("").str.startswith("vnc_")
        dropped = traced.loc[mask].drop_duplicates("bodyId")
        traced = traced.loc[~mask]
    counts = dropped.groupby("superclass").bodyId.nunique().sort_index()
    return np.sort(traced.bodyId.unique()), counts


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--brain-only", action="store_true",
                    help="remove VNC neurons and write build/graph_brain.npz")
    args = ap.parse_args(argv)
    BUILD.mkdir(exist_ok=True)

    print(f"loading weights (keeping pairs with >= {MIN_SYN} synapses) ...")
    import pyarrow.feather as pf
    import pyarrow.compute as pc

    tbl = pf.read_table(DATA / "connectome-weights.feather")
    print(f"  {tbl.num_rows:,} pre->post pairs on disk")
    tbl = tbl.filter(pc.greater_equal(tbl.column("weight"), MIN_SYN))
    pre_a = tbl.column("body_pre").to_numpy()
    post_a = tbl.column("body_post").to_numpy()
    wt_a = tbl.column("weight").to_numpy().astype(np.float32)
    del tbl
    print(f"  {len(wt_a):,} pairs kept, {int(wt_a.sum()):,} synapses")

    print("loading annotations ...")
    ann = pd.read_feather(DATA / "body-annotations.feather")
    ann["t"] = ann["type"].fillna(ann["flywireType"]).fillna(ann["instance"]).fillna("")

    print("loading neurotransmitters ...")
    nt = pd.read_feather(DATA / "body-neurotransmitters.feather")
    nt = nt[["body", "consensus_nt"]].dropna(subset=["body"])
    nt = nt.drop_duplicates(subset=["body"])

    # The weights table is keyed on every EM segment, including millions of
    # unproofread fragments. Only 'Traced' bodies are actual reconstructed
    # neurons (165,122 of them - the number in the paper's headline).
    bodies, dropped = select_neurons(ann, args.brain_only)
    for superclass_name, count in dropped.items():
        print(f"  dropped {superclass_name}: {count:,}")
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

    output = BUILD / ("graph_brain.npz" if args.brain_only else "graph.npz")
    metadata = {}
    if args.brain_only:
        metadata = dict(brain_only=np.bool_(True),
                        dropped_superclasses=dropped.index.to_numpy(dtype=str),
                        dropped_superclass_counts=dropped.to_numpy(dtype=np.int64))
    np.savez_compressed(
        output,
        data=W.data, indices=W.indices, indptr=W.indptr, shape=W.shape,
        bodies=bodies, sign=sign, types=types, superclass=superclass,
        subclass=subclass, receptor=receptor, fru=fru, nt=nt_str, **metadata,
    )
    print(f"wrote {output}")
    if args.brain_only:
        print(f"{'Graph':<20} {'Neurons':>12} {'Nonzero edges':>16}")
        for name in ("graph", "graph_brain", "graph_female"):
            path = BUILD / f"{name}.npz"
            if path.exists():
                with np.load(path, allow_pickle=False) as graph:
                    print(f"{name:<20} {len(graph['bodies']):>12,} {len(graph['data']):>16,}")


if __name__ == "__main__":
    main()
