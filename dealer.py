"""The sweet card game's durable paper tastes and loopback executor."""
import json
import math
import os
from pathlib import Path
import sys
import threading
import time

from envcfg import load_env
from gameroom import DECLARATION, WORDS, sweet_words, RULE_S
from roomkit import Executor, WriteAhead, LedgerError, atomic_write, exact_body, stale_look, make_server

FIELDS = {"card_id", "drive", "seen_at", "look_id"}


def check_body(body):
    why = exact_body(body, FIELDS)
    if why:
        return why
    if not isinstance(body["card_id"], str) or body["card_id"] not in WORDS:
        return "unknown card"


class Book:
    def __init__(self, clock=time.time):
        self.clock = clock
        self.opened = False
        self.book_id = None
        self.seq = self.intents = 0
        self.pending, self.unrewarded = {}, {}
        self.events, self.look_ids = [], set()

    def refusal(self, word, at):
        fills = [e for e in self.events if e["kind"] == "fill"]
        if any(e["card_id"] == word and at < e["at"] + 60 for e in fills[-12:]):
            return "card resting"
        if fills and at < fills[-1]["at"] + 10:
            return "too soon"

    def apply(self, e):
        try:
            self._apply(e)
        except (KeyError, TypeError, OverflowError) as exc:
            raise LedgerError(f"invalid game entry: {exc}") from exc

    def _apply(self, e):
        if e.get("mode") != "paper" or type(e["at"]) not in (int, float) or not math.isfinite(e["at"]):
            raise LedgerError("invalid paper entry")
        if e["kind"] == "open":
            if self.opened:
                raise LedgerError("repeated opening")
            self.opened, self.book_id = True, str(e["at"])
            return
        if not self.opened:
            raise LedgerError("entry before open")
        if e["kind"] == "intent":
            if check_body({k: e[k] for k in FIELDS}) or e["id"] != self.intents + 1 or e["look_id"] in self.look_ids:
                raise LedgerError("invalid or repeated intent")
            self.intents = e["id"]
            self.pending[e["id"]] = e
            self.look_ids.add(e["look_id"])
            return
        if e["seq"] != self.seq + 1:
            raise LedgerError("event out of order")
        if e["kind"] in ("fill", "refused"):
            ask = self.pending.get(e["id"])
            if ask is None or any(ask[k] != e[k] for k in FIELDS) or e["market_id"] != ask["card_id"]:
                raise LedgerError("outcome differs from intent")
            if e["kind"] == "fill":
                hour = int(e["at"] // RULE_S)
                taste = "sweet" if e["card_id"] in sweet_words(hour) else "sour"
                if (self.refusal(e["card_id"], e["at"]) or stale_look(ask, e["at"]) or
                        not 0 < abs(e["drive"]) <= 1 or e["hour"] != hour or e["taste"] != taste):
                    raise LedgerError("taste differs from rule or pick limit")
                self.unrewarded[e["seq"]] = e
            elif not e["reason"]:
                raise LedgerError("refusal has no reason")
            del self.pending[e["id"]]
        elif e["kind"] == "dopamine":
            fill = self.unrewarded.get(e["fill_seq"])
            if (fill is None or e["id"] != fill["id"] or e["market_id"] != fill["card_id"] or
                    e["look_id"] != fill["look_id"] or e["sign"] != (1 if fill["taste"] == "sweet" else -1)):
                raise LedgerError("dopamine differs from taste")
            del self.unrewarded[e["fill_seq"]]
        else:
            raise LedgerError("unknown game entry")
        self.seq = e["seq"]
        self.events.append(e)

    def public(self):
        hour = int(self.clock() // RULE_S)
        hours = {h: dict(hour=h, picks=0, sweet=0, sour=0, hit_rate=None) for h in range(hour - 6, hour + 1)}
        fills = [e for e in self.events if e["kind"] == "fill"]
        for e in fills:
            if e["hour"] in hours:
                row = hours[e["hour"]]
                row["picks"] += 1
                row[e["taste"]] += 1
                row["hit_rate"] = row["sweet"] / row["picks"]
        return {"mode": "paper", "book": self.book_id, "last_seq": self.seq,
                "hour": hour, "sweet_words": sweet_words(hour), "rule_message": "new rule: four new sweet cards",
                "this_hour": hours[hour], "history": [hours[h] for h in range(hour - 1, hour - 7, -1)],
                "resting_until": {e["card_id"]: e["at"] + 60 for e in fills if e["at"] + 60 > self.clock()},
                "tastes": fills[-100:], "room": DECLARATION.public()}


class Ledger(WriteAhead):
    def __init__(self, state_dir, clock=time.time):
        self.path = Path(state_dir) / "gameroom" / "ledger.paper.jsonl"
        self.public_path = self.path.parent / "public" / "public.json"
        self.clock, self.book = clock, Book(clock)
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
        for fill in list(self.book.unrewarded.values()):
            self.teach(fill)
        self.write_book()

    def intent(self, body):
        return self.append("intent", id=self.book.intents + 1, **body)["id"]

    def terminal(self, kind, i, **fields):
        event = self.append(kind, id=i, seq=self.book.seq + 1,
                            market_id=self.book.pending[i]["card_id"],
                            **{k: self.book.pending[i][k] for k in FIELDS}, **fields)
        self.write_book()
        return event

    def teach(self, fill):
        event = self.append("dopamine", id=fill["id"], seq=self.book.seq + 1,
                            fill_seq=fill["seq"], market_id=fill["card_id"],
                            look_id=fill["look_id"], sign=1 if fill["taste"] == "sweet" else -1)
        self.write_book()
        return event

    def write_book(self):
        if self.ok:
            try:
                atomic_write(self.public_path, json.dumps(self.book.public(), indent=1).encode("utf-8"))
                self.publish_error = None
            except OSError as exc:
                self.publish_error = str(exc)


class Dealer(Executor):
    def __init__(self, ledger, intent_token, clock=time.time):
        self.ledger, self.intent_token, self.clock = ledger, intent_token, clock
        self.lock = threading.Lock()
        self.resolver_error = None

    def health(self):
        return {"ok": self.ledger.ok, "mode": "paper", "book": self.ledger.book.book_id,
                "error": self.ledger.error, "publish_error": self.ledger.publish_error,
                "resolver_error": self.resolver_error}

    def intent(self, body):
        return self.guarded_intent(body, check_body, self._execute)

    def _execute(self, body):
        led, now = self.ledger, self.clock()
        i = led.intent(body)
        if stale_look(body, now):
            return self.refuse(i, "stale or future look")
        if not 0 < abs(body["drive"]) <= 1:
            return self.refuse(i, "drive outside range")
        why = led.book.refusal(body["card_id"], now)
        if why:
            return self.refuse(i, why)
        hour = int(now // RULE_S)
        fill = led.terminal("fill", i, at=now, hour=hour,
                            taste="sweet" if body["card_id"] in sweet_words(hour) else "sour")
        led.teach(fill)
        return 200, {"status": "booked", "event": fill}

    def resolve_once(self):
        with self.lock:
            if self.ledger.ok:
                for fill in list(self.ledger.book.unrewarded.values()):
                    self.ledger.teach(fill)
                self.ledger.write_book()


def main():
    settings = load_env()
    token = os.environ.get("FLY_INTENT_TOKEN")
    if not token:
        print("FLY_INTENT_TOKEN must be shared with the roamer", file=sys.stderr)
        return 2
    executor = Dealer(Ledger(settings.get("FLY_STATE_DIR", "state")), token)
    server = make_server(executor, int(settings.get("FLY_GAMEROOM_PORT", "4678")))
    stop = threading.Event()
    def resolve():
        while not stop.is_set():
            try:
                executor.resolve_once()
                executor.resolver_error = None
            except (OSError, ValueError) as exc:
                executor.resolver_error = str(exc)
            stop.wait(1)
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
