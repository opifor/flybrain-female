"""Loopback execution and durable paper consequences for every room."""
import copy
import hmac
import json
import math
import os
import re
from dataclasses import dataclass, asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HOST = "127.0.0.1"
# These executor constants keep the safe's limits outside the fly's decision.
TIP_DAILY_CAP_CENTS = 2500
TIP_ADDRESS_CAP_CENTS = 1000
TIP_START_CENTS = 10000


@dataclass(frozen=True)
class Declaration:
    name: str
    path: str
    cards: dict
    commit_means: str
    reward_source: str
    chosen: list
    measured: list
    how: tuple[str, ...] = ()

    def validate(self):
        if not isinstance(self.how, tuple) or (self.how and not 3 <= len(self.how) <= 8):
            raise ValueError("how needs three to eight plain sentences")
        if any(not isinstance(s, str) or not s.strip() or len(s) > 120 or
               s != s.strip() or any(c in s for c in "\n\r<>") or s[-1] not in ".!?"
               for s in self.how):
            raise ValueError("how needs plain sentences of at most 120 characters")
        if not isinstance(self.reward_source, str) or not self.reward_source.strip():
            raise ValueError(f"{self.name}: reward_source is required; say where sugar and shock come from")
        if not self.name or not re.fullmatch(r"/[a-z][a-z0-9]*", self.path):
            raise ValueError("a room needs a name and a local path")
        if not self.commit_means or not self.cards.get("source"):
            raise ValueError("a room needs cards and a commit meaning")
        period = self.cards.get("refresh_seconds")
        if type(period) not in (int, float) or not math.isfinite(period) or period <= 0:
            raise ValueError("cards need a positive refresh period")
        if any(not isinstance(v, list) or any(not isinstance(s, str) or not s.strip() for s in v)
               for v in (self.chosen, self.measured)):
            raise ValueError("chosen and measured must be sentence lists")
        return self

    def public(self):
        return asdict(self.validate())


class Registry:
    def __init__(self):
        self.rooms = {}

    def register(self, declaration, executor_url):
        declaration.validate()
        url = urlparse(executor_url)
        if url.scheme != "http" or url.hostname != HOST or url.username or url.password or url.path not in ("", "/") or url.query or url.fragment:
            raise ValueError("a room executor must be loopback")
        if declaration.path in self.rooms:
            raise ValueError("room path already registered")
        self.rooms[declaration.path] = (declaration, executor_url.rstrip("/"))

    def healthy(self, http):
        doors = []
        for declaration, url in self.rooms.values():
            try:
                code, state = http.get_json(url + "/health", timeout=2)
            except (OSError, ValueError):
                continue
            if code == 200 and isinstance(state, dict) and state.get("ok") is True and not state.get("publish_error"):
                doors.append({"token": declaration.path, "name": declaration.name,
                              "path": declaration.path, "room": declaration.public()})
        return doors


def exact_body(body, fields):
    if not isinstance(body, dict) or set(body) != fields:
        return "the body must be exactly " + str(sorted(fields))
    for key in ("drive", "seen_at"):
        try:
            valid = type(body[key]) in (int, float) and math.isfinite(body[key])
        except OverflowError:
            valid = False
        if not valid:
            return f"invalid {key}"
    if not isinstance(body["look_id"], str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", body["look_id"]):
        return "invalid look_id"


def stale_look(body, now):
    return not 0 <= now - body["seen_at"] <= 20


class LedgerError(ValueError):
    pass


def atomic_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


class WriteAhead:
    def append(self, kind, **fields):
        if not self.ok:
            raise LedgerError(self.error or "ledger unreadable")
        entry = {"kind": kind, "mode": "paper", "at": self.clock(), **fields}
        candidate = copy.deepcopy(self.book)
        candidate.apply(entry)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self.path.open("a", encoding="utf-8", newline="\n") as fh:
                fh.write(json.dumps(entry, separators=(",", ":"), allow_nan=False) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
        except OSError as exc:
            self.ok, self.error = False, str(exc)
            raise
        self.book = candidate
        return entry


class Executor:
    def health(self):
        return {"ok": self.ledger.ok, "mode": "paper",
                "book": self.ledger.book.book_id,
                "balance": self.ledger.book.balance_cents / 100 if self.ledger.ok else None,
                "error": self.ledger.error, "publish_error": self.ledger.publish_error,
                "resolver_error": self.resolver_error}

    def events(self, after=0):
        with self.lock:
            if not self.ledger.ok:
                return 503, {"error": self.ledger.error, "book": self.ledger.book.book_id,
                             "last": None, "events": []}
            return 200, {"last": self.ledger.book.seq, "book": self.ledger.book.book_id,
                         "events": [e for e in self.ledger.book.events if e["seq"] > after]}

    def guarded_intent(self, body, validate, execute):
        why = validate(body)
        if why:
            return 400, {"status": "error", "reason": why}
        if not self.lock.acquire(blocking=False):
            return 409, {"status": "busy"}
        try:
            if not self.ledger.ok:
                return 503, {"status": "error", "reason": self.ledger.error}
            if body["look_id"] in self.ledger.book.look_ids:
                return 409, {"status": "duplicate", "reason": "look already recorded"}
            return execute(body)
        finally:
            self.lock.release()

    def refuse(self, intent_id, reason):
        return 200, {"status": "refused", "reason": reason,
                     "event": self.ledger.terminal("refused", intent_id, reason=reason)}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def reply(self, code, payload):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def authed(self):
        secret = self.server.bookie.intent_token
        return bool(secret) and hmac.compare_digest(
            (self.headers.get("X-Fly-Intent") or "").encode(), secret.encode())

    def do_GET(self):
        route = urlparse(self.path)
        if route.path == "/health":
            return self.reply(200, self.server.bookie.health())
        if not self.authed():
            return self.reply(403, {"status": "forbidden"})
        if route.path == "/events":
            try:
                after = int(parse_qs(route.query).get("after", ["0"])[0])
            except ValueError:
                return self.reply(400, {"status": "error"})
            return self.reply(*self.server.bookie.events(after))
        return self.reply(404, {"status": "error"})

    def do_POST(self):
        if not self.authed():
            return self.reply(403, {"status": "forbidden"})
        if self.path != "/intent":
            return self.reply(404, {"status": "error"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 65536 or self.headers.get("Transfer-Encoding"):
                return self.reply(400, {"status": "error", "reason": "invalid body length"})
            body = json.loads(self.rfile.read(length))
        except (ValueError, UnicodeError):
            return self.reply(400, {"status": "error", "reason": "invalid JSON"})
        try:
            return self.reply(*self.server.bookie.intent(body))
        except (OSError, ValueError) as exc:
            return self.reply(500, {"status": "error", "reason": str(exc)})


def make_server(bookie, port):
    server = ThreadingHTTPServer((HOST, int(port)), Handler)
    server.daemon_threads = True
    server.bookie = bookie
    return server
