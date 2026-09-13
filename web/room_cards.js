const roomData = JSON.parse(document.getElementById('room-declaration').textContent);
document.body.className = roomData.path.slice(1);
let musicCards = [];
let currentPlaying = null;
function playingLine() {
  const line = document.querySelector('#status p');
  if (!line) return;
  const card = musicCards.find(card => card.token === String(currentPlaying?.track_id));
  line.textContent = currentPlaying ? 'now playing: ' +
    [currentPlaying.title, card?.artist, card?.license].filter(Boolean).join(' · ') : 'now playing: nothing';
}
function drawCards(cards) {
  if (roomData.path === '/musicroom') {
    musicCards = cards;
    playingLine();
  }
  if (roomData.path === '/hall') {
    document.getElementById('status').textContent = 'door order: ' + cards.map(card => card.name).join(' · ');
  }
  document.getElementById('cards').replaceChildren(...cards.map(card => {
    const node = document.createElement('div');
    node.className = 'card'; node.dataset.token = card.token;
    if (roomData.path === '/gameroom') node.classList.toggle('resting', !!card.resting);
    if (roomData.path === '/paintroom' && card.colour) {
      const swatch = document.createElement('div'); swatch.className = 'swatch';
      swatch.style.setProperty('--paint', card.colour); node.append(swatch);
    }
    if (card.area_scale != null) {
      const scale = Math.sqrt(card.area_scale);
      node.style.width = (268 * scale) + 'px';
      node.style.height = (280 * scale) + 'px';
    }
    const name = document.createElement('div'); name.className = 'name';
    name.textContent = card.address ? card.address.slice(0, 4) + '...' + card.address.slice(-4) : card.name;
    if (card.address) node.title = card.address;
    const detail = document.createElement('div'); detail.className = 'detail';
    detail.textContent = roomData.path === '/gameroom' ? '' : roomData.path === '/hall' ? (card.preview || '') : roomData.path === '/musicroom' ?
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

if (roomData.path === '/gameroom') {
  async function loadScore() {
    try {
      const response = await fetch('/gameroom/public.json', {cache:'no-store', signal:AbortSignal.timeout(4000)});
      if (!response.ok) return;
      const score = (await response.json()).this_hour;
      if (!score) return;
      document.getElementById('status').textContent = score.picks ?
        `this rule: ${score.picks} picks · ${score.sweet} sweet · hit rate ${Math.round(score.hit_rate * 100)}%` :
        'this rule: no picks yet';
    } catch (error) { /* The next reading brings the score back. */ }
  }
  loadScore(); setInterval(loadScore, 1000);
}

if (roomData.path === '/paintroom') {
  const canvas = document.getElementById('paint-canvas');
  setInterval(() => { canvas.src = '/paintroom/canvas.png?t=' + Date.now(); }, 2000);
  document.getElementById('status').textContent = 'one mark where she stands; every canvas stays in the gallery';
}

if (roomData.path === '/musicroom') {
  const line = document.createElement('p'); line.textContent = 'now playing: nothing';
  const audio = document.createElement('audio'); audio.preload = 'none';
  document.getElementById('status').append(line, audio);
  let playKey = null;
  async function loadPlaying() {
    try {
      const response = await fetch('/musicroom/public.json', {cache:'no-store', signal:AbortSignal.timeout(4000)});
      if (!response.ok) return;
      const playing = (await response.json())?.now_playing;
      currentPlaying = playing;
      playingLine();
      const key = playing ? JSON.stringify([playing.track_id, playing.started_at]) : null;
      if (key === playKey) return;
      playKey = key;
      audio.pause();
      if (!playing) {
        audio.removeAttribute('src'); audio.load(); line.textContent = 'now playing: nothing'; return;
      }
      audio.onloadedmetadata = () => {
        if (playKey !== key) return;
        audio.currentTime = Math.max(0, Math.min(playing.duration, Date.now() / 1000 - playing.started_at));
        audio.play().catch(() => { /* Playback can resume when the room permits sound. */ });
      };
      audio.src = '/musicroom/track/' + encodeURIComponent(playing.track_id);
      audio.load();
    } catch (error) { /* The next reading brings the public clock back. */ }
  }
  loadPlaying(); setInterval(loadPlaying, 1000);
}
