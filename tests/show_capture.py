"""Capture the viewer with a local relay fixture, without running the arena brain."""
import argparse
import json
import math
import re
import subprocess
import shutil
import tempfile
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
OUT = Path.home() / 'AppData/Local/Temp'
CARDS = [dict(market_id=str(i), shelf='fast', slot=i, end_at=time.time() + 3600,
              question=q, yes_price=p, category='crypto') for i, (q, p) in enumerate([
    ('Bitcoin Up or Down - September 13, 1:25AM-1:30AM ET', .36),
    ('Ethereum Up or Down - September 13, 1:25AM-1:30AM ET', .58),
    ('Bitcoin Up or Down - September 13, 1:15AM-1:30AM ET', .42),
    ('Ethereum Up or Down - September 13, 1:15AM-1:30AM ET', .63),
    ('Solana Up or Down - September 13, 1:15AM-1:30AM ET', .47),
    ('XRP Up or Down - September 13, 1:15AM-1:30AM ET', .51)])]
DATA = {'events': [], 'learning': [], 'open': [], 'settled': [], 'live': True, 'cards': CARDS}
DATA['gaze'] = dict(token='0', steps=1, needed=2, drive=.35, side='yes',
                    smell=['earth', 'rain'], since=time.time(), blind=0)
DATA['last_intent'] = dict(token='0', side='YES', drive=.35, at=time.time(), status='booked', reason=None)
MUSIC_TRACK = dict(id='123', title='Rain', artist='River', license='CC BY 3.0',
                   page='https://commons.wikimedia.org/wiki/File:Rain.ogg', duration=60, file='123.ogg')
DATA['music'] = dict(in_room=False, nudges=2, book=dict(now_playing=None, plays=[], reactions={}))
FRAME = b''
SEQ = 0
START = time.monotonic()
LIFE = dict(
    since='2026-09-13T04:07:21Z',
    who=['her. a female fruit fly brain, 139,255 neurons. FlyWire FAFB v783.',
         'she lives in her rooms: a betting room, a music room, more coming.',
         'she never speaks. the numbers do.', 'every room is paper. no real money, no real bets.',
         'the first fly streamer on kick.'],
    now=dict(room='paper room', doing='looking at ETH 15m', spikes=1312400,
             turn='left', sugar_10m=3, shock_10m=1, balance=106.2, today_delta=6.2),
    hour=dict(rooms=6, plays=2, bets=4, sold=1, won=2, lost=1, pnl=5.8, pages=12, clicks=3,
              scrolls=20, sugar=3, shock=1),
    feed=[dict(at='07:02:11', kind='bet.won', text='eth 15m won +5.20 · sugar'),
          dict(at='07:01:40', kind='page.scroll', text='she scrolled down on arxiv.org'),
          dict(at='07:00:12', kind='bet.fill', text='she bought ETH up')])
STREAM_FRAME = Path(r'build\shots\stream_frame3.png')


def fixture():
    global SEQ
    SEQ += 1
    t = time.monotonic() - START
    return dict(seq=SEQ, live=DATA['live'], age=0, url='http://127.0.0.1:4660/betroom',
                rooms={'/musicroom': DATA['music'], '/hall': {'nudges': 3}, '/betroom': {'nudges': 4}},
                **({'life': LIFE} if DATA.get('with_life', True) else {}),
                cursor=dict(x=.3 + .16 * math.sin(t * .8), y=.43 + .15 * math.cos(t * .7)),
                hz=dict(steer_L=150 + 130 * math.sin(t), steer_R=150 - 130 * math.sin(t),
                        fwd_L=100, fwd_R=200, stop=0),
                neural=dict(firing=8000 + 6500 * math.sin(t), spikes_per_sec=1300000 + 600000 * math.sin(t),
                            out=dict(forward=DATA.get('forward',.7))),
                betroom=dict(balance=104.2, win_count=1, loss_count=0,
                             open_bets=DATA['open'], settled_bets=DATA['settled']),
                betting=dict(in_room=True, bookie=dict(ok=True, at=time.time()), cards=DATA['cards'],
                             gaze=DATA['gaze'], last_intent=DATA['last_intent'],
                             events=DATA['events'], learning=dict(last=DATA['learning'])))


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        path = urlparse(self.path).path
        if path.startswith('/music/') and path.endswith('.ogg'):
            recording = Path(self.translate_path(self.path))
            if not recording.is_file():
                self.send_error(404)
                return
            body = recording.read_bytes()
            size = len(body)
            requested = self.headers.get('Range')
            match = re.fullmatch(r'bytes=(\d+)-(\d*)', requested or '')
            start, end = 0, size - 1
            if requested:
                if not match or int(match[1]) >= size:
                    self.send_response(416)
                    self.send_header('Content-Range', f'bytes */{size}')
                    self.end_headers()
                    return
                start = int(match[1])
                end = min(int(match[2]), end) if match[2] else end
            # A seek needs byte ranges, including the tail that carries Ogg duration.
            self.send_response(206 if requested else 200)
            self.send_header('Content-Type', 'audio/ogg')
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Content-Length', str(end - start + 1))
            if requested:
                self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
            self.end_headers()
            self.wfile.write(body[start:end + 1])
            return
        if path == '/state':
            body, mime = json.dumps(fixture()).encode(), 'application/json'
        elif path == '/frame.jpg':
            body, mime = FRAME, 'image/jpeg'
        elif path == '/arena':
            body, mime = (ROOT / 'web/betroom.html').read_bytes(), 'text/html'
        elif path == '/betroom/board.json':
            body, mime = json.dumps(dict(cards=CARDS)).encode(), 'application/json'
        elif path == '/betroom/public.json':
            body, mime = b'{"markets":{},"open_bets":[]}', 'application/json'
        elif path == '/api/state':
            body, mime = b'{"ok":true,"launched":false,"block":123}', 'application/json'
        else:
            return super().do_GET()
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)


INSTRUMENT = """(() => {
  window.soundContexts = []; window.notes = []; window.ink = [];
  window.seeks = [];
  window.musicStarts = [];
  const play = HTMLMediaElement.prototype.play;
  HTMLMediaElement.prototype.play = function(...a) {
    window.musicStarts.push(performance.now()); return play.apply(this, a);
  };
  window.gainRamps = [];
  const ramp = AudioParam.prototype.linearRampToValueAtTime;
  AudioParam.prototype.linearRampToValueAtTime = function(value, at) {
    window.gainRamps.push({param:this, value, at, now:window.soundContexts[0]?.currentTime});
    return ramp.call(this, value, at);
  };
  const time = Object.getOwnPropertyDescriptor(HTMLMediaElement.prototype, 'currentTime');
  Object.defineProperty(HTMLMediaElement.prototype, 'currentTime', {
    get: time.get, set(value) { window.seeks.push({value, at: performance.now()}); time.set.call(this, value); }
  });
  const clips = new WeakMap(), stacks = new WeakMap(), paths = new WeakMap();
  for (const method of ['save', 'restore', 'beginPath', 'rect', 'clip']) {
    const original = CanvasRenderingContext2D.prototype[method];
    CanvasRenderingContext2D.prototype[method] = function(...a) {
      if (method === 'save') { const stack = stacks.get(this) || []; stack.push(clips.get(this)); stacks.set(this, stack); }
      if (method === 'restore') clips.set(this, stacks.get(this)?.pop());
      if (method === 'beginPath') paths.delete(this);
      if (method === 'rect') paths.set(this, a);
      if (method === 'clip') clips.set(this, paths.get(this));
      return original.apply(this, a);
    };
  }
  const Native = window.AudioContext;
  window.AudioContext = class extends Native { constructor(...a) { super(...a); window.soundContexts.push(this); } };
  const mediaSource = AudioContext.prototype.createMediaElementSource;
  AudioContext.prototype.createMediaElementSource = function(...a) {
    window.musicSource = mediaSource.apply(this, a); return window.musicSource;
  };
  const connect = AudioNode.prototype.connect;
  window.soundEdges = [];
  AudioNode.prototype.connect = function(target, ...a) {
    window.soundEdges.push([this, target]); return connect.call(this, target, ...a);
  };
  const scheduled = new WeakMap(), setValue = AudioParam.prototype.setValueAtTime;
  AudioParam.prototype.setValueAtTime = function(value, ...a) { scheduled.set(this,value); return setValue.call(this,value,...a); };
  const start = OscillatorNode.prototype.start;
  OscillatorNode.prototype.start = function(...a) { window.notes.push(scheduled.get(this.frequency) ?? this.frequency.value); return start.apply(this,a); };
  for (const method of ['fillText','fillRect','strokeRect','ellipse','arc']) {
    const original = CanvasRenderingContext2D.prototype[method];
    CanvasRenderingContext2D.prototype[method] = function(...a) {
      if (this.canvas.getAttribute('aria-label') === 'Her brain, path and paper bets') {
        window.ink.push({method, args:a, fill:this.fillStyle, stroke:this.strokeStyle, alpha:this.globalAlpha,
          font:this.font, clip:clips.get(this), transform:Array.from(this.getTransform().toFloat64Array()), align:this.textAlign,
          width:method === 'fillText' ? Math.min(this.measureText(a[0]).width, a[3] ?? Infinity) : null});
        if (window.ink.length > 3000) window.ink.splice(0,1000);
      }
      return original.apply(this,a);
    };
  }
})();"""


def check_gaze(page, checks):
    labels = "['NO','YES','smells like: earth · rain'].every(t => window.ink.some(e => e.method === 'fillText' && e.args[0] === t))"
    arc = "e.method === 'arc' && e.args[0] === 82 && e.args[1] === 92 && e.args[2] === 30 && e.stroke === '#ff79b0'"
    stamp = "e.method === 'fillText' && e.args[0] === 'YES' && e.font.startsWith('bold 72px')"
    page.wait_for_function(labels)
    page.wait_for_function(f"window.ink.some(e => {arc} && e.args[4] > -Math.PI / 2 && e.args[4] < Math.PI / 2)")
    assert not page.evaluate(f"window.ink.some(e => {stamp})")
    DATA['last_intent'] = {**DATA['last_intent'], 'at': time.time() + 1}
    page.evaluate('window.ink = []')
    page.wait_for_function(f"window.ink.some(e => {stamp} && e.alpha === 1)")
    page.wait_for_function(f"window.ink.some(e => {arc} && e.args[4] === Math.PI * 1.5)")
    drawing = page.evaluate("window.ink.filter(e => e.method === 'fillText' && (['NO','YES','refused'].includes(e.args[0]) || e.args[0].startsWith('smells like')))")
    assert drawing
    for entry in drawing:
        assert entry['clip'] == [56, 48, 368, 336]
        a, c, x = [entry['transform'][i] for i in [0, 4, 12]]
        left = entry['args'][1] - (entry['width'] / 2 if entry['align'] == 'center' else 0)
        bounds = [a * edge + c * entry['args'][2] + x for edge in [left, left + entry['width']]]
        assert min(bounds) >= 56 and max(bounds) <= 424, entry
        if entry['args'][0].startswith('smells like'):
            assert entry['args'][1:3] == [76, 358] and entry['width'] <= 328
        elif not entry['font'].startswith('bold'):
            assert entry['args'][2] == 322
    page.screenshot(path=str(STREAM_FRAME.with_name('gaze_frame.png')))
    page.wait_for_timeout(1250)
    page.evaluate('window.ink = []')
    page.wait_for_function(labels)
    assert not page.evaluate(f"window.ink.some(e => {stamp})")
    for status in ['refused', 'unreachable']:
        DATA['last_intent'] = {**DATA['last_intent'], 'at': DATA['last_intent']['at'] + 1, 'status': status}
        page.evaluate('window.ink = []')
        page.wait_for_function("window.ink.some(e => e.method === 'fillText' && e.args[0] === 'refused')")
        assert not page.evaluate(f"window.ink.some(e => {stamp})")
    gaze = DATA['gaze']
    DATA['gaze'] = None
    DATA['last_intent'] = {**DATA['last_intent'], 'at': DATA['last_intent']['at'] + 1, 'side': 'none'}
    page.wait_for_function('window.received?.betting.gaze === null && window.received?.betting.last_intent.side === "none"')
    page.evaluate('window.ink = []')
    page.wait_for_timeout(100)
    assert not page.evaluate(f"window.ink.some(e => {arc})")
    assert not page.evaluate("window.ink.some(e => e.method === 'fillText' && (e.args[0].startsWith('smells like') || e.args[0] === 'NONE'))")
    DATA['gaze'] = {**gaze, 'drive': None, 'side': 'none', 'smell': []}
    page.wait_for_function("window.ink.some(e => e.method === 'fillText' && e.args[0] === 'smells like nothing she knows')")
    DATA['gaze'] = gaze
    checks.append('Gaze arc, scale and smell render; only a new booked receipt stamps; refusals, silence and empty smells stay distinct.')


def check_broadcast(page, checks, errors):
    from playwright.sync_api import expect

    expect(page.get_by_role('button', name='what she sees', include_hidden=True)).to_be_hidden()
    captions = ['who', 'now', 'feed', 'last hour', 'paper']
    page.wait_for_function("labels => labels.every(label => window.ink.some(e => e.method === 'fillText' && e.args[0] === label))", arg=captions)
    page.wait_for_function("window.ink.some(e => e.method === 'fillText' && e.args[0] === 'eth 15m won +5.20 · sugar')")
    page.wait_for_function("window.ink.some(e => e.method === 'fillText' && e.args[0] === '1,312,400')")
    assert abs(page.locator('img').bounding_box()['width'] - 1280) < 1
    assert round(page.locator('img').bounding_box()['height']) == 800
    STREAM_FRAME.parent.mkdir(parents=True, exist_ok=True)
    page.wait_for_function("window.ink.some(e => e.method === 'fillText' && e.args[0] === 'eth 15m won +5.20 · sugar' && e.args[2] === 550 && e.alpha === 1)")
    short = dict(at='07:02:11', kind='page.click', text='she opened a page about fruit flies ' + 'w' * 12)
    assert len(short['text']) == 48
    LIFE['feed'].insert(0, short)
    page.evaluate('window.ink = []')
    page.wait_for_function("line => window.ink.some(e => e.method === 'fillText' && e.args[0] === line && e.args[1] === 1416 && e.args[2] === 550 && e.alpha === 1 && e.font.startsWith('22px') && e.args[1] + e.width <= 1896)", arg=short['text'])
    tiles = ['rooms', 'plays', 'bets', 'won', 'lost', 'paper p&l', 'sugar', 'shock', 'nudges']
    positions = page.evaluate("labels => labels.map(label => window.ink.findLast(e => e.method === 'fillText' && e.args[0] === label && [860,965].includes(e.args[2])))", tiles)
    assert all(positions)
    for i, entry in enumerate(positions):
        assert entry['args'][1:3] == [24 + i % 5 * 124, 860 if i < 5 else 965]
        assert entry['width'] < 124
        if i % 5:
            previous = positions[i - 1]
            assert previous['args'][1] + previous['width'] < entry['args'][1]
    assert positions[5]['args'][0] == 'paper p&l'
    assert page.evaluate("window.ink.some(e => e.method === 'fillText' && e.args[0] === '9' && e.args[1] === 396 && e.args[2] === 1003)")
    assert page.evaluate("window.ink.some(e => e.method === 'fillText' && e.args[0] === 'her rooms · all paper ·') && window.ink.some(e => e.method === 'fillText' && /^femaleflybrain.com · UTC \\d{2}:\\d{2}:\\d{2}$/.test(e.args[0]))")
    page.wait_for_function("window.ink.some(e => e.method === 'fillRect' && e.args[0] === 1298 && e.args[1] === 526 && e.args[2] === 2 && e.alpha > 0 && e.alpha < 0.6)")
    page.screenshot(path=str(STREAM_FRAME))
    page.wait_for_timeout(5100)
    page.evaluate('window.ink = []')
    page.wait_for_function("window.ink.some(e => e.method === 'fillRect' && e.args[0] === 1298 && e.args[2] === 2 && e.alpha === 0)")
    for length, font in [(30, 30), (36, 26), (42, 22), (80, 22)]:
        short['text'] = 'w' * length
        page.evaluate('window.ink = []')
        page.wait_for_function("([length, font]) => window.ink.some(e => e.method === 'fillText' && e.args[1] === 664 && e.args[2] === 900 && e.font.startsWith(font + 'px') && (length === 80 ? e.args[0].endsWith('…') : e.args[0] === 'w'.repeat(length)) && e.width <= 592)", arg=[length, font])
    LIFE['feed'].pop(0)
    muted = page.context.new_page()
    muted.goto(page.url + '&mute=1')
    expect(muted.get_by_role('button', name='what she sees', include_hidden=True)).to_be_hidden()
    assert muted.locator('button:visible, input[type=range]:visible').count() == 0
    muted.close()
    incoming = dict(at='07:03:00', kind='page.click', text='she opened the next page ' + 'x' * 100)
    LIFE['feed'].insert(0, incoming)
    page.evaluate('window.ink = []')
    page.wait_for_function("window.ink.some(e => e.method === 'fillText' && e.args[0].startsWith('she opened') && e.args[0].endsWith('…') && e.args[1] === 1416 && e.args[2] < 550 && e.alpha > 0 && e.alpha < 1)")
    page.wait_for_function("window.ink.some(e => e.method === 'fillText' && e.args[0].startsWith('she opened') && e.args[2] === 550 && e.alpha === 1)")
    LIFE['feed'].pop(0)
    DATA['with_life'] = False
    page.wait_for_function('window.received && !("life" in window.received)')
    page.evaluate('window.ink = []')
    page.wait_for_function("labels => labels.every(label => window.ink.some(e => e.method === 'fillText' && e.args[0] === label))", arg=captions + ['—', 'in the —', 'paper balance — usdc'])
    assert not errors, errors
    DATA['with_life'] = True
    page.wait_for_function('window.received?.life?.now.spikes === 1312400')
    strip = page.context.new_page()
    strip.on('pageerror', lambda e: errors.append(str(e)))
    strip.goto(page.url.replace('/show.html', '/strip.html'))
    strip.wait_for_function("document.getElementById('strip').textContent === 'eth 15m won +5.20 · sugar'")
    DATA['with_life'] = False
    strip.wait_for_function("document.getElementById('strip').textContent.startsWith('Balance 104.20 USDC')")
    strip.close()
    DATA['with_life'] = True
    page.wait_for_function('window.received?.life?.now.spikes === 1312400')
    checks.append('Broadcast captions, feed, paper tag and arena bounds render; absent life draws placeholders without page errors.')
    checks.append('Incoming feed slides and ellipsises; the transparent strip prefers life and retains its fallback.')
    checks.append('48 characters fit beside the clock; nine tiles do not overlap; controls hide; strip type steps down; newest marker fades.')


def capture(port):
    global FRAME
    origin = f'http://127.0.0.1:{port}'
    static = tempfile.TemporaryDirectory(prefix='show-music-')
    static_dir = Path(static.name)
    for path in (ROOT / 'site/web').iterdir():
        if path.is_file():
            shutil.copy2(path, static_dir / path.name)
    music_dir = static_dir / 'music'
    music_dir.mkdir()
    subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-f', 'lavfi', '-i',
                    'sine=frequency=220:duration=60', '-c:a', 'libvorbis', '-q:a', '3',
                    str(music_dir / '123.ogg')], check=True)
    shutil.copy2(music_dir / '123.ogg', music_dir / '124.ogg')
    (music_dir / 'catalog.json').write_text(json.dumps([MUSIC_TRACK, {**MUSIC_TRACK, 'id': '124'}]), encoding='utf-8')
    server = ThreadingHTTPServer(('127.0.0.1', port), partial(Handler, directory=str(static_dir)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    checks = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        arena = browser.new_page(viewport=dict(width=1280, height=800))
        arena.goto(origin + '/arena')
        arena.locator('.card:not(.empty)').nth(5).wait_for()
        assert arena.locator('.question').first.evaluate("e => { const r = document.createRange(); r.selectNodeContents(e); return r.getClientRects().length; }") == 3
        FRAME = arena.screenshot(type='jpeg', quality=90)
        (OUT / 'flybrain-show-frame.jpg').write_bytes(FRAME)
        arena.close()
        context = browser.new_context(viewport=dict(width=1920, height=1080),
                                      record_video_dir=str(OUT / 'flybrain-show-video'),
                                      record_video_size=dict(width=1920, height=1080))
        context.add_init_script(INSTRUMENT)
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(origin + '/show.html?relay=' + origin)
        page.wait_for_function("document.querySelector('img').naturalWidth === 1280")
        page.evaluate("() => { window.paperShow.onState(d => window.received = d); }")
        check_gaze(page, checks)
        check_broadcast(page, checks, errors)
        check_music(page, checks)
        page.evaluate("() => { const container = document.querySelector('canvas').parentElement; window.paperShow.destroy(); window.soundContexts = []; window.notes = []; window.ink = []; window.paperShow = window.mountShow(container, {audio:true}); window.paperShow.onState(d => window.received = d); }")
        page.get_by_role('button', name='what she sees', exact=True).wait_for(state='visible')
        page.mouse.click(20,20)
        page.wait_for_function("window.soundContexts[0]?.state === 'running'")
        page.wait_for_function("[...document.querySelectorAll('span')].find(e=>e.textContent==='click for sound').hidden")
        checks.append('Audio starts on a gesture and removes the hint.')
        page.wait_for_timeout(1800)
        started = time.monotonic()
        buy = dict(kind='fill', id=1, seq=1, market_id='0', side='YES', price='9/25', stake_cents='360',
                   shares='10', look_id='buy-1', question=CARDS[0]['question'])

        def wait_state(event_seq=None, learning_seq=None):
            if event_seq is not None:
                page.wait_for_function('(seq) => window.received?.betting.events.some(e=>e.seq===seq)', arg=event_seq)
            if learning_seq is not None:
                page.wait_for_function('(seq) => window.received?.betting.learning.last.some(e=>e.seq===seq)', arg=learning_seq)

        for index, name in enumerate(['trail','bet','sell','sugar','shock','settled','retina']):
            due = started + index * 2.7
            page.wait_for_timeout(max(1, (due-time.monotonic())*1000))
            now = time.time()
            before = page.evaluate('window.notes.length')
            if name == 'bet':
                buy['at'] = now; DATA['open'] = [buy.copy()]; DATA['events'].insert(0,buy.copy()); wait_state(1)
            elif name == 'sell':
                sold = dict(kind='fill', action='sell', id=2, seq=2, position_id=1, buy_look_id='buy-1',
                            look_id='sell-2', market_id='0', side='YES', exit_price='22/25', pnl_cents='520', at=now)
                DATA['settled'] = [{**buy, **sold, 'id':1, 'kind':'sold', 'look_id':'buy-1'}]
                DATA['open'] = []; DATA['events'].insert(0,sold); wait_state(2)
            elif name in ('sugar','shock'):
                seq = 3 if name == 'sugar' else 4
                DATA['learning'].insert(0,dict(seq=seq, at=now, market_id='1' if seq==3 else '2', sign=1 if seq==3 else -1, status='delivered', eligible=[1,2]))
                wait_state(learning_seq=seq)
            elif name == 'settled':
                settled = dict(kind='settled', id=5, seq=5, market_id='3', side='YES', outcome='YES',
                               payout_cents='1000', at=now, look_id='buy-5')
                DATA['settled'].append({**settled, 'price':.36, 'stake_cents':'360', 'won':True})
                DATA['events'].insert(0,settled); wait_state(5)
            elif name == 'retina':
                page.get_by_role('button', name='what she sees', exact=True).click()
                page.wait_for_function("window.ink.some(e=>e.method==='fillText' && e.args[0]==='what she sees')")
            page.wait_for_timeout(220 if name == 'shock' else 380)
            if name == 'sell':
                assert page.evaluate("window.ink.some(e=>e.method==='fillText' && e.args[0].includes('0.36 to 0.88 / +5.20'))")
                checks.append('Sell joins its original entry and draws 0.36 to 0.88 / +5.20.')
            if name == 'settled':
                assert page.evaluate("window.ink.some(e=>e.method==='fillText' && e.args[0].includes('settled / 0.36 to 1.00 / +6.40'))")
                checks.append('Settlement joins the book record and draws settled with its payout.')
            if name in ('bet','sell','sugar','shock','settled'):
                expected = dict(bet=1,sell=2,sugar=3,shock=1,settled=3)[name]
                assert page.evaluate('window.notes.length') - before == expected, name
                checks.append(f'{name}: {expected} synthesized notes, one event delivery.')
            page.screenshot(path=str(OUT / f'flybrain-show-{name}.png'))
            if name == 'bet':
                page.wait_for_timeout(1200)
                assert page.evaluate('window.notes.length') - before == 1
                checks.append('A repeated buy event does not replay its motif.')
        page.wait_for_timeout(max(1,(started+20-time.monotonic())*1000))
        video = page.video
        context.close()
        raw_video = OUT / 'flybrain-show-raw.webm'
        video.save_as(str(raw_video))
        duration = float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration',
                                                  '-of','default=noprint_wrappers=1:nokey=1',str(raw_video)]))
        subprocess.run(['ffmpeg','-y','-v','error','-ss',str(max(0,duration-20)),'-i',str(raw_video),
                        '-t','20','-an','-c:v','libvpx','-b:v','3M',str(OUT/'flybrain-show-20s.webm')],check=True)

        for width in [1280,400]:
            panel = browser.new_page(viewport=dict(width=width,height=1000))
            panel.add_init_script(INSTRUMENT)
            panel.on('pageerror', lambda e: errors.append(str(e)))
            panel.route('https://**/*', lambda route: route.abort())
            panel.goto(origin+'/index.html?relay='+origin+'#betting')
            panel.locator('#bet-stage canvas').wait_for()
            panel.wait_for_function("document.getElementById('bet-frame').naturalWidth===1280")
            panel.wait_for_function("window.ink.some(e => e.method === 'fillText' && e.args[0] === 'smells like: earth · rain')")
            panel.locator('#betting').scroll_into_view_if_needed()
            panel.wait_for_timeout(700)
            assert panel.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
            assert panel.locator('#bet-stage canvas').bounding_box()['width'] > 100
            panel.screenshot(path=str(OUT / f'flybrain-show-panel-{width}.png'))
            checks.append(f'Betting panel at {width}px has an overlay and no page overflow.')
            panel.close()

        check_entry(browser, origin, checks, errors)

        muted = browser.new_page(viewport=dict(width=1920,height=1080))
        muted.add_init_script(INSTRUMENT)
        muted.goto(origin+'/show.html?mute=1&relay='+origin)
        muted.wait_for_function("document.querySelector('img').naturalWidth===1280")
        muted.mouse.click(20,20)
        assert muted.evaluate('window.soundContexts.length') == 0
        checks.append('mute=1 creates no audio context, including after a click.')
        DATA['live'] = False
        muted.wait_for_function("window.ink.some(e=>e.method==='fillText' && e.args[0]==='Waiting for the relay.')")
        muted.screenshot(path=str(OUT/'flybrain-show-offline.png'))
        checks.append('Offline state covers the stale frame and removes the live show.')
        assert not errors, errors
        browser.close()
        autoplay = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        obs = autoplay.new_page()
        obs.add_init_script(INSTRUMENT)
        DATA['live'] = True
        DATA['music'] = dict(in_room=True, book=dict(now_playing=dict(track_id='123', title='Rain',
                              started_at=time.time() - 12, duration=60)))
        obs.goto(origin+'/show.html?relay='+origin)
        obs.wait_for_function("window.soundContexts[0]?.state === 'running'")
        obs.wait_for_function("[...document.querySelectorAll('span')].find(e=>e.textContent==='click for sound').hidden")
        obs.wait_for_function("(() => { const a = document.querySelector('audio'); return a && !a.paused && a.currentTime > 10; })()")
        DATA['music']['in_room'] = False
        checks.append('Autoplay-permitted browser starts audio without a gesture and hides the hint.')
        obs.evaluate("() => { window.paperShow.onState(d => window.received = d); }")
        DATA['events'] = []; DATA['learning'] = []
        obs.wait_for_function('window.received?.betting.events.length===0')
        before = obs.evaluate('window.notes.length')
        loss = dict(kind='fill',action='sell',id=6,seq=6,position_id=1,buy_look_id='buy-1',
                    look_id='sell-6',market_id='0',side='YES',exit_price='1/5',pnl_cents='-160',at=time.time())
        DATA['events'] = [loss]
        obs.wait_for_function("window.ink.some(e=>e.method==='fillText' && e.args[0].includes('0.36 to 0.20 / -1.60'))")
        assert obs.evaluate('window.notes.slice(-2)') == [392,261.63]
        assert obs.evaluate('window.notes.length')-before == 2
        checks.append('Loss sell shows the entry and exit, negative PnL, and descending notes.')
        DATA['events'] = []
        obs.wait_for_function('window.received?.betting.events.length===0')
        obs.wait_for_timeout(2300)
        obs.evaluate('window.ink = []')
        before = obs.evaluate('window.notes.length')
        loss_settled = dict(kind='settled',id=7,seq=7,market_id='4',side='YES',outcome='NO',
                            payout_cents='0',at=time.time(),look_id='buy-7')
        DATA['settled'].append({**loss_settled,'price':.36,'stake_cents':'360','won':False})
        DATA['events'] = [loss_settled]
        DATA['learning'] = [dict(kind='shock',seq=7,at=time.time(),market_id='4',sign=-1,status='delivered',eligible=[1])]
        obs.wait_for_function("window.ink.some(e=>e.method==='fillText' && e.args[0].includes('settled / 0.36 to 0.00 / -3.60'))")
        obs.wait_for_timeout(1200)
        assert obs.evaluate('window.notes.length')-before == 1
        checks.append('Losing settlement has one low motif with a tail; its learning receipt does not repeat it.')
        DATA['cards'] = [{**c,'market_id':'99'} if c['slot']==0 else c for c in CARDS]
        DATA['events'] = [{**buy,'id':8,'seq':8,'at':time.time()}]
        DATA['open'] = [buy]
        obs.wait_for_function('window.received?.betting.events.some(e=>e.seq===8)')
        obs.evaluate('window.ink = []')
        obs.wait_for_timeout(300)
        assert not obs.evaluate("window.ink.some(e=>e.method==='fillRect' && e.args[0]===56 && e.args[1]===48 && e.args[2]===368)")
        assert not obs.evaluate("window.ink.some(e=>e.method==='arc' && e.args[0]===402 && e.args[1]===70)")
        checks.append('An old market cannot flash or leave a chip on a replacement card in its slot.')
        DATA['forward'] = 0
        obs.wait_for_function('window.received?.neural.out.forward===0')
        obs.evaluate('window.ink = []')
        obs.wait_for_timeout(300)
        wings = obs.evaluate("window.ink.filter(e=>e.method==='ellipse' && e.args[2]===17)")
        assert wings and all(e['args'][3] == 3 for e in wings)
        checks.append('A stop closes the wings even when raw forward rates are nonzero.')
        autoplay.close()
    server.shutdown()
    server.server_close()
    static.cleanup()
    (OUT/'flybrain-show-browser-checks.json').write_text(json.dumps(dict(checks=checks,errors=errors),indent=2),encoding='utf-8')
    print(f'{len(checks)} browser checks passed; 0 page errors')
    print(OUT/'flybrain-show-20s.webm')


def check_entry(browser, origin, checks, errors):
    from playwright.sync_api import expect

    out = Path('build/shots')
    out.mkdir(parents=True, exist_ok=True)
    for width in [1280, 400]:
        state = fixture()
        state.pop('life', None)
        state['live'] = True
        page = browser.new_page(viewport=dict(width=width, height=1000))
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.route('https://**/*', lambda route: route.abort())
        page.route(origin + '/state', lambda route: route.fulfill(json=state))
        page.goto(origin + '/index.html?relay=' + origin)
        entry = page.locator('#entry')
        expect(entry).to_be_visible()
        assert page.evaluate("document.body.firstElementChild.id === 'entry'")
        expect(page.locator('#entry-status')).to_have_text('live')
        for name in ['doing', 'spikes', 'sugar', 'shock']:
            expect(page.locator('#entry-' + name)).to_have_text('—')
        expect(page.locator('#entry-feed li span')).to_have_text(['—'] * 3)
        expect(page.locator('#entry-balance')).to_have_text('paper balance — usdc · — today')
        blocks = [page.locator('#entry-' + name).bounding_box() for name in ['who', 'now', 'where']]
        assert all(block and block['width'] > 100 for block in blocks)
        if width == 1280:
            assert blocks[0]['x'] < blocks[1]['x'] < blocks[2]['x']
            assert entry.bounding_box()['height'] >= 1000
        else:
            assert blocks[0]['y'] < blocks[1]['y'] < blocks[2]['y']
            assert page.evaluate('document.documentElement.scrollWidth <= 400')
        links = page.locator('.entry-buttons a')
        assert links.nth(0).get_attribute('href') == page.locator('.kick').get_attribute('href')
        for index, target in [(1, 'betting'), (2, 'matches')]:
            assert links.nth(index).get_attribute('href') == '#' + target
            assert page.locator('#' + target).count() == 1
        assert page.locator('#comparison .eyebrow').text_content() == 'the comparison'
        assert page.locator('.entry-down').get_attribute('href') == '#film'
        state['life'] = dict(now=dict(doing='looking at ETH 15m', room='paper room',
                                     spikes=1312400, sugar_10m=3, shock_10m=1,
                                     balance=106.2, today_delta=6.2),
                             feed=[dict(at='07:02:11', text='eth 15m resolved · she won +5.20 · sugar'),
                                   dict(at='07:01:40', text='she scrolled down 3 times on arxiv.org'),
                                   dict(at='07:00:00', text='she entered the paper room'),
                                   dict(at='06:59:00', text='older line')])
        expect(page.locator('#entry-doing')).to_have_text('looking at ETH 15m')
        expect(page.locator('#entry-room')).to_have_text('in the paper room')
        expect(page.locator('#entry-spikes')).to_have_text('1,312,400')
        expect(page.locator('#entry-sugar')).to_have_text('3')
        expect(page.locator('#entry-shock')).to_have_text('1')
        expect(page.locator('#entry-balance')).to_have_text('paper balance 106.20 usdc · +6.20 today')
        expect(page.locator('#entry-feed li span')).to_have_text([e['text'] for e in state['life']['feed'][:3]])
        expect(page.locator('#entry-feed time').first).to_have_text('07:02:11')
        entry.screenshot(path=str(out / f'entry_{width}.png'))
        state['rooms']['/musicroom'] = dict(in_room=True, book=dict(now_playing=dict(track_id='123', title='<b>Rain</b>')))
        expect(page.locator('#entry-music-title')).to_have_text('<b>Rain</b> · River · CC BY 3.0')
        expect(page.locator('#entry-music')).to_be_visible()
        assert page.locator('#entry-music-title b').count() == 0
        assert page.locator('#entry-music a').get_attribute('href') == 'https://kick.com/femalefly'
        assert page.evaluate("[...document.querySelectorAll('audio')].every(a => a.paused && !a.getAttribute('src'))")
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        state['live'] = False
        expect(page.locator('#entry-music')).to_be_hidden()
        expect(page.locator('#entry-status')).to_have_text('offline')
        expect(page.locator('#entry-status')).not_to_have_class('entry-status on')
        state['life']['now'].update(balance=None, today_delta=None, room='the web')
        expect(page.locator('#entry-balance')).to_have_text('paper balance — usdc · — today')
        expect(page.locator('#entry-room')).to_have_text('in the web')
        state['life']['now'].update(balance=0, today_delta=-2.5, doing='<b>plain text</b>')
        expect(page.locator('#entry-balance')).to_have_text('paper balance 0.00 usdc · -2.50 today')
        expect(page.locator('#entry-doing')).to_have_text('<b>plain text</b>')
        assert page.locator('#entry-doing b').count() == 0
        del state['life']
        expect(page.locator('#entry-doing')).to_have_text('—')
        expect(page.locator('#entry-feed li span')).to_have_text(['—'] * 3)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        checks.append(f'Entry at {width}px: three blocks, links, placeholders, live data, offline, and plain text.')
        page.close()


def check_music(page, checks):
    play = dict(track_id='123', title='Rain', started_at=time.time() - 12, duration=60)
    DATA['music'] = dict(in_room=True, book=dict(now_playing=play, plays=[], reactions={}))
    page.mouse.click(20, 20)
    page.wait_for_function("window.ink.some(e => e.method === 'fillText' && e.args[0] === 'Rain · River · CC BY 3.0')")
    page.wait_for_function("(() => { const a = document.querySelector('audio'), p = window.received?.rooms['/musicroom'].book.now_playing; return a?.src.endsWith('/music/123.ogg') && !a.paused && Math.abs(a.currentTime - (Date.now()/1000 - p.started_at)) < 1; })()")
    assert page.locator('audio').count() == 1
    drone = "window.soundEdges.find(e => e[1] instanceof StereoPannerNode)[0].gain.value"
    page.wait_for_function(f"Math.abs({drone} - 0.25) < 0.001")
    page.wait_for_timeout(2100)
    page.evaluate('window.seeks = []')
    logs = []
    page.on('console', lambda message: logs.append(message.text) if message.text.startswith('music sync ') else None)
    for _ in range(3):
        play['started_at'] += 0.5
        page.wait_for_function("start => window.received?.rooms['/musicroom'].book.now_playing.started_at === start", arg=play['started_at'])
    assert page.evaluate('window.seeks.length') == 0
    play['started_at'] -= 5
    page.wait_for_function('window.seeks.length === 1')
    play['started_at'] -= 5
    page.wait_for_function("start => window.received?.rooms['/musicroom'].book.now_playing.started_at === start", arg=play['started_at'])
    assert page.evaluate('window.seeks.length') == 1
    assert page.evaluate('window.seeks[0].at - window.musicStarts.at(-1) >= 2000')
    assert len(logs) == 1 and re.fullmatch(r'music sync \+\d+\.\ds', logs[0])
    play['started_at'] += 5
    checks.append('Half-second timestamp changes never seek; a five-second jump seeks once and the cooldown holds.')
    assert page.evaluate("(() => { const master = window.soundEdges.find(e => e[0] === window.musicSource)?.[1]; return master instanceof GainNode && window.soundEdges.some(e => e[0] === master && e[1] === window.soundContexts[0].destination) && window.soundEdges.some(e => e[0] instanceof StereoPannerNode && e[1] === master); })()")
    page.get_by_role('button', name='mute', exact=True, include_hidden=True).evaluate('(b) => b.click()')
    page.wait_for_function("window.soundEdges.find(e => e[0] === window.musicSource)[1].gain.value < 0.001")
    page.locator('input[type=range]').evaluate("e => { e.value = '0.8'; e.dispatchEvent(new Event('input')); }")
    page.get_by_role('button', name='unmute', exact=True, include_hidden=True).evaluate('(b) => b.click()')
    page.wait_for_function("Math.abs(window.soundEdges.find(e => e[0] === window.musicSource)[1].gain.value - 0.2) < 0.001")
    page.locator('input[type=range]').evaluate("e => { e.value = '0.5'; e.dispatchEvent(new Event('input')); }")
    page.screenshot(path=str(STREAM_FRAME.with_name('music_frame.png')))
    muted = page.context.new_page()
    muted.goto(page.url + '&mute=1')
    muted.wait_for_function("document.querySelector('audio')?.src.endsWith('/music/123.ogg') && document.querySelector('audio').currentTime > 10")
    assert muted.evaluate("document.querySelector('audio').muted && window.soundContexts.length === 0")
    muted.close()
    for track_id in ['124', '124']:
        play = dict(track_id=track_id, title='Rain', started_at=time.time() - 5, duration=60)
        DATA['music']['book']['now_playing'] = play
        page.wait_for_function("start => { const a = document.querySelector('audio'); return window.received?.rooms['/musicroom'].book.now_playing.started_at === start && a.src.endsWith('/music/124.ogg') && !a.paused && Math.abs(a.currentTime - (Date.now()/1000 - start)) < 1; }", arg=play['started_at'])
        assert page.locator('audio').count() == 1
    DATA['music']['book']['now_playing'] = None
    page.wait_for_function("(() => { const a = document.querySelector('audio'); return a.paused && !a.getAttribute('src'); })()")
    page.wait_for_function(f"Math.abs({drone} - 1) < 0.001")
    assert page.evaluate("(() => { const param = window.soundEdges.find(e => e[1] instanceof StereoPannerNode)[0].gain; const release = window.gainRamps.findLast(r => r.param === param && r.value === 1); return release && Math.abs(release.at - release.now - 1) < 0.02; })()")
    DATA['music']['book']['now_playing'] = {**play, 'started_at': time.time() - 5}
    page.wait_for_function("!document.querySelector('audio').paused")
    DATA['live'] = False
    page.wait_for_function("(() => { const a = document.querySelector('audio'); return a.paused && !a.getAttribute('src'); })()")
    DATA['live'] = True
    page.wait_for_function("!document.querySelector('audio').paused")
    DATA['music']['book']['now_playing'] = {**play, 'started_at': time.time() - 61}
    page.wait_for_function("document.querySelector('audio').paused && window.received.rooms['/musicroom'].book.now_playing.started_at < Date.now()/1000 - 60")
    DATA['music']['book']['now_playing'] = {**play, 'started_at': time.time() - 5}
    page.wait_for_function("!document.querySelector('audio').paused")
    DATA['music']['in_room'] = False
    page.wait_for_function("(() => { const a = document.querySelector('audio'); return a.paused && !a.getAttribute('src'); })()")
    page.evaluate('window.ink = []')
    page.wait_for_function("window.ink.some(e => e.method === 'fillText' && e.args[0] === 'in the paper room')")
    assert not page.evaluate("window.ink.some(e => e.method === 'fillText' && e.args[0] === 'Rain · River · CC BY 3.0')")
    checks.append('Music credits, shared master volume/mute, seek correction, muted playback, track changes, repeat plays, null, expiry, offline and room exit pass.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=4788)
    capture(parser.parse_args().port)
