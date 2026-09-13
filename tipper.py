"""Paper tips spend a fixture balance; only fixture thanks can teach."""
import json
import math
import os
import re
import sys
import threading
import time
from fractions import Fraction
from pathlib import Path

from envcfg import load_env
from room import _atomic_write
from roomkit import (Executor, WriteAhead, LedgerError, exact_body, stale_look,
                     make_server, TIP_DAILY_CAP_CENTS, TIP_ADDRESS_CAP_CENTS, TIP_START_CENTS)
from tiproom import DECLARATION, FIXTURES, wallets

FIELDS = {"address", "drive", "seen_at", "look_id"}
LIVE_REFUSAL = "live tipping is not built; this build is paper only"


def check_body(body):
    why = exact_body(body, FIELDS)
    if why:
        return why
    if not isinstance(body["address"], str) or not re.fullmatch(r"0x[0-9a-f]{40}", body["address"]):
        return "invalid address"


class Book:
    def __init__(self):
        self.opened = False
        self.balance_cents = self.seq = self.intents = 0
        self.pending, self.daily, self.addresses = {}, {}, {}
        self.events, self.look_ids, self.thanks_ids = [], set(), set()

    def apply(self, event):
        try:
            return self._apply(event)
        except (KeyError, TypeError, OverflowError) as exc:
            raise LedgerError(f"invalid tip entry: {exc}") from exc

    def _apply(self, e):
        if e.get("mode") != "paper":
            raise LedgerError("this is not a paper entry")
        if e["kind"] == "open":
            if self.opened or int(e["start_cents"]) < 0:
                raise LedgerError("invalid opening balance")
            self.opened = True
            self.balance_cents = int(e["start_cents"])
            return
        if not self.opened:
            raise LedgerError("entry before open")
        if e["kind"] == "intent":
            if check_body({k: e[k] for k in FIELDS}) or e["id"] != self.intents + 1 or e["look_id"] in self.look_ids:
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
                amount = math.floor(Fraction(abs(e["drive"])) * self.balance_cents)
                day = int(e["at"] // 86400)
                if not 0 < abs(e["drive"]) <= 1 or amount <= 0 or amount != int(e["amount_cents"]):
                    raise LedgerError("tip differs from drive times balance")
                if self.daily.get(day, 0) + amount > TIP_DAILY_CAP_CENTS or self.addresses.get(e["address"], 0) + amount > TIP_ADDRESS_CAP_CENTS:
                    raise LedgerError("tip exceeds an executor cap")
                self.balance_cents -= amount
                self.daily[day] = self.daily.get(day, 0) + amount
                self.addresses[e["address"]] = self.addresses.get(e["address"], 0) + amount
            elif not e["reason"]:
                raise LedgerError("refusal has no reason")
            del self.pending[e["id"]]
        elif e["kind"] == "dopamine":
            fill = next((v for v in self.events if v["kind"] == "fill" and v["seq"] == e["fill_seq"]), None)
            if not fill or any(e[k] != fill[k] for k in ("id", "look_id", "address")) or e["sign"] != 1:
                raise LedgerError("thanks differs from tip")
            if e["thanks_id"] in self.thanks_ids or any(v.get("fill_seq") == e["fill_seq"] for v in self.events):
                raise LedgerError("thanks already delivered")
            self.thanks_ids.add(e["thanks_id"])
        else:
            raise LedgerError("unknown tip entry")
        self.seq = e["seq"]
        self.events.append(e)

    def public(self):
        return {"mode": "paper", "balance_cents": self.balance_cents,
                "balance": self.balance_cents / 100, "last_seq": self.seq,
                "tips": [e for e in self.events if e["kind"] == "fill"],
                "events": self.events[-100:], "room": DECLARATION.public(),
                "executor_constants": {"daily_cap_cents": TIP_DAILY_CAP_CENTS,
                                       "address_cap_cents": TIP_ADDRESS_CAP_CENTS}}


class Ledger(WriteAhead):
    def __init__(self, state_dir, clock=time.time):
        self.path = Path(state_dir) / "tiproom" / "ledger.paper.jsonl"
        self.public_path = self.path.parent / "public" / "public.json"
        self.clock, self.book = clock, Book()
        self.ok, self.error, self.publish_error = True, None, None
        try:
            if self.path.exists():
                for line in self.path.read_text(encoding="utf-8").splitlines():
                    self.book.apply(json.loads(line))
        except (OSError, ValueError) as exc:
            self.ok, self.error = False, str(exc)
            return
        if not self.book.opened:
            self.append("open", start_cents=TIP_START_CENTS, room=DECLARATION.public())
        for i in list(self.book.pending):
            self.terminal("refused", i, reason="interrupted")
        self.write_book()

    def intent(self, body):
        return self.append("intent", id=self.book.intents + 1, **body)["id"]

    def terminal(self, kind, i, **fields):
        ask = self.book.pending[i]
        event = self.append(kind, id=i, seq=self.book.seq + 1,
                            **{k: ask[k] for k in FIELDS}, **fields)
        self.write_book()
        return event

    def write_book(self):
        if not self.ok:
            return
        try:
            _atomic_write(self.public_path, json.dumps(self.book.public(), indent=1).encode("utf-8"))
            self.publish_error = None
        except OSError as exc:
            self.publish_error = str(exc)


class Tipper(Executor):
    def __init__(self, ledger, intent_token, clock=time.time, thanks=None):
        self.ledger, self.intent_token, self.clock = ledger, intent_token, clock
        self.lock = threading.Lock()
        self.resolver_error = None
        self.addresses = {c["address"] for c in wallets()}
        self.thanks = thanks if thanks is not None else json.loads((FIXTURES / "thanks.json").read_text(encoding="utf-8"))

    def intent(self, body):
        return self.guarded_intent(body, check_body, self._execute)

    def _execute(self, body):
        led = self.ledger
        i = led.intent(body)
        if stale_look(body, self.clock()):
            return self.refuse(i, "stale or future look")
        if body["address"] not in self.addresses:
            return self.refuse(i, "wallet absent from fixture")
        if not 0 < abs(body["drive"]) <= 1:
            return self.refuse(i, "drive outside range")
        amount = math.floor(Fraction(abs(body["drive"])) * led.book.balance_cents)
        if amount <= 0:
            return self.refuse(i, "nothing to spend")
        if led.book.daily.get(int(self.clock() // 86400), 0) + amount > TIP_DAILY_CAP_CENTS:
            return self.refuse(i, "daily cap")
        if led.book.addresses.get(body["address"], 0) + amount > TIP_ADDRESS_CAP_CENTS:
            return self.refuse(i, "per-address cap")
        return 200, {"status": "booked", "event": led.terminal("fill", i, amount_cents=amount)}

    def resolve_once(self):
        delivered = []
        with self.lock:
            if not self.ledger.ok:
                return delivered
            for thanks in self.thanks:
                if thanks["id"] in self.ledger.book.thanks_ids:
                    continue
                fill = next((e for e in self.ledger.book.events if e["kind"] == "fill"
                             and e["address"] == thanks["address"]
                             and not any(v.get("fill_seq") == e["seq"] for v in self.ledger.book.events)), None)
                if fill is None:
                    continue
                event = self.ledger.append("dopamine", id=fill["id"], seq=self.ledger.book.seq + 1,
                    fill_seq=fill["seq"], address=fill["address"], look_id=fill["look_id"],
                    thanks_id=thanks["id"], sign=1, source="fixture thanks")
                self.ledger.write_book()
                delivered.append(event)
        return delivered


def main():
    settings = load_env()
    if settings.get("FLY_TIPROOM_LIVE") == "1":
        print(LIVE_REFUSAL, file=sys.stderr)
        return 2
    token = os.environ.get("FLY_INTENT_TOKEN")
    if not token:
        print("FLY_INTENT_TOKEN must be minted for this boot and shared with the roamer", file=sys.stderr)
        return 2
    ledger = Ledger(settings.get("FLY_STATE_DIR", str(Path(__file__).parent / "build")))
    executor = Tipper(ledger, token)
    server = make_server(executor, int(settings.get("FLY_TIPROOM_PORT", "4673")))
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
