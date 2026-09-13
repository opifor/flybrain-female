import importlib.util
from pathlib import Path

import numpy as np
import pytest


def test_build_counts(tmp_path):
    spec = importlib.util.spec_from_file_location('brain_page', Path(__file__).parent / 'site/brain_page.py')
    page = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(page)
    graph = tmp_path / 'tiny.npz'
    np.savez(graph, types=['L1', 'L2', 'EPG', '<b>'],
             superclass=['optic', 'optic', 'central', '<script>'], sign=[1, -1, 1, 0],
             data=np.array([1.375, -2.75, 4.125]), indices=[0, 1, 2],
             indptr=[0, 1, 2, 3, 3], shape=[4, 4])
    output = tmp_path / 'brain.html'
    html = page.build(graph, output)
    assert '4 neurons · 3 signed connections · 30 synaptic contacts' in html
    assert '2 excitatory connections and 1 inhibitory connections' in html
    assert '20 excitatory and 10 inhibitory contacts' in html
    assert 'optic: <strong>2</strong> cells' in html
    assert 'compass: <strong>1</strong> cells' in html
    for name in ('taste', 'compass', 'clock', 'weather'):
        assert f'<h3>{name}</h3>' in html
    assert '1 cells that keep a heading' in html
    assert '<details><summary>how these were counted</summary>' in html
    doors = html.split('<section id="closed-doors">')[1].split('</section>')[0]
    cards, notes = doors.split('<details>')
    assert cards.count('<article>') == 4
    assert 'Matched type' not in cards and 'Labels found:' not in cards
    assert notes.count('Matched type') == notes.count('Labels found:') == 4
    assert 'L1 total: <strong>1</strong> cells' in html
    assert '&lt;script&gt;' in html and '<script>' not in html
    assert str(tmp_path) not in html and str(Path(__file__).parent) not in html
    assert not output.read_bytes().startswith(b'\xef\xbb\xbf')
    assert output.read_text(encoding='utf-8') == html


def test_published_brain_matches_graph(tmp_path):
    root = Path(__file__).resolve().parent
    graph = root / 'build/graph_female.npz'
    if not graph.exists():
        pytest.skip('The full graph is not present.')
    spec = importlib.util.spec_from_file_location('brain_page', root / 'site/brain_page.py')
    page = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(page)
    output = tmp_path / 'brain.html'
    page.build(graph, output)
    assert output.read_bytes() == (root / 'site/web/brain.html').read_bytes()
