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
    detail.textContent = card.holding_days != null ? card.holding_days + ' days held / fixture' : card.room.commit_means;
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
