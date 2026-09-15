# flycoinrh

A real fruit fly brain, simulated neuron by neuron, driving the
[pons launchpad](https://www.ponsfamily.com/launchpad) on Robinhood Chain.

165,122 neurons. 10,228,000 signed synaptic connections. Every one of them
measured from an actual male *Drosophila melanogaster* by electron microscopy —
not invented, not sampled from a distribution, not a neural network "inspired
by" a brain.

This is the Robinhood Chain half. The Solana half — same brain, pump.fun —
lives at [ad7584/flycoin](https://github.com/ad7584/flycoin).

## What it actually does

Press START and a real Chromium opens ponsfamily.com/launchpad. Its screenshots
are sampled through the fly's **892 retinotopic hex columns** into L1 and L2 —
the lamina monopolar cells that are the direct postsynaptic targets of
photoreceptors R1–R6. 165,122 neurons integrate. The cursor comes back out of
the descending neurons a fly actually walks with:

| neuron | what it does in a fly | what it does here |
|---|---|---|
| **DNa02** left vs right | steering — a fly turns by left/right asymmetry | cursor x |
| **DNa01** | forward walking | cursor y |
| **MDN** | the Moonwalker descending neuron — walking backwards | reverse |
| **DNp09** | stopping | the click |

Then it connects the wallet, accepts the launchpad's terms, uploads the token
image, fills the form — name, ticker, description and the `x.com/` handle —
picks the paired asset out of a 57-item list of tokenised equities, opens
**Advanced**, sets the creator tax, and launches.

## The fly is loose on the internet

`roam.py` gives it a browser and no instructions. A page is screenshotted,
sampled through the 892 hex columns, and 165,122 neurons decide where the
cursor goes. If a click lands on a link, the fly is somewhere new. When its
forward drive pushes past the bottom of the window the page scrolls, so it
walks down a page the way it walks across one.

It is watchable live at **[flybrain.online](https://flybrain.online)** — the
page it is looking at, the neurons firing, and what its descending neurons are
doing, all read out of the running simulation.

```bash
py roam.py            # http://localhost:4660, no start button
```

There is no start and no stop. It roams when the process is up, and if a run
dies it waits six seconds and starts another life.

### The rails, and why each one is there

A random clicker on the open internet, streamed publicly, from a machine that
also holds a funded wallet, is a genuinely bad idea unless it is fenced.

- **No wallet.** This browser gets no key, no provider and no extension. The
  roaming browser and the launching browser share nothing but the brain.
- **No keyboard.** The fly cannot type, so it cannot fill a field, write a
  message or answer a prompt.
- **Every click is checked before it lands.** Anything that reads as a submit,
  an upload, a payment or a sign-in is vetoed, and the veto count is on screen.
- **A domain fence.** The first thing built was a keyword blocklist; the first
  thing tested was `p0rn.com`, which walked straight through it. Keyword
  filters do not hold, so the real control is an allowlist of link-rich
  domains. `FLY_ROAM_OPEN=1` removes the fence and should not be left on for an
  unattended public stream.
- No downloads, no popups, no dialogs, and a hop budget so a dead end does not
  become a permanent home.

### What the readouts actually are

Nothing on that page is decoration. `flysim` was extended to report it:

| on screen | what it is |
|---|---|
| neurons firing | a per-neuron bit set on every spike in the window |
| spikes/sec | total spikes divided by simulated time |
| membrane | mean membrane potential at the end of the window |
| visual / motor | firing neurons intersected with L1/L2 and the DN groups |
| the scatter | those neurons at their **measured soma coordinates** |
| DNa02 / DNa01 / MDN / DNp09 | the recorded rates already driving the cursor |

`FlyPilot.step(detail=True)` returns the extra readout as a fifth value, so
every existing caller still unpacks four and is unaffected.

The site itself is in `site/` — a static page on Vercel plus one serverless
function that proxies the chain, because the public Robinhood node
intermittently answers `Access-Control-Allow-Origin: *,*`, which browsers
refuse. The live feed comes from the hosted roaming service over a websocket;
if that service is unreachable the page falls back to a published tunnel address.


### The voice

The fly has no language, so its journal is written for it, and `voice.py` is
the writer. Observe: pull `/state` from the live roamer, the live token page
and the on-chain launch constants into one packet. Read: fetch a short
allowlist of real pages (its own token page, its own site, the pages the fly
itself walked through, and a few reference pages on memecoins and tokenised
stocks) and pass excerpts in. Write: a language model drafts a first-person
entry from that packet and nothing else. Check: every number in the draft must
appear in the packet, and any trading or hype language fails it; a rejected
draft is dropped, there is no second draft, and nothing edits the text. What
it keeps in its journal is checked the same way before it is kept. Post,
through `xpost.py`, which records every post before it is sent, caps posts
per day and refuses repeats and near-repeats. There is no command that posts
text by hand: the only route to the fly's account is a draft that passed the
check. The offline `stub` model, used by the tests, writes to its own journal
and can never post. Two things in this project are invented, and both are
labelled: the reward signal in the mushroom body, and the words. Everything
else is a measurement.

```bash
py voice.py --once --dry      # observe, read, write one entry; post nothing
py voice.py --loop            # every FLY_VOICE_EVERY_H hours
py voice.py --show            # the journal so far
```

## Why Robinhood Chain is the better half of this project

pump.fun's backend answers `401 Unauthorized` to an injected wallet, so its own
Create button can never complete a launch — the Solana repo has to bypass the
site entirely and mint through a signed transaction.

The pons launchpad **accepts the injected EIP-1193 wallet directly**. It
auto-connects with no modal, `eth_chainId` returns `0x1237`, `personal_sign`
round-trips. So here the site's own button is the real path — and on
2026-09-10 the fly's click went all the way through it to a mined block.

## It launched

The fly read the form through its retina and typed into it. The rig chose the
paired asset, opened **Advanced**, set the creator tax, clicked **Launch
token**, then clicked **Confirm** in the launchpad's own dialog. That click
produced exactly one `eth_sendTransaction`, which was signed in Python and
broadcast. Three of the launches, including the real one:

| | first launch | paired against GOOGL | **$FLYBRAIN** |
|---|---|---|---|
| token | test (TEST) | test (TEST) | flybrain (FLYBRAIN) |
| contract | first address below | second address below | third address below |
| transaction | `0x1b3cda17…45484932` | `0x9602a50f…00e5aca2` | `0x63b2164f…0d12a4f1c` |
| block | 59557979 | 59581451 | 59614342 |
| creator | `0x739C…bFc3` | `0x739C…bFc3` | `0x6ce4085E…b42A` (a fresh wallet) |
| pair | ETH, graduates at 4.2 ETH | **GOOGL**, graduates at 24.2 GOOGL | **GOOGL** |
| tax | 2.00% | 2.00% | 1.00% |
| cost | 0.000973 ETH | 0.000979 ETH | 0.000977 ETH |

Contract addresses, in table order:

- `0xd00d0419651c893e8c04edf5e0e074e950c370d3`
- `0xcc80a38afd807bfed1b9c21b6f236ea8ee651dc3`
- `0x4eb990547bce4a982432ca88cf5fae7eed1a2d35`

Every `status` `0x1`, every one 1,000,000,000 supply fixed at launch. The
test launches came from the first wallet; the real one, $FLYBRAIN, from a
second wallet created for it. Its creator fees accrue as GOOGL and are shown
on [its token page](
https://www.ponsfamily.com/launchpad/0x4eb990547bce4a982432ca88cf5fae7eed1a2d35)
— read them there rather than here, because they move. The first launch in full:

| | |
|---|---|
| token | **test (TEST)** |
| contract | `0xd00d0419651c893e8c04edf5e0e074e950c370d3` |
| transaction | `0x1b3cda17f6456c9a4a67989770be97812e6ca67b3f1f1fb85d2ff04645484932` |
| block | 59557979, status **SUCCESS**, 3,621,799 gas at 0.13 gwei |
| creator | `0x739Ccc9dd8Ed6412F00782927dbd087c4e72bFc3` — the fly's wallet |
| creator fee | 2% (trade fee 3.00%, 2.00% to the creator) |
| cost | 0.000973 ETH — 0.0005 launch fee plus 0.000473 gas |

- https://www.ponsfamily.com/launchpad/0xd00d0419651c893e8c04edf5e0e074e950c370d3
- Look up the full transaction above at https://robinhoodchain.blockscout.com/

Read the receipt yourself rather than taking the table's word for it:

```bash
curl -s https://rpc.mainnet.chain.robinhood.com \
  -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"eth_getTransactionReceipt","params":[
"0x1b3cda17f6456c9a4a67989770be97812e6ca67b3f1f1fb85d2ff04645484932"]}'
```

`from` is the fly's wallet, `status` is `0x1`, and among the logs is a fresh
ERC-20 at `0xd00d…70d3` whose `name()` returns `test` and `symbol()` returns
`TEST`.

### The paired asset

pons pairs a new token against something already on Robinhood Chain, and what
is on Robinhood Chain is mostly tokenised equities — the menu is **57 assets**:
NVDA, SPCX, GOOGL, TSLA, GME, AAPL, SPY, and so on down to gold, oil and
Treasuries. The default is ETH. `set_pair_asset()` changes it, and the choice
is real: graduation goes from `4.2 ETH` to `24.2 GOOGL`.

The launch fee stays in ETH either way — the page says `GOOGL pair, ETH 0.0005
due` — so pairing against an equity needs none of that equity in the wallet.

```bash
FLY_RH_PAIR=GOOGL FLY_RH_TAX=2 py rhlive.py --port 4651
```

Two things about that menu are worth knowing if you automate it. It is a 262px
window onto a 2,064px list with **its own** scrollbar, so page scrolling cannot
reach inside it — `smooth_scroll_in()` eases the container's own `scrollTop`,
because `scrollIntoView` teleports and the list would cut from ETH to GOOGL
between two frames. And Playwright's `get_by_role("button", name="GOOGL")`
never resolves against it; the rows have to be found by `textContent` and
clicked at coordinates.

### Step 06: it learns now

`mushroom.py` is the one place in this project a weight is allowed to move,
and it moves where a fly's weights actually move — the Kenyon cell to MBON
synapse, under dopamine.

The rule is the measured one. A Kenyon cell active shortly before a
dopaminergic neuron fires has **that synapse depressed**, not strengthened.
Learning in a fly is subtraction: the mushroom body starts able to drive every
response and experience carves away the ones that did not pay. So there is no
potentiation here, only depression with a floor and a slow drift back toward
baseline standing in for forgetting.

Which MBONs count as reward-side and which as punishment-side is **not
hardcoded from a table**. For each MBON, total PAM input weight is compared
against total PPL1 input and the stronger wins. That split puts MBON01, 02 and
03 on the reward side and MBON04, 10 and 11 on the punishment side, which is
where the literature puts them — a good sign it is finding real structure
rather than noise.

```
44,042 KC->MBON synapses     27,939 reward-side     14,349 punish-side
```

Measured, with controls — twenty rewarded encounters with one view:

| population | change | expected |
|---|---|---|
| reward-side MBONs | **−6.0%** | depressed, it was the addressed compartment |
| punishment-side MBONs | −0.9% | ~0, never addressed |
| Kenyon cells | +0.3% | ~0, upstream of the synapse that changed |

**The reward signal is not real, and the module says so in as many words.** A
fly is rewarded by sugar, not by reaching a web page. Novelty stands in for it
here, and that is a modelling choice made by a person — the fly has no say in
it. The circuit, the plasticity site and the direction of the rule are the
parts that are real.

### Where it roams, and where it does not

The open web, plus the chain it launched its own token on: Wikipedia,
Wikimedia Commons, Wikisource, Hacker News, Project Gutenberg, Open Library,
xkcd, arXiv — and the pons launchpad, Blockscout, and the fly's own token page.

Four places were tried and dropped, all for the same reason: a real browser
gets nothing usable from them.

| tried | what a headless browser actually gets |
|---|---|
| Google | 335 chars behind an "unusual traffic" wall |
| X | 623 chars of "Continue with phone" |
| old.reddit | blocked outright |
| archive.org | 0 chars — paints nothing headless, even at `networkidle` |

Open Library stands in for the Internet Archive, since it renders. The list is
what it is because a retina needs a page that exists, not because those sites
were uninteresting.

Keeping it on two domains was tried too, and the failure was quieter: 93 pages
and 110 clicks in 49 minutes across **6 unique pages**. It was moving the whole
time and going nowhere.

Trade controls are blocked and vetoed now that it roams a launchpad. It has no
wallet and a trade is impossible, but the claim was that every click is
checked, and it did once reach a "Buy token" page before that was tightened.

### Why there is no object store in the path

The public feed used to push a frame and a summary to a blob store twice a
second. That suspended the store on operation count — thirteen megabytes held,
every read answering `403` — and took the live feed down with it. Before that
it had a subtler problem: the CDN answered `X-Vercel-Cache: HIT` with an `Age`
of twenty seconds on a fixed pathname no matter what cache headers went with
the upload, because public blobs are treated as immutable.

So the fly opens a cloudflared quick tunnel instead and the socket carries
frames, telemetry and events for free. The only thing published anywhere is
where the tunnel is — `site/web/live.json`, written when the address changes,
which the page reads. Quick tunnel addresses are random and change every run,
so nothing is hardcoded.


### Waiting for the chain, not for the click

A launch that had already succeeded looked exactly like a hang. The run loop
broke as soon as the page *asked* for a signature, so the rig declared itself
done about two seconds later — with the launchpad still showing "Confirming",
the recording cut, and the token appearing on-chain a few seconds after
everything had stopped.

The loop now waits for the receipt, on camera, and `send_transaction` takes
`wait_receipt=False` so the page gets its hash immediately: it is blocked on
that call and cannot render its own confirming state until the hash returns.

Then it ends where pump.fun would. pons does **not** redirect after a launch —
it leaves you on the empty create form — so `show_coin_page()` reads the token
address out of the receipt logs (the contract that answers `name()` and
`symbol()`), opens that token's page, accepts the terms gate that navigating
re-arms, and scrolls down it. The last thing on screen is the coin.

### The socials field

The X handle is `input[placeholder="handle"]`, `aria-label="X profile handle"`,
behind an `x.com/` prefix; Telegram sits next to it as `community`. Neither has
a name or an id, so the placeholder is the only stable handle on them. It is
typed like every other field and set by `FLY_RH_X`.

It is also optional on the form, and the rig treats it that way — a missing
field logs and the run continues rather than dying on a selector.

> The default is `elonmusk`, which is a **test value**. It has only ever been
> typed in dry runs. Putting a real person's handle on a live token presents
> that token as theirs, which is impersonation and gets both the token and the
> creator wallet flagged. Set `FLY_RH_X` to something you own before any live
> launch, or clear it.

### Dark mode was a flip, not a set

`go_dark()` clicks the site's theme *toggle*. That turned `/create` dark, and
then the coin page — which the site already remembered as dark — got flipped
back to **light** for the closing shot. It now measures the body background's
luma first and only flips when it has to, so the run both starts and ends dark.

### The bug that made the first attempt look like a success

The first live run reported a signed transaction and then nothing: the balance
never moved. `hexbytes >= 1.0` changed `.hex()` to return the raw hex *without*
the `0x` prefix, so `eth_sendRawTransaction` rejected the payload — and because
the failure came back through `page.expose_function`, the launchpad swallowed
it and the page just sat there. `send_transaction` now re-prefixes, logs a
rejection loudly, and polls for the receipt so a silent failure is not
possible.

## Check it yourself

**The chain.** Robinhood Chain is an Arbitrum Nitro L2 — chain id **4663**, RPC
`https://rpc.mainnet.chain.robinhood.com`, gas in ETH at about 0.13 gwei.

**The wallet.** `py rhwallet.py new` generates a secp256k1 keypair, writes the
secret straight into gitignored `.env`, and prints only the address. It is never
printed, never returned, never passed through a chat window.

**The transaction path.** `py rhdryrun.py` exercises every step except the
broadcast: chain id, nonce, gas price, a real signed transaction, and — the
part that matters — recovering the signature and checking it against the
wallet's own address. Nothing is broadcast; there is no code path in that file
that can send.

```
chain id        4663 ok
nonce           0
gas price       0.1358 gwei
signed tx       110 bytes
recovered from  0x739Ccc9d…bFc3  MATCHES
estimateGas     21000 units
```

**The connectome.** CC-BY, from a public bucket, no account and no key:

```
https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/
  body-annotations-male-cns-v1.0-minconf-0.5.feather      14 MB
  body-neurotransmitters-male-cns-v1.0.feather            42 MB
  connectome-weights-male-cns-v1.0-minconf-0.5.feather   1.1 GB
```

`py build_graph.py` turns those into 165,122 traced neurons and 10,228,000
signed edges. If your numbers differ from mine, one of us has a bug.

## What is NOT real, stated plainly

- **The fly does not fill the whole form.** It reliably gets the description,
  often the ticker, rarely the name, and does not navigate to the launch button
  on its own. The rig completes whatever it misses, and the on-screen log says
  which fields were which — `by FLY: …  ·  by rig: …`.
- **Light mode breaks it.** The fly's retina is a luminance map and every bit of
  tuning it has was done against dark UI. On the launchpad's default light theme
  it filled **0 of 3** fields; in dark mode, **2 of 3**. The rig switches the
  theme before it starts, and that gap is the clearest evidence its vision is
  doing real work.
- **The idle animation is decoration.** During a run every dot is a neuron at a
  measured soma coordinate. While idle it is a fly-shaped scatter, and the panel
  label changes to say so.
- **The launch is one signature, and the rig arms it.** The launchpad asks for
  a single `eth_sendTransaction`; there is no second approval and no separate
  ERC-20 allowance. But the rig is what presses **Confirm** in the dialog, not
  the fly — the fly's contribution ends at the form and the launch button.
- **The fly does not choose the paired asset.** It cannot read `GOOGL` at 892
  columns; picking a row out of a 57-item list is the rig following
  `FLY_RH_PAIR`. The same goes for the creator tax and the X handle.
- **The test tokens are tests.** `test (TEST)`, launched to prove the path
  end-to-end. It is not a project and nobody should buy it.
- **The voice is a narrator.** The fly has no language. Every journal entry
  and every post on X is written by a language model handed the fly's
  telemetry and the live numbers from its token page, and asked to write in
  the first person. Every number in a draft is checked against that packet;
  a draft with a number that is not in it, or with trading language, is
  thrown away. The neurons, the pages and the fees are real. The words, and
  any "confusion" or "curiosity" in them, are the narrator's.

## Running it

```bash
py rhwallet.py new              # create the wallet, then fund it (~0.002 ETH)
py rhdryrun.py                  # prove the signing path, spend nothing
py rhlive.py                    # http://localhost:4651, press START
py record.py --port 4651        # record the run to build/recordings/
```

A launch costs about **0.001 ETH** all in, so ~0.002 ETH in the wallet is
enough for a first one with room for the gas estimate to be wrong.

Two flags gate everything, both in `.env`, both off by default:

- `FLY_ALLOW_BROWSER=1` — required before a browser will open against a real
  site at all. A button in a web page is not a strong enough guard for that.
- `FLY_RH_LIVE=1` — required before any transaction is signed. Funding the
  wallet does not, on its own, arm anything.

## Fork it

```bash
git clone https://github.com/fruitflydev/flycoinrh
cd flycoinrh
pip install -r requirements.txt
python -m playwright install chromium

# the connectome itself - 1.1 GB, CC-BY, no account and no key
# (URLs under "Check it yourself" below), into data/
py build_graph.py            # -> build/graph.npz, 165,122 neurons

cp .env.example .env         # then set FLY_ALLOW_BROWSER=1
py roam.py                   # http://localhost:4660
```

MIT for the code. The connectome is **not ours to license** and stays CC-BY
wherever it goes — keep the attribution, it is the whole reason any of this is
real.

Things worth pointing it at that we have not:

- **A different readout.** The cursor comes out of DNa02, DNa01, MDN and DNp09
  because those are what a fly walks with. Nothing says the output has to be a
  cursor.
- **The olfactory channel.** 2,635 ORNs across 53 receptor types are sitting
  there unused. cVA through ORN_DA1 drives pC1 at 222 Hz untrained, so the
  pathway works — it just has nothing plugged into it.
- **A real reward.** Ours is novelty, which is invented. Anything measurable
  and honest would be better.
- **Somewhere else entirely.** A game, a robot, a microscope. The brain does
  not know it is on a launchpad.

If you build something with it, open an issue — we would rather see it than
not.


## A female in the room

`courtship.HerBody` is a second body in `backrooms_world.Room`, with a
139,255-neuron female brain built from FlyWire FAFB v783.
He sings, she hears through JO-A and JO-B, and her pC1 and vpoDN are read.
The published v5 run pairs six conditions on ten seeds for 20 seconds each;
the v6 addendum pairs gated and p1drive against those v5 song records.

Build the male graph as above, then get the six female CSV exports from
[FlyWire Codex](https://codex.flywire.ai/). An account is required to export;
the data stays CC-BY 4.0. Put these files in `data/female/`:

- `classification.csv.gz`
- `consolidated_cell_types.csv.gz`
- `neurons.csv.gz`
- `column_assignment.csv.gz`
- `coordinates.csv.gz`
- `connections_princeton.csv.gz`

```bash
py build_graph_female.py
py courtship_experiment.py --protocol v5 --quick 1 --out build/courtship_smoke
py courtship_experiment.py --protocol v5 --out build/courtship_local
py courtship_experiment.py --protocol v6 --baseline build/courtship_experiment.json --brain flysim_gpu.FlyBrainGPU --out build/courtship_addendum_local
py graft_sag.py
py courtship_experiment.py --protocol v7 --brain flysim_gpu.FlyBrainGPU --out build/courtship_v7_local
py restore_sag.py
py calibrate_sag.py
py courtship_experiment.py --protocol v8 --brain flysim_gpu.FlyBrainGPU --out build/courtship_v8_local
py courtship_experiment.py --protocol v9 --brain flysim_gpu.FlyBrainGPU --out build/courtship_v9_local
py courtship_experiment.py --protocol v10 --male-scale 0.9 --brain flysim_gpu.FlyBrainGPU --out build/courtship_v10_local
py courtship_experiment.py --protocol v11 --male-scale 0.9 --brain flysim_gpu.FlyBrainGPU --out build/courtship_v11_local
py functional_sign.py
py courtship_experiment.py --protocol v12 --brain flysim_gpu.FlyBrainGPU --out build/courtship_v12_local
py courtship_experiment.py --protocol v13 --male-scale 0.9 --brain flysim_gpu.FlyBrainGPU --out build/courtship_v13_local
py courtship_experiment.py --protocol v14 --male-scale 0.9 --brain flysim_gpu.FlyBrainGPU --out build/courtship_v14_local
```

For the graft, first download the public BANC v888 compiled data into
`data/banc/`, with no login: [banc_888_meta.feather](https://storage.googleapis.com/lee-lab_brain-and-nerve-cord-fly-connectome/compiled_data/banc_888/banc_888_meta.feather)
(about 57 MB) and [banc_888_edgelist_simple_v3.feather](https://storage.googleapis.com/lee-lab_brain-and-nerve-cord-fly-connectome/compiled_data/banc_888/banc_888_edgelist_simple_v3.feather)
(about 359 MB). The same files are in
`gs://lee-lab_brain-and-nerve-cord-fly-connectome/compiled_data/banc_888/`.
Attribution: Bates, Phelps, Kim et al., Nature 2026 (BANC); title to be confirmed.
See NOTICE for the data attribution and license confirmation caveat.

Quick runs use two seeds and 80 steps. Add `--brain flysim_gpu.FlyBrainGPU`
to the v5 commands to use the GPU for both brains, as the published run did.
The addendum must use the same brain class as its baseline.
Each prefix gets `_experiment.json`, `_trajectories.npz`, `_trajectories.png`
and `_report.md`. The published prefixes, `build/courtship`,
`build/courtship_addendum`, `build/courtship_v7`, `build/courtship_v8`,
`build/courtship_v9`, `build/courtship_v10`, `build/courtship_v11`,
`build/courtship_v12`, `build/courtship_v13` and `build/courtship_v14`, are refused, including case variants and file aliases.

The evidence is in [the v5 report](build/courtship_report.md) and
[the v6 addendum](build/courtship_addendum_report.md); the addendum records
its baseline's SHA256. Support requires a paired difference above two
standard errors across ten seeds; P5 and P13 require both comparisons.

| Protocol | Prediction | Verdict |
|---|---|---|
| v5 | P1: her vpoDN, song > silence | supported |
| v5 | P2: her pC1, song > silence | supported |
| v5 | P3: timing, song > jittered | not supported |
| v5 | P4: approach, song closer than silence | not supported |
| v5 | P5: pIP10 and delivered song, song > mute | not supported |
| v5 | P6: her vpoDN, song > mute | not supported |
| v5 | P8: his P1, song > noscent | not supported |
| v5 | P9: her vpoDN, virgin > mated | not supported |
| v5 | P11: his LC10a, sight > no sight | not supported |
| v6 | P9': her vpoDN, v5 song > gated | not supported |
| v6 | P13: pIP10 and delivered song, p1drive > v5 song | supported |
| v6 | P14: her vpoDN, p1drive > v5 song | supported |
| v7 | P17: her vpoDN, virgin_song > mated_song; +61.8 Hz, SE 0.94 | supported |
| v7 | P18: her vpoDN, virgin_song > virgin_silence; -0.4 Hz, SE 1.13 | not supported |
| v7 | P19: her pC1, virgin_song > mated_song; +34.3 Hz, SE 0.73 | supported |

In v5, song met the accept rule on nine of ten seeds, with approach on three and retreat on seven; silence met it on none, with approach on one and retreat on nine. Accept means vpoDN above zero in at least three windows; song produced some vpoDN activity on all ten seeds, while silence produced none.

She hears him through the waveform: song raised her vpoDN and pC1 over silence. Timing did not beat a copy with the same energy, and song did not bring them closer. Removing her scent did not lower his P1; cutting his P1 outputs did not lower his pIP10 or song, and sight did not establish an increase in his LC10a. In the part-one graph, the transmitter-sign rule dropped her SAG outputs, as [the later audit explains](build/courtship_v8_report.md#limitations); closing pC1 by hand did not establish a no. Driving his P1 from above did raise his pIP10, the song reaching her, and her vpoDN. These unsupported comparisons do not establish that their effects are exactly zero.

What was chosen or missing in part one:

- Her ear now hears a waveform in 5 ms slices and her brain runs the full 50 ms of every step; effects are smaller in this regime than in the first run.
- In the built graph used by v5/v6, the sex-peptide state input has no outputs; gated cuts pC1 outputs by hand. The v8 audit below corrects the earlier anatomical explanation: her SAG export contains synapses that the transmitter-sign rule removed.
- p1drive is an intervention.
- Her eye is blind; dark and silence coincide. Her raw excitation scale is 1.0 by choice.
- vpoDN is DNp37 by alias, two cells; pC1a-e has ten cells. His P1 is an uncertain dictionary group of 86 cells; contact cells carry a putative ppk23 label.
- Her scent is a chosen drive, not a measured plume; cVA is zero with no other male. She has no pheromone input.
- Song amplitude comes from pIP10; mode uses motor means near ceiling. Pulse rhythm and carriers are synthesis choices, not wing mechanics.
- The ear filter uses the whole current block, with boundary effects and lookahead. Jitter changes pulse density; matching trial energy does not match local envelopes or spectra. Ear clipping is recorded per trial.
- He is inside the loop, so distance includes both bodies. No adaptation mechanism was added or established.
- Gains, motion mappings, start geometry and accept rules are chosen. SpsP identity is unverified; oviDN is a readout without an ovipositor body. Male eye and soma-side availability are recorded per trial.

[The first run, with a rate ear](build/courtship_v3_report.md), is kept for comparison.

### Part two: she can say no

**Protocol v8 restores her own measured SAG synapses.** The [full v8 report](build/courtship_v8_report.md) and [experiment record](build/courtship_v8_experiment.json) support a state-dependent reduction in her receptivity command, with the song still unnecessary for her yes.

Her axon and its synapses are in the FAFB export. The [audit correction](build/courtship_v8_report.md#limitations) identifies a builder limitation: [the transmitter-sign rule](build_graph_female.py) keeps acetylcholine as positive and GABA and glutamate as negative, while serotonin gets sign zero and its edges are dropped from `build/graph_female.npz`. The SAG consensus transmitter is serotonin. The same rule silences outputs from about 2,900 other cells in [the base graph](build/graph_female.npz).

The [restoration record](build/sag_restore.json) counts two AN_SMP_2 cells with 1,375 outgoing synapses and two AN_FLA_SMP_2 cells with 1,952: all 3,327 are restored as individual female pre/post pairs in `build/graph_female_own_sag.npz`. BANC supplied a second individual showing the same route, motivating another look at her export. The [target comparison](build/sag_restore_printout.txt) shows the same pC1a > pC1b > pC1c order in both individuals:

| Target type | Her own synapses | BANC synapses |
|---|---:|---:|
| pC1a | 615 | 317 |
| pC1b | 387 | 204 |
| pC1c | 179 | 131 |

**CHOSEN:** the restored SAG sign is +1, meaning activity encourages the next cell to fire, on the functional evidence from Feng and colleagues cited in [the restoration record](build/sag_restore.json). FAFB consensus serotonin and BANC prediction dopamine do not themselves fix that effect sign. The [v8 protocol](build/courtship_v8_report.md) drives both SAG types, four cells, at a steady 50 Hz for virgin and zero for mated; the upstream sex-peptide sensory neurons, SPSN, are not modelled. Her positive-weight scale stays at 0.7, carried over from v7 without tuning on the v8 ladder. His side is unchanged.

A first run, [v7](build/courtship_v7_report.md), grafted BANC's measured outputs onto her map. The audit then found her own export carries the route; v8 restores her own synapses. The BANC-graft variant remains published in [its full record](build/courtship_v7_experiment.json). Both records support P17 and P19 and do not support P18, as the table below shows; the measured differences change.

The [v8 record](build/courtship_v8_experiment.json) uses the same four conditions and P17/P18/P19/P20 predictions as v7, paired across ten seeds with 400 steps per condition on the GPU. Song delivers his waveform to her; silence zeros it while his brain keeps running. vpoDN is her receptivity command readout and pC1 her receptivity cell group. Hz means spikes per second; SE is the standard error of the paired difference. The [verdict rule](build/courtship_v8_report.md) requires a positive paired mean greater than two SE. Values below are rounded from the linked records.

| Record | Prediction and comparison | Mean difference, Hz | SE, Hz | Verdict |
|---|---|---:|---:|---|
| [v7](build/courtship_v7_experiment.json) | P17: vpoDN, virgin_song − mated_song | 61.79 | 0.94 | supported |
| [v8](build/courtship_v8_experiment.json) | P17: vpoDN, virgin_song − mated_song | 73.76 | 0.96 | supported |
| [v7](build/courtship_v7_experiment.json) | P18: vpoDN, virgin_song − virgin_silence | −0.41 | 1.13 | not supported |
| [v8](build/courtship_v8_experiment.json) | P18: vpoDN, virgin_song − virgin_silence | −0.32 | 1.03 | not supported |
| [v7](build/courtship_v7_experiment.json) | P19: pC1, virgin_song − mated_song | 34.26 | 0.73 | supported |
| [v8](build/courtship_v8_experiment.json) | P19: pC1, virgin_song − mated_song | 38.68 | 0.34 | supported |

The v8 condition means and accept counts come from [the per-seed P20 readouts](build/courtship_v8_experiment.json); P20 is descriptive and has no verdict.

| Condition | Her vpoDN, mean Hz | Her pC1, mean Hz | Accept rule met |
|---|---:|---:|---:|
| virgin_song | 74.00 | 38.73 | 10/10 |
| mated_song | 0.24 | 0.05 | 4/10 |
| virgin_silence | 74.32 | 38.81 | 10/10 |
| mated_silence | 0.00 | 0.00 | 0/10 |

For comparison, [v7 accept counts](build/courtship_v7_report.md#p20-descriptive-no-verdict), in the same condition order, were 10/10, 6/10, 10/10 and 0/10.

P17's state difference is positive on every seed, and P19 supports a state effect in pC1 too. This is a no in the rate comparison, not complete refusal on every trial: [the chosen accept rule](build/courtship_v8_report.md) needs only vpoDN above zero in at least three windows, and mated_song still meets it on four seeds. His P1 and pIP10 readings remain descriptive; they do not establish that he decides or adapts.

**P18 is not supported in the full v8 record.** Virgin silence still produces 74.32 Hz vpoDN and meets the accept rule on all ten seeds. The song-minus-silence difference is small relative to that silence level. Her state can open the gate on its own: the song is still not required for her yes. The [full result and calibration ladder](build/courtship_v8_report.md) do not establish a gate that needs both state and song.

The loop is built end to end: he decides · he sings · she hears · she answers · he adapts. Three of five steps hold, now with a no added to “she answers”; this combines [the earlier song and hearing comparisons](build/courtship_v5_report.md) and [P1-drive results](build/courtship_v6_report.md) with [v8's state comparison](build/courtship_v8_report.md). The open steps, “he decides” and “he adapts”, remain unestablished.

### Part three: he decides, he adapts

This part of the loop did not hold: he decides and he adapts are not established as tested. **v9** pre-registered a dose-response sweep, reducing only his positive connection weights to 0.9, 0.8 and 0.7, with the female setup from v8 and ten paired seeds per scale. Song kept both cues; mute blocked outputs from P1, his candidate decision cell group; noscent removed both scent inputs. P21 required song to exceed mute in both pIP10, his song command neuron, and delivered RMS, the waveform's root-mean-square amplitude. It failed at every scale; P22, P1 song minus noscent, reversed at every scale (means and SE below). Removing scent raised P1 on every seed, but pIP10 fell on two seeds at 0.9. P23 descriptively records song pIP10 means of 7.31, 3.35 and 1.15 Hz across those scales, alongside delivered amplitude, P1, total male activity and her response; these are not additional verdicts. P24 states that LC10a, the visual cell group used for the adaptation test, is not reachable from this eye. Sources: [v9 report](build/courtship_v9_report.md), [record](build/courtship_v9_experiment.json).

**v10** pre-registered a geometry intervention at male scale 0.9: the highest tested scale, chosen by the v9 rule because none established P21. Sight drove LC10a from her measured apparent size and bearing; blind omitted that drive; shuffled replayed it out of order. The female setup stayed at v8, with ten paired seeds. P25 passed: LC10a increased by 14.30 Hz (SE 2.42), confirming that the added drive landed, not that his eye worked. P26 did not establish adaptation: neither neural song amplitude nor mode (pulse-versus-sine balance) tracked the previous window's drive more strongly in sight than shuffled. P27 did not support turning toward her. P28 descriptively showed higher pIP10 with sight than blind (8.55 versus 3.78 Hz) and shorter mean distance (5.73 versus 7.71 mm); both bodies contribute to distance. Sources: [v10 report](build/courtship_v10_report.md), [record](build/courtship_v10_experiment.json).

**v11** pre-registered separate cue removals at male scale 0.9, retaining the v8 female setup and ten paired seeds: song kept both cues, noscent_orn removed only olfactory input, noscent_contact removed only contact input, and noscent removed both. P29 supported increased P1 after olfactory removal, by 6.78 Hz (SE 1.31); P30 did not support an increase after contact removal. P31 required both pIP10 and delivered RMS to increase: olfactory removal passed, contact removal did not. P32 is descriptive, with no verdict: removing both versus olfactory input alone changed P1 by -0.46 Hz (SE 0.31), and removing both versus contact alone changed it by 6.21 Hz (SE 1.40); the record also gives song, her receptivity command and accept rule, distance, approach/retreat and contact exposure. Her scent reaches him as Or47b olfactory drive plus contact drive labelled putative ppk23, an unverified receptor assignment. In this map these inputs take routes with different signs to P1, meaning activity can encourage or suppress downstream firing. The dictionary's vAB3 relay cells are glutamatergic here, so the transmitter-sign rule treats their outputs as inhibitory. Sources: [v11 report](build/courtship_v11_report.md), [record](build/courtship_v11_experiment.json), [input wiring](backrooms_world.py), [dictionary](backrooms_dictionary.py), [male graph](build/graph.npz) and [sign rule](build_graph.py).

#### Four more levers, same answer

**v12: transmitter sign.** The functional-sign graph makes vAB3 outputs positive (+1, encouraging firing) and restores inhibitory GABA outputs for 23 mAL cells labelled "unclear". With ten paired seeds in song, mute and noscent at scales 0.9 and 0.8, P33 did not establish P1 control of song at either scale. P34, P1 song minus noscent, was negative at 0.9 (-1.45 Hz, SE 1.03) and reversed at 0.8 (-2.07 Hz, SE 0.35). The correction did not recover the command chain. Sources: [v12 report](build/courtship_v12_report.md), [record](build/courtship_v12_experiment.json), [sign overrides](build/male_fsign.json).

**v13: contrast eye.** Uniform grey now gives no visual drive; the eye responds to differences from that background. Using the base male graph at scale 0.9, ten paired seeds compared song, mute, noscent_orn (olfactory input removed, contact kept) and blind. P36 did not support more LC10a activity in song than blind (-0.0144 Hz, SE 0.0113). P37 (command control), P38 (P1 response to scent) and P39 (song following the previous window's LC10a activity) were also unsupported; both song amplitude and pulse-versus-sine balance failed the latter comparison against a shifted sequence. Descriptively, his network averaged about 42 Hz per neuron in song, mute and blind, versus 22.7 Hz in noscent_orn. Sources: [v13 report](build/courtship_v13_report.md), [record](build/courtship_v13_experiment.json).

**v14: olfactory dose.** With the contrast eye and male scale 0.9, ten paired seeds compared song, mute and noscent_orn at maximum olfactory drives of 200, 50 and 20 Hz; the delivered input falls with distance. P41 did not support a lower total rate at the lowest dose: song at 200 minus 20 Hz was -1.23 Hz per neuron (SE 0.47), a reversal. Even the lowest tested dose sustained the high-rate state. P42 (P1 control of song) and P43 (P1 response to scent) were not established at any dose. "Ignition" means a window above 30 Hz per neuron: its fraction in song was 0.95625-0.99925 across doses, versus 0.504 without olfactory input; mute ranged from 0.919 to 0.99975. Sources: [v14 report](build/courtship_v14_report.md), [record](build/courtship_v14_experiment.json).

A second adult male brain-and-nerve-cord map does not exist: [MaleCNS v1.0](https://male-cns.janelia.org/) is the newest available map, and [MANC](https://www.janelia.org/project-team/flyem/manc-connectome) contains the nerve cord only.

All table entries are paired mean differences +/- SE (standard error), rounded from those records; Hz means spikes per second. Support requires a positive difference greater than two SE across ten seeds. P21, P31, P33, P37 and P42 require both listed measurements; v9, v12 and v14 additionally forbid a reversal at another tested scale or dose. P26 and P39 compare rank correlations, which measure whether values rise and fall together; their amplitude and mode channels are both shown. P39 subtracts a control made by shifting the LC10a sequence by half a trial, retaining the same one-window lag. RMS and correlation values are unitless; turning is a fraction of windows. The v14 rows show olfactory dose as well as male weight scale; P41 is one comparison across doses.

| Protocol / scale | Prediction and subtraction | Mean difference +/- SE | Verdict |
|---|---|---|---|
| v9 / 0.9 | P21: song - mute | pIP10: 1.1725 +/- 1.7513 Hz; RMS: 0.002246 +/- 0.003041 | not established |
| v9 / 0.9 | P22: P1, song - noscent | -6.3210 +/- 1.2277 Hz | reversed |
| v9 / 0.8 | P21: song - mute | pIP10: 1.2775 +/- 0.6477 Hz; RMS: 0.004244 +/- 0.001986 | not established; RMS alone supported |
| v9 / 0.8 | P22: P1, song - noscent | -2.3188 +/- 0.2425 Hz | reversed |
| v9 / 0.7 | P21: song - mute | pIP10: 0.4225 +/- 0.4586 Hz; RMS: 0.002131 +/- 0.001928 | not established |
| v9 / 0.7 | P22: P1, song - noscent | -1.9853 +/- 0.1340 Hz | reversed |
| v10 / 0.9 | P25: LC10a, sight - blind | 14.3022 +/- 2.4222 Hz | supported |
| v10 / 0.9 | P26: lagged correlation, sight - shuffled | amplitude: 0.006174 +/- 0.033891; mode: -0.010539 +/- 0.041981 | not established |
| v10 / 0.9 | P27: turning toward her, sight - blind | -0.008500 +/- 0.008098 | not supported |
| v11 / 0.9 | P29: P1, noscent_orn - song | 6.7796 +/- 1.3130 Hz | supported |
| v11 / 0.9 | P30: P1, noscent_contact - song | 0.1072 +/- 0.3319 Hz | not supported |
| v11 / 0.9 | P31: noscent_orn - song | pIP10: 15.9900 +/- 6.9886 Hz; RMS: 0.013545 +/- 0.006468 | supported, both |
| v11 / 0.9 | P31: noscent_contact - song | pIP10: 0.4850 +/- 1.2644 Hz; RMS: -0.000404 +/- 0.001281 | not supported |
| v12 / 0.9 | P33: song - mute | pIP10: 1.1025 +/- 2.7380 Hz; RMS: 0.004528 +/- 0.006029 | not established |
| v12 / 0.9 | P34: P1, song - noscent | -1.4493 +/- 1.0293 Hz | not supported; negative |
| v12 / 0.8 | P33: song - mute | pIP10: 3.0475 +/- 2.2487 Hz; RMS: 0.001928 +/- 0.002379 | not established |
| v12 / 0.8 | P34: P1, song - noscent | -2.0658 +/- 0.3541 Hz | reversed |
| v13 / 0.9 | P36: LC10a, song - blind | -0.0144 +/- 0.0113 Hz | not supported |
| v13 / 0.9 | P37: song - mute | pIP10: 0.4525 +/- 2.1572 Hz; RMS: -0.002622 +/- 0.006631 | not supported |
| v13 / 0.9 | P38: P1, song - noscent_orn | -1.7912 +/- 1.1828 Hz | not supported |
| v13 / 0.9 | P39: lagged correlation, song - shifted | amplitude: -0.043805 +/- 0.026932; mode: -0.051251 +/- 0.045995 | not supported |
| v14 / 0.9 / 200 - 20 Hz | P41: total male rate, song | -1.2322 +/- 0.4711 Hz per neuron | not supported; reversed |
| v14 / 0.9 / 200 Hz | P42: song - mute | pIP10: 0.5950 +/- 2.1939 Hz; RMS: -0.002368 +/- 0.006698 | not established |
| v14 / 0.9 / 200 Hz | P43: P1, song - noscent_orn | -1.7883 +/- 1.1806 Hz | not established |
| v14 / 0.9 / 50 Hz | P42: song - mute | pIP10: 1.4750 +/- 6.6954 Hz; RMS: -0.003459 +/- 0.014927 | not established |
| v14 / 0.9 / 50 Hz | P43: P1, song - noscent_orn | -0.8423 +/- 1.2344 Hz | not established |
| v14 / 0.9 / 20 Hz | P42: song - mute | pIP10: 5.9775 +/- 9.4634 Hz; RMS: 0.003278 +/- 0.013880 | not established |
| v14 / 0.9 / 20 Hz | P43: P1, song - noscent_orn | -0.4390 +/- 0.8938 Hz | not established |

**What this means, after the levers.** In this male model, olfactory input at every tested dose drives the whole network into a high-rate state: about 42 Hz per neuron, with ignition on almost every song window. In that state his command cells do not control his song by the registered tests; this does not prove their effect is exactly zero. Cooling, functional sign corrections across three cell groups (her SAG, his vAB3 and mAL), a contrast eye and a lower olfactory dose have not established the missing command chain. The remaining candidates are the network dynamics themselves: firing thresholds (how much input triggers a spike), the refractory period (the pause after a spike), and weight scale (connection strength), calibrated against known behaviours as in the [reference model's validation of feeding and grooming](https://www.nature.com/articles/s41586-024-07763-9); and the synthesis choices that turn neural activity into sound. These are model-level changes, larger than a protocol. "He decides" and "he adapts" stay open until then.

### What comes next

- **Transmitter-sign rule tested.** The narrow functional corrections did not recover his command chain; they do not settle the signs of all other cell groups.
- **Contrast eye tested.** Removing the grey background drive did not establish increased LC10a activity or adaptation.
- **No second male map.** MaleCNS remains the available adult male brain-and-nerve-cord map; MANC cannot replace its brain.
- **Olfactory dose tested.** The lowest tested scent dose still sustained the high-rate state and did not establish command control.
- **Calibrating the model.** Test network dynamics against known behaviours and revisit how neural activity becomes song before claiming decision or adaptation.
- **Her nerve cord.** The full BANC graph is built; her wing, leg and abdominal
  motor neurons are the next readouts.
- **More than one male.** The backrooms already step four bodies; a room with one
  female and several singers asks who she walks beside.
- **A third brain.** The two maps share most of their cell types; a mosaic of the two, run in the same room, is the next experiment, pre-registered like the others.

Further experiments need their own preregistered protocols and published records; model calibration also needs explicit validation against known behaviours.

## Hosting it

The roaming service runs as a single container. Build the graph first, so
`build/graph.npz` and `data/body-annotations.feather` exist, then:

```bash
docker build -t flybrain .
docker run -p 4660:4660 flybrain      # http://localhost:4660
```

To host it on Railway, run `railway up` from a checkout that has the graph
built; the data files are not in git, so a deploy straight from GitHub has
nothing to load. The service reads `PORT` and binds to every interface.

| variable | purpose |
|---|---|
| `PORT` | set by the host |
| `FLY_STATE_DIR` | where `mb_gains.npz` is kept |

Point `FLY_STATE_DIR` at a volume such as `/data` so learning survives redeploys.

The container has no wallet and no chain keys, and never signs anything.

## Credits

Connectome data © HHMI Janelia FlyEM, the Cambridge Connectomics Group and
Google Research, released CC-BY. Simulation approach after Shiu et al. 2024 and
Lappalainen et al. 2024. Not affiliated with any of them, nor with pons or
Robinhood.
