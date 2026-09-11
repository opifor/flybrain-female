// Same-origin proxy to the Robinhood Chain node.
//
// The public node's CORS is unreliable: it intermittently answers
// "Access-Control-Allow-Origin: *,*" - a duplicated header that every browser
// rejects - so reading the chain straight from the page showed "offline" at
// random. This runs server-side, where CORS does not apply, and the page then
// talks only to its own origin.
//
// It reads. There is no key here and no method in the allowlist that writes.

const RPC = process.env.FLY_RH_RPC || 'https://rpc.mainnet.chain.robinhood.com';
const TOKEN = (process.env.FLY_TOKEN || '').toLowerCase();
const WALLET = process.env.FLY_WALLET || '';
const BIRTH = process.env.FLY_TOKEN_BLOCK || '0x0';
const TRANSFER = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef';
const FEE_ETH = 0.00055;

let holdersCache = { at: 0, holders: null, transfers: null };
const HOLD_TTL = 120000;

async function rpc(method, params) {
  const r = await fetch(RPC, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ jsonrpc: '2.0', id: 1, method, params }),
  });
  const j = await r.json();
  if (j.error) throw new Error(j.error.message || 'rpc error');
  return j.result;
}

const int = (h) => (h ? parseInt(h, 16) : 0);

function abiString(x) {
  if (!x || x.length < 130) return '';
  const n = parseInt(x.slice(66, 130), 16);
  let out = '';
  for (let i = 0; i < n; i++) out += String.fromCharCode(parseInt(x.substr(130 + i * 2, 2), 16));
  return out;
}

async function holders() {
  const now = Date.now();
  if (holdersCache.holders != null && now - holdersCache.at < HOLD_TTL) return holdersCache;
  try {
    const logs = await rpc('eth_getLogs', [{
      address: TOKEN, fromBlock: BIRTH, toBlock: 'latest', topics: [TRANSFER],
    }]);
    const seen = new Set();
    for (const l of logs) if (l.topics.length >= 3) seen.add('0x' + l.topics[2].slice(-40));
    seen.delete('0x' + '0'.repeat(40));
    holdersCache = { at: now, holders: seen.size, transfers: logs.length };
  } catch (e) { /* keep the last good numbers */ }
  return holdersCache;
}

export default async function handler(req, res) {
  res.setHeader('Cache-Control', 's-maxage=15, stale-while-revalidate=60');
  try {
    if (!TOKEN) {
      const blk = await rpc('eth_blockNumber', []);
      res.status(200).json({ ok: true, launched: false, block: int(blk),
        updated: Math.floor(Date.now() / 1000) });
      return;
    }
    const [blk, sup, sym, bal] = await Promise.all([
      rpc('eth_blockNumber', []),
      rpc('eth_call', [{ to: TOKEN, data: '0x18160ddd' }, 'latest']),
      rpc('eth_call', [{ to: TOKEN, data: '0x95d89b41' }, 'latest']),
      rpc('eth_getBalance', [WALLET, 'latest']),
    ]);
    const h = await holders();
    const eth = int(bal) / 1e18;
    res.status(200).json({
      ok: true,
      launched: true,
      block: int(blk),
      budget_eth: eth,
      launches_left: Math.floor(eth / FEE_ETH),
      token: {
        address: TOKEN,
        symbol: abiString(sym),
        supply: Number(BigInt(sup)) / 1e18,
        holders: h.holders,
        transfers: h.transfers,
        pair: process.env.FLY_PAIR || 'GOOGL',
        creator_tax_pct: Number(process.env.FLY_TAX_PCT || 2),
      },
      updated: Math.floor(Date.now() / 1000),
    });
  } catch (e) {
    res.status(200).json({ ok: false, error: String(e.message || e).slice(0, 160) });
  }
}
