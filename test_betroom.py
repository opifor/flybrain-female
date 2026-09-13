"""The upstream dwell and readout tests, adapted to binary bets."""
import asyncio

import json

import tempfile

import unittest

from pathlib import Path

import numpy as np

import calibration

from betroom import Room

TOKEN_A = "111"

TOKEN_B = "222"

IMG = np.full((800, 1280), 0.05, dtype=np.float32)

RECTS = [
    {"token": TOKEN_A, "held": False, "x": 0.0, "y": 0.0, "w": 280.0, "h": 200.0},
    {"token": TOKEN_B, "held": True, "x": 300.0, "y": 0.0, "w": 280.0, "h": 200.0},
]

IN_A = (100.0, 100.0)

IN_B = (400.0, 100.0)

OUTSIDE = (900.0, 600.0)

class FakeBrain:

    def __init__(self):
        self.n = 8
        self.runs = []
        self.fired = np.array([1, 3], dtype=np.int64)

    def run(self, drive, steps, gains=None, record=None, seed=0):
        self.runs.append({"drive": drive, "steps": steps, "seed": seed})
        return {"_fired": self.fired}

class FakeEye:
    def look(self, img, cx, cy):
        return {(0, 1): float(np.mean(img)) * 180.0}

def card_at(cx, cy):
    for r in RECTS:
        if r["x"] <= cx < r["x"] + r["w"] and r["y"] <= cy < r["y"] + r["h"]:
            return r["token"]
    return None

class FakePilot:

    def __init__(self):
        self.eye = FakeEye()
        self.sim_steps = 60
        self.click = False
        self.calls = []
        self.fired = {TOKEN_A: np.array([1, 3], dtype=np.int64),
                      TOKEN_B: np.array([2, 4], dtype=np.int64)}

    def step(self, img, cx, cy, gains=None, seed=0, detail=False,
             extra_drive=None, extra_record=None):
        self.calls.append({"cx": cx, "cy": cy, "seed": seed, "extra_drive": extra_drive})
        fired = self.fired.get(card_at(cx, cy), np.array([], dtype=np.int64))
        return (0.0, 0.0, self.click, {"stop": 400.0},
                {"fired": fired, "firing": int(len(fired))})

class FakeMB:

    reward_side = np.array([10, 11])
    punish_side = np.array([20, 21])
    calibration = "pn05_apl10_kc03"
    sides_sha = "0f0f"

    def __init__(self, fb):
        self.fb = fb
        self.log = []


        self.kc = np.array([1, 2, 3, 4], dtype=np.int64)
        self.pre = np.array([1, 2, 3, 4], dtype=np.int64)
        self.side = np.array([-1, -1, 1, 1], dtype=np.int8)
        self.base = np.array([300.0, 100.0, 100.0, 100.0], dtype=np.float64)
        self.gain = np.ones(4, dtype=np.float64)

    def observe(self, fired):
        self.log.append(("observe", 0 if fired is None else int(len(fired))))

    def forget(self):
        self.log.append(("forget", None))

    def forget_trace(self):
        self.log.append(("forget_trace", None))

    def dopamine(self, valence, amount=1.0):
        self.log.append(("dopamine", (int(valence), round(float(amount), 6))))
        return 7

    def apply(self):
        self.log.append(("apply", None))

    def save(self):
        self.log.append(("save", None))
        return True

class FakeNose:
    def smell(self, name, symbol="", description=""):
        return {"odorants": [{"name": "geosmin", "weight": 1.0, "why": "test"}],
                "profile": {"DM1": 0.5}}

    def drive(self, smell):
        return {(5, 6): 100.0}

class FakePage:
    def __init__(self, rects=None):
        self.rects = RECTS if rects is None else rects

    async def evaluate(self, js, arg=None):
        return [dict(r) for r in self.rects]

class FakeHttp:

    def __init__(self):
        self.posts = []
        self.gets = []
        self.intent_reply = (200, {"status": "booked", "event": {}})
        self.intent_raises = None
        self.marks = {}
        self.events = {"events": [], "last": 0}

    def post_json(self, url, body, headers=None, timeout=None):
        self.posts.append({"url": url, "body": body, "headers": dict(headers or {}),
                           "timeout": timeout})
        if url.endswith("/intent"):
            if self.intent_raises is not None:
                raise self.intent_raises
            return self.intent_reply
        if url.endswith("/marks"):
            return 200, {"marks": {t: self.marks.get(t, {"value_eth": None, "venue": None,
                                                         "block": None, "reason": "unknown"})
                                   for t in body["tokens"]}}
        return 404, {}

    def get_json(self, url, headers=None, timeout=None):
        self.gets.append(url)
        return 200, json.loads(json.dumps(self.events))

    def intents(self):
        return [p for p in self.posts if p["url"].endswith("/intent")]

class Jobs:

    def __init__(self):
        self.queue = []

    def __call__(self, fn, *args):
        self.queue.append((fn, args))

    def flush(self):
        while self.queue:
            fn, args = self.queue.pop(0)
            fn(*args)

class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.now = [1_700_000_000.0]
        self.fb = FakeBrain()
        self.pilot = FakePilot()
        self.mb = FakeMB(self.fb)
        self.http = FakeHttp()
        self.jobs = Jobs()
        self.page = FakePage()
        self.board = []


        self.write_book([{"token": TOKEN_B, "symbol": "MUD", "name": "Mud"}])
        self.room = Room(self.fb, self.pilot, self.mb, FakeNose(), None, self.tmp,
                         "http://127.0.0.1:4671", "secret",
                         fetch_board=lambda: list(self.board), http=self.http,
                         clock=lambda: self.now[0], spawn=self.jobs)


        self.room.seq_known = True
        self.room.meta = {t: {"market_id": t, "token_ids": [t + "1", t + "2"], "name": t, "question": t} for t in (TOKEN_A, TOKEN_B)}


    def step(self, at, seed=1, click=None):
        if click is not None:
            self.pilot.click = click
        return asyncio.run(self.room.step(self.page, IMG, at[0], at[1], seed))

    def readings(self, A=(300.0, 100.0), B=(100.0, 100.0)):
        self.mb.base[:] = [A[0], B[0], A[1], B[1]]

    def likes(self):
        self.readings(A=(300.0, 100.0), B=(100.0, 100.0))

    def dislikes(self):
        self.readings(A=(100.0, 300.0), B=(100.0, 100.0))

    def look_around(self, at):
        for r in self.page.rects:
            if not (r["x"] <= at[0] < r["x"] + r["w"] and r["y"] <= at[1] < r["y"] + r["h"]):
                self.step((r["x"] + r["w"] / 2.0, r["y"] + r["h"] / 2.0), seed=0)
                return True
        return False

    def commit(self, at, steps=2, flush=True, look_around=True):
        if look_around:
            self.look_around(at)
        for i in range(steps):
            self.step(at, seed=i + 1, click=(i == steps - 1))
        self.pilot.click = False
        if flush:
            self.jobs.flush()

    def looks(self):
        return sorted(p.stem for p in (self.room.dir / "looks").glob("*.json"))

    def write_book(self, positions, mode="paper"):
        p = self.tmp / "betroom" / "public" / "public.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"mode": mode, "positions": positions}), encoding="utf-8")

    def pump_events(self, events, last=None):
        self.http.events = {"events": events,
                            "last": len(events) if last is None else last}
        self.room.poll_events()
        self.jobs.flush()
        self.room.poll_events()

class Dwell(Base):
    def test_leaving_the_card_ends_the_dwell(self):
        self.step(IN_A)
        self.assertEqual(self.room._dwell["steps"], 1)
        self.step(OUTSIDE)
        self.assertIsNone(self.room._dwell)

    def test_another_card_starts_a_new_dwell(self):
        self.step(IN_A)
        self.step(IN_A)
        self.assertEqual(self.room._dwell["steps"], 2)
        self.step(IN_B)
        self.assertEqual(self.room._dwell["token"], TOKEN_B)
        self.assertEqual(self.room._dwell["steps"], 1)

    def test_two_looks_of_evidence_are_needed(self):
        self.commit(IN_A, steps=1)
        self.assertEqual(self.http.intents(), [])
        self.assertEqual(self.looks(), [])
        self.assertEqual(self.room.counters["commits"], 0)

    def test_a_look_at_another_card_is_not_evidence_about_this_one(self):
        self.step(IN_B)
        self.commit(IN_A, steps=1, look_around=False)
        self.assertEqual(self.http.intents(), [])
        self.assertEqual(self.looks(), [])
        self.assertEqual(self.room.counters["commits"], 0)

    def test_a_stop_off_every_card_does_nothing(self):
        self.step(OUTSIDE, click=True)
        self.step(OUTSIDE, click=True)
        self.assertEqual(self.http.intents(), [])
        self.assertEqual(self.looks(), [])
        self.assertEqual(self.room.counters["commits"], 0)

    def test_a_commit_spends_the_evidence(self):
        self.commit(IN_A)
        self.assertIsNone(self.room._dwell)

    def test_one_run_of_the_brain_per_step(self):
        for _ in range(4):
            self.step(IN_A)
            self.step(IN_B)
        self.assertEqual(len(self.pilot.calls), 8)
        self.assertEqual(self.fb.runs, [])

    def test_the_reference_is_the_other_cards_this_visit_has_looked_at(self):
        self.step(IN_A)
        self.assertEqual(self.room._dwell["reference"], [])
        self.step(IN_B)
        self.assertEqual(self.room._dwell["reference"], [TOKEN_A])
        self.step(IN_A)
        self.assertEqual(self.room._dwell["reference"], [TOKEN_B])

    def test_a_card_is_never_its_own_reference(self):
        self.step(IN_A)
        self.step(IN_A)
        self.assertEqual(self.room._dwell["reference"], [])
        self.assertEqual(self.room._dwell["pairs"], 0)

    def test_walking_out_empties_the_room_behind_the_fly(self):
        asyncio.run(self.room.enter(self.page))
        self.step(IN_A)
        self.step(IN_B)
        self.assertEqual(self.room._dwell["reference"], [TOKEN_A])
        self.room.leave()
        asyncio.run(self.room.enter(self.page))
        self.step(IN_B)
        self.assertEqual(self.room._dwell["reference"], [])

    def test_one_card_in_the_room_is_not_a_choice(self):
        self.page.rects = [RECTS[0]]
        self.likes()
        self.commit(IN_A)
        self.assertEqual(self.http.intents(), [])
        look = json.loads((self.room.dir / "looks" / f"{self.looks()[0]}.json").read_text())
        self.assertIsNone(look["drive"])
        self.assertEqual(look["pairs"], 0)
        self.assertEqual(look["reference"], [])

    def test_off_a_card_there_is_no_smell_and_no_reading(self):
        self.step(IN_A)
        self.step(OUTSIDE)
        self.assertIsNone(self.pilot.calls[-1]["extra_drive"])
        self.assertEqual(self.fb.runs, [])
        self.assertEqual(sorted(self.room._seen), [TOKEN_A])

class HowALookIsRead(Base):

    def test_only_the_synapses_whose_kenyon_cell_fired_are_counted(self):

        self.readings(A=(300.0, 100.0), B=(9e6, 9e6))
        self.step(IN_A)
        self.assertEqual((self.room._dwell["A"], self.room._dwell["V"]), (300.0, 100.0))
        self.assertEqual(self.room._seen[TOKEN_A], (300.0, 100.0))

    def test_the_sides_are_split_by_which_dopamine_reaches_them(self):


        self.readings(A=(317.0, 101.0))
        self.step(IN_A)
        self.assertEqual(self.room._dwell["A"], 317.0)
        self.assertEqual(self.room._dwell["V"], 101.0)

    def test_the_reading_is_what_calibration_says_it_is(self):
        self.readings(A=(300.0, 100.0))
        self.step(IN_A)
        self.assertEqual(self.room._seen[TOKEN_A],
                         calibration.syn_drive(self.mb, np.array([1, 3])))

    def test_depressing_an_avoidance_synapse_lifts_the_card(self):
        self.likes()
        self.step(IN_B)
        self.step(IN_A)
        before = self.room._drive_of(self.room._dwell)
        self.mb.gain[2] = 0.5
        self.step(IN_B)
        self.step(IN_A)
        self.assertGreater(self.room._drive_of(self.room._dwell), before)

    def test_the_dwell_averages_its_looks(self):
        self.likes()
        self.step(IN_B)
        self.step(IN_A)
        one = self.room._drive_of(self.room._dwell)
        self.step(IN_A)
        self.assertEqual(self.room._dwell["steps"], 2)
        self.assertEqual(self.room._dwell["pairs"], 2)
        self.assertAlmostEqual(self.room._drive_of(self.room._dwell), one)

class ALookThatReadNothing(Base):

    def blind(self, card="A"):
        if card == "A":
            self.readings(A=(0.0, 0.0), B=(100.0, 300.0))
        else:
            self.readings(A=(300.0, 100.0), B=(0.0, 0.0))

    def test_an_empty_reading_is_not_the_room_behind_the_fly(self):
        self.blind("B")
        self.step(IN_B)
        self.step(IN_A)
        self.assertEqual(self.room._dwell["reference"], [])
        self.assertEqual(self.room._dwell["pairs"], 0)
        self.assertIsNone(self.room._drive_of(self.room._dwell))

    def test_an_empty_reading_is_not_a_look_at_all(self):
        self.blind("A")
        self.step(IN_A)
        self.assertEqual(self.room._dwell["steps"], 0)
        self.assertEqual(self.room._dwell["blind"], 1)
        self.assertEqual(self.room._seen, {})
        self.assertEqual(self.room.counters["looks"], 0)

    def test_a_blind_step_is_not_evidence_and_commits_nothing(self):
        self.step(IN_B)
        self.blind("A")
        self.commit(IN_A, look_around=False)
        self.assertEqual(self.http.intents(), [])
        self.assertEqual(self.looks(), [])

    def test_a_real_reading_next_to_an_empty_one_still_counts(self):
        self.readings(A=(300.0, 100.0), B=(0.0, 0.0))
        self.step(IN_B)
        self.step(IN_A)
        self.assertEqual(sorted(self.room._seen), [TOKEN_A])
        self.assertEqual(self.room._dwell["steps"], 1)

class Commit(Base):
    def test_opposite_reading_commits_even_when_page_says_unheld(self):
        self.room.public.write_text(json.dumps({"open_bets": [
            {"market_id": TOKEN_A, "token_id": TOKEN_A + "2", "side": "NO", "look_id": "original"}]}))
        self.room.refs[TOKEN_A] = ["original"]
        self.likes()
        self.commit(IN_A)
        self.assertEqual(len(self.http.intents()), 1)
        self.assertEqual(self.http.intents()[0]["body"]["side"], "YES")
        self.assertIn("original", self.room.protected_looks())

    def test_booked_intent_blocks_until_settlement_event(self):
        self.likes()
        self.commit(IN_A)
        look = self.http.intents()[0]["body"]["look_id"]
        self.commit(IN_A)
        self.assertEqual(len(self.http.intents()), 1)
        self.room._apply_event({"kind": "settled", "seq": 1, "market_id": TOKEN_A,
                                "look_id": look, "side": "YES", "outcome": "YES"})
        self.commit(IN_A)
        self.assertEqual(len(self.http.intents()), 2)

    def test_liking_a_coin_is_a_buy(self):
        self.likes()
        self.commit(IN_A)
        sent = self.http.intents()
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0]["body"]["side"], "YES")
        self.assertEqual(sent[0]["body"]["market_id"], TOKEN_A)
        self.assertGreater(sent[0]["body"]["drive"], 0)

    def test_liking_a_coin_it_holds_is_still_a_buy(self):
        self.readings(A=(100.0, 100.0), B=(300.0, 100.0))
        self.commit(IN_B)
        self.assertEqual(self.http.intents()[0]["body"]["side"], "YES")

    def test_disliking_a_coin_it_holds_is_a_sell(self):
        self.readings(A=(100.0, 100.0), B=(100.0, 300.0))
        self.commit(IN_B)
        sent = self.http.intents()
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0]["body"]["side"], "NO")
        self.assertLess(sent[0]["body"]["drive"], 0)

    def test_disliking_an_unheld_market_bets_no(self):
        self.dislikes()
        self.commit(IN_A)
        self.assertEqual(len(self.http.intents()), 1)
        self.assertEqual(self.http.intents()[0]["body"]["side"], "NO")
        self.assertEqual(len(self.looks()), 1)

    def test_an_indifferent_commit_sends_nothing(self):
        self.readings(A=(100.0, 100.0), B=(100.0, 100.0))
        self.commit(IN_A)
        self.assertEqual(self.http.intents(), [])
        self.assertEqual(self.room.counters["commits"], 1)
        self.assertEqual(len(self.looks()), 1)

    def test_a_card_that_leans_exactly_like_the_room_is_indifferent(self):
        self.readings(A=(300.0, 100.0), B=(60.0, 20.0))
        self.commit(IN_A)
        look = json.loads((self.room.dir / "looks" / f"{self.looks()[0]}.json").read_text())
        self.assertEqual(look["drive"], 0.0)
        self.assertEqual(self.http.intents(), [])

    def test_above_the_room_is_positive_and_below_it_is_negative(self):
        self.http.intent_reply = (200, {"status": "refused"})
        self.likes()
        self.commit(IN_A)
        self.assertGreater(self.http.intents()[0]["body"]["drive"], 0)
        self.dislikes()
        self.commit(IN_A)
        last = json.loads((self.room.dir / "looks" / f"{self.looks()[-1]}.json").read_text())
        self.assertLess(last["drive"], 0)

    def test_doubling_both_sides_of_a_card_changes_nothing(self):
        self.http.intent_reply = (200, {"status": "refused"})
        self.readings(A=(300.0, 100.0), B=(100.0, 100.0))
        self.commit(IN_A)
        self.readings(A=(600.0, 200.0), B=(200.0, 200.0))
        self.commit(IN_A)
        quiet, loud = (p["body"]["drive"] for p in self.http.intents())
        self.assertAlmostEqual(loud, quiet)

    def test_the_intent_body_is_exactly_the_five_fields(self):
        self.likes()
        self.commit(IN_A)
        body = self.http.intents()[0]["body"]
        self.assertEqual(set(body), {"market_id", "token_id", "side", "drive", "seen_at", "look_id"})
        self.assertEqual(body["seen_at"], self.now[0])
        self.assertTrue((self.room.dir / "looks" / f"{body['look_id']}.json").exists())

    def test_the_intent_token_is_the_only_credential(self):
        self.likes()
        self.commit(IN_A)
        self.assertEqual(self.http.intents()[0]["headers"]["X-Fly-Intent"], "secret")

    def test_the_drive_reaches_the_executor_unclipped(self):
        self.readings(A=(317.0, 101.0), B=(97.0, 103.0))
        self.commit(IN_A)
        want = calibration.relative((317.0, 101.0), [(97.0, 103.0)])
        self.assertEqual(self.http.intents()[0]["body"]["drive"], want)
        self.assertNotEqual(want, round(want, 3))

    def test_nothing_clips_it_but_the_ends_of_the_range(self):
        self.readings(A=(400.0, 0.0), B=(0.0, 400.0))
        self.commit(IN_A)
        self.assertEqual(self.http.intents()[0]["body"]["drive"], 1.0)

    def test_a_commit_while_an_intent_is_in_flight_is_not_sent(self):
        self.likes()
        self.commit(IN_A, flush=False)
        self.commit(IN_B, flush=False)
        self.jobs.flush()
        self.assertEqual(len(self.http.intents()), 1)
        self.assertEqual(self.room.counters["busy"], 1)
        self.assertEqual(self.room.last_intents[-1]["status"], "busy")
        self.assertEqual(len(self.looks()), 2)

    def test_the_look_record_holds_what_a_replay_needs(self):
        self.likes()
        self.commit(IN_A)
        look = json.loads((self.room.dir / "looks" / f"{self.looks()[0]}.json").read_text())
        for key in ("look_id", "at", "token", "symbol", "name", "smell", "card_rect", "cursor",
                    "seed", "drive", "A", "V", "leaning", "dwell_steps", "pairs", "reference",
                    "reference_leaning", "calibration", "sides_sha", "board_item", "crop",
                    "frame", "mode"):
            self.assertIn(key, look)
        for gone in ("A0", "V0", "ground"):
            self.assertNotIn(gone, look, "the blank control is gone and so are its fields")
        self.assertEqual([r["token"] for r in look["reference"]], [TOKEN_B])
        self.assertTrue(look["reference"][0]["smell"]["profile"])


        self.assertEqual((look["A"], look["V"]), (600.0, 200.0))
        self.assertAlmostEqual(look["leaning"], 0.5)
        self.assertEqual(look["reference"][0]["leaning"], 0.0)
        self.assertEqual(look["reference_leaning"], 0.0)
        self.assertAlmostEqual(look["drive"], 0.5)
        self.assertEqual(look["cursor"], list(IN_A))
        self.assertEqual(look["dwell_steps"], 2)
        self.assertEqual(look["calibration"], "pn05_apl10_kc03")
        self.assertEqual(look["mode"], "paper")
        self.assertEqual(look["crop"], [0, 0, 250, 205])

    def test_the_record_cannot_be_read_two_ways(self):
        self.likes()
        self.step(IN_B)
        self.readings(A=(300.0, 100.0))
        self.step(IN_A)
        self.readings(A=(100.0, 100.0))
        self.step(IN_A, click=True)
        self.pilot.click = False
        look = json.loads((self.room.dir / "looks" / f"{self.looks()[0]}.json").read_text())
        self.assertEqual((look["A"], look["V"]), (400.0, 200.0))
        self.assertEqual((look["A_mean"], look["V_mean"]), (200.0, 100.0))
        self.assertAlmostEqual(look["leaning"], 0.25)
        self.assertAlmostEqual(look["leaning_of_sums"], 1.0 / 3.0)
        self.assertNotAlmostEqual(look["leaning"], look["leaning_of_sums"])

    def test_the_record_says_how_much_of_the_window_was_this_card(self):
        self.likes()
        self.commit(IN_A)
        look = json.loads((self.room.dir / "looks" / f"{self.looks()[0]}.json").read_text())


        self.assertAlmostEqual(look["on_card"], 50000.0 / 51250.0, places=4)

    def test_the_record_says_how_much_of_the_brain_was_in_it(self):
        self.likes()
        self.commit(IN_A)
        look = json.loads((self.room.dir / "looks" / f"{self.looks()[0]}.json").read_text())
        self.assertEqual(look["kc_mean"], 2.0)
        self.assertAlmostEqual(look["kc_frac"], 0.5)
        self.assertEqual(look["blind_steps"], 0)

    def test_a_refused_reply_is_reported_on_a_later_step(self):
        self.likes()
        self.http.intent_reply = (200, {"status": "refused", "reason": "nothing to spend"})
        self.commit(IN_A)
        self.jobs.flush()
        self.step(OUTSIDE)
        self.assertEqual(self.room.last_intents[-1]["status"], "refused")
        self.assertEqual(self.room.last_intents[-1]["reason"], "nothing to spend")

class TheFirstCardOfAVisit(Base):

    def test_nothing_commits_before_a_second_card_has_been_seen(self):
        self.likes()
        self.commit(IN_A, look_around=False)
        self.assertEqual(self.http.intents(), [])
        self.assertEqual(self.room.counters["commits"], 1)
        self.assertEqual(self.room.counters["intents"], 0)
        look = json.loads((self.room.dir / "looks" / f"{self.looks()[0]}.json").read_text())
        self.assertIsNone(look["drive"])
        self.assertEqual(look["pairs"], 0)

    def test_the_stop_is_logged_with_a_reason(self):
        self.likes()
        self.commit(IN_A, look_around=False)
        last = self.room.last_intents[-1]
        self.assertEqual(last["status"], "no reference")
        self.assertEqual(last["side"], "none")
        self.assertIsNone(last["drive"])
        self.assertIn("no other card", last["reason"])

    def test_and_then_the_next_card_can_commit(self):
        self.likes()
        self.commit(IN_A, look_around=False)
        self.commit(IN_B, look_around=False)
        self.assertEqual(len(self.http.intents()), 1)
        self.assertEqual(self.http.intents()[0]["body"]["market_id"], TOKEN_B)

    def test_a_fresh_visit_starts_with_nothing_behind_the_fly(self):
        self.likes()
        asyncio.run(self.room.enter(self.page))
        self.jobs.flush()
        self.commit(IN_B, look_around=False)
        self.assertEqual(self.http.intents(), [])
        self.assertEqual(self.room.last_intents[-1]["status"], "no reference")

class State(Base):
    def test_what_the_page_and_the_stream_are_told(self):
        self.likes()
        asyncio.run(self.room.enter(self.page))
        self.jobs.flush()
        self.step(IN_B)
        self.step(IN_A)
        s = self.room.state()
        self.assertTrue(s["in_room"])
        self.assertEqual(s["visits"], 1)
        self.assertEqual(s["seen"], 2)
        self.assertEqual(s["now"]["token"], TOKEN_A)
        self.assertEqual(s["now"]["dwell_steps"], 1)
        self.assertGreater(s["now"]["drive"], 0)
        self.assertEqual(s["learning"], {"sugar": 0, "shock": 0, "last": []})
        for key in ("looks", "commits", "intents", "booked", "refused", "dislikes", "busy",
                    "last_intents", "board_size", "board_error", "board_updated"):
            self.assertIn(key, s)

    def test_looks_and_commits_are_not_the_same_number(self):
        self.likes()
        asyncio.run(self.room.enter(self.page))
        self.jobs.flush()
        for _ in range(3):
            self.step(IN_B)
            self.step(IN_A)
        self.step(IN_A, click=True)
        self.pilot.click = False
        s = self.room.state()
        self.assertEqual(s["commits"], 1)
        self.assertEqual(s["looks"], 7)
        self.assertEqual(self.room.counters["looks"], 7)

    def test_the_first_card_of_a_visit_has_no_drive_to_report(self):
        self.likes()
        asyncio.run(self.room.enter(self.page))
        self.jobs.flush()
        self.step(IN_A)
        self.assertEqual(self.room.state()["seen"], 1)
        self.assertIsNone(self.room.state()["now"]["drive"])

    def test_leaving_ends_the_visit(self):
        asyncio.run(self.room.enter(self.page))
        self.step(IN_A)
        self.room.leave()
        self.assertFalse(self.room.state()["in_room"])
        self.assertIsNone(self.room.state()["now"])

class Eligibility(Base):

    def test_arriving_at_a_card_drops_what_came_before_it(self):
        self.step(IN_A)
        self.assertIn(("forget_trace", None), self.mb.log)
        n = len(self.mb.log)
        self.step(IN_A)
        self.assertNotIn(("forget_trace", None), self.mb.log[n:])
        self.step(IN_B)
        self.assertIn(("forget_trace", None), self.mb.log[n:])

    def test_the_look_itself_is_observed_after_the_wipe(self):
        self.step(IN_A)
        self.assertEqual([k for k, _ in self.mb.log][:3], ["forget_trace", "observe", "forget"])

    def test_off_the_cards_nothing_is_wiped(self):
        self.step(OUTSIDE)
        self.assertNotIn(("forget_trace", None), self.mb.log)
