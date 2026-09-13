const roomData = JSON.parse(document.getElementById('room-declaration').textContent);
document.body.className = roomData.path.slice(1);
function drawCards(cards) {
  document.getElementById('cards').replaceChildren(...cards.map(card => {
    const node = document.createElement('div');
    node.className = 'card'; node.dataset.token = card.token;
    if (card.area_scale != null) {
      const scale = Math.sqrt(card.area_scale);
      node.style.width = (268 * scale) + 'px';
      node.style.height = (280 * scale) + 'px';
    }
    const name = document.createElement('div'); name.className = 'name';
    name.textContent = card.address ? card.address.slice(0, 4) + '...' + card.address.slice(-4) : card.name;
    if (card.address) node.title = card.address;
    const detail = document.createElement('div'); detail.className = 'detail';
    detail.textContent = roomData.path === '/musicroom' ?
      card.artist + ' / ' + card.license + ' / ' + Math.round(card.duration) + ' seconds' :
      card.holding_days != null ? card.holding_days + ' days held / fixture' : card.room.commit_means;
    node.append(name, detail); return node;
  }));
}
async function loadCards() {
  try {
    const response = await fetch(roomData.path + '/board.json', {cache:'no-store', signal:AbortSignal.timeout(4000)});
    if (!response.ok) throw Error('board unavailable');
    drawCards((await response.json()).cards || []);
  } catch (error) { drawCards([]); }
}
loadCards(); setInterval(loadCards, 2000);

if (roomData.path === '/musicroom') {
  const line = document.createElement('p'); line.textContent = 'now playing: nothing';
  const audio = document.createElement('audio'); audio.controls = true; audio.preload = 'none';
  document.getElementById('cards').after(line, audio);
  let playKey = null;
  async function loadPlaying() {
    try {
      const response = await fetch('/musicroom/public.json', {cache:'no-store', signal:AbortSignal.timeout(4000)});
      if (!response.ok) return;
      const playing = (await response.json())?.now_playing;
      const key = playing ? JSON.stringify([playing.track_id, playing.started_at]) : null;
      if (key === playKey) return;
      playKey = key;
      audio.pause();
      if (!playing) {
        audio.removeAttribute('src'); audio.load(); line.textContent = 'now playing: nothing'; return;
      }
      line.textContent = 'now playing: ' + playing.title;
      audio.onloadedmetadata = () => {
        if (playKey !== key) return;
        audio.currentTime = Math.max(0, Math.min(playing.duration, Date.now() / 1000 - playing.started_at));
        audio.play().catch(() => { line.textContent = 'now playing: ' + playing.title + ' / press play to hear it'; });
      };
      audio.src = '/musicroom/track/' + encodeURIComponent(playing.track_id);
      audio.load();
    } catch (error) { /* The next reading brings the public clock back. */ }
  }
  loadPlaying(); setInterval(loadPlaying, 1000);
}
