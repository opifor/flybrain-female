(() => {
  const el = id => document.getElementById(id);
  const origin = new URLSearchParams(location.search).get('relay') || 'https://live.femaleflybrain.com';
  const number = n => typeof n === 'string' && n.includes('/') ? n.split('/').map(Number).reduce((a, b) => a / b) : Number(n);
  const money = n => number(n).toFixed(2);
  const signed = n => (n >= 0 ? '+' : '') + money(n);
  const show = window.paperShow || (el('bet-stage') ? mountShow(el('bet-stage'), {audio:false}) : null);
  function events(book, status) {
    const rows = [], seen = new Set(), refused = new Map();
    const records = [...(book.open_bets || []), ...(book.settled_bets || []),
      ...(status.events || []).filter(e => e.kind === 'refused' || (e.kind === 'fill' && e.action !== 'sell'))];
    for (const e of records) {
      const key = `${e.kind}:${e.seq}`;
      if (seen.has(key)) continue;
      seen.add(key);
      const at = Number(e.at || e.seen_at);
      if (e.kind === 'refused') {
        const minute = Math.floor(at / 60);
        const group = refused.get(minute) || {count: 0, at: 0};
        refused.set(minute, {count: group.count + 1, at: Math.max(group.at, at)});
        continue;
      }
      const side = e.side === 'YES' ? 'Up' : 'Down';
      const market = e.question || 'market';
      const stake = Number(e.stake_cents) / 100;
      let line;
      if (e.kind === 'sold' || (e.kind === 'fill' && e.action === 'sell')) {
        line = `sold ${side} on ${market} at ${money(e.exit_price ?? e.price)}, ${signed(Number(e.pnl_cents) / 100)}`;
      } else if (e.kind === 'fill') {
        line = `bought ${side} on ${market}, ${money(stake)} USDC at ${money(e.price)}`;
      } else if (e.kind === 'settled') {
        line = `settled ${side} on ${market}, ${e.won ?? (e.side === e.outcome) ? 'won' : 'lost'}, ${signed(Number(e.payout_cents) / 100 - stake)}`;
      }
      if (line) rows.push({at, line});
    }
    for (const group of refused.values()) rows.push({at: group.at, line: `${group.count} refusals in this minute`});
    for (const e of status.learning?.last || []) {
      if (e.status !== 'delivered') continue;
      rows.push({at: e.at, line: `${e.sign > 0 ? 'sugar' : 'shock'}, ${e.eligible.length} Kenyon cells`});
    }
    return rows.sort((a, b) => b.at - a.at).slice(0, 60);
  }
  function render(d) {
    const status = d?.betting || {}, book = d?.betroom;
    const live = d?.live === true && Number(d.age) < 15;
    const health = status.bookie;
    const ready = live && book && health?.ok === true && Math.abs(Date.now() / 1000 - health.at) < 15;
    const message = !live ? 'The relay is offline.' : !ready ? 'The paper bookie is unavailable.' : status.in_room ? 'She is in the betting room.' : 'She is not in the betting room.';
    const summary = ready ? `Balance ${money(book.balance)} USDC / ${book.win_count} wins / ${book.loss_count} losses / ${book.open_bets.length} open bets` : 'Paper book unavailable.';
    const rows = ready ? events(book, status) : [];
    if (el('strip')) {
      el('strip').textContent = `${ready ? 'Balance ' + money(book.balance) + ' USDC' : 'Balance unavailable'} / ${ready && status.in_room ? rows[0]?.line || 'No recent activity.' : message} / paper`;
      return;
    }
    el('bet-status').textContent = message;
    el('bet-summary').textContent = summary;
    el('bet-feed').replaceChildren(...rows.map(e => {
      const li = document.createElement('li');
      li.textContent = `${new Date(e.at * 1000).toISOString().slice(11, 19)} UTC / ${e.line}`;
      return li;
    }));
  }
  async function tick() {
    try {
      const r = await fetch(origin + '/state', {cache: 'no-store', signal: AbortSignal.timeout(8000)});
      if (!r.ok) throw new Error('relay unavailable');
      render(await r.json());
    } catch (e) { render(null); }
    setTimeout(tick, 1000);
  }
  if (show) show.onState(render);
  else tick();
})();
