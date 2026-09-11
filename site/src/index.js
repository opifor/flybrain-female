// Same-origin proxy to the Robinhood Chain node, as a Worker.
//
// The public node's CORS is unreliable: it intermittently answers
// "Access-Control-Allow-Origin: *,*" - a duplicated header that every browser
// rejects - so reading the chain straight from the page showed "offline" at
// random. This runs at the edge, where CORS does not apply, and the page then
// talks only to its own origin. Everything that is not /api/state falls
// through to the static assets.
//
// It reads. There is no key here and no method in the allowlist that writes.

const TRANSFER = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef';
const FEE_ETH = 0.00055;
const CACHE_CONTROL = 's-maxage=15, stale-while-revalidate=60';

// Lives per isolate; a cold start rescans the logs, which is acceptable.
let holdersCache = { at: 0, holders: null, transfers: null };
const HOLD_TTL = 120000;

async function rpc(url, method, params) {
  const r = await fetch(url, {
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

async function holders(url, token, birth) {
  const now = Date.now();
  if (holdersCache.holders != null && now - holdersCache.at < HOLD_TTL) return holdersCache;
  try {
    const logs = await rpc(url, 'eth_getLogs', [{
      address: token, fromBlock: birth, toBlock: 'latest', topics: [TRANSFER],
    }]);
    const seen = new Set();
    for (const l of logs) if (l.topics.length >= 3) seen.add('0x' + l.topics[2].slice(-40));
    seen.delete('0x' + '0'.repeat(40));
    holdersCache = { at: now, holders: seen.size, transfers: logs.length };
  } catch (e) { /* keep the last good numbers */ }
  return holdersCache;
}

// Constants of a launched token, read once per isolate; the last good answer,
// served whenever the public node rate-limits us. Errors are never cached.
let constCache = { token: null, symbol: null, supply: null };
let lastGood = null;

async function state(env) {
  const url = env.FLY_RH_RPC || 'https://rpc.mainnet.chain.robinhood.com';
  const token = (env.FLY_TOKEN || '').toLowerCase();
  const wallet = env.FLY_WALLET || '';
  const birth = env.FLY_TOKEN_BLOCK || '0x0';
  try {
    if (!token) {
      const blk = await rpc(url, 'eth_blockNumber', []);
      return { ok: true, launched: false, block: int(blk), updated: Math.floor(Date.now() / 1000) };
    }
    // sequential on purpose: the public node rate-limits bursts from one edge
    const blk = await rpc(url, 'eth_blockNumber', []);
    if (constCache.token !== token) {
      const sup = await rpc(url, 'eth_call', [{ to: token, data: '0x18160ddd' }, 'latest']);
      const sym = await rpc(url, 'eth_call', [{ to: token, data: '0x95d89b41' }, 'latest']);
      constCache = { token, symbol: abiString(sym), supply: Number(BigInt(sup)) / 1e18 };
    }
    const bal = await rpc(url, 'eth_getBalance', [wallet, 'latest']);
    const h = await holders(url, token, birth);
    const eth = int(bal) / 1e18;
    lastGood = {
      ok: true,
      launched: true,
      block: int(blk),
      budget_eth: eth,
      launches_left: Math.floor(eth / FEE_ETH),
      token: {
        address: token,
        symbol: constCache.symbol,
        supply: constCache.supply,
        holders: h.holders,
        transfers: h.transfers,
        pair: env.FLY_PAIR || 'GOOGL',
        creator_tax_pct: Number(env.FLY_TAX_PCT || 1),
      },
      updated: Math.floor(Date.now() / 1000),
    };
    return lastGood;
  } catch (e) {
    const err = String(e.message || e).slice(0, 160);
    if (lastGood) return { ...lastGood, stale: true, error: err };
    if (!token) return { ok: false, error: err };
    // The node is rate-limiting this edge. What the launch itself settled is
    // known without asking anyone: say so, and leave the live numbers empty.
    return {
      ok: true, launched: true, stale: true, error: err,
      block: null, budget_eth: null, launches_left: null,
      token: {
        address: token, symbol: env.FLY_SYMBOL || 'HER',
        supply: Number(env.FLY_SUPPLY || 1e9),
        holders: null, transfers: null,
        pair: env.FLY_PAIR || 'GOOGL',
        creator_tax_pct: Number(env.FLY_TAX_PCT || 1),
      },
      updated: Math.floor(Date.now() / 1000),
    };
  }
}

export default {
  async fetch(request, env, ctx) {
    const u = new URL(request.url);
    if (u.pathname !== '/api/state' && u.pathname !== '/api/state/') return env.ASSETS.fetch(request);
    if (request.method !== 'GET') return new Response('method not allowed', { status: 405 });

    // One cache key per edge, regardless of query string, so the node sees at
    // most one request per 15 s from each location.
    const cache = caches.default;
    const key = new Request(u.origin + '/api/state', { method: 'GET' });
    const hit = await cache.match(key);
    if (hit) return hit;

    const st = await state(env);
    const body = JSON.stringify(st);
    const res = new Response(body, {
      headers: { 'content-type': 'application/json', 'cache-control': st.ok ? CACHE_CONTROL : 'no-store' },
    });
    if (st.ok) ctx.waitUntil(cache.put(key, res.clone()));
    return res;
  },
};
