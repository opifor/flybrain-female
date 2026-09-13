import copy
import json

import pytest

from life import Life


def moment(**fields):
    return {"url": "", "visited": [], "events": [], "stats": {"clicks": 0, "scrolled": 0},
            "hz": {}, "neural": {}, **fields}


def texts(block, kind):
    return [r["text"] for r in block["feed"] if r["kind"] == kind]


def position(**fields):
    return dict(id=1, seq=1, market_id="eth", question="Ethereum Up or Down - September 13, 12:00AM-12:15AM ET", side="YES",
                price=0.4, stake=4, stake_cents="400", **fields)


def paper(opened=None, settled=None):
    return moment(betting={"in_room": True, "cards": [dict(market_id="eth", question="Ethereum Up or Down - September 13, 12:00AM-12:15AM ET", slot=0)],
                           "learning": {"last": []}},
                  betroom={"balance": 100, "open_bets": opened or [], "settled_bets": settled or []})


def test_page_and_scroll_updates_survive_restart(tmp_path):
    life = Life(tmp_path)
    state = moment(url="https://www.example.org/", visited=[{"url": "https://www.example.org/", "title": "page", "at": 100}])
    block = life.observe(state, 100)
    assert texts(block, "page.open") == ["she opened example.org"]
    for n in range(1, 4):
        state["stats"]["scrolled"] = n
        state["events"].append({"t": 100+n, "m": "scrolled down"})
        block = life.observe(state, 100+n)
    assert texts(block, "page.scroll") == ["she scrolled down 3 times on example.org"]
    assert block["hour"]["scrolls"] == 3
    restored = Life(tmp_path).observe(state, 104)
    assert restored["feed"] == block["feed"]
    assert restored["hour"] == block["hour"]


def test_open_bet_and_cursor(tmp_path):
    life = Life(tmp_path)
    state = paper([position()])
    block = life.observe(state, 100)
    assert texts(block, "bet.placed") == ["she bet yes on eth 15m at 0.40 · 4.00 paper usdc"]
    assert block["now"]["doing"] == "holding yes on eth 15m"
    state["betroom"]["open_bets"] = []
    state.update(cx=100, cy=100)
    assert life.observe(state, 101)["now"]["doing"] == "looking at eth 15m"
    state.update(cx=440)
    assert life.observe(state, 102)["now"]["doing"] == "looking at the board"


@pytest.mark.parametrize("won,payout,kind,pnl,reward", [(True, "1000", "won", 6, "sugar"), (False, "0", "lost", -4, "shock")])
@pytest.mark.parametrize("lesson_first", [False, True])
def test_settlement_and_delivered_lesson(tmp_path, won, payout, kind, pnl, reward, lesson_first):
    life = Life(tmp_path)
    state = paper([position()])
    life.observe(state, 100)
    state["betting"]["learning"]["last"] = [dict(seq=3, status="delivered", sign=1 if won else -1, eligible=[1, 2], at=101)]
    if lesson_first:
        life.observe(state, 101)
    state["betroom"]["open_bets"] = []
    state["betroom"]["settled_bets"] = [{**position(), "seq": 2, "kind": "settled", "won": won, "payout_cents": payout}]
    block = life.observe(state, 102)
    assert len(texts(block, "bet." + kind)) == 1
    assert block["hour"][kind] == 1
    assert block["hour"]["pnl"] == pnl
    assert block["hour"][reward] == 1
    assert not texts(block, reward)
    assert Life(tmp_path).observe(state, 103)["hour"] == block["hour"]


def test_hour_expires_and_minimal_is_untouched(tmp_path):
    life = Life(tmp_path)
    state = moment()
    before = copy.deepcopy(state)
    block = life.observe(state, 100)
    assert state == before
    assert block["feed"] == []
    assert block["now"]["balance"] is None and block["now"]["today_delta"] is None
    state.update(url="https://example.org")
    assert life.observe(state, 101)["hour"]["pages"] == 1
    block = life.observe(state, 3701)
    assert block["hour"]["pages"] == 0
    assert not texts(block, "page.open")


@pytest.mark.parametrize("left,right,expected", [(10, 60, "right"), (60, 10, "left"), (20, 0, "straight"), (0, 20, "straight")])
def test_turn(tmp_path, left, right, expected):
    assert Life(tmp_path).observe(moment(hz={"steer_L": left, "steer_R": right}), 100)["now"]["turn"] == expected


@pytest.mark.parametrize("path,room,doing", [("/hall", "hall", "walking the hall"), ("/tiproom", "tip room", "visiting the tip room")])
def test_rooms_and_stale_entry(tmp_path, path, room, doing):
    life = Life(tmp_path)
    state = moment(url="http://localhost:4660"+path, rooms={"/hall": {"events": [{"kind": "entered", "path": path, "at": 100}]}})
    block = life.observe(state, 100)
    assert block["now"]["room"] == room and block["now"]["doing"] == doing
    state["url"] = "https://arxiv.org/list/q-bio.NC"
    block = life.observe(state, 101)
    assert block["now"]["doing"] == "reading arxiv.org"
    assert texts(block, "page.open") == ["she opened arxiv.org/list/q-bio.NC"]


def test_sales_refusals_streak_and_balance(tmp_path):
    life = Life(tmp_path)
    state = paper()
    life.observe(state, 86390)
    state["betroom"].update(balance=106, settled_bets=[{**position(), "kind": "sold", "pnl": 6, "won": True}])
    state["betting"]["events"] = [{"seq": 2, "kind": "refused"}, {"seq": 3, "kind": "refused"}]
    block = life.observe(state, 86391)
    assert texts(block, "bet.sold") == ["she left eth 15m early · +6.00 paper usdc"]
    assert texts(block, "bet.refused") == ["the bookie said no 2 times this minute"]
    assert block["hour"]["sold"] == 1 and block["hour"]["won"] == 0
    assert block["now"]["today_delta"] == 6
    restored = Life(tmp_path)
    assert restored.observe(state, 86392)["now"]["today_delta"] == 6
    assert restored.observe(state, 86400)["now"]["today_delta"] == 0
    for n in (4, 5):
        state["betroom"]["settled_bets"].append({**position(), "id": n, "seq": n, "kind": "settled", "won": True, "payout_cents": "1000"})
    block = life.observe(state, 86401)
    assert texts(block, "streak") == ["3 wins in a row"]


def test_brain_thresholds_and_cooldowns(tmp_path):
    life = Life(tmp_path)
    life.observe(moment(neural={"spikes_per_sec": 100}), 100)
    block = life.observe(moment(neural={"spikes_per_sec": 201}), 101)
    assert len(texts(block, "brain.storm")) == 1
    block = life.observe(moment(neural={"spikes_per_sec": 1000}), 102)
    assert len(texts(block, "brain.storm")) == 1
    life.observe(moment(), 103)
    assert texts(life.observe(moment(), 162), "brain.quiet") == []
    assert texts(life.observe(moment(), 163), "brain.quiet") == ["quiet brain · 1 min under 1 spikes/s"]
    assert len(texts(life.observe(moment(), 164), "brain.quiet")) == 1


def test_rotation_and_text_limits(tmp_path):
    life = Life(tmp_path)
    state = paper([position()])
    state["betting"]["cards"][0].update(symbol="x"*80)
    block = life.observe(state, 100)
    assert texts(block, "bet.placed")[0].endswith("4.00 paper usdc")
    with life.path.open("a", encoding="utf-8") as stream:
        stream.write(" " * (5*1024*1024) + "\n")
    state["betroom"]["balance"] = 101
    block = life.observe(state, 101)
    assert (tmp_path / "feed.1.jsonl").exists()
    assert Life(tmp_path).observe(state, 102)["hour"] == block["hour"]
    assert all(len(r["text"]) <= 64 for r in block["feed"])
    assert not life.path.read_bytes().startswith(b"\xef\xbb\xbf")
    assert json.loads((tmp_path / "day.json").read_text())["balance"] == 100


def test_clicks_lessons_and_feed_limit(tmp_path):
    life = Life(tmp_path)
    state = moment(url="https://example.org", betting={"learning": {"last": []}})
    life.observe(state, 100)
    state["stats"]["clicks"] = 2
    state["events"] = [{"t": 101, "m": "did not click - a form"}]
    state["betting"]["learning"]["last"] = [dict(seq=1, status="delivered", sign=1, eligible=[1, 2, 3])]
    block = life.observe(state, 101)
    assert texts(block, "sugar") == ["sugar · 3 kenyon cells"]
    assert texts(block, "page.noclick") == ["she looked at a link on example.org and did not click"]
    assert block["hour"]["clicks"] == 2 and block["now"]["sugar_10m"] == 1
    assert Life(tmp_path).observe(state, 102)["feed"] == block["feed"]
    for n in range(50):
        state["url"] = f"https://example.org/{n}"
        block = life.observe(state, 103+n)
    assert len(block["feed"]) == 40
    assert block["feed"][0]["text"] == "she opened example.org/49"
    assert life.observe(state, 702)["now"]["sugar_10m"] == 0


def test_fill_between_ticks_and_late_lesson(tmp_path):
    life = Life(tmp_path)
    state = paper()
    life.observe(state, 100)
    state["betting"]["events"] = [{**position(), "kind": "fill", "price": "2/5"}]
    state["betroom"]["settled_bets"] = [{**position(), "seq": 2, "kind": "settled", "won": True, "payout_cents": "1000"}]
    block = life.observe(state, 101)
    assert block["hour"]["bets"] == 1 and block["hour"]["won"] == 1
    state["betting"]["learning"]["last"] = [dict(seq=3, status="delivered", sign=1, eligible=[1])]
    block = life.observe(state, 105)
    assert not texts(block, "sugar")
    assert block["hour"]["sugar"] == 1
    restored = Life(tmp_path)
    state["url"] = "https://example.org"
    state["betting"]["in_room"] = False
    block = restored.observe(state, 106)
    assert texts(block, "page.open") == ["she opened example.org"]


def test_label_reads_the_question():
    from life import label
    assert label({"question": "Bitcoin Up or Down - September 13, 12:00AM-12:15AM ET"}, []) == "btc 15m"
    assert label({"question": "Ethereum Up or Down - September 12, 11:55PM-12:00AM ET"}, []) == "eth 5m"
    assert label({"question": "Will the price of Bitcoin be above $82,000 on September 13?"}, []) == "btc above $82,000"
    assert label({"market_id": "1"}, [{"market_id": "1", "question": "Who wins the game tonight?"}]) == "who wins the game tonigh"
