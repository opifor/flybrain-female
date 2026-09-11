# Female Flybrain

A real female fruit fly brain, simulated neuron by neuron, driving the
[pons launchpad](https://www.ponsfamily.com/launchpad) on Robinhood Chain.

139,255 neurons. 3,641,142 signed synaptic connections. Every one of them
measured from an actual female *Drosophila melanogaster* by electron microscopy
— not invented, not sampled from a distribution, not a neural network "inspired
by" a brain.

The male rig is [fruitflydev/flycoinrh](https://github.com/fruitflydev/flycoinrh);
this is the same rig with the other sex's brain in it. The retina, the
descending-neuron readout, the rails and the launch path were all built there
first, and this fork exists because that work was published openly enough to
run a different brain through. Thank you for it.

Her connectome is FlyWire FAFB v783, the female adult brain reconstructed at
Princeton and Cambridge with the FlyWire consortium, released CC-BY 4.0
(Dorkenwald et al., *Nature* 2024; Schlegel et al., *Nature* 2024).

## What it actually does

Press START and a real Chromium opens ponsfamily.com/launchpad. Its screenshots
are sampled through her **retinotopic hex columns** — both eyes on one shared
grid, 785 columns per eye, filled by 783 left and 789 right L1 cells — into L1
and L2, the lamina monopolar cells that are the direct postsynaptic targets of
photoreceptors R1–R6. 139,255 neurons integrate. The cursor comes back out of
the descending neurons a fly actually walks with:

| neuron | count | what it does in a fly | what it does here |
|---|---|---|---|
| **DNa02** left vs right | 1 per side | steering — a fly turns by left/right asymmetry | cursor x |
| **DNa01** | 1 | forward walking | cursor y |
| **MDN** | 4 | the Moonwalker descending neuron — walking backwards | reverse |
| **DNp09** | 2 | stopping | the click |

The readout is identical to the male's by name and count, with one difference:
the male's click also reads MN9, a name that does not exist in her data, so her
click comes from the 24 proboscis motor neurons instead.

One simulation step takes 0.12 s in her graph, against 0.33 s in the male's.

Then it connects the wallet, accepts the launchpad's terms, uploads the token
image, fills the form — name, ticker, description and the `x.com/` handle —
picks the paired asset out of a 57-item list of tokenised equities, opens
**Advanced**, sets the creator tax, and launches.

## What building her actually took

Six things had to be found out the hard way. They are all logged, and none of
them is a tuning story with a happy ending bolted on.

**She was blind at first.** With FlyWire's per-cell neurotransmitter labels she
saturated on every screen: on a blank white page 19,215 neurons fired and the
steering neurons sat at their 416 Hz ceiling. L1 — the ON-pathway input — came
back as a mix of 836 glutamate, 323 GABA, 608 unknown and a few acetylcholine
cells, and one mislabelled excitatory L1→L5 synapse at 20.6 mV was enough to
light the whole medulla. The male dataset has one transmitter per cell type and
never has this problem. Taking the transmitter by majority vote at the level of
the cell type changed 22,889 labels and filled 18,605 unknowns; the white
screen went from 19,215 firings to 691 and the descending neurons went quiet.

**One eye is not enough.** The first build used a single hemisphere and she
drifted the same way on every page — DNa01 on one side never fired at all. The
male retina uses both eyes on one grid. So does she now.

**One constant instead of a training run.** Scaling her excitatory weights by
0.5 brings DNa02 into the same band as the trained male: the fraction of time
it spends at its ceiling drops from 0.62 to 0.04, and turning on real pages
goes from 0.12 to 0.77. That is one number, not a trained network. It is stored
in the graph file as `exc_scale`, alongside a per-graph `click_hz` of 100 Hz —
the male's 330 Hz threshold never fires for her.

**She was taught the form the same way he was.** The 1+1 evolution strategy
from upstream was ported as `train_form.py` and run over 55 cell types for 247
evaluations. Offline replay gets 2 of 3 fields, the same as the male. Live on
the launchpad she typed the ticker herself — 1 of 3 — and the rig filled the
rest.

**Roaming needed its own gains.** Retina luminance adaptation, forward/back
balance and a 120-type roaming gain live in `assets/gains_female_roam.npz`.
With them she does 152 scrolls in 5 minutes on real pages, and the seed list is
weighted toward random articles so that a reset puts her somewhere she has not
been.

**The mushroom body split was wrong, in both brains.** `mushroom.py` decided
which MBONs were reward-side and which were punishment-side by reading
MBON→dopamine feedback — the matrix the wrong way round. Recomputed from the
true dopaminergic inputs, the male graph gives **39 reward, 56 punishment and 2
unassigned**, and the textbook split only partly survives: MBON04 and eight of
nine MBON10 neurons land on the reward side. That correction went back upstream
as a pull request.

## The fly is loose on the internet

`roam.py` gives her a browser and no instructions. A page is screenshotted,
sampled through the hex columns, and 139,255 neurons decide where the cursor
goes. If a click lands on a link, she is somewhere new. When her forward drive
pushes past the bottom of the window the page scrolls, so she walks down a page
the way she walks across one.

It is watchable live at
**[femaleflybrain.com](https://femaleflybrain.com)** — the page she is looking
at, the neurons firing, and what her descending neurons are doing, all read out
of the running simulation.

```bash
py roam.py            # http://localhost:4660, no start button
```

There is no start and no stop. She roams when the process is up, and if a run
dies it waits six seconds and starts another life.

### The rails, and why each one is there

A random clicker on the open internet, streamed publicly, from a machine that
also holds a funded wallet, is a genuinely bad idea unless it is fenced.

- **No wallet.** This browser gets no key, no provider and no extension. The
  roaming browser and the launching browser share nothing but the brain.
- **No keyboard.** She cannot type, so she cannot fill a field, write a message
  or answer a prompt.
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

Nothing on that page is decoration. `flysim` reports it:

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

The site itself is in `site/` — a Cloudflare Worker serving the static page
and answering `/api/state` from the chain on the edge, because the public
Robinhood node intermittently answers `Access-Control-Allow-Origin: *,*`,
which browsers refuse. The relay in `site/relay/` is a second Worker with a
Durable Object: the rig posts one state and one frame to it, viewers read
them from the edge cache, and nothing about the feed needs the machine she
runs on to be reachable. It lives at
[live.femaleflybrain.com](https://live.femaleflybrain.com). The Vercel and
Railway files under `site/` are the upstream deployment paths, kept so the
male rig's instructions still hold.

## Why Robinhood Chain

pump.fun's backend answers `401 Unauthorized` to an injected wallet, so its own
Create button can never complete a launch — a Solana build has to bypass the
site entirely and mint through a signed transaction.

The pons launchpad **accepts the injected EIP-1193 wallet directly**. It
auto-connects with no modal, `eth_chainId` returns `0x1237`, `personal_sign`
round-trips. So here the site's own button is the real path — and on
2026-09-10 the male's click went all the way through it to a mined block.

## Her launch

$HER launches today. Nothing below is filled in yet; it is filled from the
receipt, not from an announcement.

| | |
|---|---|
| token | pending |
| contract | pending |
| transaction | pending |
| block | pending |
| creator | pending |
| pair | GOOGL — pending |
| creator tax | 1.00% — pending |
| cost | pending |

The creator wallet holds nothing and there is no initial buy. Whatever the
table says when it is filled will be checkable on-chain by anyone who wants to
check it.

## Her brother's launches

The same rig, the male brain, five launches on Robinhood Chain; these two are
the first and the latest.

| | first launch | paired against GOOGL |
|---|---|---|
| token | test (TEST) | test (TEST) |
| contract | `0xd00d0419651c893e8c04edf5e0e074e950c370d3` | `0xcc80a38afd807bfed1b9c21b6f236ea8ee651dc3` |
| transaction | `0x1b3cda17…45484932` | `0x9602a50f…00e5aca2` |
| block | 59557979 | 59581451 |
| pair | ETH, graduates at 4.2 ETH | **GOOGL**, graduates at 24.2 GOOGL |
| cost | 0.000973 ETH | 0.000979 ETH |

Every `status` `0x1`, every creator `0x739Ccc9dd8Ed6412F00782927dbd087c4e72bFc3`
— his wallet — every one 2.00% creator tax and 1,000,000,000 supply fixed at
launch. The first one is public end to end:

- https://www.ponsfamily.com/launchpad/0xd00d0419651c893e8c04edf5e0e074e950c370d3
- https://robinhoodchain.blockscout.com/tx/0x1b3cda17f6456c9a4a67989770be97812e6ca67b3f1f1fb85d2ff04645484932

### The paired asset

pons pairs a new token against something already on Robinhood Chain, and what
is on Robinhood Chain is mostly tokenised equities — the menu is **57 assets**:
NVDA, SPCX, GOOGL, TSLA, GME, AAPL, SPY, and so on down to gold, oil and
Treasuries. The default is ETH. `set_pair_asset()` changes it, and the choice
is real: graduation goes from `4.2 ETH` to `24.2 GOOGL`.

The launch fee stays in ETH either way — the page says `GOOGL pair, ETH 0.0005
due` — so pairing against an equity needs none of that equity in the wallet.

```bash
FLY_RH_PAIR=GOOGL FLY_RH_TAX=1 py rhlive.py --port 4651
```

If you automate that menu: it is a 262px window onto a 2,064px list with **its
own** scrollbar, so `smooth_scroll_in()` has to ease the container's own
`scrollTop`, and Playwright's `get_by_role("button", name="GOOGL")` never
resolves against it — the rows are found by `textContent` and clicked at
coordinates.

### Step 06: it learns now

`mushroom.py` is the one place in this project a weight is allowed to move, and
it moves where a fly's weights actually move — the Kenyon cell to MBON synapse,
under dopamine.

The rule is the measured one. A Kenyon cell active shortly before a
dopaminergic neuron fires has **that synapse depressed**, not strengthened.
Learning in a fly is subtraction: the mushroom body starts able to drive every
response and experience carves away the ones that did not pay. So there is no
potentiation here, only depression with a floor and a slow drift back toward
baseline standing in for forgetting. Across 44,042 KC→MBON synapses, twenty
rewarded encounters with one view depress the addressed compartment by 6.0%,
leave the unaddressed one at −0.9%, and move the Kenyon cells themselves by
+0.3% — which is what a rule acting at that one synapse should look like.

Which MBONs count as reward-side and which as punishment-side is **not
hardcoded from a table**. For each MBON the dopaminergic input is weighed, PAM
against PPL1, and the stronger wins. Building her turned up that the comparison
had been reading that matrix the wrong way round — MBON→dopamine feedback
rather than dopamine→MBON input — so the measurement above carries the old
labels. With the true inputs the male graph gives 39 reward, 56 punishment and
2 unassigned, and the literature split holds only partly: MBON04 and eight of
nine MBON10 neurons come out on the reward side. The correction was sent
upstream as a pull request.

**The reward signal is not real, and the module says so in as many words.** A
fly is rewarded by sugar, not by reaching a web page. Novelty stands in for it
here, and that is a modelling choice made by a person — the fly has no say in
it. The circuit, the plasticity site and the direction of the rule are the
parts that are real.

### Where it roams, and where it does not

The open web, plus the chain she launched her own token on: Wikipedia,
Wikimedia Commons, Wikisource, Hacker News, Project Gutenberg, Open Library,
xkcd, arXiv — and the pons launchpad, Blockscout, and her own token page.

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
were uninteresting. Keeping it on two domains was tried too, and the failure
was quieter: 93 pages and 110 clicks in 49 minutes across **6 unique pages** —
moving the whole time and going nowhere.

Trade controls are blocked and vetoed now that she roams a launchpad. She has
no wallet and a trade is impossible, but the claim was that every click is
checked, and it did once reach a "Buy token" page before that was tightened.

### The feed, and why no object store is in the path

The public feed used to push a frame and a summary to a blob store twice a
second, which suspended the store on operation count and took the feed down
with it. The rig opens a cloudflared quick tunnel instead and the socket
carries frames, telemetry and events for free. The only thing published
anywhere is where the tunnel is — `site/web/live.json`, written when the
address changes, which the page reads. Quick tunnel addresses are random and
change every run, so nothing is hardcoded.

### Waiting for the chain, not for the click

A launch that had already succeeded once looked exactly like a hang: the run
loop broke as soon as the page *asked* for a signature, so the rig declared
itself done with the launchpad still showing "Confirming". The loop now waits
for the receipt, on camera, and `send_transaction` takes `wait_receipt=False`
so the page gets its hash immediately.

pons does **not** redirect after a launch — it leaves you on the empty create
form — so `show_coin_page()` reads the token address out of the receipt logs,
opens that token's page, accepts the terms gate that navigating re-arms, and
scrolls down it. The last thing on screen is the coin.

### The socials field

The X handle is `input[placeholder="handle"]`, `aria-label="X profile handle"`,
behind an `x.com/` prefix; Telegram sits next to it as `community`. Neither has
a name or an id, so the placeholder is the only stable handle on them. It is
typed like every other field and set by `FLY_RH_X`, which here is `opifor`.

> The shipped default is empty, and an empty `FLY_RH_X` leaves the field
> alone. Putting a real person's handle on a live token presents
> that token as theirs, which is impersonation and gets both the token and the
> creator wallet flagged. Set `FLY_RH_X` to something you own before any live
> launch, or clear it.

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

**A receipt.** Any transaction in the tables above can be read straight off the
node rather than taken on trust:

```bash
curl -s https://rpc.mainnet.chain.robinhood.com -H 'content-type: application/json' -d '{"jsonrpc":"2.0","id":1,"method":"eth_getTransactionReceipt","params":["0x1b3cda17f6456c9a4a67989770be97812e6ca67b3f1f1fb85d2ff04645484932"]}'
```

`from` is the creator wallet, `status` is `0x1`, and among the logs is the
fresh ERC-20 whose `name()` and `symbol()` answer.

**Her connectome.** FlyWire FAFB v783, CC-BY 4.0, from codex.flywire.ai with a
free account — eight CSV.gz exports into `data/female/`. Follow FlyWire's own
citation guidelines; they are the reason this fork exists at all.
`py build_graph_female.py` turns those into 139,255 neurons and 3,641,142
signed edges, after the type-level neurotransmitter consensus described above.
FlyWire's filtered connection table keeps pairs with at least 5 synapses; the
male build keeps at least 3. If your numbers differ from mine, one of us has a
bug.

## What is NOT real, stated plainly

- **She does not fill the whole form.** Offline she gets 2 of 3 fields; live on
  the launchpad she typed the ticker and nothing else. The rig completes
  whatever she misses, and the on-screen log says which fields were which —
  `by FLY: …  ·  by rig: …`.
- **The type-level neurotransmitter consensus is a modelling choice.** FlyWire
  publishes a label per cell, and taking a majority per cell type overrides
  what the dataset says about individual cells. It is what made her see at all,
  which is an argument for it and not a proof of it.
- **The 0.5 excitatory scale is a fit, not biology.** It is one constant chosen
  because it puts her steering neuron in the same band as the trained male. No
  fly has it.
- **785 columns per eye is FlyWire's column assignment**, not a measured optic
  flow. The grid is inherited from the dataset's own assignment of cells to
  columns.
- **Light mode breaks it.** The retina is a luminance map and every bit of
  tuning it has was done against dark UI. The rig switches the theme before it
  starts, and on the male that gap — 0 of 3 fields light, 2 of 3 dark — is the
  clearest evidence the vision is doing real work.
- **The idle animation is decoration.** During a run every dot is a neuron at a
  measured soma coordinate. While idle it is a fly-shaped scatter, and the panel
  label changes to say so.
- **The launch is one signature, and the rig arms it.** The launchpad asks for
  a single `eth_sendTransaction`; there is no second approval and no separate
  ERC-20 allowance. But the rig is what presses **Confirm** in the dialog, not
  the fly — her contribution ends at the form and the launch button.
- **She does not choose the paired asset.** She cannot read `GOOGL` at 785
  columns per eye; picking a row out of a 57-item list is the rig following
  `FLY_RH_PAIR`. The same goes for the creator tax and the X handle.
- **The tokens in the brother's table are tests.** `test (TEST)`, launched to
  prove the path end-to-end. They are not projects and nobody should buy them.

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
git clone https://github.com/opifor/flybrain-female
cd flybrain-female
pip install -r requirements.txt
python -m playwright install chromium

# her connectome - CC-BY 4.0, codex.flywire.ai, free account,
# eight CSV.gz exports into data/female/
py build_graph_female.py     # -> build/graph_female.npz, 139,255 neurons

cp .env.example .env         # then set FLY_ALLOW_BROWSER=1
py roam.py                   # http://localhost:4660
```

Set `FLY_GRAPH=build/graph_female.npz` in `.env`, or load it directly with
`FlyBrain("build/graph_female.npz")`. Her build uses both eyes on a shared grid
with excitatory scale 0.5 and `click_hz` 100 Hz; those constants live in the
graph file and are printed by `compare.py`. The roamer and `measure.py` prefer
`assets/gains_female_roam.npz`, whose graph-matched `adapt`, `back_scale`,
`drive_hz` and `click_hz` settings control luminance adaptation and motor
balance, while the form rig keeps `assets/gains_female.npz` (`measure.py
--no-roam` measures that profile).

The male brain still runs here unchanged: the 1.1 GB CC-BY exports from the
public `flyem-male-cns` bucket into `data/`, then `py build_graph.py` for
`build/graph.npz` and 165,122 neurons. Nothing in the rig cares which graph it
is given.

Five tools came with her and work on either brain: `compare.py` prints two
graphs side by side, `calibrate.py` finds the scale constants, `measure.py`
reports roaming and form behaviour over real pages, `form_episode.py` replays a
form offline, and `train_form.py` runs the 1+1 evolution strategy that taught
her the fields.

The site uses `FLY_TOKEN`, `FLY_WALLET`, `FLY_TOKEN_BLOCK`, `FLY_PAIR`,
`FLY_TAX_PCT` and `FLY_LIVE_REPO`, and says "not launched yet" until
`FLY_TOKEN` is set. `FLY_RELAY_URL` and `FLY_RELAY_TOKEN` make the rig publish
its state and frame to the relay in `site/relay/`; without them the page reads
the rig's tunnel directly.

MIT for the code. The connectome is **not ours to license** and stays CC-BY
wherever it goes — keep the attribution, it is the whole reason any of this is
real.

Things worth pointing her at that we have not: a readout that is not a cursor,
the olfactory channel (unused in both brains — in the male build cVA through
ORN_DA1 drives pC1 at 222 Hz untrained, so the pathway works and has nothing
plugged into it), a reward that is measurable rather than invented, and
somewhere else entirely — a game, a robot, a microscope. The brain does not
know it is on a launchpad.

If you build something with it, open an issue — we would rather see it than
not.

## Credits

[fruitflydev/flycoinrh](https://github.com/fruitflydev/flycoinrh) first: the
rig, the retina, the descending-neuron readout, the form training method and
the launch path are all theirs, and this fork is a graph swap on top of
published work.

Female connectome data from FlyWire, FAFB v783 — © the FlyWire consortium
(Princeton, Cambridge and partners), released CC-BY 4.0. Dorkenwald et al.,
*Nature* 2024; Schlegel et al., *Nature* 2024.

Male connectome data © HHMI Janelia FlyEM, the Cambridge Connectomics Group and
Google Research, released CC-BY, for the male build that still runs here.

Sign convention after Shiu et al. 2024; simulation approach after Shiu et al.
2024 and Lappalainen et al. 2024. Not affiliated with any of them, nor with
pons or Robinhood.

Live: [femaleflybrain.com](https://femaleflybrain.com) · X:
[@opifor](https://x.com/opifor)
