import copy
import json

import pytest

from life import Life


def test_house_identity_and_hour(tmp_path):
    life = Life(tmp_path)
    state = moment(url="http://127.0.0.1:4660/hall")
    block = life.observe(state, 100)
    assert block["who"] == [
        "her. a female fruit fly brain, 139,255 neurons. FlyWire FAFB v783.",
        "she lives in her rooms: a betting room, a music room, more coming.",
        "she never speaks. the numbers do.",
        "every room is paper for now; the plan is to take the rooms on-chain.",
        "the first fly streamer on kick."]
    assert block["hour"]["rooms"] == 1 and block["hour"]["plays"] == 0
    play = dict(track_id="1", title="Rain", started_at=101)
    state = moment(url="http://127.0.0.1:4660/musicroom",
                   rooms={"/musicroom": dict(in_room=True, book=dict(now_playing=play))})
    block = life.observe(state, 101)
    assert block["hour"]["rooms"] == 2 and block["hour"]["plays"] == 1
    assert Life(tmp_path).observe(state, 102)["hour"] == block["hour"]
    block = life.observe(state, 3700)
    assert block["hour"]["rooms"] == 1 and block["hour"]["plays"] == 1
    block = life.observe(state, 3701)
    assert block["hour"]["rooms"] == block["hour"]["plays"] == 0
    assert set("bets sold won lost pnl pages clicks scrolls sugar shock".split()) <= block["hour"].keys()


def moment(**fields):
    return {"url": "", "visited": [], "events": [], "stats": {"clicks": 0, "scrolled": 0},
            "hz": {}, "neural": {}, **fields}


def texts(block, kind):
    return [r["text"] for r in block["feed"] if r["kind"] == kind]


def test_music_feed_and_restart(tmp_path):
    catalogue = tmp_path / "catalog.json"
    catalogue.write_text(json.dumps([dict(id=123, title="Rain", artist="River")]), encoding="utf-8")
    play = dict(track_id="123", title="Rain", started_at=100, duration=90)
    book = dict(now_playing=play, plays=[{**play, "ended_at": None}],
                reactions={"tracks": {"123": {"sugar": 4, "shock": 1}}})
    state = moment(url="http://127.0.0.1:4660/musicroom",
                   rooms={"/musicroom": dict(in_room=True, book=book)})
    life = Life(tmp_path / "feed", music_catalogue=catalogue)
    block = life.observe(state, 110)
    assert block["now"]["room"] == "music room"
    assert block["now"]["doing"] == "listening to Rain"
    assert texts(block, "music.play") == ["she put on Rain by River"]
    assert not texts(block, "music.react")
    book["reactions"]["tracks"]["123"].update(sugar=5, shock=2)
    block = life.observe(state, 120)
    assert set(texts(block, "music.react")) == {"a listener sent sugar for Rain", "a listener sent shock for Rain"}
    assert block["hour"]["sugar"] == block["hour"]["shock"] == 1
    book["plays"][0]["ended_at"] = 135
    book["now_playing"] = None
    life = Life(tmp_path / "feed", music_catalogue=catalogue)
    block = life.observe(state, 140)
    assert texts(block, "music.end") == ["Rain ended · she stayed 35 s"]
    assert next(r["at"] for r in block["feed"] if r["kind"] == "music.end") == "00:02:15"
    assert len(texts(block, "music.play")) == 1
    assert len(texts(block, "music.react")) == 2
    assert life.observe(state, 141)["feed"] == block["feed"]
    play = {**play, "started_at": 145}
    book["now_playing"] = play
    book["plays"].append({**play, "ended_at": None})
    assert len(texts(life.observe(state, 150), "music.play")) == 2
    state["rooms"]["/musicroom"]["in_room"] = False
    state["url"] = "https://example.com/"
    assert life.observe(state, 151)["now"]["doing"] == "reading example.com"


def test_long_music_title_preserves_artist_and_stay(tmp_path):
    catalogue = tmp_path / "catalog.json"
    catalogue.write_text(json.dumps([dict(id="1", title="r" * 100, artist="River")]), encoding="utf-8")
    play = dict(track_id="1", title="r" * 100, started_at=100, ended_at=140)
    state = moment(rooms={"/musicroom": dict(in_room=True, book=dict(plays=[play]))})
    life = Life(tmp_path / "feed", music_catalogue=catalogue)
    block = life.observe(state, 150)
    assert texts(block, "music.play")[0].endswith(" by River")
    assert texts(block, "music.end")[0].endswith(" ended · she stayed 40 s")
    assert all(len(row["text"]) <= 48 for row in block["feed"])
    life.observe(moment(), 151)
    assert len(texts(life.observe(state, 152), "music.play")) == 1
    assert len(texts(life.observe(state, 153), "music.end")) == 1


def test_music_assets_build_skip_and_limits(tmp_path, monkeypatch):
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location("music_assets", Path(__file__).parent / "site/music_assets.py")
    assets = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(assets)
    source = tmp_path / "data/music"
    source.mkdir(parents=True)
    catalogue = source / "catalog.json"
    row = dict(id=123, title="Rain", artist="River", license="CC BY 3.0",
               page="https://commons.wikimedia.org/wiki/File:Rain.ogg", duration=30,
               file="data/music/123.wav")
    catalogue.write_text(json.dumps([row]), encoding="utf-8")
    calls = []
    def transcode(command, check):
        calls.append(command)
        assert check and command[command.index("-i") + 1] == str(source / "123.wav")
        assert command[command.index("-c:a") + 1] == "libvorbis"
        assert command[command.index("-q:a") + 1] == "3"
        Path(command[-1]).write_bytes(b"ogg fixture")
    monkeypatch.setattr(assets.subprocess, "run", transcode)
    output = tmp_path / "web/music"
    rows = assets.build(catalogue, output)
    assert rows == [{**{k: v for k, v in row.items() if k != "file"}, "id": "123", "file": "123.ogg"}]
    assert json.loads((output / "catalog.json").read_text(encoding="utf-8")) == rows
    assets.build(catalogue, output)
    assert len(calls) == 1
    monkeypatch.setattr(assets, "LIMIT", 2)
    with pytest.raises(ValueError, match="8 MB"):
        assets.build(catalogue, output)
    row["id"] = "../escape"
    catalogue.write_text(json.dumps([row]), encoding="utf-8")
    with pytest.raises(ValueError, match="filename"):
        assets.build(catalogue, output)


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
    assert texts(block, "bet.placed") == ["she bet yes on eth 15m at 0.40 · 4.00 paper"]
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
    assert texts(block, "bet.sold") == ["she left eth 15m early · +6.00 paper"]
    assert texts(block, "bet.refused") == ["the bookie said no 2× this minute"]
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
    assert texts(block, "bet.placed")[0].endswith("4.00 paper")
    with life.path.open("a", encoding="utf-8") as stream:
        stream.write(" " * (5*1024*1024) + "\n")
    state["betroom"]["balance"] = 101
    block = life.observe(state, 101)
    assert (tmp_path / "feed.1.jsonl").exists()
    assert Life(tmp_path).observe(state, 102)["hour"] == block["hour"]
    assert all(len(r["text"]) <= 48 for r in block["feed"])
    assert not life.path.read_bytes().startswith(b"\xef\xbb\xbf")
    assert json.loads((tmp_path / "day.json").read_text())["balance"] == 104


def test_clicks_lessons_and_feed_limit(tmp_path):
    life = Life(tmp_path)
    state = moment(url="https://example.org", betting={"learning": {"last": []}})
    life.observe(state, 100)
    state["stats"]["clicks"] = 2
    state["events"] = [{"t": 101, "m": "did not click - a form"}]
    state["betting"]["learning"]["last"] = [dict(seq=1, status="delivered", sign=1, eligible=[1, 2, 3])]
    block = life.observe(state, 101)
    assert texts(block, "sugar") == ["sugar · 3 kenyon cells"]
    assert texts(block, "page.noclick") == ["she skipped a link on example.org"]
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
    assert label({"market_id": "1"}, [{"market_id": "1", "question": "Who wins the game tonight?"}]) == "who wins the game tonight?"


def test_record_times_cold_start_and_hour(tmp_path):
    state = paper([position(at=4400)], [
        {**position(), "id": n, "seq": n, "at": at, "won": True, "pnl": 2}
        for n, at in enumerate([1400, 1401, 4399, 4400, 4900], 2)
    ])
    life = Life(tmp_path)
    block = life.observe(state, 5000)
    assert block["hour"]["won"] == 4
    assert block["hour"]["pnl"] == 8
    assert len(texts(block, "bet.won")) == 2
    assert texts(block, "streak") == ["5 wins in a row"]
    assert [r["at"] for r in block["feed"] if r["kind"] == "bet.won"] == ["01:21:40", "01:13:20"]
    assert life.rows["buy:1:1"]["ts"] == 4400
    assert Life(tmp_path).observe(state, 5001)["hour"]["won"] == 3
    state["betroom"]["settled_bets"].append({**position(), "id": 20, "seq": 20, "at": 4402, "kind": "sold", "pnl": 1})
    block = life.observe(state, 5100)
    assert next(r["at"] for r in block["feed"] if r["kind"] == "bet.sold") == "01:13:22"


def test_old_streak_is_silent_and_final_loss_breaks_streak(tmp_path):
    state = paper(settled=[{**position(), "id": n, "seq": n, "at": 100 + n, "won": True} for n in range(5)])
    life = Life(tmp_path)
    assert not texts(life.observe(state, 1000), "streak")
    state["betroom"]["settled_bets"].extend([
        {**position(), "id": 10, "seq": 10, "at": 1001, "won": True},
        {**position(), "id": 11, "seq": 11, "at": 1002, "won": False},
    ])
    assert not texts(life.observe(state, 1003), "streak")


@pytest.mark.parametrize("stake", [14.43, "1443"])
def test_equity_baseline_current_restart_and_day(tmp_path, stake):
    state = paper([{**position(), "stake": stake, "stake_cents": "1443"}])
    state["betroom"]["balance"] = 85.57
    life = Life(tmp_path)
    assert life.observe(state, 100)["now"]["today_delta"] == 0
    state["betroom"].update(open_bets=[], balance=103)
    assert Life(tmp_path).observe(state, 101)["now"]["today_delta"] == 3
    state["betroom"].update(open_bets=[{**position(), "stake": stake, "stake_cents": "1443"}], balance=88.57)
    assert life.observe(state, 102)["now"]["today_delta"] == 3
    assert life.observe(state, 86400)["now"]["today_delta"] == 0


def test_refusals_wait_five_minutes_and_keep_pending_across_restart(tmp_path):
    state = paper()
    state["betting"]["events"] = [{"kind": "refused", "seq": 1}]
    life = Life(tmp_path)
    assert texts(life.observe(state, 100), "bet.refused") == ["the bookie said no 1× this minute"]
    state["betting"]["events"] += [{"kind": "refused", "seq": n} for n in range(2, 42)]
    assert len(texts(life.observe(state, 200), "bet.refused")) == 1
    life = Life(tmp_path)
    assert len(texts(life.observe(state, 399), "bet.refused")) == 1
    assert texts(life.observe(state, 400), "bet.refused") == ["the bookie said no 40× this minute", "the bookie said no 1× this minute"]
    assert len(texts(life.observe(state, 700), "bet.refused")) == 2


def test_long_market_preserves_outcome_and_amount(tmp_path):
    state = paper([{**position(), "question": "a" * 200}], [{**position(), "seq": 2, "question": "b" * 200, "won": False, "pnl": -4}])
    block = Life(tmp_path).observe(state, 100)
    assert texts(block, "bet.placed")[0].endswith("at 0.40 · 4.00 paper")
    assert texts(block, "bet.lost")[0].endswith("resolved · lost -4.00 · shock")
    assert all(len(row["text"]) <= 48 for row in block["feed"])


def test_long_variable_words_and_full_fields(tmp_path):
    title = "Small extraordinary melodies drifting across the evening sky"
    question = "Will extraordinary rainfall arrive before the end of September?"
    life = Life(tmp_path)
    life.music_tracks = {"1": {"artist": "River"}}
    state = paper([{**position(), "question": question}])
    state["rooms"] = {"/musicroom": {"book": {"now_playing": {
        "track_id": "1", "title": title, "started_at": 100}}}}
    block = life.observe(state, 100)
    play = next(r for r in block["feed"] if r["kind"] == "music.play")
    bet = next(r for r in block["feed"] if r["kind"] == "bet.placed")
    assert play["text"] == "she put on Small extraordinary\u2026 by River"
    assert bet["text"] == "she bet yes on will\u2026 at 0.40 \u00b7 4.00 paper"
    assert play["title"] == title and bet["question"] == question
    assert len(play["text"]) <= 48 and len(bet["text"]) <= 48


def test_old_lessons_are_absorbed_on_a_fresh_start(tmp_path):
    life = Life(tmp_path)
    state = paper()
    state["betting"]["learning"]["last"] = [
        dict(seq=1, status="delivered", sign=1, eligible=[1, 2], at=100.0),
        dict(seq=2, status="delivered", sign=-1, eligible=[3], at=3500.0)]
    block = life.observe(state, 3600.0)
    assert [r["kind"] for r in block["feed"] if r["kind"] in ("sugar", "shock")] == ["shock"]
    assert next(r for r in block["feed"] if r["kind"] == "shock")["at"] == "00:58:20"
    assert block["hour"]["sugar"] == 1 and block["hour"]["shock"] == 1


def test_a_removed_directory_comes_back(tmp_path):
    import shutil
    life = Life(tmp_path / "life")
    shutil.rmtree(tmp_path / "life")
    block = life.observe(paper(), 100)
    assert block["now"]["room"] == "paper room"
    assert (tmp_path / "life" / "feed.jsonl").exists()


@pytest.mark.parametrize("by,sentence", [
    ("door", "she chose the door and left the music room"),
    ("clock", "the music room closed after six minutes"),
])
def test_room_exit_sentences_and_repeated_observations(tmp_path, by, sentence):
    life = Life(tmp_path)
    state = moment(rooms={"/musicroom": {"last_exit": {"by": by, "at": 100}}})
    block = life.observe(state, 100)
    assert texts(block, "room.exit." + by) == [sentence]
    before = life.path.read_bytes()
    life.observe(state, 101)
    assert life.path.read_bytes() == before
    life = Life(tmp_path)
    assert texts(life.observe(state, 102), "room.exit." + by) == [sentence]
    state["rooms"]["/musicroom"]["last_exit"]["at"] = 103
    assert texts(life.observe(state, 103), "room.exit." + by) == [sentence, sentence]


def test_loopback_paths_name_her_rooms(tmp_path):
    life = Life(tmp_path)
    state = moment(url="http://127.0.0.1:4660/hall")
    block = life.observe(state, 100)
    assert block["now"]["room"] == "hall"
    assert not texts(block, "page.open")
    state = moment(url="http://127.0.0.1:4660/musicroom")
    block = life.observe(state, 101)
    assert block["now"]["room"] == "music room"
