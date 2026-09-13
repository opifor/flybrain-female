"""The published rules stay faithful to each room."""
import importlib.util
from html import unescape
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('rooms_pages', ROOT / 'site/rooms_pages.py')
pages = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pages)


def test_rooms_pages(tmp_path):
    pages.generate(tmp_path)
    assert sorted(p.name for p in tmp_path.iterdir()) == ['betting.html', 'hall.html', 'index.html', 'music.html', 'tips.html']
    index = (tmp_path / 'index.html').read_text(encoding='utf-8')
    positions = []
    for slug, declaration in pages.ROOMS:
        text = unescape((tmp_path / f'{slug}.html').read_text(encoding='utf-8'))
        for sentence in declaration.how:
            assert sentence in text
        assert declaration.reward_source in text
        positions.append(index.index(f'<h2>{declaration.name}</h2>'))
    assert positions == sorted(positions)
    for path in tmp_path.iterdir():
        raw = path.read_bytes()
        text = raw.decode('utf-8')
        assert not raw.startswith(b'\xef\xbb\xbf')
        assert 'Temp' not in text
        assert not re.search(r'\b[A-Za-z]:[\\/]|file://|/Users/|/home/', text)
        assert raw == (pages.WEB / 'rooms' / path.name).read_bytes()
