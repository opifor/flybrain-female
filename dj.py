"""The paper DJ keeps plays and listeners' reactions in a durable book."""
import hashlib
import json
import logging
import math
import os
from pathlib import Path
import sys
import threading
import time

from envcfg import load_env
from musicroom import CATALOGUE, DECLARATION, catalogue
from roomkit import Executor, WriteAhead, LedgerError, atomic_write, exact_body, stale_look, make_server

FIELDS = {"track_id", "drive", "seen_at", "look_id"}
LIVE_REFUSAL = "live music is not built; this build is paper only"


def check_body(body, tracks=None):
    why = exact_body(body, FIELDS)
    if why:
        return why
    if tracks is None:
        tracks = {row["id"]: row for row in catalogue()}
    if not isinstance(body["track_id"], str) or body["track_id"] not in tracks:
        return "track absent from catalogue"


class Book:
    def __init__(self, tracks, clock=time.time):
        self.tracks, self.clock = tracks, clock
        self.opened = False
        self.balance_cents = self.seq = self.intents = 0
        self.pending = {}
        self.events, self.look_ids, self.reaction_ids = [], set(), set()

    def fills(self):
        return [e for e in self.events if e["kind"] == "fill"]

    def playing(self, at):
        fills = self.fills()
        if fills and fills[-1]["started_at"] <= at < fills[-1]["started_at"] + fills[-1]["duration"]:
            return fills[-1]

    def refusal(self, track_id, at):
        playing = self.playing(at)
        if playing:
            if at - playing["started_at"] < 30:
                return "still playing"
            if track_id == playing["track_id"]:
                return "already playing"

    def apply(self, event):
        try:
            self._apply(event)
        except (KeyError, TypeError, OverflowError) as exc:
            raise LedgerError(f"invalid music entry: {exc}") from exc

    def _apply(self, e):
        if e.get("mode") != "paper" or type(e["at"]) not in (int, float) or not math.isfinite(e["at"]):
            raise LedgerError("invalid paper entry")
        if e["kind"] == "open":
            if self.opened:
                raise LedgerError("repeated opening")
            self.opened = True
            return
        if not self.opened:
            raise LedgerError("entry before open")
        if e["kind"] == "intent":
            if check_body({k: e[k] for k in FIELDS}, self.tracks) or e["id"] != self.intents + 1 or e["look_id"] in self.look_ids:
                raise LedgerError("invalid or repeated intent")
            self.intents = e["id"]
            self.look_ids.add(e["look_id"])
            self.pending[e["id"]] = e
            return
        if e["seq"] != self.seq + 1:
            raise LedgerError("event out of order")
        if e["kind"] in ("fill", "refused"):
            ask = self.pending.get(e["id"])
            if ask is None or any(ask[k] != e[k] for k in FIELDS):
                raise LedgerError("outcome differs from intent")
            if e["kind"] == "fill":
                track = self.tracks[e["track_id"]]
                if (self.refusal(e["track_id"], e["at"]) or stale_look(ask, e["at"]) or
                        not 0 < abs(e["drive"]) <= 1 or e["started_at"] != e["at"] or
                        e["duration"] != track["duration"] or e["title"] != track["title"] or
                        type(e["duration"]) not in (int, float) or not math.isfinite(e["duration"]) or e["duration"] <= 0):
                    raise LedgerError("play differs from catalogue or playback limit")
            elif not e["reason"]:
                raise LedgerError("refusal has no reason")
            del self.pending[e["id"]]
        elif e["kind"] == "dopamine":
            fill = next((f for f in self.fills()[-2:] if f["seq"] == e["fill_seq"]), None)
            if (fill is None or any(e[k] != fill[k] for k in ("id", "track_id", "look_id")) or
                    e["eligible"] != [fill["look_id"]] or e["reaction_id"] in self.reaction_ids or
                    e["reaction_kind"] not in ("sugar", "shock") or
                    e["sign"] != (1 if e["reaction_kind"] == "sugar" else -1) or
                    e["who"] not in ("listener", "chat", "operator") or
                    not fill["started_at"] <= e["reaction_at"] <= e["at"]):
                raise LedgerError("reaction differs from play")
            self.reaction_ids.add(e["reaction_id"])
        else:
            raise LedgerError("unknown music entry")
        self.seq = e["seq"]
        self.events.append(e)

    def public(self):
        now = self.clock()
        fills = self.fills()
        plays = []
        for index, fill in enumerate(fills):
            end = fill["started_at"] + fill["duration"]
            if index + 1 < len(fills):
                end = min(end, fills[index + 1]["started_at"])
            plays.append({k: fill[k] for k in ("track_id", "title", "started_at")})
            plays[-1]["ended_at"] = end if end <= now else None
        reactions = {"sugar": 0, "shock": 0, "tracks": {}}
        for e in self.events:
            if e["kind"] == "dopamine":
                reactions[e["reaction_kind"]] += 1
                counts = reactions["tracks"].setdefault(e["track_id"], {"sugar": 0, "shock": 0})
                counts[e["reaction_kind"]] += 1
        playing = self.playing(now)
        return {"mode": "paper", "last_seq": self.seq,
                "now_playing": {k: playing[k] for k in ("track_id", "title", "started_at", "duration")} if playing else None,
                "plays": plays[-40:], "reactions": reactions,
                "disclosure": " ".join(DECLARATION.chosen + DECLARATION.measured), "room": DECLARATION.public()}


class Ledger(WriteAhead):
    def __init__(self, state_dir, clock=time.time, catalogue_path=CATALOGUE):
        self.path = Path(state_dir) / "musicroom" / "ledger.paper.jsonl"
        self.public_path = self.path.parent / "public" / "public.json"
        self.clock = clock
        self.book = Book({r["id"]: r for r in catalogue(catalogue_path)}, clock)
        self.ok, self.error, self.publish_error = True, None, None
        try:
            if self.path.exists():
                for line in self.path.read_text(encoding="utf-8").splitlines():
                    self.book.apply(json.loads(line))
        except (OSError, ValueError) as exc:
            self.ok, self.error = False, str(exc)
            return
        if not self.book.opened:
            self.append("open", room=DECLARATION.public())
        for i in list(self.book.pending):
            self.terminal("refused", i, reason="interrupted")
        self.write_book()

    def intent(self, body):
        return self.append("intent", id=self.book.intents + 1, **body)["id"]

    def terminal(self, kind, i, **fields):
        event = self.append(kind, id=i, seq=self.book.seq + 1,
                            **{k: self.book.pending[i][k] for k in FIELDS}, **fields)
        self.write_book()
        return event

    def write_book(self):
        if self.ok:
            try:
                atomic_write(self.public_path, json.dumps(self.book.public(), indent=1).encode("utf-8"))
                self.publish_error = None
            except OSError as exc:
                self.publish_error = str(exc)


class DJ(Executor):
    def __init__(self, ledger, intent_token, clock=time.time):
        self.ledger, self.intent_token, self.clock = ledger, intent_token, clock
        self.lock = threading.Lock()
        self.resolver_error = None
        self.reactions_path = ledger.path.parent / "reactions.jsonl"
        self.ignored_path = ledger.path.parent / "reactions.ignored.jsonl"
        self.ignored = set()
        if self.ignored_path.exists():
            self.ignored = {json.loads(line)["reaction_id"] for line in self.ignored_path.read_text(encoding="utf-8").splitlines()}

    def intent(self, body):
        return self.guarded_intent(body, lambda b: check_body(b, self.ledger.book.tracks), self._execute)

    def _execute(self, body):
        led = self.ledger
        i = led.intent(body)
        now = self.clock()
        if stale_look(body, now):
            return self.refuse(i, "stale or future look")
        if not 0 < abs(body["drive"]) <= 1:
            return self.refuse(i, "drive outside range")
        why = led.book.refusal(body["track_id"], now)
        if why:
            return self.refuse(i, why)
        track = led.book.tracks[body["track_id"]]
        return 200, {"status": "booked", "event": led.terminal("fill", i,
                    at=now, started_at=now, duration=track["duration"], title=track["title"])}

    def _ignore(self, reaction_id, reason):
        logging.warning("music reaction ignored: %s", reason)
        with self.ignored_path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps({"reaction_id": reaction_id, "reason": reason}) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        self.ignored.add(reaction_id)

    def resolve_once(self):
        delivered = []
        with self.lock:
            if not self.ledger.ok:
                return delivered
            try:
                lines = self.reactions_path.read_bytes().splitlines(keepends=True) if self.reactions_path.exists() else []
                for index, raw in enumerate(lines):
                    if not raw.endswith(b"\n"):
                        break
                    reaction_id = hashlib.sha256(str(index).encode("ascii") + b":" + raw).hexdigest()
                    if reaction_id in self.ledger.book.reaction_ids or reaction_id in self.ignored:
                        continue
                    try:
                        reaction = json.loads(raw)
                        if (not isinstance(reaction, dict) or reaction.get("kind") not in ("sugar", "shock") or
                                reaction.get("who") not in ("listener", "chat", "operator") or
                                not isinstance(reaction.get("track_id"), str) or
                                type(reaction.get("at")) not in (int, float) or not math.isfinite(reaction["at"]) or
                                reaction["at"] > self.clock()):
                            raise ValueError("invalid reaction")
                    except (ValueError, UnicodeError) as exc:
                        self._ignore(reaction_id, str(exc))
                        continue
                    fill = next((f for f in reversed(self.ledger.book.fills()[-2:])
                                 if f["track_id"] == reaction["track_id"] and f["started_at"] <= reaction["at"]), None)
                    if fill is None:
                        self._ignore(reaction_id, "track is not the current or previous play")
                        continue
                    event = self.ledger.append("dopamine", id=fill["id"], seq=self.ledger.book.seq + 1,
                        fill_seq=fill["seq"], track_id=fill["track_id"], look_id=fill["look_id"],
                        eligible=[fill["look_id"]], reaction_id=reaction_id, reaction_at=reaction["at"],
                        reaction_kind=reaction["kind"], who=reaction["who"],
                        sign=1 if reaction["kind"] == "sugar" else -1, source="listener reaction")
                    delivered.append(event)
                self.resolver_error = None
            except (OSError, ValueError) as exc:
                self.resolver_error = str(exc)
            self.ledger.write_book()
        return delivered


def main():
    settings = load_env()
    if settings.get("FLY_MUSICROOM_LIVE") == "1":
        print(LIVE_REFUSAL, file=sys.stderr)
        return 2
    token = os.environ.get("FLY_INTENT_TOKEN")
    if not token:
        print("FLY_INTENT_TOKEN must be shared with the roamer", file=sys.stderr)
        return 2
    ledger = Ledger(settings.get("FLY_STATE_DIR", "state"),
                    catalogue_path=settings.get("FLY_MUSICROOM_CATALOGUE", CATALOGUE))
    executor = DJ(ledger, token)
    server = make_server(executor, int(settings.get("FLY_MUSICROOM_PORT", "4674")))
    stop = threading.Event()
    def resolve():
        while not stop.is_set():
            executor.resolve_once()
            stop.wait(2)
    worker = threading.Thread(target=resolve, daemon=True)
    worker.start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        server.server_close()
        worker.join(timeout=5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
