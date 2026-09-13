"""A taste teaches the saved cells, and the record follows the two-hour clock."""
import json

import pytest
from playwright.sync_api import sync_playwright, expect

import dealer
import gameroom
import room_pages
from room import RECTS_JS
from test_rooms import make_room
from test_rooms_site import pages
from life import Life


def setup_game(tmp_path, now):
    ledger = dealer.Ledger(tmp_path, clock=lambda: now[0])
    return dealer.Dealer(ledger, "fixture", clock=lambda: now[0])


def pick(ex, word, look):
    return ex.intent(dict(card_id=word, drive=0.5, seen_at=ex.clock(), look_id=look))


def test_hour_draw():
    for hour in range(100):
        draw = gameroom.sweet_words(hour)
        assert draw == gameroom.sweet_words(hour)
        assert len(set(draw)) == 4
        assert set(draw) <= set(gameroom.WORDS)
    assert gameroom.sweet_words(5) != gameroom.sweet_words(11)


@pytest.mark.parametrize("sweet", [True, False])
def test_taste_teaches_saved_cells_and_replays(tmp_path, sweet):
    now = [36000.0]
    ex = setup_game(tmp_path, now)
    word = next(w for w in gameroom.WORDS if (w in gameroom.sweet_words(5)) == sweet)
    assert pick(ex, word, "taste")[1]["status"] == "booked"
    fill, reward = ex.events()[1]["events"]
    sign = 1 if sweet else -1
    assert fill["taste"] == ("sweet" if sweet else "sour")
    assert reward == dict(kind="dopamine", mode="paper", at=now[0], id=1, seq=2,
                          fill_seq=1, market_id=word, look_id="taste", sign=sign)
    room = make_room(gameroom.Room, tmp_path)
    room.looks_dir.mkdir(parents=True)
    (room.looks_dir / "taste.json").write_text(json.dumps(dict(
        token=word, brain_id=room.brain_id, eligible=[2, 4])), encoding="utf-8")
    room.refs[word] = ["taste"]
    room._apply_event(reward)
    room._apply_event(reward)
    assert room.mb.log.count(("dopamine", (sign, 1.0))) == 1
    assert ("observe", 2) in room.mb.log
    assert room.last_dopamine[-1]["status"] == "delivered"
    assert room.last_dopamine[-1]["eligible"] == [2, 4]
    assert word not in room.refs
    assert setup_game(tmp_path, now).events() == ex.events()


def test_limits_and_hour_bookkeeping(tmp_path):
    now = [7190.0]
    ex = setup_game(tmp_path, now)
    sweet = gameroom.sweet_words(0)[0]
    sour = next(w for w in gameroom.WORDS if w not in gameroom.sweet_words(1))
    assert pick(ex, sweet, "first")[1]["status"] == "booked"
    assert pick(ex, sweet, "rest")[1]["reason"] == "card resting"
    other = next(w for w in gameroom.WORDS if w != sweet)
    now[0] = 7199.999
    assert pick(ex, other, "soon")[1]["reason"] == "too soon"
    now[0] = 7200
    if sour == sweet:
        sour = next(w for w in gameroom.WORDS if w != sweet and w not in gameroom.sweet_words(1))
    assert pick(ex, sour, "next-hour")[1]["status"] == "booked"
    ex.resolve_once()
    public = json.loads(ex.ledger.public_path.read_text())
    assert public["sweet_words"] == list(gameroom.sweet_words(1))
    assert public["this_hour"] == dict(hour=1, picks=1, sweet=0, sour=1, hit_rate=0)
    assert public["history"][0] == dict(hour=0, picks=1, sweet=1, sour=0, hit_rate=1)
    assert len(public["history"]) == 6
    now[0] = 7249.999
    assert pick(ex, sweet, "still-rest")[1]["reason"] == "card resting"
    now[0] = 7250
    assert pick(ex, sweet, "rest-over")[1]["status"] == "booked"
    expected = 0.5 if sweet in gameroom.sweet_words(1) else 0
    assert ex.ledger.book.public()["this_hour"]["hit_rate"] == expected
    now[0] = 14400
    ex.resolve_once()
    assert ex.ledger.book.public()["this_hour"]["picks"] == 0
    assert ex.ledger.book.public()["history"][0]["picks"] == 2


def test_recovery_and_bad_ledger(tmp_path):
    now = [36000.0]
    ex = setup_game(tmp_path, now)
    pick(ex, "apple", "first")
    lines = ex.ledger.path.read_text().splitlines()
    ex.ledger.path.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
    recovered = setup_game(tmp_path, now)
    assert [e["kind"] for e in recovered.events()[1]["events"]] == ["fill", "dopamine"]
    assert setup_game(tmp_path, now).events() == recovered.events()
    with ex.ledger.path.open("a", encoding="utf-8") as stream:
        stream.write("broken\n")
    assert pick(setup_game(tmp_path, now), "lemon", "bad")[0] == 503


def test_word_board_shuffle_smell_and_rest(tmp_path):
    room = make_room(gameroom.Room, tmp_path)
    room.clock = lambda: 36000
    room.refresh_board(force=True)
    before = room.board()["cards"]
    assert len(before) == 12 and {c["name"] for c in before} == set(gameroom.WORDS)
    assert not any("sweet" in json.dumps(c) or "sour" in json.dumps(c) for c in before)
    assert room.board_source()() == room._board["cards"]
    smells = []
    room.nose.smell = lambda word: smells.append(word) or word
    assert room.smell_of("apple") == "apple" and smells == ["apple"]
    room.clock = lambda: 36060
    room.refresh_board()
    assert room.board()["cards"] != before
    room.read_book = lambda: {"resting_until": {"apple": 36120}}
    assert next(c for c in room.board()["cards"] if c["token"] == "apple")["resting"]
    assert not room.can_commit("apple", 36119)
    assert room.can_commit("apple", 36120)
    assert room.can_commit("/hall", 36119)


def test_browser_layout_and_audience_rule(tmp_path):
    room = make_room(gameroom.Room, tmp_path)
    room.refresh_board(force=True)
    cards = room.board()["cards"]
    cards[0]["resting"] = True
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.route("**/board.json", lambda route: route.fulfill(json={"cards": cards}))
        page.route("http://127.0.0.1/gameroom", lambda route: route.fulfill(
            body=room_pages.pages()["gameroom"], content_type="text/html"))
        page.goto("http://127.0.0.1/gameroom")
        expect(page.locator(".card")).to_have_count(12)
        expect(page.locator(".name")).to_have_text([c["name"] for c in cards])
        expect(page.locator(".resting")).to_have_count(1)
        rects = page.evaluate(RECTS_JS)
        boxes = [r for r in rects if r["token"] != "/hall"]
        assert boxes == [dict(token=c["token"], held=False, x=56+296*(i%4), y=48+216*(i//4), w=280, h=200)
                         for i, c in enumerate(cards)]
        for i, box in enumerate(boxes):
            for other in boxes[i+1:] + [r for r in rects if r["token"] == "/hall"]:
                assert (box["x"]+box["w"] <= other["x"] or other["x"]+other["w"] <= box["x"] or
                        box["y"]+box["h"] <= other["y"] or other["y"]+other["h"] <= box["y"])
        room._last_rects = rects
        assert room.state()["rects"][cards[0]["token"]] == dict(x=56, y=48, w=280, h=200)
        page.screenshot(path=str(tmp_path / "game.png"))
        pages.generate(tmp_path / "site")
        now = [36000.0]
        ex = setup_game(tmp_path, now)
        public = ex.ledger.book.public()
        page.route("**/state", lambda route: route.fulfill(json={
            "live": True, "rooms": {"/gameroom": {"book": public}}}))
        page.route("**/show.js", lambda route: route.fulfill(body="window.mountShow=()=>({onState:()=>{}})"))
        html = (tmp_path / "site/game.html").read_text(encoding="utf-8").replace('id="bet-stage"', 'id="preview-stage"')
        page.route("http://127.0.0.1/game", lambda route: route.fulfill(body=html, content_type="text/html"))
        page.goto("http://127.0.0.1/game")
        expect(page.locator('[data-live="book"]')).to_contain_text(
            "sweet this hour: " + ", ".join(public["sweet_words"]))
        expect(page.locator('[data-live="book"] li')).to_have_count(6)
        now[0] += 7200
        public.update(ex.ledger.book.public())
        expect(page.locator('[data-live="book"]')).to_contain_text(
            "sweet this hour: " + ", ".join(public["sweet_words"]))
        browser.close()


def test_life_tastes_and_hour_change(tmp_path):
    now = [36000.0]
    ex = setup_game(tmp_path, now)
    life = Life(tmp_path / "life")
    pick(ex, "apple", "first")
    def observe():
        return life.observe({"url": "http://127.0.0.1:8000/gameroom", "rooms": {
            "/gameroom": {"in_room": True, "book": ex.ledger.book.public()}}}, now[0])
    state = observe()
    taste = ex.ledger.book.public()["tastes"][0]["taste"]
    assert f"she tasted apple \u00b7 {taste}" in [r["text"] for r in state["feed"]]
    observe()
    assert sum(r["kind"] == "room.enter" for r in life.rows.values()) == 1
    now[0] += 7200
    state = observe()
    assert "new rule, new sweet cards" in [r["text"] for r in state["feed"]]
    assert state["now"]["room"] == "game room"
    assert all(len(r["text"]) <= 48 for r in state["feed"])
