import importlib.util
from pathlib import Path

import numpy as np


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
    assert 'Compass EPG: <strong>1</strong> cells' in html
    assert 'L1 total: <strong>1</strong> cells' in html
    assert '&lt;script&gt;' in html and '<script>' not in html
    assert str(tmp_path) not in html and str(Path(__file__).parent) not in html
    assert not output.read_bytes().startswith(b'\xef\xbb\xbf')
    assert output.read_text(encoding='utf-8') == html
