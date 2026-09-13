const slots = {fast: []};
for (const [shelf, count] of [['fast', 6]]) {
  for (let i = 0; i < count; i++) {
    const node = document.createElement('div');
    node.className = 'card empty';
    node.innerHTML = '<div class="category"></div><div class="question"></div><div class="bar"><div class="fill"></div></div><div class="price"></div>';
    document.getElementById(shelf).appendChild(node);
    slots[shelf].push(node);
  }
}
let board = [];
let bookState = {markets: {}, open_bets: []};
const colours = {crypto: '#b99bd9', politics: '#8aaacb', sports: '#9fbe93', other: '#c4b28e'};
function draw() {
  for (const shelf of ['fast']) {
    const items = board.filter(c => c.shelf === shelf);
    slots[shelf].forEach((node, index) => {
      const item = items.find(c => c.slot === index && c.end_at > Date.now() / 1000);
      node.className = item ? 'card' : 'card empty';
      node.dataset.token = item ? item.market_id : '';
      if (!item) return;
      const held = bookState.markets?.[item.market_id]?.open === true;
      node.classList.toggle('held', held);
      node.querySelector('.question').textContent = item.question;
      node.querySelector('.fill').style.width = (item.yes_price * 100) + '%';
      node.querySelector('.category').style.background = colours[item.category.toLowerCase()] || colours.other;
      const remaining = Math.max(0, item.end_at - Date.now() / 1000);
      const brightness = Math.round(55 + 170 * (1 - Math.min(1, remaining / (shelf === 'fast' ? 900 : 604800))));
      node.style.borderColor = `rgb(${brightness},${brightness},${brightness})`;
      node.querySelector('.price').textContent = `YES ${(item.yes_price * 100).toFixed(1)}% / ${Math.ceil(remaining / 60)} min to close / ${item.category}`;
    });
  }
}
async function loadBoard() {
  try {
    const response = await fetch('/betroom/board.json', {cache:'no-store'});
    if (!response.ok) throw Error('board unavailable');
    const data = await response.json();
    board = data.cards || [];
    draw();
  } catch (error) { }
}
async function loadBook() {
  try {
    const response = await fetch('/betroom/public.json', {cache:'no-store'});
    if (!response.ok) throw Error('paper book unavailable');
    const book = await response.json();
    if (!book) throw Error('paper book unavailable');
    bookState = book;
    draw();
  } catch (error) { }
}
loadBoard(); loadBook();
setInterval(loadBoard, 2000);
setInterval(loadBook, 2000);
setInterval(draw, 1000);
