"""Publish the rooms' own rules beside their paper records."""
from html import escape
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import hall
import betroom
import musicroom
import tiproom

ROOMS = [('hall', hall.DECLARATION), ('betting', betroom.DECLARATION),
         ('music', musicroom.DECLARATION), ('tips', tiproom.DECLARATION)]
WEB = ROOT / 'site' / 'web'
LEDE = ('A real female fruit fly brain, 139,255 neurons, simulated live. '
        'She lives in a house of rooms and chooses where to go. '
        "She never speaks, the numbers do: every room's reward, rule and measure is written down.")
VISION = ('<section class="vision" aria-label="The house grows"><p>These rooms are the beginning. '
          'Many more rooms are coming. The house grows with what she can sense and what people build for her. '
          'You can propose a room to <a href="https://x.com/opifor">@opifor</a> or in the '
          '<a href="https://github.com/opifor/flybrain-female">GitHub repository</a>.</p></section>')


def items(lines):
    return ''.join(f'<li>{escape(line, quote=False)}</li>' for line in lines)


def generate(destination=WEB / 'rooms'):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    css = (WEB / 'rooms.css').read_text(encoding='utf-8')
    script = (WEB / 'rooms.js').read_text(encoding='utf-8')

    def write(slug, title, body, arena=False):
        way_back = ('<nav class="room-back" aria-label="Return"><a href="/rooms/">← her rooms</a>'
                    '<button type="button" data-back hidden>back</button></nav>') if slug != 'index' else ''
        page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<base href="../"><title>{escape(title)} · Female Flybrain</title>
<link rel="icon" href="/fly.png">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&amp;family=Archivo:wght@400;500;600&amp;family=IBM+Plex+Mono:wght@400;500&amp;display=swap">
<style>{css}</style></head><body>
<header><a href="/">Female Flybrain · Her Rooms</a><nav aria-label="Main">
<a href="/rooms/">rooms</a><a href="/brain.html">brain</a><a href="/story.html">story</a><a href="/show.html">show</a><a href="/#ca-text">$HER</a><a href="/watch.html">watch</a></nav></header>
<main>{way_back}<h1>{escape(title)}</h1><p class="lede">{LEDE}</p>{body}</main>
{'<script src="show.js"></script>' if arena else ''}<script>{script}</script></body></html>
'''
        (destination / f'{slug}.html').write_text(page, encoding='utf-8')

    cards = []
    for slug, declaration in ROOMS:
        d = declaration.public()
        seconds = d['cards']['refresh_seconds']
        period = {2: 'two seconds', 30: 'thirty seconds', 60: 'one minute'}.get(seconds, f'{seconds:g} seconds')
        e = lambda key: escape(d[key], quote=False)
        pending = '<p class="pending">in preparation</p>' if slug == 'tips' else ''
        if slug == 'music':
            pending = ('<p class="pending">beta · v1</p><p>The shelf holds test tracks from Wikimedia Commons '
                       'under CC licences; more are coming. Listener reactions will reach her through the stream chat later.</p>')
        badge = '<p class="badge" data-live="badge">relay offline</p>'
        cards.append(f'<article data-room="{e("path")}"><h2>{e("name")}</h2>{pending}<p>{e("commit_means")}</p><p>{e("reward_source")}</p>{badge}<a class="button" href="rooms/{slug}.html">how she plays here</a></article>')
        counters = ''.join(f'<div><dt>{key}</dt><dd data-live="{key}">—</dd></div>' for key in ('visits', 'looks', 'commits', 'nudges', 'sugar', 'shock'))
        promise = f'<p class="promise">{e("commit_means")}</p>' if slug == 'tips' else ''
        rehearsal = '<p class="pending">rehearsal · fixture wallets and practice thanks</p>' if slug == 'tips' else ''
        body = f'''<div data-room="{e('path')}"><p class="path">{e('path')}</p>{pending}{promise}
<section class="steps-section"><h2>how she plays here</h2>{rehearsal}<ol class="steps">{items(d['how'])}</ol></section>
<div class="columns"><section class="room-card"><h2>what a person chose</h2><ul>{items(d['chosen'])}</ul></section>
<section class="room-card"><h2>what is measured</h2><ul>{items(d['measured'])}</ul></section></div>
<section class="room-card sources"><h2>where the cards come from</h2><p>{escape(d['cards']['source'], quote=False)}. Refreshed every {period}.</p>
<h2>reward</h2><p>{e('reward_source')}</p></section>
<section class="room-card record"><h2>her paper (for now) record</h2>{badge}<dl class="counters">{counters}</dl>
<p>in room: <span data-live="in_room">—</span></p><p>last exit: <span data-live="last_exit">—</span></p>
<div data-live="book">Paper (for now) book unavailable.</div></section></div>'''
        arena = slug in ('betting', 'music', 'hall')
        if arena:
            body += ('<section><h2>her screen right now</h2>'
                     "<p>whatever room she is in appears here; the paper (for now) record above is this room's</p>"
                     '<div id="bet-stage"></div></section>')
        write(slug, d['name'], body, arena)
    write('index', 'Her Rooms', VISION + '<div class="rooms">' + ''.join(cards) + '</div>')


if __name__ == '__main__':
    generate()
