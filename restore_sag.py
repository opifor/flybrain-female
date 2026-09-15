"""Restore the female's own SAG pairs removed by the transmitter-sign rule.

Both FAFB SAG types are included, retaining individual pre/post identities.
The +1 effect sign is a functional modelling choice, not a transmitter inference.
"""
import argparse
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

from graft_sag import sha256

ROOT = Path(__file__).parent
SAG_TYPES = ('AN_SMP_2', 'AN_FLA_SMP_2')
SIGN_CHOICE = (
    'CHOSEN: SAG sign +1 follows functional evidence: SAG activity promotes virgin '
    'receptivity and is silenced after mating (Feng, Palfreyman, Hasemeyer, Talsma, '
    'Dickson 2014 Neuron 83:135). The FAFB transmitter consensus is serotonin; '
    'the BANC prediction for the same types is dopamine. Neither prediction fixes '
    'the sign of the effect.')


def banc_table(report=ROOT/'build/sag_graft.json', data_dir=ROOT/'data/banc'):
    """Read the published type census, or recompute it without writing a graft."""
    if Path(report).is_file():
        data = json.loads(Path(report).read_text(encoding='utf-8'))
        if 'per_type' in data:
            rows = list(data['per_type'])
            rows.append(dict(target_type='', synapses=data.get('unnamed_synapses_excluded', 0)))
            return rows
    meta = pd.read_feather(Path(data_dir)/'banc_888_meta.feather')
    edges = pd.read_feather(Path(data_dir)/'banc_888_edgelist_simple_v3.feather')
    lookup = pd.Series(meta.fafb_cell_type.fillna('').to_numpy(), index=meta.banc_888_id.astype(np.int64))
    selected = edges[edges.pre.astype(np.int64).isin(meta.loc[meta.cell_type == 'ANXXX983', 'banc_888_id'].astype(np.int64))].copy()
    selected['target_type'] = selected.post.astype(np.int64).map(lookup).fillna('')
    return [dict(target_type=t, synapses=int(n)) for t, n in selected.groupby('target_type')['count'].sum().items()]


def comparison_table(own, banc):
    own_lookup = {r['target_type']: r for r in own}
    banc_lookup = {r['target_type']: r['synapses'] for r in banc}
    names = sorted(own_lookup.keys() | banc_lookup.keys(),
                   key=lambda t: (-own_lookup.get(t, {}).get('synapses', 0), t))
    lines = ['| Target type | Own AN_SMP_2 | Own AN_FLA_SMP_2 | Own total | BANC both donors |',
             '|---|---:|---:|---:|---:|']
    for t in names:
        r = own_lookup.get(t, {})
        by = r.get('by_source_type', {})
        lines.append(f"| {t or '(unnamed)'} | {by.get(SAG_TYPES[0], 0)} | {by.get(SAG_TYPES[1], 0)} | {r.get('synapses', 0)} | {banc_lookup.get(t, 0)} |")
    return '\n'.join(lines)


def build(female=ROOT/'build/graph_female.npz', connections=ROOT/'data/female/connections_princeton.csv.gz',
          output=ROOT/'build/graph_female_own_sag.npz', report=ROOT/'build/sag_restore.json',
          banc_report=ROOT/'build/sag_graft.json', banc_dir=ROOT/'data/banc'):
    female, connections, output, report = map(Path, (female, connections, output, report))
    for target in (output, report):
        if any(target.exists() and os.path.samefile(target, source) for source in (female, connections)):
            raise ValueError('output aliases a source file')
    if output.exists() and report.exists() and os.path.samefile(output, report):
        raise ValueError('graph and report alias each other')
    with np.load(female, allow_pickle=False) as z:
        archive = dict(z)
    w = sp.csr_matrix((archive['data'], archive['indices'], archive['indptr']), shape=tuple(archive['shape']))
    mask = np.isin(archive['types'], SAG_TYPES)
    if not mask.any():
        raise ValueError('no FAFB SAG cells')
    if w[:, mask].nnz:
        raise ValueError('FAFB SAG cells already have outputs')
    ids = pd.Index(archive['bodies'])
    if not ids.is_unique:
        raise ValueError('female cell ids must be unique')
    selected, row_count = [], 0
    for chunk in pd.read_csv(connections, usecols=['pre_root_id', 'post_root_id', 'syn_count'], chunksize=500_000):
        row_count += len(chunk)
        selected.append(chunk[chunk.pre_root_id.isin(ids[mask])])
    pairs = pd.concat(selected).groupby(['pre_root_id', 'post_root_id'], sort=False).syn_count.sum().reset_index()
    pairs['pre_idx'] = ids.get_indexer(pairs.pre_root_id)
    pairs['post_idx'] = ids.get_indexer(pairs.post_root_id)
    pairs['source_type'] = archive['types'][pairs.pre_idx]
    valid = (pairs.post_idx >= 0) & (pairs.syn_count >= 5)
    restored = pairs[valid].copy()
    restored['target_type'] = archive['types'][restored.post_idx]
    per_type = {}
    for t in SAG_TYPES:
        cells = []
        for i in np.flatnonzero(archive['types'] == t):
            raw = pairs[pairs.pre_idx == i]
            kept = restored[restored.pre_idx == i]
            cells.append(dict(root_id=int(ids[i]), exported_synapses=int(raw.syn_count.sum()),
                              restored_synapses=int(kept.syn_count.sum())))
        per_type[t] = dict(cell_count=len(cells), cells=cells,
                           exported_synapses=sum(c['exported_synapses'] for c in cells),
                           restored_synapses=sum(c['restored_synapses'] for c in cells))
        print(f"{t}: {len(cells)} cells; exported {per_type[t]['exported_synapses']}; restored {per_type[t]['restored_synapses']}; cells={cells}")
    empty = [t for t in SAG_TYPES if not per_type[t]['exported_synapses']]
    print('Empty outgoing types: ' + (', '.join(empty) or 'none'))
    table = []
    for t, rows in restored.groupby('target_type'):
        table.append(dict(target_type=t, synapses=int(rows.syn_count.sum()),
                          by_source_type={s: int(rows.loc[rows.source_type == s, 'syn_count'].sum()) for s in SAG_TYPES}))
    table.sort(key=lambda r: (-r['synapses'], r['target_type']))
    metadata = dict(sources=[dict(file=p.name, sha256=sha256(p)) for p in (connections, female)],
                    csv_rows=row_count, per_type=per_type, per_target_type=table,
                    empty_types=empty, synapses_restored=int(restored.syn_count.sum()),
                    excluded_synapses=int(pairs.loc[~valid, 'syn_count'].sum()),
                    floor=5, synapse_mv=.275, sign_choice=SIGN_CHOICE,
                    mapping='individual female pre/post ids; pair sum >= 5; post cell must be in graph')
    w = (w + sp.csr_matrix((restored.syn_count.to_numpy(dtype=np.float32)*np.float32(.275),
                           (restored.post_idx, restored.pre_idx)), shape=w.shape)).tocsr()
    # Preserve transmitter labels; sign records the explicit intervention on these cells.
    if 'sign' in archive:
        archive['sign'] = archive['sign'].copy()
        archive['sign'][mask] = 1
    archive.update(data=w.data, indices=w.indices, indptr=w.indptr,
                   restore=np.array([json.dumps(metadata, sort_keys=True)]))
    comparison = comparison_table(table, banc_table(banc_report, banc_dir))
    output.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output, **archive)
    report.write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    print(comparison)
    print(SIGN_CHOICE)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--female', type=Path, default=ROOT/'build/graph_female.npz')
    parser.add_argument('--connections', type=Path, default=ROOT/'data/female/connections_princeton.csv.gz')
    parser.add_argument('--output', type=Path, default=ROOT/'build/graph_female_own_sag.npz')
    parser.add_argument('--report', type=Path, default=ROOT/'build/sag_restore.json')
    args = parser.parse_args()
    build(args.female, args.connections, args.output, args.report)
