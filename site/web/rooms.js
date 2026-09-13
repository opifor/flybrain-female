(() => {
  'use strict';
  const back = document.querySelector('[data-back]');
  if (back && history.length > 1) {
    back.hidden = false;
    back.addEventListener('click', () => history.back());
  }
  const origin = new URLSearchParams(location.search).get('relay') || 'https://live.femaleflybrain.com';
  const number = value => value == null || !Number.isFinite(Number(value)) ? '—' : Number(value).toLocaleString('en-US');
  const time = value => {
    if (value == null) return '—';
    const date = new Date(typeof value === 'number' ? value * 1000 : value);
    return Number.isNaN(date.getTime()) ? '—' : date.toISOString().slice(11, 16) + ' UTC';
  };
  const node = (tag, text) => { const el = document.createElement(tag); el.textContent = text; return el; };
  let catalogue = new Map(), latest;
  fetch('music/catalog.json').then(r => r.ok ? r.json() : []).then(rows => {
    catalogue = new Map(rows.map(row => [String(row.id), row]));
    if (latest) render(latest);
  }).catch(() => {});
  function table(headers, rows) {
    const el = document.createElement('table'), head = document.createElement('tr');
    for (const title of headers) { const th = node('th', title); th.scope = 'col'; head.append(th); }
    const thead = document.createElement('thead'); thead.append(head); el.append(thead);
    const body = document.createElement('tbody');
    for (const row of rows) {
      const tr = document.createElement('tr');
      for (const value of row) { const td = document.createElement('td'); td.append(value instanceof Node ? value : document.createTextNode(String(value ?? '—'))); tr.append(td); }
      body.append(tr);
    }
    el.append(body); return el;
  }
  function credits(play) {
    const track = {...catalogue.get(String(play.track_id)), ...play};
    const link = node('span', 'Commons link unavailable');
    try {
      const url = new URL(track.page);
      if (url.protocol === 'https:' && url.hostname === 'commons.wikimedia.org') {
        const a = node('a', 'Commons'); a.href = url.href; return [track.license || '—', a];
      }
    } catch (_) {}
    return [track.license || '—', link];
  }
  function book(room, path) {
    const b = room.book, out = document.createElement('div');
    if (path === '/hall') {
      const doors = b?.doors || room.doors;
      out.append(node('p', 'door order: ' + (Array.isArray(doors) ? doors.map(d => typeof d === 'string' ? d : d.name || d.path).join(' → ') : 'unavailable')));
      const entries = b?.entries || room.events || [];
      out.append(table(['last entries', 'at'], entries.slice(-10).reverse().map(e => [e.text || e.path, time(e.at)])));
      if (!entries.length) out.append(node('p', 'No entries available.'));
    } else if (!b) out.append(node('p', 'Book unavailable.'));
    else if (path === '/betroom') {
      const rows = [];
      for (const [key, status] of [['open_bets', 'open'], ['settled_bets', 'settled']]) {
        for (const bet of (b[key] || []).slice(-10).reverse()) {
          const pnl = bet.pnl_cents != null ? Number(bet.pnl_cents) / 100 : bet.payout_cents != null && bet.stake_cents != null ? (Number(bet.payout_cents) - Number(bet.stake_cents)) / 100 : null;
          rows.push([status, bet.question || bet.market_id, bet.side, number(pnl)]);
        }
      }
      out.append(table(['status', 'market', 'side', 'PnL · USDC'], rows));
      if (!rows.length) out.append(node('p', 'No bets recorded.'));
    } else if (path === '/musicroom') {
      const rows = [];
      if (b.now_playing) rows.push(['now playing', b.now_playing.title, ...credits(b.now_playing)]);
      else out.append(node('p', 'Nothing playing.'));
      for (const play of (b.plays || []).slice(-10).reverse()) rows.push([time(play.started_at), play.title, ...credits(play)]);
      out.append(table(['play', 'track', 'license', 'source'], rows));
      out.append(node('p', `listener reactions: ${number(b.reactions?.sugar)} sugar · ${number(b.reactions?.shock)} shock`));
    } else out.append(node('p', 'In preparation.'));
    return out;
  }
  function render(state) {
    latest = state;
    const live = state?.live === true && (state.age == null || Number(state.age) < 15);
    for (const block of document.querySelectorAll('[data-room]')) {
      const path = block.dataset.room, room = live ? state.rooms?.[path] : null;
      for (const field of block.querySelectorAll('[data-live]')) {
        const key = field.dataset.live;
        if (key === 'book') { field.replaceChildren(room ? book(room, path) : node('p', 'Book unavailable.')); continue; }
        let value = '—';
        if (key === 'badge') {
          const seen = time(room?.last_exit?.at ?? room?.entered_at);
          value = !live ? 'relay offline' : !room ? 'room unavailable' : room.in_room ? 'she is here' : seen !== '—' ? 'last seen ' + seen : 'not seen yet';
        } else if (room && key === 'in_room') value = room.in_room ? 'yes' : 'no';
        else if (room && key === 'last_exit') value = room.last_exit ? `${time(room.last_exit.at)} · ${room.last_exit.by || '—'}` : 'no exit recorded';
        else if (room) value = number(room[key] ?? room.learning?.[key]);
        field.textContent = value;
      }
    }
  }
  async function tick() {
    try {
      const response = await fetch(origin + '/state', {cache:'no-store', signal:AbortSignal.timeout(8000)});
      if (!response.ok) throw new Error('relay unavailable');
      render(await response.json());
    } catch (_) { render(null); }
    setTimeout(tick, 1000);
  }
  const stage = document.getElementById('bet-stage');
  if (stage) window.mountShow(stage, {audio:false}).onState(render);
  else tick();
})();
