(() => {
  'use strict';
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const number = v => typeof v === 'string' && v.includes('/') ? v.split('/').map(Number).reduce((a, b) => a / b) : Number(v ?? 0);
  const price = v => v == null ? '?' : number(v).toFixed(2);
  const signed = v => (v >= 0 ? '+' : '') + v.toFixed(2);
  const key = e => `${e.kind}:${e.seq ?? e.id ?? `${e.at}:${e.market_id}:${e.action || ''}`}`;

  function makeSound(media) {
    let ctx, master, pan, tone, drone, filt, lfo, on = false, volume = 0.5, ducked = false;
    function init() {
      if (ctx) return;
      ctx = new (window.AudioContext || window.webkitAudioContext)();
      master = ctx.createGain(); master.gain.value = 0;
      ctx.createMediaElementSource(media).connect(master);
      pan = ctx.createStereoPanner(); tone = ctx.createGain(); tone.gain.value = 0;
      drone = ctx.createGain(); drone.gain.value = media.paused ? 1 : 0.25;
      ducked = !media.paused;
      const trem = ctx.createGain(); trem.gain.value = 0.7;
      filt = ctx.createBiquadFilter(); filt.type = 'lowpass'; filt.frequency.value = 200; filt.Q.value = 2;
      lfo = ctx.createOscillator(); lfo.frequency.value = 0.5;
      const lfoG = ctx.createGain(); lfoG.gain.value = 0.3;
      lfo.connect(lfoG).connect(trem.gain); lfo.start();
      for (const [type, detune] of [['sine', -6], ['triangle', 6]]) {
        const o = ctx.createOscillator(); o.type = type; o.frequency.value = 110; o.detune.value = detune;
        o.connect(filt); o.start();
      }
      filt.connect(trem).connect(tone).connect(drone).connect(pan).connect(master).connect(ctx.destination);
    }
    function ping(freq, dur, level, delay = 0, hard = false) {
      if (!on || ctx?.state !== 'running') return;
      const t = ctx.currentTime + delay, o = ctx.createOscillator(), g = ctx.createGain();
      o.type = hard ? 'triangle' : 'sine'; o.frequency.setValueAtTime(freq, t);
      if (hard) o.frequency.exponentialRampToValueAtTime(freq / 2, t + dur);
      g.gain.setValueAtTime(0.0001, t);
      g.gain.exponentialRampToValueAtTime(level, t + 0.008);
      g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
      o.connect(g).connect(master); o.start(t); o.stop(t + dur + 0.02);
      o.onended = () => { o.disconnect(); g.disconnect(); };
    }
    return {
      duck(playing) {
        if (!ctx || playing === ducked) return;
        ducked = playing;
        const t = ctx.currentTime;
        drone.gain.cancelAndHoldAtTime(t);
        drone.gain.linearRampToValueAtTime(playing ? 0.25 : 1, t + (playing ? 0.08 : 1));
      },
      async start() { init(); on = true; await ctx.resume(); master.gain.setTargetAtTime(on ? volume * 0.25 : 0, ctx.currentTime, 0.15); return ctx.state === 'running'; },
      mute(value) { on = !value; if (ctx) master.gain.setTargetAtTime(on ? volume * 0.25 : 0, ctx.currentTime, 0.08); },
      volume(value) { volume = clamp(value); if (ctx && on) master.gain.setTargetAtTime(volume * 0.25, ctx.currentTime, 0.08); },
      state(d, live) {
        if (!ctx) return;
        const t = ctx.currentTime, n = d?.neural || {}, hz = d?.hz || n.dn || {}, f = clamp(number(n.firing) / 8000);
        filt.frequency.setTargetAtTime(200 + 2200 * f, t, 0.4);
        lfo.frequency.setTargetAtTime(0.5 + 5.5 * f, t, 0.4);
        pan.pan.setTargetAtTime(clamp((number(hz.steer_R) - number(hz.steer_L)) / 300, -0.8, 0.8), t, 0.4);
        tone.gain.setTargetAtTime(live ? 1 : 0, t, 0.3);
      },
      moment(kind, win, settled) {
        if (kind === 'buy') ping(146.83, 0.28, 0.22);
        else if (kind === 'sell') { ping(win ? 261.63 : 392, 0.22, 0.15); ping(win ? 392 : 261.63, 0.3, 0.15, 0.14); }
        else if (win) for (const f of [261.63, 329.63, 392]) ping(f, settled ? 0.9 : 0.45, 0.09);
        else ping(90, settled ? 0.65 : 0.23, 0.3, 0, true);
      },
      get running() { return on && ctx?.state === 'running'; },
      destroy() { if (ctx) ctx.close(); }
    };
  }

  window.mountShow = function mountShow(container, {audio = false, size, layout} = {}) {
    const broadcast = layout === 'broadcast' || (size?.width === 1920 && size?.height === 1080);
    const origin = new URLSearchParams(location.search).get('relay') || 'https://live.femaleflybrain.com';
    const forcedMute = new URLSearchParams(location.search).get('mute') === '1';
    const musicAudio = document.createElement('audio');
    musicAudio.hidden = true; musicAudio.preload = 'auto';
    musicAudio.muted = !audio || forcedMute;
    container.append(musicAudio);
    const sound = audio && !forcedMute ? makeSound(musicAudio) : null;
    let music = null, musicKey = null, musicCredits = new Map();
    let musicPlayedAt = -Infinity, musicSeekAt = -Infinity, musicInitial = false;
    musicAudio.addEventListener('playing', () => sound?.duck(true));
    for (const event of ['pause', 'ended', 'emptied']) musicAudio.addEventListener(event, () => sound?.duck(false));
    fetch('music/catalog.json').then(r => r.ok ? r.json() : []).then(rows => {
      musicCredits = new Map(rows.map(row => [String(row.id), row]));
    }).catch(() => {});
    function syncMusic() {
      if (!music || !audio) return;
      const offset = Math.max(0, Date.now() / 1000 - number(music.started_at));
      if (offset >= number(music.duration)) { musicAudio.pause(); return; }
      if (musicAudio.readyState >= 1) {
        const end = Number.isFinite(musicAudio.duration) ? musicAudio.duration : number(music.duration);
        if (offset >= end) { musicAudio.pause(); return; }
        const now = performance.now(), drift = offset - musicAudio.currentTime;
        if (musicInitial) {
          musicAudio.currentTime = offset; musicInitial = false;
        } else if (Math.abs(drift) > 3 && now - musicSeekAt >= 10000 && now - musicPlayedAt >= 2000) {
          musicAudio.currentTime = offset; musicSeekAt = now;
          console.log(`music sync ${drift >= 0 ? '+' : ''}${drift.toFixed(1)}s`);
        }
        if (musicAudio.paused) {
          musicPlayedAt = now;
          musicAudio.play().catch(() => {});
        }
      }
    }
    musicAudio.addEventListener('loadedmetadata', syncMusic);
    function acceptMusic(d, healthy) {
      const room = d?.rooms?.['/musicroom'];
      music = healthy && room?.in_room ? room.book?.now_playing : null;
      const next = music ? String(music.track_id) : null;
      if (next !== musicKey) {
        musicKey = next; musicAudio.pause();
        musicInitial = true; musicPlayedAt = -Infinity;
        if (music && audio) musicAudio.src = `music/${encodeURIComponent(String(music.track_id))}.ogg`;
        else { musicAudio.removeAttribute('src'); musicAudio.load(); }
      }
      syncMusic();
    }
    container.style.position = 'relative'; container.style.overflow = 'hidden';
    if (size) container.style.aspectRatio = `${size.width} / ${size.height}`;
    let img = container.querySelector('img');
    if (!img) { img = document.createElement('img'); container.append(img); }
    img.alt = 'The page she is looking at'; img.crossOrigin = 'anonymous';
    Object.assign(img.style, {position:'absolute', inset:'0', width:'100%', height:'100%', objectFit:'contain'});
    if (broadcast) Object.assign(img.style, {width:'66.6666667%', height:'74.0740741%'});
    const canvas = document.createElement('canvas'), g = canvas.getContext('2d');
    canvas.setAttribute('aria-label', 'Her brain, path and paper bets');
    Object.assign(canvas.style, {position:'absolute', inset:'0', width:'100%', height:'100%', pointerEvents:'none'});
    container.append(canvas);
    const controls = document.createElement('div');
    Object.assign(controls.style, {position:'absolute', right:'8px', bottom:'8px', display:'flex', alignItems:'center', gap:'8px', maxWidth:'calc(100% - 16px)', zIndex:'3'});
    container.append(controls);
    if (forcedMute || broadcast) controls.style.display = 'none';
    function button(label) {
      const b = document.createElement('button'); b.textContent = label; b.type = 'button';
      Object.assign(b.style, {font:'11px ui-monospace,monospace', color:'#c9c4cc', background:'#101116dd', border:'1px solid #4a3a44', borderRadius:'3px', padding:'5px 8px', cursor:'pointer'});
      controls.append(b); return b;
    }
    const retinaButton = button('what she sees');
    let retina = false; retinaButton.setAttribute('aria-pressed', 'false');
    retinaButton.onclick = () => { retina = !retina; retinaButton.setAttribute('aria-pressed', String(retina)); };
    let hint, muteButton, muted = forcedMute;
    function unlock() {
      if (!sound || muted) return;
      sound.start().then(ok => { if (ok && hint) hint.hidden = true; syncMusic(); }).catch(() => {});
    }
    if (sound) {
      muteButton = button('mute'); muteButton.setAttribute('aria-pressed', 'false');
      muteButton.onclick = () => { muted = !muted; sound.mute(muted); muteButton.textContent = muted ? 'unmute' : 'mute'; muteButton.setAttribute('aria-pressed', String(muted)); if (!muted) unlock(); };
      const volume = document.createElement('input'); volume.type = 'range'; volume.min = 0; volume.max = 1; volume.step = 0.01; volume.value = 0.5;
      volume.setAttribute('aria-label', 'Master volume'); volume.style.cssText = 'width:64px;accent-color:#ff79b0';
      volume.oninput = () => sound.volume(Number(volume.value)); controls.append(volume);
      hint = document.createElement('span'); hint.textContent = 'click for sound'; hint.style.cssText = 'font:11px ui-monospace,monospace;color:#d9c7cf'; controls.append(hint);
      document.addEventListener('pointerdown', unlock); document.addEventListener('keydown', unlock); unlock();
    }
    const sample = document.createElement('canvas'), sg = sample.getContext('2d', {willReadFrequently:true});
    let pixels = null, state = null, live = false, sequence = null, trail = [], moments = [], cursor = null, target = null;
    let timer, raf, destroyed = false, lastTime = performance.now(), lastPoll = 0, imageReady = false;
    const whoStart = performance.now();
    let feed = [], previousFeed = [], feedAt = 0;
    let gazeKey = null, gazeProgress = 0, gazeDrive = 0, intentKey, decision = null;
    const seen = new Set(), cards = new Map(), records = new Map(), listeners = new Set();
    img.onload = () => {
      imageReady = true; sample.width = img.naturalWidth; sample.height = img.naturalHeight;
      try { sg.drawImage(img, 0, 0); pixels = sg.getImageData(0, 0, sample.width, sample.height).data; } catch (_) { pixels = null; }
    };
    img.onerror = () => { imageReady = false; pixels = null; };
    const observer = new ResizeObserver(() => {
      const r = container.getBoundingClientRect(), d = Math.min(devicePixelRatio || 1, 2);
      canvas.width = Math.max(1, Math.round(r.width * d)); canvas.height = Math.max(1, Math.round(r.height * d));
    }); observer.observe(container);
    function rect(e) {
      const card = cards.get(String(e.market_id));
      if (!card || card.shelf !== 'fast' || !Number.isInteger(card.slot) || card.slot < 0 || card.slot > 5) return null;
      // Old settlements must not illuminate a different market that inherited the slot.
      if (!(state?.betting?.cards || []).some(c => c.market_id === card.market_id && c.slot === card.slot)) return null;
      return {x:56 + card.slot % 3 * 400, y:48 + Math.floor(card.slot / 3) * 368, w:368, h:336};
    }
    function accept(d) {
      const now = performance.now(); state = d; lastPoll = now;
      if (broadcast) {
        const next = d?.life?.feed?.slice(0, 14) || [];
        if (JSON.stringify(next) !== JSON.stringify(feed)) {
          previousFeed = feed; feed = next; feedAt = now;
        }
      }
      live = d?.live === true && number(d.age) < 15;
      acceptMusic(d, live);
      sound?.state(d, live);
      for (const f of listeners) f(d);
      if (!live) { trail = []; moments = []; return; }
      if (d.cursor) { target = {x:clamp(number(d.cursor.x)) * 1280, y:clamp(number(d.cursor.y)) * 800}; if (!cursor) cursor = {...target}; }
      for (const c of d.betting?.cards || []) cards.set(String(c.market_id), c);
      const intent = d.betting?.last_intent;
      const nextIntent = intent ? `${intent.at}:${intent.token}` : null;
      if (nextIntent && nextIntent !== intentKey) {
        // A saved receipt should not stamp again when someone joins the stream.
        if (intentKey !== undefined) decision = {...intent, side:String(intent.side).toLowerCase(), started:now};
        intentKey = nextIntent;
      } else if (intentKey === undefined) intentKey = null;
      for (const e of [...(d.betroom?.open_bets || []), ...(d.betroom?.settled_bets || [])]) records.set(String(e.id ?? e.look_id), e);
      if (d.seq !== sequence || !imageReady) { sequence = d.seq; img.src = origin + '/frame.jpg?s=' + encodeURIComponent(d.seq); }
      const events = [...(d.betting?.events || []), ...(d.betting?.learning?.last || []).filter(e => e.status === 'delivered' && e.sign !== 0).map(e => ({...e, kind:e.sign > 0 ? 'sugar' : 'shock'}))];
      events.sort((a, b) => number(a.at) - number(b.at));
      for (const raw of events) {
        const id = key(raw); if (seen.has(id)) continue; seen.add(id);
        if (raw.seq != null && ['sugar','shock'].includes(raw.kind) && events.some(e => e.kind === 'settled' && e.seq === raw.seq)) continue;
        // Joining a stream does not perform the entire ledger again.
        if (Math.abs(Date.now() / 1000 - number(raw.at)) > 12) continue;
        const record = records.get(String(raw.position_id ?? raw.id ?? raw.look_id)) || [...records.values()].find(e => e.look_id === (raw.buy_look_id ?? raw.look_id)) || {};
        const e = {...record, ...raw}, settled = e.kind === 'settled';
        const kind = e.kind === 'fill' ? (e.action === 'sell' ? 'sell' : 'buy') : e.kind === 'sold' ? 'sell' : e.kind;
        if (!['buy','sell','sugar','shock','settled'].includes(kind)) continue;
        const pnl = e.pnl_cents != null ? number(e.pnl_cents) / 100 : (number(e.payout_cents) - number(e.stake_cents)) / 100;
        const win = kind === 'sugar' || (kind !== 'shock' && (settled ? (e.won ?? e.side === e.outcome) : pnl >= 0));
        moments.push({e, kind, win, pnl, settled, at:now, from:{...(cursor || {x:640,y:400})}});
        sound?.moment(kind, win, settled);
      }
      if (seen.size > 4096) { const keep = [...seen].slice(-2048); seen.clear(); keep.forEach(k => seen.add(k)); }
      if (records.size > 2048) for (const k of [...records.keys()].slice(0, 1024)) records.delete(k);
      if (cards.size > 2048) for (const k of [...cards.keys()].slice(0, 1024)) cards.delete(k);
    }
    async function poll() {
      try {
        const r = await fetch(origin + '/state', {cache:'no-store', signal:AbortSignal.timeout(8000)});
        if (!r.ok) throw Error('relay unavailable');
        const d = await r.json(); if (!destroyed) accept(d);
      } catch (_) { if (!destroyed) accept(null); }
      if (!destroyed) timer = setTimeout(poll, document.hidden ? 5000 : 1000);
    }
    function ellipse(x, y, rx, ry, angle = 0) { g.beginPath(); g.ellipse(x, y, rx, ry, angle, 0, Math.PI * 2); g.fill(); }
    function chip(x, y, alpha = 1) {
      g.save(); g.globalAlpha *= alpha; g.fillStyle = '#e9c987'; g.strokeStyle = '#5d4027'; g.lineWidth = 2;
      g.beginPath(); g.arc(x, y, 10, 0, Math.PI * 2); g.fill(); g.stroke();
      g.strokeStyle = '#fff1c3'; g.beginPath(); g.arc(x, y, 6, 0, Math.PI * 2); g.stroke(); g.restore();
    }
    function hex(x, y, r, light) {
      g.beginPath(); for (let i = 0; i < 6; i++) { const a = Math.PI / 3 * i; const px = x + Math.cos(a) * r, py = y + Math.sin(a) * r; i ? g.lineTo(px,py) : g.moveTo(px,py); }
      g.closePath(); g.fillStyle = `rgb(${light},${light},${light})`; g.fill(); g.strokeStyle = '#16171b'; g.lineWidth = 0.7; g.stroke();
    }
    function drawRetina() {
      const x = 958, y = 540;
      g.fillStyle = '#090a0ef2'; g.fillRect(x - 12, y - 30, 322, 256);
      g.fillStyle = '#e3c8d3'; g.font = '13px ui-monospace,monospace'; g.fillText('what she sees', x, y - 10);
      if (!pixels) { g.fillStyle = '#9a929d'; g.fillText('frame sampling unavailable', x, y + 100); return; }
      const cx = target.x / 1280 * sample.width, cy = target.y / 800 * sample.height;
      for (let col = 0; col < 33; col++) for (let row = 0; row < 21; row++) {
        const u = col * 9 / 300, v = (row * 10 + (col % 2) * 5) / 210;
        const px = clamp(Math.floor(cx - 150 + u * 300), 0, sample.width - 1), py = clamp(Math.floor(cy - 105 + v * 210), 0, sample.height - 1);
        const i = (py * sample.width + px) * 4, light = Math.round(0.299 * pixels[i] + 0.587 * pixels[i+1] + 0.114 * pixels[i+2]);
        hex(x + u * 300, y + v * 210, 6, light);
      }
    }
    function drawBroadcast(now) {
      g.setTransform(canvas.width / 1920, 0, 0, canvas.height / 1080, 0, 0);
      g.fillStyle = '#090a0c'; g.fillRect(1280, 0, 640, 1080); g.fillRect(0, 800, 1280, 280);
      g.fillStyle = '#292d35';
      g.fillRect(1280, 0, 1, 1080); g.fillRect(1304, 200, 592, 1); g.fillRect(1304, 470, 592, 1);
      g.fillRect(0, 800, 1280, 1); g.fillRect(640, 824, 1, 232);
      const life = state?.life, current = life?.now || {}, hour = life?.hour || {};
      const value = v => v == null ? '—' : String(v);
      const money = v => v == null ? '—' : number(v).toFixed(2);
      const delta = v => v == null ? '—' : signed(number(v));
      function text(line, x, y, width, font = 22, color = '#e9edf3') {
        g.font = `${font}px ui-monospace,monospace`; g.fillStyle = color;
        let shown = value(line);
        if (g.measureText(shown).width > width) {
          while (shown.length && g.measureText(shown + '…').width > width) shown = shown.slice(0, -1);
          shown += '…';
        }
        g.fillText(shown, x, y);
      }
      const caption = (line, x, y) => text(line, x, y, 592, 18, '#ff79b0');
      caption('who', 1304, 36);
      const who = life?.who?.length ? life.who : ['—'];
      const elapsed = (now - whoStart) / 20000, index = Math.floor(elapsed) % who.length;
      const blend = clamp((elapsed % 1) * 20000 / 800);
      function identity(line, alpha) {
        g.save(); g.globalAlpha = alpha;
        // Keep long identity lines readable without shrinking the type.
        g.font = '22px ui-monospace,monospace';
        const words = String(line).split(' ');
        for (let row = 0; row < 3 && words.length; row++) {
          let line = words.shift();
          while (words.length && g.measureText(line + ' ' + words[0]).width <= 592) line += ' ' + words.shift();
          text(line, 1304, 73 + row * 28, 592);
        }
        g.restore();
      }
      if (elapsed >= 1 && blend < 1) identity(who[(index + who.length - 1) % who.length], 1 - blend);
      identity(who[index], elapsed < 1 ? 1 : blend);
      text('paper money', 1304, 166, 150); text('· 139,255 neurons ·', 1462, 166, 260);
      g.fillStyle = state?.live ? '#ff79b0' : '#8b93a1'; ellipse(1760, 159, 5, 5);
      text('live', 1776, 166, 100);
      caption('now', 1304, 235);
      text(current.doing, 1304, 276, 592, 30);
      if (music) {
        const credit = musicCredits.get(String(music.track_id)) || {};
        g.strokeStyle = '#8b93a1'; g.lineWidth = 1.5;
        g.beginPath(); g.moveTo(1315, 302); g.lineTo(1315, 286); g.lineTo(1322, 289); g.stroke();
        g.beginPath(); g.ellipse(1311, 302, 4, 2.5, -0.4, 0, Math.PI * 2); g.stroke();
        const suffix = ` · ${credit.artist || 'unknown artist'} · ${credit.license || 'license pending'}`;
        g.font = '16px ui-monospace,monospace';
        let title = String(music.title);
        while (title.length && g.measureText(title + suffix).width > 566) title = title.slice(0, -1);
        if (title !== String(music.title)) title = title.slice(0, -1) + '…';
        text(title + suffix, 1330, 307, 566, 16, '#8b93a1');
      } else text(current.room == null ? 'in the —' : `in the ${current.room.replace(/^the /, '')}`, 1304, 310, 592, 22, '#8b93a1');
      ['spikes/s', 'turn', 'sugar', 'shock'].forEach((label, i) => {
        const x = 1304 + i * 148;
        text(label, x, 349, 140, 22, '#8b93a1');
        if (i !== 1) text(i === 0 ? (current.spikes == null ? '—' : number(current.spikes).toLocaleString('en-US')) : current[i === 2 ? 'sugar_10m' : 'shock_10m'], x, 383, 144);
        else if (['left', 'right'].includes(current.turn)) {
          const direction = current.turn === 'left' ? -1 : 1;
          g.fillStyle = '#e9edf3'; g.beginPath(); g.moveTo(x + 22 + direction * 12, 373);
          g.lineTo(x + 22 - direction * 12, 362); g.lineTo(x + 22 - direction * 12, 384); g.closePath(); g.fill();
        } else if (current.turn === 'straight') { g.fillStyle = '#e9edf3'; ellipse(x + 22, 373, 5, 5); }
        else text('—', x, 383, 144);
      });
      text(`paper balance ${money(current.balance)} usdc`, 1304, 423, 592);
      text(`${delta(current.today_delta)} today`, 1304, 453, 592, 22, '#8b93a1');
      caption('feed', 1304, 508);
      const progress = clamp((now - feedAt) / 400);
      function feedRows(rows, offset, alpha, newest = false) {
        g.save(); g.beginPath(); g.rect(1298, 523, 598, 537); g.clip(); g.globalAlpha = alpha;
        rows.forEach((row, i) => {
          const y = 550 + i * 37 + offset;
          text(row.at, 1304, y, 106, 22, '#8b93a1');
          g.font = '22px ui-monospace,monospace'; g.fillStyle = '#e9edf3';
          const line = value(row.text), width = 480;
          // Keep a full short line beside the clock, even with wide letters.
          if ([...line].length <= 48 && g.measureText(line).width > width) g.fillText(line, 1416, y, width);
          else text(line, 1416, y, width);
          if (newest && i === 0) {
            g.save(); g.globalAlpha *= 0.6 * clamp(1 - (now - feedAt) / 5000);
            g.fillStyle = '#ff79b0'; g.fillRect(1298, y - 24, 2, 28); g.restore();
          }
        }); g.restore();
      }
      if (progress < 1) feedRows(previousFeed, progress * 37, 1 - progress);
      feedRows(feed.length ? feed : [{at:'—', text:'—'}], (progress - 1) * 37, progress, true);
      caption('last hour', 24, 839);
      const metrics = [['rooms','rooms'], ['plays','plays'], ['bets','bets'], ['won','won'], ['lost','lost'], ['paper p&l','pnl'], ['sugar','sugar'], ['shock','shock'], ['nudges','nudges']];
      const nudges = Object.values(state?.rooms || {}).reduce((sum, room) => sum + number(room?.nudges), 0);
      metrics.forEach(([label, field], i) => {
        const x = 24 + i % 5 * 124, y = i < 5 ? 860 : 965;
        text(label, x, y, 120, 18, '#8b93a1');
        text(field === 'nudges' ? nudges : field === 'pnl' ? delta(hour[field]) : hour[field], x, y + 38, 121, 30,
          field === 'pnl' && hour[field] != null ? (hour[field] >= 0 ? '#f8d694' : '#ff4153') : '#e9edf3');
      });
      caption('paper', 664, 839);
      let stripFont = 30;
      for (const font of [30, 26, 22]) {
        stripFont = font; g.font = `${font}px ui-monospace,monospace`;
        if (g.measureText(value(feed[0]?.text)).width <= 592) break;
      }
      text(feed[0]?.text, 664, 900, 592, stripFont);
      text('her rooms · all paper ·', 664, 997, 592);
      text(`femaleflybrain.com · UTC ${new Date().toISOString().slice(11, 19)}`, 664, 1031, 592);
    }
    function drawGaze(now, dt) {
      if (!state.betting?.in_room) return;
      const gaze = state.betting.gaze;
      const currentKey = gaze ? `${gaze.token}:${gaze.since}` : null;
      if (currentKey !== gazeKey) { gazeKey = currentKey; gazeProgress = 0; gazeDrive = 0; }
      const ease = 1 - Math.exp(-dt * 12);
      function ring(r, progress) {
        g.strokeStyle = '#ff79b0'; g.lineWidth = 2;
        g.beginPath(); g.arc(r.x + 26, r.y + 44, 30, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * progress); g.stroke();
      }
      if (gaze) {
        gazeProgress += (clamp(number(gaze.steps) / Math.max(1, number(gaze.needed))) - gazeProgress) * ease;
        gazeDrive += (clamp(number(gaze.drive), -1, 1) - gazeDrive) * ease;
        const r = rect({market_id:gaze.token});
        if (r) {
          g.save(); g.beginPath(); g.rect(r.x, r.y, r.w, r.h); g.clip();
          ring(r, gazeProgress);
          const y = r.y + r.h - 62, left = r.x + 66, right = r.x + r.w - 70;
          const leaning = gaze.drive != null && Math.abs(number(gaze.drive)) >= 0.02;
          g.fillStyle = '#181b20'; g.fillRect(r.x + 20, y - 22, r.w - 40, 70);
          g.font = '20px ui-monospace,monospace';
          g.fillStyle = leaning && gaze.drive < 0 ? '#e9edf3' : '#818a97'; g.fillText('NO', r.x + 20, y);
          g.fillStyle = leaning && gaze.drive > 0 ? '#e9edf3' : '#818a97'; g.fillText('YES', r.x + r.w - 20 - g.measureText('YES').width, y);
          g.strokeStyle = '#818a97'; g.lineWidth = 1; g.beginPath(); g.moveTo(left, y - 6); g.lineTo(right, y - 6); g.stroke();
          g.fillStyle = leaning ? '#e9c987' : '#818a97'; ellipse(left + (gazeDrive + 1) / 2 * (right - left), y - 6, 4, 4);
          g.font = '18px ui-sans-serif,system-ui,sans-serif'; g.fillStyle = '#818a97';
          const words = (gaze.smell || []).slice(0, 6);
          g.fillText(words.length ? `smells like: ${words.join(' · ')}` : 'smells like nothing she knows', r.x + 20, r.y + r.h - 26, r.w - 40);
          g.restore();
        }
      }
      if (!decision || now - decision.started >= 1200) return;
      const r = rect({market_id:decision.token}), age = now - decision.started;
      if (!r || !['yes', 'no'].includes(decision.side)) return;
      g.save();
      g.beginPath(); g.rect(r.x, r.y, r.w, r.h); g.clip();
      if (decision.status === 'booked') {
        if (age < 600) ring(r, 1);
        g.globalAlpha *= clamp((1200 - age) / 500);
        g.translate(r.x + r.w / 2, r.y + 142); g.rotate(-8 * Math.PI / 180);
        g.textAlign = 'center'; g.font = 'bold 72px ui-sans-serif,system-ui,sans-serif';
        g.fillStyle = decision.side === 'yes' ? '#ff79b0' : '#8b93a1'; g.fillText(decision.side.toUpperCase(), 0, 0);
      } else {
        g.fillStyle = '#818a97'; g.font = '18px ui-monospace,monospace'; g.fillText('refused', r.x + 18, r.y + 320);
      }
      g.restore();
    }
    function draw(now) {
      if (destroyed) return;
      const dt = Math.min(0.1, (now - lastTime) / 1000); lastTime = now;
      g.setTransform(1,0,0,1,0,0); g.clearRect(0,0,canvas.width,canvas.height);
      const w = img.naturalWidth || 1280, h = img.naturalHeight || 800, scale = Math.min(canvas.width / w, canvas.height / h);
      const fw = w * scale, fh = h * scale, ox = (canvas.width-fw)/2, oy = (canvas.height-fh)/2;
      g.setTransform(fw/1280,0,0,fh/800,ox,oy);
      if (broadcast) g.setTransform(canvas.width / 1920, 0, 0, canvas.height / 1080, 0, 0);
      g.save();
      if (broadcast) { g.beginPath(); g.rect(0, 0, 1280, 800); g.clip(); }
      const healthy = live && now - lastPoll < 15000;
      if (!healthy || !imageReady) {
        g.fillStyle = '#090a0ccc'; g.fillRect(0,0,1280,800); g.fillStyle = '#c4b9c0'; g.font = '17px ui-monospace,monospace';
        g.textAlign = 'center'; g.fillText(!healthy ? 'Waiting for the relay.' : 'Waiting for a live frame.',640,400); g.textAlign = 'left';
        if (!healthy) { sound?.state(null,false); acceptMusic(null, false); }
      } else if (cursor && target) {
        const n = state.neural || {}, hz = state.hz || n.dn || {}, firing = clamp(number(n.firing)/16000), spike = clamp(number(n.spikes_per_sec)/2000000);
        moments = moments.filter(m => now - m.at < 2200);
        const pause = moments.some(m => (m.kind === 'sugar' || (m.settled && m.win)) && now-m.at < 1000);
        if (!pause) { const a = 1 - Math.exp(-dt * 9); cursor.x += (target.x-cursor.x)*a; cursor.y += (target.y-cursor.y)*a; }
        const hue = 330 + clamp((number(hz.steer_L)-number(hz.steer_R))/300,-1,1)*65;
        trail.push({x:cursor.x,y:cursor.y,at:now,hue,light:40+firing*35}); trail = trail.filter(p => now-p.at < 2600);
        g.lineWidth = 3; g.lineCap = 'round';
        for (let i=1;i<trail.length;i++) { const p = trail[i]; g.strokeStyle = `hsla(${p.hue},85%,${p.light}%,${(1-(now-p.at)/2600)*0.65})`; g.beginPath(); g.moveTo(trail[i-1].x,trail[i-1].y); g.lineTo(p.x,p.y); g.stroke(); }
        if (state.betting?.in_room) for (const e of state.betroom?.open_bets || []) { const r = rect(e); if (r) chip(r.x+r.w-22,r.y+22); }
        for (const m of moments) {
          const age = (now-m.at)/1000, p = clamp(age/0.8), r = state.betting?.in_room ? rect(m.e) : null;
          const tx = r ? r.x+r.w-22 : m.from.x, ty = r ? r.y+22 : m.from.y;
          g.save(); g.globalAlpha = clamp((2.2-age)/0.6);
          if (m.kind === 'buy' && r && age < 1) {
            g.fillStyle = `rgba(255,205,137,${0.28*Math.sin(Math.PI*clamp(age))})`; g.fillRect(r.x,r.y,r.w,r.h);
            g.strokeStyle = '#f6b5c9'; g.lineWidth = 2; g.beginPath(); g.moveTo(cursor.x+18,cursor.y);
            g.lineTo(cursor.x+18+(tx-cursor.x-18)*Math.sin(Math.PI*p),cursor.y+(ty-cursor.y)*Math.sin(Math.PI*p)); g.stroke();
            chip(tx,ty-90*(1-p));
          } else if (m.kind === 'sell') chip(tx+(cursor.x-tx)*p,ty+(cursor.y-ty)*p,1-p);
          if (['sugar','shock','settled'].includes(m.kind) && age < 1.15) {
            const fade = Math.sin(Math.PI*clamp(age/1.15));
            if (r) { g.fillStyle = m.win ? `rgba(255,195,91,${fade*0.42})` : `rgba(0,0,0,${fade*0.65})`; g.fillRect(r.x,r.y,r.w,r.h); }
            if (m.win && r) for (let j=0;j<5;j++) chip(tx+Math.cos(j*1.26)*age*42,ty+Math.sin(j*1.26)*age*42,1-age/1.15);
            if (!m.win && age < 0.65) { g.strokeStyle = `rgba(255,65,83,${(1-age/0.65)*(0.5+0.5*Math.cos(age*35))})`; g.lineWidth = 15; g.strokeRect(7,7,1266,786); }
          }
          if (m.kind === 'sell' || m.settled) {
            const line = `${m.settled ? 'settled / ' : ''}${price(m.e.entry_price ?? m.e.price)} to ${price(m.e.exit_price ?? (m.settled ? (m.win ? 1 : 0) : m.e.price))} / ${signed(m.pnl)}`;
            g.font = 'bold 17px ui-monospace,monospace'; const width = g.measureText(line).width;
            const x = clamp(tx-width/2,12,1268-width), y = Math.max(35,ty-25-age*25);
            g.fillStyle = '#0b0c10ee'; g.fillRect(x-8,y-21,width+16,30); g.fillStyle = m.win ? '#f8d694' : '#ff9cb1'; g.fillText(line,x,y);
          }
          g.restore();
        }
        const shock = moments.find(m => (m.kind === 'shock' || (m.settled && !m.win)) && now-m.at < 650);
        const hop = shock ? Math.sin(Math.PI*(now-shock.at)/650)*24 : 0;
        g.save(); g.translate(cursor.x-hop,cursor.y-hop*0.5);
        const glow = g.createRadialGradient(0,0,2,0,0,22+spike*35); glow.addColorStop(0,'#ff79b02b'); glow.addColorStop(1,'#ff79b000'); g.fillStyle = glow; ellipse(0,0,22+spike*35,22+spike*35);
        const forward = number(hz.fwd_L)+number(hz.fwd_R), stop = pause || forward <= 0 || n.out?.forward === 0 || number(hz.stop) >= forward;
        const beat = stop ? 0 : Math.abs(Math.sin(now/1000*Math.PI*2*clamp(forward/60,0,12)));
        g.fillStyle = '#ff79b059'; for (const side of [-1,1]) ellipse(-5,side*(stop ? 5 : 10+beat*9),17,stop ? 3 : 5,side*(stop ? 0.1 : 0.5+beat*0.3));
        g.fillStyle = '#ff79b0'; ellipse(0,0,15,10); ellipse(15,-1,7,7);
        const orn = n.orn_hz ?? state.betting?.orn_hz, twitch = orn == null ? 0 : Math.sin(now/65)*clamp(number(orn)/100)*7;
        g.strokeStyle = '#fcb2ce'; g.lineWidth = 1.5; for (const side of [-1,1]) { g.beginPath(); g.moveTo(19,side*3); g.lineTo(29+twitch,side*(9+twitch)); g.stroke(); }
        g.restore();
        const entry = state.rooms?.['/hall']?.events?.at(-1);
        if (entry && Math.abs(Date.now() / 1000 - number(entry.at)) < 12) {
          g.fillStyle = '#0b0c10ee'; g.fillRect(24, 20, 680, 46);
          g.fillStyle = '#e9edf3'; g.font = '20px ui-monospace,monospace';
          g.fillText(entry.text, 40, 50);
        }
        drawGaze(now, dt);
        if (retina) drawRetina();
      }
      g.restore();
      if (broadcast) drawBroadcast(now);
      raf = requestAnimationFrame(draw);
    }
    poll(); raf = requestAnimationFrame(draw);
    return {
      onState(fn) { listeners.add(fn); if (state) fn(state); return () => listeners.delete(fn); },
      destroy() { destroyed = true; clearTimeout(timer); cancelAnimationFrame(raf); observer.disconnect(); musicAudio.pause(); musicAudio.removeAttribute('src'); musicAudio.load(); musicAudio.remove(); sound?.destroy(); document.removeEventListener('pointerdown',unlock); document.removeEventListener('keydown',unlock); canvas.remove(); controls.remove(); img.onload = img.onerror = null; },
    };
  };
})();
