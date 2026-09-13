"""A small, durable account of what she has been doing."""
import json
import re
import time
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from statistics import median
from urllib.parse import urlsplit

WHO = ["her. a female fruit fly brain, 139,255 neurons. FlyWire FAFB v783.",
       "she never speaks. the numbers do.", "paper money only. no real bets.",
       "the first fly streamer on kick."]
COUNTS = "bets sold won lost pnl pages clicks scrolls sugar shock".split()
FEED_LIMIT = 48  # Longer lines disappear beyond the stream column.


def stake_value(pos):
    stake = pos.get("stake")
    return float(stake) if isinstance(stake, (int, float)) else int(pos.get("stake_cents", stake or 0)) / 100


def market_line(prefix, market, suffix):
    return prefix + market[:max(0, FEED_LIMIT - len(prefix + suffix))] + suffix


def stamp(now, fmt="%Y-%m-%dT%H:%M:%SZ"):
    return datetime.fromtimestamp(now, timezone.utc).strftime(fmt)


def domain(url, path=False):
    try:
        parts = urlsplit(url)
        host = (parts.hostname or "").lower().removeprefix("www.")
        tail = parts.path.rstrip("/")
        if path and len(host + tail) <= 40 and re.fullmatch(r"[/\w.~-]*", tail):
            host += tail
        return host
    except ValueError:
        return ""


COINS = {"bitcoin": "btc", "ethereum": "eth", "solana": "sol", "xrp": "xrp",
         "dogecoin": "doge", "litecoin": "ltc", "cardano": "ada"}
WINDOW = re.compile(r"^(\w+) up or down - .*?(\d{1,2}):(\d{2})(am|pm)-(\d{1,2}):(\d{2})(am|pm)")
ABOVE = re.compile(r"price of (\w+) be (above|below) \$([\d,]+)")


def label(record, cards):
    """A market in a few characters: 'btc 15m', 'eth above $4,200', else the question's head."""
    card = next((c for c in cards if c.get("market_id") == record.get("market_id")), {})
    data = {**card, **record}
    q = " ".join(str(data.get("question") or data.get("name") or "the board").lower().split())
    m = WINDOW.match(q)
    if m:
        coin = COINS.get(m.group(1), m.group(1)[:4])
        start = (int(m.group(2)) % 12 + (12 if m.group(4) == "pm" else 0)) * 60 + int(m.group(3))
        end = (int(m.group(5)) % 12 + (12 if m.group(7) == "pm" else 0)) * 60 + int(m.group(6))
        return f"{coin} {(end - start) % 1440}m"
    m = ABOVE.search(q)
    if m:
        return f"{COINS.get(m.group(1), m.group(1)[:4])} {m.group(2)} ${m.group(3)}"
    return q[:24].rstrip(" ,-?!")


class Life:
    def __init__(self, dir="build/life", music_catalogue="data/music/catalog.json"):
        self.dir = Path(dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.path = self.dir / "feed.jsonl"
        self.rows, self.seen, self.stats = {}, set(), {}
        self.url, self.room, self.since = "", "the web", None
        self.samples, self.quiet = [], None
        self.cooldown, self.high, self.wins = {}, None, 0
        self.day = {}
        self.music_catalogue = Path(music_catalogue)
        self.music_tracks = {}
        for path in (self.dir / "feed.1.jsonl", self.path):
            if path.exists():
                with path.open(encoding="utf-8") as stream:
                    for line in stream:
                        try:
                            row = json.loads(line)
                            self.rows[row["id"]] = row
                        except (ValueError, KeyError, TypeError):
                            continue
        try:
            self.day = json.loads((self.dir / "day.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
        self.serial = max((r.get("serial", 0) for r in self.rows.values()), default=0)
        self.since = self.day.get("since")
        saved = self.day.get("memory", {})
        self.seen = {tuple(key) for key in saved.get("seen", [])}
        self.stats, self.url = saved.get("stats", {}), saved.get("url", "")
        self.room, self.high = saved.get("room", "the web"), saved.get("high")
        self.wins, self.cooldown = saved.get("wins", 0), saved.get("cooldown", {})
        self.cards = saved.get("cards", [])
        self.music_reactions = saved.get("music_reactions", {})
        self.first = not self.day and not self.rows

    def _fresh(self, family, value):
        key = (family, json.dumps(value, sort_keys=True))
        self.current_seen.add(key)
        if key in self.seen:
            return False
        self.seen.add(key)
        return True

    def _line(self, kind, text, now, counts=None, key=None, **extra):
        self.dir.mkdir(parents=True, exist_ok=True)
        self.serial += 1
        key = key or f"{now}:{self.serial}"
        row = dict(id=key, serial=self.serial, ts=now, at=stamp(now, "%H:%M:%S"),
                   kind=kind, text=text.replace("!", "")[:FEED_LIMIT], counts=counts or {}, **extra)
        self.rows[key] = row
        if self.path.exists() and self.path.stat().st_size > 5 * 1024 * 1024:
            self.path.replace(self.dir / "feed.1.jsonl")
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row

    def observe(self, state: dict, now: float | None = None) -> dict:
        now = time.time() if now is None else now
        self.current_seen = set()
        self.since = self.since or stamp(now)
        self.rows = {k: r for k, r in self.rows.items() if now - 3600 < r["ts"] <= now}
        betting, book = state.get("betting") or {}, state.get("betroom") or {}
        cards, url = betting.get("cards", []), state.get("url", "")
        self.cards = list({c.get("market_id"): c for c in self.cards + cards}.values())[-200:]
        host = domain(url)
        music = state.get("rooms", {}).get("/musicroom") or {}
        music_book = music.get("book") or {}
        playing = music_book.get("now_playing")
        if music_book and not self.music_tracks:
            try:
                self.music_tracks = {str(r["id"]): r for r in
                                     json.loads(self.music_catalogue.read_text(encoding="utf-8"))}
            except (OSError, ValueError):
                pass
        plays = list(music_book.get("plays", []))
        if playing and not any((p.get("track_id"), p.get("started_at")) ==
                               (playing.get("track_id"), playing.get("started_at")) for p in plays):
            plays.append(playing)
        for play in plays:
            title = play.get("title", "the track")
            artist = self.music_tracks.get(str(play.get("track_id")), {}).get("artist", "unknown artist")
            start = play["started_at"]
            identity = [str(play.get("track_id")), start]
            key = f"music:{play.get('track_id')}:{start}"
            if self._fresh("music.play", identity) and key not in self.rows:
                self._line("music.play", market_line("she put on ", title, f" by {artist}"), start, key=key,
                           hidden=self.first and start < now - 600)
            end = play.get("ended_at")
            if end is not None and end <= now and self._fresh("music.end", identity) and key + ":end" not in self.rows:
                self._line("music.end", market_line("", title, f" ended · she stayed {max(0, round(end - start))} s"), end,
                           key=key + ":end",
                           hidden=self.first and end < now - 600)
        reactions = music_book.get("reactions", {}).get("tracks", {})
        for track_id, counts in reactions.items():
            title = self.music_tracks.get(str(track_id), {}).get("title") or next(
                (p["title"] for p in reversed(plays) if str(p.get("track_id")) == str(track_id)), "the track")
            previous = self.music_reactions.get(str(track_id), {})
            for kind in ("sugar", "shock"):
                total = counts.get(kind, 0)
                added = max(0, total - previous.get(kind, 0))
                if added and not self.first:
                    self._line("music.react", f"a listener sent {kind} for {title}", now, {kind: added})
            self.music_reactions[str(track_id)] = dict(counts)
        entries = state.get("rooms", {}).get("/hall", {}).get("events", [])
        entered = [e for e in entries if e.get("kind") == "entered"]
        room = "paper room" if betting.get("in_room") else "the web"
        if music.get("in_room"):
            room = "music room"
        parts = urlsplit(url) if url else None
        if room == "the web" and parts and parts.hostname in ("127.0.0.1", "localhost"):
            # Her own house answers on loopback; the path names the room she stands in.
            room = {"/hall": "hall", "/betroom": "paper room", "/tiproom": "tip room",
                    "/musicroom": "music room"}.get(parts.path.rstrip("/"), "the web")
        if room == "the web" and entered:
            latest = max(entered, key=lambda e: e.get("at", 0))
            # A retained doorway event must not follow her onto an unrelated page.
            path = urlsplit(url).path if url else latest.get("path")
            if path == latest.get("path"):
                room = {"/hall": "hall", "/tiproom": "tip room", "/musicroom": "music room"}.get(path, "the web")
        if room != self.room:
            self._line("room.enter", f"she walked into the {room.removeprefix('the ')}", now)
        self.room = room
        visits = state.get("visited", [])
        opened = []
        for visit in visits:
            if self._fresh("visit", visit):
                opened.append(visit.get("url", ""))
        if url and url != self.url and url not in opened:
            opened.append(url)
        for target in opened:
            if domain(target) and room == "the web":
                self._line("page.open", f"she opened {domain(target, True)}", now, {"pages": 1})
        self.url = url
        events = [e for e in state.get("events", []) if self._fresh("event", e)]
        stats = state.get("stats", {})
        for counter, kind in (("clicks", "page.click"), ("scrolled", "page.scroll")):
            n = max(0, stats.get(counter, 0) - self.stats.get(counter, 0))
            if not n or not host or room != "the web":
                continue
            if counter == "clicks":
                self._line(kind, f"she clicked on {host}", now, {"clicks": n})
                continue
            directions = [e.get("m", "") for e in events
                          if e.get("m") in ("scrolled down", "scrolled up")]
            if not directions:
                continue
            direction = directions[-1].split()[-1]
            old = next((r for r in reversed(list(self.rows.values()))
                        if r["kind"] == kind and r.get("host") == host
                        and r.get("direction") == direction and now - r.get("start", r["ts"]) <= 20), None)
            total = n + (old["counts"]["scrolls"] if old else 0)
            self._line(kind, f"she scrolled {direction} {total} times on {host}", now,
                       {"scrolls": total}, key=old["id"] if old else None,
                       host=host, direction=direction, start=old["start"] if old else now)
        self.stats = dict(stats)
        for event in events:
            if event.get("m", "").startswith("did not click") and host:
                self._line("page.noclick", f"she skipped a link on {host}", now)
        fills = [e for e in betting.get("events", []) if e.get("kind") == "fill"
                 and e.get("action") != "sell" and "price" in e]
        for pos in book.get("open_bets", []) + fills:
            key = f"buy:{pos.get('id')}:{pos.get('seq')}"
            if self._fresh("buy", key) and key not in self.rows:
                market, side = label(pos, self.cards), str(pos.get("side", "yes")).lower()
                price = float(Fraction(str(pos.get("price", 0))))
                stake = stake_value(pos)
                at = pos.get("at", now)
                suffix = f" at {price:.2f} · {stake:.2f} paper"
                prefix = f"she bet {side} on "
                self._line("bet.placed", market_line(prefix, market, suffix),
                           at, {"bets": 1}, key=key, hidden=self.first and at < now - 600)
        streak_at = None
        for pos in sorted(book.get("settled_bets", []), key=lambda p: (p.get("at", now), p.get("seq", 0))):
            key = f"settled:{pos.get('id')}:{pos.get('seq')}"
            if not self._fresh("settled", key) or key in self.rows:
                continue
            market = label(pos, self.cards)
            at = pos.get("at", now)
            hidden = self.first and at < now - 600
            pnl = float(pos.get("pnl", (int(pos.get("payout_cents", 0)) - int(pos.get("stake_cents", 0))) / 100))
            sold, won = pos.get("kind") == "sold", pos.get("won", False)
            kind = "sold" if sold else "won" if won else "lost"
            text = (market_line("she left ", market, f" early · {pnl:+.2f} paper") if sold else
                    market_line("", market, f" resolved · {'won' if won else 'lost'} {pnl:+.2f} · {'sugar' if won else 'shock'}"))
            counts = {kind: 1, "pnl": pnl}
            if not sold:
                counts["sugar" if won else "shock"] = 1
                for row in list(self.rows.values()):
                    if row["kind"] == ("sugar" if won else "shock") and abs(at-row["ts"]) <= 5:
                        self._line(row["kind"], row["text"], row["ts"], key=row["id"], hidden=True)
            self._line("bet." + kind, text, at, counts, key=key, hidden=hidden)
            self.wins = self.wins + 1 if won else 0
            streak_at = None if hidden else at
        if self.wins >= 3 and streak_at is not None:
            self._line("streak", f"{self.wins} wins in a row", streak_at)
        refused = self.cooldown.get("refused_pending", 0)
        for event in betting.get("events", []):
            if event.get("kind") == "refused" and self._fresh("refused", event.get("seq")):
                refused += 1
        if refused and now - self.cooldown.get("refused", -float("inf")) >= 300:
            self._line("bet.refused", f"the bookie said no {refused}× this minute", now, n=refused)
            self.cooldown["refused"] = now
            refused = 0
        self.cooldown["refused_pending"] = refused
        for lesson in betting.get("learning", {}).get("last", []):
            if lesson.get("status") != "delivered" or not lesson.get("sign"):
                continue
            if not self._fresh("lesson", lesson.get("seq")):
                continue
            kind = "sugar" if lesson["sign"] > 0 else "shock"
            implied = "bet.won" if kind == "sugar" else "bet.lost"
            at = float(lesson.get("at", now))
            if not any(r["kind"] == implied and abs(at-r["ts"]) <= 5 for r in self.rows.values()):
                self._line(kind, f"{kind} · {len(lesson.get('eligible', []))} kenyon cells", at, {kind: 1},
                           hidden=self.first and at < now - 600)
        balance = book.get("balance")
        delta = None
        if balance is not None:
            equity = balance + sum(stake_value(pos) for pos in book.get("open_bets", []))
            date = stamp(now, "%Y-%m-%d")
            if self.day.get("date") != date:
                self.day.update(date=date, balance=equity)
            delta = round(equity - self.day["balance"], 2)
            if self.high is not None and balance > self.high:
                self._line("balance.high", f"new paper high · {balance:.2f} usdc", now)
            self.high = max(balance, self.high if self.high is not None else balance)
        spikes = int(state.get("neural", {}).get("spikes_per_sec", 0) or 0)
        self.samples = [(t, v) for t, v in self.samples if t > now - 600]
        if self.samples and spikes > 2 * median(v for _, v in self.samples):
            if now - self.cooldown.get("storm", -float("inf")) >= 300:
                self._line("brain.storm", f"spike storm · {spikes} spikes/s", now)
                self.cooldown["storm"] = now
        self.samples.append((now, spikes))
        self.quiet = (now if self.quiet is None else self.quiet) if spikes < 1 else None
        if self.quiet is not None and now - self.quiet >= 60 and now - self.cooldown.get("quiet", -float("inf")) >= 600:
            self._line("brain.quiet", f"quiet brain · {int((now-self.quiet)//60)} min under 1 spikes/s", now)
            self.cooldown["quiet"] = now
        self.first = False
        self.rows = {k: r for k, r in self.rows.items() if now - 3600 < r["ts"] <= now}
        hour = {k: round(sum(r["counts"].get(k, 0) for r in self.rows.values()), 2) for k in COUNTS}
        recent = {k: sum(r["counts"].get(k, 0) for r in self.rows.values() if r["ts"] > now-600)
                  for k in ("sugar", "shock")}
        doing = {"hall": "walking the hall", "tip room": "visiting the tip room",
                 "music room": f"listening to {playing['title']}" if playing else "looking at the music shelf",
                 "the web": f"reading {host}"}.get(room, "looking at the board")
        if room == "paper room":
            opened = book.get("open_bets", [])
            if opened:
                doing = f"holding {str(opened[0].get('side', 'yes')).lower()} on {label(opened[0], cards)}"
            else:
                x, y = state.get("cx", -1)-56, state.get("cy", -1)-48
                slot = int(y // 368) * 3 + int(x // 400)
                card = next((c for c in cards if c.get("slot") == slot), None)
                if card and 0 <= x < 1168 and y >= 0 and x % 400 < 368 and y % 368 < 336:
                    doing = "looking at " + label(card, cards)
        hz = state.get("hz", {})
        turn = hz.get("steer_L", 0) - hz.get("steer_R", 0)
        feed = sorted((r for r in self.rows.values() if not r.get("hidden")),
                      key=lambda r: (r["ts"], r["serial"]), reverse=True)[:40]
        self.seen = self.current_seen
        self.day.update(since=self.since, memory=dict(seen=sorted(self.seen), stats=self.stats,
                        url=self.url, room=self.room, high=self.high, wins=self.wins,
                        cooldown=self.cooldown, cards=self.cards, music_reactions=self.music_reactions))
        self.dir.mkdir(parents=True, exist_ok=True)
        pending = self.dir / "day.tmp"
        pending.write_text(json.dumps(self.day), encoding="utf-8")
        pending.replace(self.dir / "day.json")
        return dict(since=self.since, who=list(WHO), now=dict(room=room, doing=doing[:48], spikes=spikes,
                    turn="left" if turn > 20 else "right" if turn < -20 else "straight",
                    sugar_10m=recent["sugar"], shock_10m=recent["shock"], balance=balance, today_delta=delta),
                    hour=hour, feed=[dict(at=r["at"], kind=r["kind"], text=r["text"][:FEED_LIMIT]) for r in feed])
