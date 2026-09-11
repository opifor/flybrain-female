// The rig posts its latest state and frame here once every half second; every
// viewer reads the same two objects back through the edge cache. Nothing
// about a viewer ever reaches the machine the fly runs on.

const MAX_BODY = 600 * 1024;
const LIVE_S = 15;

const CACHE = {
  'Cache-Control': 'public, max-age=1, s-maxage=1',
  'Access-Control-Allow-Origin': '*',
};

function text(body, status = 200, extra = {}) {
  return new Response(body, {
    status,
    headers: { 'Content-Type': 'text/plain; charset=utf-8', ...CACHE, ...extra },
  });
}

export class Latest {
  constructor(state, env) {
    this.state = {};
    this.frame = null;
    this.updated = 0;
    this.seq = 0;
  }

  async fetch(request) {
    const url = new URL(request.url);
    if (request.method === 'POST' && url.pathname === '/publish') {
      const form = await request.formData();
      const raw = form.get('state');
      if (typeof raw !== 'string') return text('state missing', 400);
      let parsed;
      try { parsed = JSON.parse(raw); } catch (e) { return text('state is not json', 400); }
      const frame = form.get('frame');
      if (frame && typeof frame !== 'string') {
        this.frame = new Uint8Array(await frame.arrayBuffer());
      }
      this.state = parsed;
      this.updated = Math.floor(Date.now() / 1000);
      this.seq += 1;
      return new Response(JSON.stringify({ ok: true, seq: this.seq }), {
        headers: { 'Content-Type': 'application/json' },
      });
    }

    if (url.pathname === '/state') {
      const age = Math.floor(Date.now() / 1000) - this.updated;
      const body = {
        ...this.state, seq: this.seq, updated: this.updated, age,
        live: this.updated > 0 && age < LIVE_S,
      };
      return new Response(JSON.stringify(body), {
        headers: { 'Content-Type': 'application/json', ...CACHE },
      });
    }

    if (url.pathname === '/frame.jpg') {
      if (!this.frame) return text('no frame yet', 404);
      return new Response(this.frame, {
        headers: { 'Content-Type': 'image/jpeg', ...CACHE },
      });
    }

    if (url.pathname === '/') return text('flybrain relay ' + this.seq);
    return text('not found', 404);
  }
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const stub = env.LATEST.get(env.LATEST.idFromName('live'));

    if (request.method === 'POST') {
      if (url.pathname !== '/publish') return text('not found', 404);
      const auth = request.headers.get('Authorization') || '';
      if (!env.PUBLISH_TOKEN || auth !== 'Bearer ' + env.PUBLISH_TOKEN) {
        return text('unauthorized', 401);
      }
      const len = Number(request.headers.get('Content-Length') || 0);
      if (len > MAX_BODY) return text('too large', 413);
      return stub.fetch(request);
    }

    if (request.method !== 'GET') return text('not found', 404);

    // One second at the edge: with 5,000 viewers polling, the object behind
    // this still sees about one request per second per location.
    const cache = caches.default;
    const hit = await cache.match(request);
    if (hit) return hit;
    const res = await stub.fetch(request);
    ctx.waitUntil(cache.put(request, res.clone()));
    return res;
  },
};
