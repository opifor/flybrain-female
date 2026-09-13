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
        if slug in ('betting', 'music', 'hall'):
            assert text.count('<h2>her screen right now</h2>') == 1
            assert "whatever room she is in appears here; the record above is this room's" in text
            assert text.count('id="bet-stage"') == 1
            assert '<script src="show.js"></script>' in text
        positions.append(index.index(f'<h2>{declaration.name}</h2>'))
    assert positions == sorted(positions)
    assert 'class="vision"' in index
    assert 'Many more rooms are coming.' in index
    assert 'https://x.com/opifor' in index
    assert 'https://github.com/opifor/flybrain-female' in index
    assert 'in preparation' in index and 'beta · v1' in index
    for slug, declaration in pages.ROOMS:
        text = (tmp_path / f'{slug}.html').read_text(encoding='utf-8')
        assert '<a href="/rooms/">← her rooms</a>' in text
        assert 'data-back hidden' in text and 'history.back()' in text
        assert '<span class="paper">' not in text
        assert '<ol class="steps">' in text
        assert 'class="room-card record"' in text
    for slug in ('betting', 'music', 'tips'):
        text = (tmp_path / f'{slug}.html').read_text(encoding='utf-8')
        assert text.count('paper for now') == 1
        assert 'the plan is to take' in text and 'on-chain.' in text
    for card in re.findall(r'<article.*?</article>', index):
        if any(f'rooms/{slug}.html' in card for slug in ('betting', 'music', 'tips')):
            assert card.count('paper for now') == 1
    tips = (tmp_path / 'tips.html').read_text(encoding='utf-8')
    assert all(word in tips for word in ('post about her', 'rehearsal', 'nothing moves', '$HER'))
    assert 'beta · v1' in (tmp_path / 'music.html').read_text(encoding='utf-8')
    for path in tmp_path.iterdir():
        raw = path.read_bytes()
        text = raw.decode('utf-8')
        assert '(' + 'for now)' not in text
        assert not raw.startswith(b'\xef\xbb\xbf')
        assert 'Temp' not in text
        assert not re.search(r'\b[A-Za-z]:[\\/]|file://|/Users/|/home/', text)
        assert raw == (pages.WEB / 'rooms' / path.name).read_bytes()
