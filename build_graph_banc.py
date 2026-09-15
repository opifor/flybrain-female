"""Build the BANC v888 female brain and ventral nerve cord graph.

CHOSEN: exclude glia/not_a_neuron/trachea; retain edges with count >= 5.
Weight = count * 0.275 mV * presynaptic sign: acetylcholine +1,
gaba/glutamate -1, every other transmitter 0 (drop and count those edges).
Types use cell_type with empty/missing values falling back to fafb_cell_type.
No eyes: zero hex coordinates, has_hex False, eye none. Raw exc_scale 1.0,
click_hz 100, adapt False, back_scale 1.0. Modulatory wiring is not simulated.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

ROOT = Path(__file__).parent


def build(data_dir=ROOT / "data" / "banc", output=ROOT / "build" / "graph_banc.npz"):
    data_dir, output = Path(data_dir), Path(output)
    meta = pd.read_feather(data_dir / "banc_888_meta.feather")
    ann = meta.loc[~meta.super_class.isin(["glia", "not_a_neuron", "trachea"])].copy()
    bodies = ann.banc_888_id.to_numpy(dtype=np.int64)
    idx = pd.Index(bodies)
    if not idx.is_unique:
        raise ValueError("neuron ids must be unique")
    n = len(ann)

    def strings(column):
        return ann[column].fillna("").to_numpy().astype(str)

    types, fafb = strings("cell_type"), strings("fafb_cell_type")
    types = np.where(types == "", fafb, types)
    nt = strings("neurotransmitter_predicted").astype("U24")
    sign = pd.Series(nt).map({"acetylcholine": 1, "gaba": -1, "glutamate": -1}).fillna(0).to_numpy(np.float32)
    superclass, subclass = strings("super_class"), strings("cell_sub_class")
    effector = strings("body_part_effector")
    soma = ann.root_position.fillna("").str.split(",", expand=True).reindex(columns=range(3))
    soma = soma.apply(pd.to_numeric, errors="coerce").to_numpy(np.float32)
    edges = pd.read_feather(data_dir / "banc_888_edgelist_simple_v3.feather",
                           columns=["pre", "post", "count"])
    edges = edges.astype({"pre": np.int64, "post": np.int64})
    spsn = subclass == "sex_peptide_sensory_neuron"
    print("CHOSEN: neuron universe excludes glia/not_a_neuron/trachea; count >= 5")
    print("CHOSEN: count * 0.275 mV; acetylcholine +1; gaba/glutamate -1; all others 0/drop")
    print("CHOSEN: cell_type fallback fafb_cell_type; eye none; exc_scale 1; click_hz 100; adapt False; back_scale 1")
    print(f"neurons: {n:,}; excluded rows: {len(meta)-n:,}")
    print(f"SPSN cells: {spsn.sum()}; outgoing synapses (all disk edges): {edges.loc[edges.pre.isin(bodies[spsn]), 'count'].sum():,}")
    total = len(edges)
    edges = edges.loc[edges['count'] >= 5]
    threshold = total - len(edges)
    c, r = idx.get_indexer(edges.pre), idx.get_indexer(edges.post)
    valid = (c >= 0) & (r >= 0)
    outside = int((~valid).sum())
    counts = edges['count'].to_numpy(np.float32)[valid]
    c, r = c[valid], r[valid]
    keep = sign[c] != 0
    zero = int((~keep).sum())
    w = sp.csr_matrix((counts[keep] * np.float32(.275) * sign[c[keep]],
                       (r[keep], c[keep])), shape=(n, n), dtype=np.float32)
    w.sum_duplicates()
    print(f"edges on disk: {total:,}; kept rows: {keep.sum():,}; dropped: {threshold+outside+zero:,}")
    print(f"dropped below threshold: {threshold:,}; outside neurons: {outside:,}; zero sign: {zero:,}")
    print(f"CSR edges: {w.nnz:,}; positive: {(w.data > 0).sum():,}; negative: {(w.data < 0).sum():,}; zero: {(w.data == 0).sum()}")
    for label, pattern in (("pC1", r"^pC1[a-e]$"), ("DNp37", r"^DNp37$"),
                           ("oviDN", r"^(?:oviDNa_a|oviDNa_b|oviDNb)$"),
                           ("JO-A", r"^JO-A$"), ("JO-B", r"^JO-B$")):
        print(f"{label} cells: {pd.Series(types).str.match(pattern).sum()}")
    print("motor neurons per effector:", pd.Series(effector[superclass == "motor"]).value_counts().sort_index().to_dict())
    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output, data=w.data, indices=w.indices, indptr=w.indptr,
                        shape=w.shape, bodies=bodies, sign=sign, types=types,
                        fafb_types=fafb, superclass=superclass, subclass=subclass,
                        receptor=np.full(n, ""), fru=np.full(n, ""), nt=nt, nt_cell=nt,
                        hex1=np.zeros(n, np.int32), hex2=np.zeros(n, np.int32),
                        has_hex=np.zeros(n, bool), soma=soma,
                        soma_side=ann.side.map({"left": "L", "right": "R"}).fillna("").to_numpy().astype(str),
                        eye=np.array(["none"]), exc_scale=np.float32(1),
                        click_hz=np.float32(100), adapt=np.bool_(False), back_scale=np.float32(1),
                        region=strings("region"), cell_class=strings("cell_class"), effector=effector)
    print(f"wrote {output.name}")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data" / "banc")
    parser.add_argument("--output", type=Path, default=ROOT / "build" / "graph_banc.npz")
    args = parser.parse_args()
    build(args.data_dir, args.output)
