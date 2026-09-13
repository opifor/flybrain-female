"""A paper USDC book replayed from a write-ahead ledger.

Stakes are whole cents. Shares are exact fractions, written as strings; a
winning payout rounds down to cents and records the remainder. Nothing is
booked until its entry has been flushed and fsynced.
"""
import json
import math
import os
import time
from fractions import Fraction
from pathlib import Path

from polymarket import DISCLOSURE
from roomkit import WriteAhead, LedgerError, atomic_write

CHOSEN = {"size": "floor(abs(drive) * free USDC cents)",
          "pacing": "one open bet per market",
          "shares": "stake USDC / CLOB midpoint, exact fraction",
          "payout": "winning shares rounded down to USDC cents; remainder recorded",
          "resolution": "Gamma closed=true and outcomePrices exactly 1/0 or 0/1",
          "learning": "winning bet +1, losing bet -1, recorded dwell Kenyon cells",
          "paper_omissions": ["fees", "spread", "liquidity", "orderMinSize"]}


def room_declaration():
    from betroom import DECLARATION
    return DECLARATION.public()


def paths(state_dir):
    room = Path(state_dir) / "betroom"
    return {"room": room, "ledger": room / "ledger.paper.jsonl",
            "book": room / "book.paper.json", "public": room / "public" / "public.json"}


class Book:
    def __init__(self):
        self.opened = False
        self.book_id = None
        self.balance_cents = self.start_cents = self.seq = self.intents = 0
        self.pending, self.positions = {}, {}
        self.events, self.settled = [], []
        self.counts = {"wins": 0, "losses": 0, "refused": 0}
        self.refusals = {}
        self.look_ids = set()

    def apply(self, e):
        try:
            return self._apply(e)
        except (KeyError, TypeError, ZeroDivisionError, OverflowError) as exc:
            raise LedgerError(f"invalid ledger entry: {exc}") from exc

    def _apply(self, e):
        if e.get("mode") != "paper":
            raise LedgerError("this is not a paper entry")
        kind = e["kind"]
        if kind == "open":
            if self.opened:
                raise LedgerError("ledger opened twice")
            start = int(e["start_cents"])
            if start < 0:
                raise LedgerError("negative starting balance")
            self.balance_cents = self.start_cents = start
            self.opened = True
            self.book_id = str(e["at"])
            return e
        if not self.opened:
            raise LedgerError("entry before open")
        i = int(e["id"])
        if kind == "intent":
            if i != self.intents + 1 or e["look_id"] in self.look_ids:
                raise LedgerError("intent repeated or out of order")
            self.intents = i
            self.pending[i] = e
            self.look_ids.add(e["look_id"])
            return e
        if int(e["seq"]) != self.seq + 1:
            raise LedgerError("event out of order")
        if kind in ("fill", "refused"):
            if i not in self.pending:
                raise LedgerError("outcome has no open intent")
            ask = self.pending[i]
            if any(e[k] != ask[k] for k in ("market_id", "token_id", "side", "drive", "look_id")):
                raise LedgerError("outcome differs from intent")
            if kind == "fill" and e.get("action") == "sell":
                self._sell(e, ask)
            elif kind == "fill":
                stake, price, shares = int(e["stake_cents"]), Fraction(e["price"]), Fraction(e["shares"])
                drive = Fraction(ask["drive"])
                if ask["side"] not in ("YES", "NO") or not 0 < abs(drive) <= 1 or (drive > 0) != (ask["side"] == "YES"):
                    raise LedgerError("side disagrees with drive")
                if stake != math.floor(abs(drive) * self.balance_cents) or stake <= 0:
                    raise LedgerError("stake differs from drive times balance")
                if not 0 < price < 1 or shares != Fraction(stake, 100) / price:
                    raise LedgerError("invalid fill arithmetic")
                self.balance_cents -= stake
                self.positions[i] = dict(e, outcome=None)
            else:
                if not e["reason"]:
                    raise LedgerError("refusal has no reason")
                self.counts["refused"] += 1
                self.refusals[e["reason"]] = self.refusals.get(e["reason"], 0) + 1
            del self.pending[i]
        elif kind == "dopamine":
            fill = next((v for v in self.events if v["seq"] == e["fill_seq"]), None)
            if not fill or fill.get("action") != "sell" or fill["kind"] != "fill":
                raise LedgerError("dopamine has no sell fill")
            if any(v.get("fill_seq") == e["fill_seq"] for v in self.events):
                raise LedgerError("dopamine repeated")
            pnl = int(fill["pnl_cents"])
            if (e["sign"] != (1 if pnl > 0 else -1 if pnl < 0 else 0) or
                    e["look_id"] != fill["buy_look_id"] or e["market_id"] != fill["market_id"] or i != fill["id"]):
                raise LedgerError("dopamine differs from sell fill")
        elif kind == "settled":
            if i not in self.positions:
                raise LedgerError("settlement has no open bet")
            pos = self.positions[i]
            if any(e[k] != pos[k] for k in ("market_id", "token_id", "side", "look_id", "question")):
                raise LedgerError("settlement differs from its open bet")
            if e["outcome"] not in ("YES", "NO"):
                raise LedgerError("unknown outcome")
            won = pos["side"] == e["outcome"]
            exact = Fraction(pos["shares"]) * 100 if won else Fraction(0)
            payout = math.floor(exact)
            if int(e["payout_cents"]) != payout or Fraction(e["rounding_cents"]) != exact - payout:
                raise LedgerError("invalid payout arithmetic")
            self.balance_cents += payout
            self.counts["wins" if won else "losses"] += 1
            self.settled.append({**pos, **e, "won": won})
            self.settled = self.settled[-50:]
            del self.positions[i]
        else:
            raise LedgerError(f"unknown entry {kind}")
        self.seq = int(e["seq"])
        self.events.append(e)
        return e

    def _sell(self, e, ask):
        pos = self.positions.get(e["position_id"])
        if not pos or ask.get("action") != "sell":
            raise LedgerError("sell has no open bet")
        drive = Fraction(ask["drive"])
        if (not 0 < abs(drive) <= 1 or (drive > 0) != (ask["side"] == "YES") or
                ask["side"] == pos["side"] or e["market_id"] != pos["market_id"] or
                e["buy_look_id"] != pos["look_id"] or e["held_token_id"] != pos["token_id"]):
            raise LedgerError("sell differs from its open bet")
        price = Fraction(e["exit_price"])
        exact = Fraction(pos["shares"]) * price * 100
        payout = math.floor(exact)
        pnl = payout - int(pos["stake_cents"])
        if (not 0 < price < 1 or int(e["payout_cents"]) != payout or
                Fraction(e["rounding_cents"]) != exact - payout or int(e["pnl_cents"]) != pnl):
            raise LedgerError("invalid sell arithmetic")
        self.balance_cents += payout
        if pnl:
            self.counts["wins" if pnl > 0 else "losses"] += 1
        self.settled.append({**pos, "kind": "sold", "exit_price": str(price),
                             "payout_cents": str(payout), "pnl_cents": str(pnl),
                             "rounding_cents": str(exact - payout), "pnl": pnl / 100,
                             "at": e["at"], "seq": e["seq"], "sell_look_id": e["look_id"],
                             "won": pnl > 0})
        self.settled = self.settled[-50:]
        del self.positions[e["position_id"]]

    def state(self):
        return {"mode": "paper", "start_cents": self.start_cents,
                "balance_cents": self.balance_cents, "seq": self.seq, "intents": self.intents,
                "positions": list(self.positions.values()), "pending": list(self.pending.values()),
                "settled": self.settled, "counts": self.counts, "refusals": self.refusals}

    def public(self, at=None):
        def display(p):
            return {**p, "stake": int(p["stake_cents"]) / 100,
                    **({"exit_price": float(Fraction(p["exit_price"]))} if "exit_price" in p else {}),
                    "price": float(Fraction(p["price"])), "shares": float(Fraction(p["shares"]))}
        markets = {e["market_id"]: {"open": False} for e in self.events}
        for p in self.positions.values():
            markets[p["market_id"]] = {"open": True}
        return {"mode": "paper", "balance": self.balance_cents / 100,
                "markets": markets, "refusals": dict(self.refusals),
                "balance_cents": self.balance_cents, "start_balance": self.start_cents / 100,
                "open_bets": [display(p) for p in self.positions.values()],
                "settled_bets": [display(p) for p in self.settled],
                "win_count": self.counts["wins"], "loss_count": self.counts["losses"],
                "counts": dict(self.counts), "last_seq": self.seq,
                "disclosure": DISCLOSURE, "chosen": CHOSEN,
                "room": room_declaration(),
                "updated": time.time() if at is None else at}


class Ledger(WriteAhead):
    def __init__(self, path, start_cents=10000, clock=time.time):
        self.path = Path(path)
        if self.path.name != "ledger.paper.jsonl":
            raise ValueError("this build uses ledger.paper.jsonl only")
        self.book_path = self.path.parent / "book.paper.json"
        self.public_path = self.path.parent / "public" / "public.json"
        self.clock = clock
        self.book = Book()
        self.ok, self.error, self.publish_error = True, None, None
        try:
            if self.path.exists():
                self.book = rebuild(self.path)
        except (OSError, ValueError) as exc:
            self.ok, self.error = False, str(exc)
            return
        if not self.book.opened:
            self.append("open", start_cents=str(int(start_cents)), disclosure=DISCLOSURE, chosen=CHOSEN)
        for i, ask in list(self.book.pending.items()):
            self.terminal("refused", i, reason="interrupted")
        for ev in list(self.book.events):
            if ev["kind"] == "fill" and ev.get("action") == "sell" and not any(
                    v.get("fill_seq") == ev["seq"] for v in self.book.events):
                self.teach_sell(ev)
        self.write_book()


    def intent(self, fields):
        return self.append("intent", id=self.book.intents + 1, **fields)["id"]

    def terminal(self, kind, i, **fields):
        ask = self.book.pending[i]
        context = {k: ask[k] for k in ("market_id", "token_id", "side", "drive", "look_id", "seen_at")}
        ev = self.append(kind, id=i, seq=self.book.seq + 1, **context, **fields)
        self.write_book()
        return ev

    def settle(self, i, outcome, observation):
        pos = self.book.positions[i]
        exact = Fraction(pos["shares"]) * 100 if pos["side"] == outcome else Fraction(0)
        payout = math.floor(exact)
        context = {k: pos[k] for k in ("market_id", "token_id", "side", "look_id", "question")}
        ev = self.append("settled", id=i, seq=self.book.seq + 1, **context,
                         outcome=outcome, payout_cents=str(payout),
                         rounding_cents=str(exact - payout), observation=observation)
        self.write_book()
        return ev

    def sell(self, i, position_id, price, quoted_at):
        pos = self.book.positions[position_id]
        exact = Fraction(pos["shares"]) * price * 100
        payout = math.floor(exact)
        ev = self.terminal("fill", i, action="sell", position_id=position_id,
                           buy_look_id=pos["look_id"], held_token_id=pos["token_id"],
                           exit_price=str(price), payout_cents=str(payout),
                           pnl_cents=str(payout - int(pos["stake_cents"])),
                           rounding_cents=str(exact - payout),
                           quote_source="CLOB midpoint", quoted_at=quoted_at)
        self.teach_sell(ev)
        return ev

    def teach_sell(self, fill):
        pnl = int(fill["pnl_cents"])
        ev = self.append("dopamine", id=fill["id"], seq=self.book.seq + 1,
                         fill_seq=fill["seq"], market_id=fill["market_id"],
                         look_id=fill["buy_look_id"], sign=1 if pnl > 0 else -1 if pnl < 0 else 0)
        self.write_book()
        return ev

    def write_book(self):
        if not self.ok:
            return
        try:
            atomic_write(self.book_path, json.dumps(self.book.state(), indent=1).encode("utf-8"))
            atomic_write(self.public_path, json.dumps(self.book.public(), indent=1).encode("utf-8"))
            self.publish_error = None
        except OSError as exc:
            self.publish_error = str(exc)
            print(f"[betbook] ledger intact; publication failed: {exc}", flush=True)


def rebuild(path):
    book = Book()
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            book.apply(json.loads(line))
        except (ValueError, AttributeError) as exc:
            raise LedgerError(f"line {n}: {exc}") from exc
    return book
