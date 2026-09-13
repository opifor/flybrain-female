import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

const source = await readFile(new URL('./site/relay/src/index.js', import.meta.url), 'utf8');
const {Latest, default: relay} = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
const values = new Map();
const storage = {get: async key => values.get(key), put: async (key, value) => values.set(key, value)};
storage.transaction = async fn => fn(storage);
let latest = new Latest({storage}, {});
const env = {PUBLISH_TOKEN: 'fixture', LATEST: {idFromName: () => 'live', get: () => latest}};
const path = 'https://fixture.test/paintroom/canvas.png';
let response = await relay.fetch(new Request(path, {method: 'POST', body: 'no'}), env, {});
assert.equal(response.status, 401);
assert.equal(values.size, 0);
const bytes = new Uint8Array(220000).map((_, i) => i % 251);
response = await relay.fetch(new Request(path, {method: 'POST', body: bytes,
  headers: {Authorization: 'Bearer fixture'}}), env, {});
assert.equal(response.status, 200);
latest = new Latest({storage}, {});
response = await latest.fetch(new Request(path));
assert.equal(response.headers.get('Content-Type'), 'image/png');
assert.deepEqual(new Uint8Array(await response.arrayBuffer()), bytes);
const gallery = 'https://fixture.test/paintroom/gallery/2023-11-14-2213.png';
await latest.fetch(new Request(gallery, {method: 'POST', body: bytes}));
await latest.fetch(new Request(path, {method: 'POST', body: new Uint8Array([1, 2, 3])}));
assert.deepEqual(new Uint8Array(await (await latest.fetch(new Request(gallery))).arrayBuffer()), bytes);
assert.equal((await latest.fetch(new Request('https://fixture.test/paintroom/gallery/bad.png'))).status, 404);
console.log('3 passed');
