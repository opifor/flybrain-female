"""Capture the viewer with a local relay fixture, without running the arena brain."""
import argparse
import json
import math
import subprocess
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
    ('Bitcoin Up or Down - next 5 minutes', .36),
    ('Ethereum Up or Down - next 5 minutes', .58),
    ('Bitcoin Up or Down - next 15 minutes', .42),
    ('Ethereum Up or Down - next 15 minutes', .63),
    ('Solana Up or Down - next 15 minutes', .47),
    ('XRP Up or Down - next 15 minutes', .51)])]
DATA = {'events': [], 'learning': [], 'open': [], 'settled': [], 'live': True, 'cards': CARDS}
FRAME = b''
SEQ = 0
START = time.monotonic()


def fixture():
    global SEQ
    SEQ += 1
    t = time.monotonic() - START
    return dict(seq=SEQ, live=DATA['live'], age=0, url='http://127.0.0.1:4660/betroom',
                cursor=dict(x=.3 + .16 * math.sin(t * .8), y=.43 + .15 * math.cos(t * .7)),
                hz=dict(steer_L=150 + 130 * math.sin(t), steer_R=150 - 130 * math.sin(t),
                        fwd_L=100, fwd_R=200, stop=0),
                neural=dict(firing=8000 + 6500 * math.sin(t), spikes_per_sec=1300000 + 600000 * math.sin(t),
                            out=dict(forward=DATA.get('forward',.7))),
                betroom=dict(balance=104.2, win_count=1, loss_count=0,
                             open_bets=DATA['open'], settled_bets=DATA['settled']),
                betting=dict(in_room=True, bookie=dict(ok=True, at=time.time()), cards=DATA['cards'],
                             events=DATA['events'], learning=dict(last=DATA['learning'])))


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        path = urlparse(self.path).path
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
  const Native = window.AudioContext;
  window.AudioContext = class extends Native { constructor(...a) { super(...a); window.soundContexts.push(this); } };
  const scheduled = new WeakMap(), setValue = AudioParam.prototype.setValueAtTime;
  AudioParam.prototype.setValueAtTime = function(value, ...a) { scheduled.set(this,value); return setValue.call(this,value,...a); };
  const start = OscillatorNode.prototype.start;
  OscillatorNode.prototype.start = function(...a) { window.notes.push(scheduled.get(this.frequency) ?? this.frequency.value); return start.apply(this,a); };
  for (const method of ['fillText','fillRect','strokeRect','ellipse','arc']) {
    const original = CanvasRenderingContext2D.prototype[method];
    CanvasRenderingContext2D.prototype[method] = function(...a) {
      if (this.canvas.getAttribute('aria-label') === 'Her brain, path and paper bets') {
        window.ink.push({method, args:a, fill:this.fillStyle, stroke:this.strokeStyle});
        if (window.ink.length > 3000) window.ink.splice(0,1000);
      }
      return original.apply(this,a);
    };
  }
})();"""


def capture(port):
    global FRAME
    origin = f'http://127.0.0.1:{port}'
    server = ThreadingHTTPServer(('127.0.0.1', port), partial(Handler, directory=str(ROOT / 'site/web')))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    checks = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        arena = browser.new_page(viewport=dict(width=1280, height=800))
        arena.goto(origin + '/arena')
        arena.locator('.card:not(.empty)').nth(5).wait_for()
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
            panel.on('pageerror', lambda e: errors.append(str(e)))
            panel.route('https://**/*', lambda route: route.abort())
            panel.goto(origin+'/index.html?relay='+origin+'#betting')
            panel.locator('#bet-stage canvas').wait_for()
            panel.wait_for_function("document.getElementById('bet-frame').naturalWidth===1280")
            panel.locator('#betting').scroll_into_view_if_needed()
            panel.wait_for_timeout(700)
            assert panel.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
            assert panel.locator('#bet-stage canvas').bounding_box()['width'] > 100
            panel.screenshot(path=str(OUT / f'flybrain-show-panel-{width}.png'))
            checks.append(f'Betting panel at {width}px has an overlay and no page overflow.')
            panel.close()

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
        obs.goto(origin+'/show.html?relay='+origin)
        obs.wait_for_function("window.soundContexts[0]?.state === 'running'")
        obs.wait_for_function("[...document.querySelectorAll('span')].find(e=>e.textContent==='click for sound').hidden")
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
    (OUT/'flybrain-show-browser-checks.json').write_text(json.dumps(dict(checks=checks,errors=errors),indent=2),encoding='utf-8')
    print(f'{len(checks)} browser checks passed; 0 page errors')
    print(OUT/'flybrain-show-20s.webm')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=4788)
    capture(parser.parse_args().port)
