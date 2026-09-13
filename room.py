"""The eye, dwell, intent and remembered lesson shared by the rooms."""
import json
import hashlib
import os
import re
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
import calibration
from roomkit import atomic_write as _atomic_write

DWELL_MIN = 2
BOARD_MAX_AGE_S = 30
CHAIN_TIMEOUT_S = 45
FOV_W, FOV_H = 300, 210
RECTS_JS = """() => Array.from(document.querySelectorAll('[data-token]')).map(e => {
  const r = e.getBoundingClientRect();
  return {token: e.getAttribute('data-token') || '',
          held: false, x: r.left, y: r.top, w: r.width, h: r.height};
})"""

def _thread(fn, *args):
    threading.Thread(target=fn, args=args, daemon=True).start()

def answered_unbooked(status, http=None):
    try:
        code = int(http)
    except (TypeError, ValueError):
        code = None
    if code is not None and 400 <= code < 500:
        return True
    if code is not None and code >= 500:
        return False                  # the far side broke; nothing was said about the intent
    s = str(status)
    return s in ("refused", "busy") or s.startswith("http 4")

class LoopbackHttp:

    def __init__(self, timeout=10.0):
        self.timeout = float(timeout)

    def _call(self, url, data=None, headers=None, timeout=None):
        req = urllib.request.Request(
            url, data=data, method="POST" if data is not None else "GET",
            headers={"Accept": "application/json", **({"Content-Type": "application/json"} if data else {}),
                     **(headers or {})})
        try:
            with urllib.request.urlopen(req, timeout=float(timeout or self.timeout)) as r:
                return r.status, json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as exc:            # a refusal is an answer, not a failure
            try:
                return exc.code, json.loads(exc.read() or b"{}")
            except ValueError:
                return exc.code, {}

    def get_json(self, url, headers=None, timeout=None):
        return self._call(url, None, headers, timeout)

    def post_json(self, url, body, headers=None, timeout=None):
        return self._call(url, json.dumps(body).encode("utf-8"), headers, timeout)

class Room:
    declaration = None
    disclosure = ""
    event_token_key = "card_id"

    def board_source(self):
        raise NotImplementedError("a room needs a board source")

    def can_commit(self, token, at):
        return not self.refs.get(token)

    def intent_body(self, token, drive, at, look_id):
        raise NotImplementedError("a room needs a commit meaning")

    dwell_min = DWELL_MIN
    max_looks = 2000

    def board(self):
        return {**self._board, "cards": [c for c in self._board["cards"]
                if c.get("end_at", float("inf")) > self._now()],
                "disclosure": self.disclosure, "room": self.declaration.public(), "error": self._board_error}

    def _board_worker(self):
        try:
            cards = self.fetch_board()
            for c in cards:
                self.remember(c["token"], c)
            self._board = {"cards": cards, "updated": self._now()}
            self._board_error = None
            self._save_room()
        except (OSError, ValueError, KeyError, TypeError) as exc:
            self._board_error = str(exc)
            self._say(f"board fetch failed: {exc}")
        finally:
            self._board_busy = False

    def smell_of(self, token):
        return None

    def extra_drive(self, smell):
        return self.nose.drive(smell) if smell else None

    async def _rects(self, page):
        raw = await page.evaluate(RECTS_JS)
        return [r for r in raw if r.get("token") in self.meta and
                float(r.get("w", 0)) > 0 and float(r.get("h", 0)) > 0]

    def _commit(self, img, cx, cy, seed, card, dwell, drive, smell):
        at, token = self._now(), card["token"]
        if not self.can_commit(token, at):
            return
        self.counters["commits"] += 1
        look_id = self._write_look(at, img, cx, cy, seed, card, dwell, drive, smell)
        if drive is None:
            self._note_intent(at, token, "none", None, "no reference",
                              "the fly has looked at no other card in this visit")
            return
        if drive == 0:
            return
        if self._intent is not None:
            self.counters["busy"] += 1
            self._note_intent(at, token, "none", drive, "busy", "an intent is in flight")
            return
        body = self.intent_body(token, drive, at, look_id)
        self._intent = {"body": body, "symbol": token, "at": at, "done": False, "result": None}
        self.counters["intents"] += 1
        self.refs.setdefault(token, []).append(look_id)
        self._save_room()
        self.spawn(self._intent_worker, self._intent)
        self._prune_looks()

    def protected_looks(self):
        return {look for ids in self.refs.values() for look in ids}

    def _read_look(self, look_id):
        if not isinstance(look_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", look_id):
            return None
        try:
            return json.loads((self.looks_dir / f"{look_id}.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    def poll_events(self):
        self.refresh_board()
        pending, self._events_result = self._events_result, None
        if pending is not None and not pending.get("error"):
            for ev in pending.get("events", []):
                if ev["seq"] <= self.last_seq:
                    continue
                self._apply_event(ev)
                self.last_seq = ev["seq"]
                self._save_room()
        if not self._events_busy and self._now() - self._events_at >= 2:
            self._events_busy, self._events_at = True, self._now()
            self.spawn(self._events_worker, self.last_seq)

    def _events_worker(self, after):
        try:
            health_code, health = self.http.get_json(self.executor_url + "/health")
            self.bookie_status = {"at": self._now(), "ok": health_code == 200 and
                                  health.get("ok") is True and not health.get("publish_error")}
            code, result = self.http.get_json(f"{self.executor_url}/events?after={after}",
                                             headers={"X-Fly-Intent": self.intent_token})
            if code == 200:
                self._events_result = result
                self.public_events = (self.public_events + result.get("events", []))[-100:]
        except (OSError, ValueError) as exc:
            self.bookie_status = {"at": self._now(), "ok": False}
            self._say(f"events unavailable: {exc}")
        finally:
            self._events_busy = False

    def _apply_event(self, ev):
        token, look_id = ev.get(self.event_token_key), ev.get("look_id")
        if ev["kind"] == "fill":
            self.counters["booked"] += 1
        elif ev["kind"] == "refused":
            self.counters["refused"] += 1
            self._drop_ref(token, look_id)
        elif ev["kind"] == "dopamine":
            self._teach(ev)
            self._drop_ref(token, look_id)

    def reward_sign(self, ev):
        return ev["sign"]

    def _teach(self, ev):
        if ev["seq"] in self._claimed:
            return
        look = self._read_look(ev.get("look_id"))
        eligible = (look or {}).get("eligible", [])
        if look and look.get("brain_id") != self.brain_id:
            eligible = []
        sign = self.reward_sign(ev)
        record = {"mode": "paper", "at": self._now(), "seq": ev["seq"],
                  self.event_token_key: ev[self.event_token_key], "look_id": ev["look_id"],
                  "sign": sign, "amount": 1.0, "eligible": eligible,
                  "status": "break even" if sign == 0 else "pending" if eligible else "missing eligibility"}
        if look and look.get("token") != ev[self.event_token_key]:
            raise ValueError("settlement does not match its look")
        self.dopamine_file.parent.mkdir(parents=True, exist_ok=True)
        # A durable claim prevents a restart from delivering the same lesson twice.
        with self.dopamine_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
            f.flush()
            os.fsync(f.fileno())
        self._claimed.add(ev["seq"])
        if eligible and sign:
            self.mb.forget_trace()
            try:
                self.mb.observe(np.asarray(eligible, dtype=np.int64))
                record["synapses_hit"] = int(self.mb.dopamine(sign))
                self.mb.apply()
                if self.mb.save() is False:
                    raise OSError("mushroom body could not save the lesson")
                self._forget_room()
            finally:
                self.mb.forget_trace()
            self.counters["sugar" if sign > 0 else "shock"] += 1
            record["status"] = "delivered"
            with self.dopamine_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
                f.flush()
                os.fsync(f.fileno())
        self.last_dopamine.append(record)
        self.last_dopamine = self.last_dopamine[-10:]

    def _save_room(self):
        with self._lock:
            _atomic_write(self.room_file, json.dumps({"mode": "paper", "meta": self.meta,
                "refs": self.refs, "last_seq": self.last_seq, "look_seq": self._look_seq,
                "counters": self.counters, "last_intents": self.last_intents,
                "last_dopamine": self.last_dopamine, "cards": self._board["cards"]}, indent=1).encode("utf-8"))

    def _load_room(self):
        if self.room_file.exists():
            d = json.loads(self.room_file.read_text(encoding="utf-8"))
            self.meta, self.refs = d["meta"], d["refs"]
            self.last_seq, self._look_seq = d["last_seq"], d["look_seq"]
            self.counters.update(d["counters"])
            self.last_intents, self.last_dopamine = d["last_intents"], d["last_dopamine"]
            self._board["cards"] = d["cards"]
        if self.dopamine_file.exists():
            for line in self.dopamine_file.read_text(encoding="utf-8").splitlines():
                event = json.loads(line)
                self._claimed.add(event["seq"])
                self.last_seq = max(self.last_seq, event["seq"])

    def __init__(self, fb, pilot, mb, nose, gains, state_dir, executor_url,
                 intent_token, fetch_board=None, http=None, clock=time.time, spawn=None):
        self.declaration.validate()
        from urllib.parse import urlparse
        url = urlparse(executor_url)
        if url.scheme != "http" or url.hostname != "127.0.0.1" or url.username or url.password or url.path not in ("", "/") or url.query or url.fragment:
            raise ValueError("the room speaks only to its loopback bookie")
        self.fb, self.pilot, self.mb, self.nose, self.gains = fb, pilot, mb, nose, gains
        self.dir = Path(state_dir) / self.declaration.path.strip("/")
        self.looks_dir = self.dir / "looks"
        self.public = self.dir / "public" / "public.json"
        self.room_file = self.dir / "room.json"
        self.dopamine_file = self.dir / "dopamine.jsonl"
        self.executor_url, self.intent_token = executor_url.rstrip("/"), intent_token
        self.clock, self.spawn = clock, spawn or _thread
        self.http, self.fetch_board = http or LoopbackHttp(), fetch_board or self.board_source()
        self.readout = calibration.readout(mb)
        digest = hashlib.sha256(str(fb.n).encode("ascii"))
        for values in (getattr(fb, "bodies", []), mb.kc, mb.pre, getattr(mb, "post", []), mb.side):
            digest.update(np.asarray(values, dtype=np.int64).tobytes())
        self.brain_id = digest.hexdigest()
        self._claimed = set()
        self.in_room = False
        self.counters = dict.fromkeys(("visits", "looks", "commits", "intents", "booked",
                                      "refused", "dislikes", "busy", "sugar", "shock"), 0)
        self._board = {"cards": [], "updated": 0}
        self._board_busy = False
        self._board_error = None
        self._dwell = self._intent = None
        self._seen, self._smell, self.meta, self.refs = {}, {}, {}, {}
        self._held = set()
        self._look_seq = self.last_seq = 0
        self.last_intents, self.last_dopamine = [], []
        self._said_no_book = False
        self._events_result = None
        self._events_busy = False
        self._events_at = 0
        self.bookie_status = {"at": 0, "ok": False}
        self.public_events = []
        self._lock = threading.Lock()
        self._load_room()

    @property
    def mode(self):
        return "paper"

    def _say(self, message):
        print(f"[{self.declaration.path.strip(chr(47))}] {message}", flush=True)

    def refresh_board(self, force=False):
        if self._board_busy:
            return False
        if not force and self._now() - self._board["updated"] < self.declaration.cards["refresh_seconds"]:
            return False
        self._board_busy = True
        self.spawn(self._board_worker)
        return True

    def remember(self, token, meta):
        cur = dict(self.meta.get(token) or {})
        for k, v in (meta or {}).items():
            if v not in (None, ""):
                cur[k] = v
        self.meta[token] = cur

    def read_book(self):
        try:
            book = json.loads(self.public.read_text(encoding="utf-8"))
        except FileNotFoundError:
            if not self._said_no_book:
                self._said_no_book = True
                self._say(f"no paper book at {self.public} - the executor writes it; "
                          "until it exists the room holds nothing")
            return {}
        except (OSError, ValueError) as exc:
            if not self._said_no_book:
                self._said_no_book = True
                self._say(f"the paper book at {self.public} cannot be read: {str(exc)[:90]}")
            return {}
        self._said_no_book = False
        return book

    async def enter(self, page):
        self.in_room = True
        self.counters["visits"] += 1
        self._dwell = None
        self._seen = {}
        self.refresh_board(force=True)
        self._save_room()

    def leave(self):
        self.in_room = False
        self._dwell = None
        self._seen = {}
        self._save_room()

    async def step(self, page, img, cx, cy, seed):
        self._collect_intent()
        self.refresh_board()
        rects = await self._rects(page)
        card = self._card_at(rects, cx, cy)
        token = card["token"] if card else None
        if token is not None and (self._dwell is None or self._dwell["token"] != token):
            self.mb.forget_trace()

        smell = self.smell_of(token) if token else None
        dx, dy, click, hz, info = self.pilot.step(
            img, cx, cy, gains=self.gains, seed=seed, detail=True,
            extra_drive=self.extra_drive(smell),
            extra_record=self.readout)

        self.mb.observe(info.get("fired"))
        self.mb.forget()

        dwell = self._advance_dwell(card)
        if dwell is not None:
            own = calibration.syn_drive(self.mb, info.get("fired"))
            if not calibration.has_reading(own):
                dwell["blind"] += 1
            else:
                dwell.setdefault("eligible", set()).update(int(k) for k in (info.get("fired") if info.get("fired") is not None else []) if k in self.mb.kc)
                others = self._room_behind(token)
                dwell["steps"] += 1
                dwell["A"] += own[0]
                dwell["V"] += own[1]
                dwell["kc"] += self._kc_fired(info.get("fired"))
                dwell["lean_sum"] += calibration.leaning(own)
                dwell["cursor"] = [float(cx), float(cy)]
                self.counters["looks"] += 1
                if others:
                    dwell["drive_sum"] += calibration.relative(own, [r for _, r in others])
                    dwell["pairs"] += 1
                    dwell["reference"] = [t for t, _ in others]
                self._seen[token] = own

        drive = self._drive_of(dwell)
        if click and dwell is not None and dwell["steps"] >= self.dwell_min:
            self._commit(img, cx, cy, seed, card, dwell, drive, smell)
            self._dwell = None                     # a commit spends the evidence
        elif click:
            pass                                   # a stop off a card, or too soon, is nothing


        info[self.declaration.path.strip("/")] = {"token": token, "drive": drive,
                            "dwell_steps": int(self._dwell["steps"]) if self._dwell else 0}
        return dx, dy, click, hz, info

    @staticmethod
    def _card_at(rects, cx, cy):
        for r in rects:
            if r["x"] <= cx < r["x"] + r["w"] and r["y"] <= cy < r["y"] + r["h"]:
                return r
        return None

    def _advance_dwell(self, card):
        if card is None:
            self._dwell = None
            return None
        d = self._dwell
        if d is None or d["token"] != card["token"]:
            d = {"token": card["token"], "steps": 0, "blind": 0, "A": 0.0, "V": 0.0,
                 "kc": 0, "lean_sum": 0.0,
                 "pairs": 0, "drive_sum": 0.0, "reference": [],
                 "cursor": None, "mark": None, "card": card}
            self._dwell = d
        d["held"] = card["token"] in self._held      # the book, not the page
        d["card"] = card
        return d

    def _kc_fired(self, fired):
        kc = getattr(self.mb, "kc", None)
        if fired is None or kc is None or not len(kc):
            return 0
        return int(np.isin(np.asarray(kc), np.asarray(fired)).sum())

    def _drive_of(self, dwell):
        if not dwell or dwell["steps"] <= 0 or dwell["pairs"] <= 0:
            return None
        return float(np.clip(dwell["drive_sum"] / float(dwell["pairs"]), -1.0, 1.0))

    def _room_behind(self, token):
        return sorted((t, r) for t, r in self._seen.items()
                      if t != token and calibration.has_reading(r))

    def _intent_worker(self, slot):
        out = {"status": "unreachable", "reason": "no answer from the executor", "http": None}
        try:
            status, obj = self.http.post_json(
                self.executor_url + "/intent", dict(slot["body"]),
                headers={"X-Fly-Intent": self.intent_token},
                timeout=CHAIN_TIMEOUT_S)
            if isinstance(obj, dict) and obj:
                out = dict(obj)
                out.setdefault("status", f"http {status}")
            else:
                out = {"status": f"http {status}", "reason": ""}
            out["http"] = status
        except (OSError, ValueError) as exc:
            out = {"status": "unreachable", "reason": str(exc)[:120], "http": None}
        slot["result"] = out
        slot["done"] = True

    def _collect_intent(self):
        slot = self._intent
        if slot is None or not slot.get("done"):
            return
        res = slot.get("result") or {}
        status = str(res.get("status") or "unknown")
        self._note_intent(slot["at"], slot["symbol"], slot["body"].get("side", self.declaration.commit_means),
                          slot["body"]["drive"], status, res.get("reason"))
        if answered_unbooked(status, res.get("http")):
            self._drop_ref(slot["symbol"], slot["body"]["look_id"])
        self._intent = None
        self._save_room()

    def _note_intent(self, at, symbol, side, drive, status, reason=None):
        self.last_intents.append({"at": int(at), "symbol": symbol, "side": side,
                                  "drive": None if drive is None else round(float(drive), 6),
                                  "status": status,
                                  "reason": (str(reason)[:120] if reason else None)})
        self.last_intents = self.last_intents[-10:]

    def _write_look(self, at, img, cx, cy, seed, card, dwell, drive, smell):
        self._look_seq += 1
        look_id = f"{int(at * 1000):013d}-{self._look_seq:04d}"
        h, w = int(img.shape[0]), int(img.shape[1])
        x0 = max(0, min(w, int(round(cx - FOV_W / 2.0))))
        y0 = max(0, min(h, int(round(cy - FOV_H / 2.0))))
        x1 = max(x0, min(w, int(round(cx + FOV_W / 2.0))))
        y1 = max(y0, min(h, int(round(cy + FOV_H / 2.0))))
        m = self.meta.get(card["token"]) or {}
        steps = max(1, int(dwell["steps"]))
        reference = [{"token": t, "leaning": calibration.leaning(self._seen[t]),
                      "smell": self.smell_of(t)}
                     for t in dwell["reference"]
                     if t in self._seen and calibration.has_reading(self._seen[t])]
        kc = getattr(self.mb, "kc", None)
        kc_cells = max(1, 0 if kc is None else len(kc))
        ox = max(0.0, min(float(x1), card["x"] + card["w"]) - max(float(x0), card["x"]))
        oy = max(0.0, min(float(y1), card["y"] + card["h"]) - max(float(y0), card["y"]))
        window = float(max(1, (x1 - x0) * (y1 - y0)))
        record = {
            "look_id": look_id, "at": at, "token": card["token"],
            "symbol": m.get("symbol") or "", "name": m.get("name") or "",
            "smell": smell, "card_rect": [card["x"], card["y"], card["w"], card["h"]],
            "cursor": [float(cx), float(cy)], "seed": int(seed), "drive": drive,
            "A": dwell["A"], "V": dwell["V"], "leaning": dwell["lean_sum"] / float(steps),
            "A_mean": dwell["A"] / float(steps), "V_mean": dwell["V"] / float(steps),
            "leaning_of_sums": calibration.leaning((dwell["A"], dwell["V"])),
            "kc_mean": dwell["kc"] / float(steps),
            "kc_frac": dwell["kc"] / float(steps) / float(kc_cells),
            "on_card": round(ox * oy / window, 4),
            "dwell_steps": int(dwell["steps"]), "blind_steps": int(dwell["blind"]),
            "pairs": int(dwell["pairs"]),
            "reference": reference,
            "reference_leaning": (float(np.mean([r["leaning"] for r in reference]))
                                  if reference else None),
            "calibration": str(getattr(self.mb, "calibration", calibration.CHOSEN)),
            "sides_sha": str(getattr(self.mb, "sides_sha", "")),
            "board_item": dict(self.meta.get(card["token"], {})),
            "disclosure": self.disclosure,
            "eligible": sorted(dwell.get("eligible", set())),
            "brain_id": self.brain_id,
            "crop": [x0, y0, x1 - x0, y1 - y0], "frame": [h, w],
            "mode": self.mode,
        }
        self.looks_dir.mkdir(parents=True, exist_ok=True)
        _atomic_write(self.looks_dir / f"{look_id}.json",
                      json.dumps(record, indent=1).encode("utf-8"))
        self._write_png(self.looks_dir / f"{look_id}.png", img[y0:y1, x0:x1])
        return look_id

    @staticmethod
    def _write_png(path, crop):
        try:
            from PIL import Image
            arr = np.rint(np.clip(np.asarray(crop, dtype=np.float32), 0.0, 1.0) * 255.0)
            Image.fromarray(arr.astype(np.uint8), mode="L").save(str(path))
            return True
        except (OSError, ValueError):
            return False

    def _read_crop(self, look_id):
        try:
            from PIL import Image
            with Image.open(str(self.looks_dir / f"{look_id}.png")) as im:
                return np.asarray(im.convert("L"), dtype=np.float32) / 255.0
        except (OSError, ValueError):
            return None

    def _prune_looks(self):
        try:
            files = sorted(self.looks_dir.glob("*.json"))
        except (OSError, ValueError):
            return
        over = len(files) - int(self.max_looks)
        if over <= 0:
            return
        keep = self.protected_looks()
        for p in files:
            if over <= 0:
                break
            if p.stem in keep:
                continue
            for q in (p, p.with_suffix(".png")):
                try:
                    q.unlink()
                except OSError:
                    pass
            over -= 1

    def _drop_ref(self, token, look_id):
        ids = self.refs.get(token)
        if not ids or not look_id:
            return
        left = [i for i in ids if i != look_id]
        if left:
            self.refs[token] = left
        else:
            self.refs.pop(token, None)

    def _forget_room(self):
        self._seen = {}
        d = self._dwell
        if d is not None:
            d.update({"steps": 0, "blind": 0, "A": 0.0, "V": 0.0, "kc": 0, "lean_sum": 0.0,
                      "pairs": 0, "drive_sum": 0.0, "reference": [], "eligible": set()})

    def state(self):
        d = self._dwell
        now = None
        if d is not None:
            m = self.meta.get(d["token"]) or {}
            now = {"token": d["token"], "symbol": m.get("symbol") or "",
                   "name": m.get("name") or "", "held": bool(d.get("held")),
                   "drive": self._drive_of(d), "dwell_steps": int(d["steps"])}
        c = self.counters
        return {"room": self.declaration.public(), "in_room": bool(self.in_room), "visits": c["visits"], "looks": c["looks"],
                "commits": c["commits"], "intents": c["intents"], "booked": c["booked"],
                "refused": c["refused"], "dislikes": c["dislikes"], "busy": c["busy"],
                "seen": len(self._seen),
                "now": now, "last_intents": self.last_intents[-10:],
                "learning": {"sugar": c["sugar"], "shock": c["shock"],
                             "last": self.last_dopamine[-10:]},
                "board_size": len(self._board["cards"]),
                "board_error": self._board_error,
                "board_updated": int(self._board["updated"])}

    def _now(self):
        return float(self.clock())
