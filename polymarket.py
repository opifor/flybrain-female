"""Public observations for the paper room. Every request is a GET."""
import json
import time
import urllib.request
from datetime import datetime
from fractions import Fraction
from urllib.parse import urlencode

GAMMA = "https://gamma-api.polymarket.com/markets"
CLOB = "https://clob.polymarket.com/midpoint"
DISCLOSURE = (
    "CHOSEN by people: a person chose current BTC and ETH 5-minute markets and "
    "BTC, ETH, SOL and XRP 15-minute markets because they resolve in minutes, "
    "so her learning signal arrives while she is still in the room; refreshed "
    "every 30 seconds. Up means YES and Down means NO "
    "on the fast shelf. A market's smell is a human mapping from its question "
    "words to DoOR odorants, scaled toward total 2.0. The fly cannot read the "
    "words. The picture is for the viewers. Category colours, price bars and "
    "time-to-close edge brightness are human encodings."
)


def get_json(url):
    request = urllib.request.Request(url, headers={"Accept": "application/json",
                                                  "User-Agent": "flybrain-paper-room"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def array(value):
    value = json.loads(value) if isinstance(value, str) else value
    if not isinstance(value, list):
        raise ValueError("expected an array")
    return value


def timestamp(value):
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("endDate has no timezone")
    return dt.timestamp()


def binary(raw, fast=False):
    if raw.get("negRisk") or raw.get("negRiskMarketID") or any(
            e.get("negRisk") for e in raw.get("events", [])):
        raise ValueError("negRisk group")
    outcomes = array(raw["outcomes"])
    if outcomes != ["Yes", "No"] and not (fast and outcomes == ["Up", "Down"]):
        raise ValueError("not a supported binary market")
    tokens = array(raw["clobTokenIds"])
    prices = [Fraction(p) for p in array(raw["outcomePrices"])]
    if len(tokens) != 2 or len(set(tokens)) != 2 or not all(
            isinstance(t, str) and t.isascii() and t.isdigit() for t in tokens):
        raise ValueError("invalid outcome tokens")
    if len(prices) != 2 or any(p < 0 or p > 1 for p in prices):
        raise ValueError("invalid outcome prices")
    return outcomes, tokens, prices


def card(raw, shelf, now):
    outcomes, tokens, prices = binary(raw, fast=shelf == "fast")
    end = timestamp(raw["endDate"])
    if raw.get("closed") is not False or raw.get("active") is not True or end <= now:
        raise ValueError("market is not open")
    if shelf == "slow" and end > now + 7 * 86400:
        raise ValueError("market closes beyond seven days")
    market_id = str(raw["id"])
    if not market_id.isascii() or not market_id.isdigit():
        raise ValueError("invalid market id")
    return {"token": market_id, "market_id": market_id, "question": raw["question"],
            "name": raw["question"], "symbol": shelf, "slug": raw["slug"],
            "token_ids": tokens, "outcomes": outcomes, "yes_price": float(prices[0]),
            "end_at": end, "volume24hr": float(raw.get("volume24hr") or 0),
            "category": str(raw.get("category") or ("crypto" if shelf == "fast" else "other")),
            "shelf": shelf, "held": False}


class Markets:
    def __init__(self, fetch=get_json, clock=time.time):
        self.fetch, self.clock = fetch, clock

    def market(self, market_id):
        # Gamma leaves closed markets out of an id query unless asked for
        # them, and a settled bet is exactly a closed market: ask twice.
        for extra in ({}, {"closed": "true"}):
            rows = self.fetch(GAMMA + "?" + urlencode({"id": market_id, **extra}))
            for raw in rows:
                if str(raw.get("id")) == str(market_id):
                    return raw
        raise ValueError("market absent from Gamma")

    def midpoint(self, token_id):
        raw = self.fetch(CLOB + "?" + urlencode({"token_id": token_id}))
        price = Fraction(raw["mid"])
        if not 0 < price < 1:
            raise ValueError("midpoint cannot price an open bet")
        return price

    def board(self):
        now = self.clock()
        cards = []
        for slot, (asset, minutes) in enumerate((
                ("btc", 5), ("eth", 5), ("btc", 15), ("eth", 15), ("sol", 15), ("xrp", 15))):
            window = int(now) - int(now) % (minutes * 60)
            slug = f"{asset}-updown-{minutes}m-{window}"
            for raw in self.fetch(GAMMA + "?" + urlencode({"slug": slug})):
                if raw.get("slug") != slug:
                    continue
                try:
                    cards.append({**card(raw, "fast", now), "slot": slot,
                                  "end_at": window + minutes * 60})
                    break
                except (KeyError, TypeError, ValueError):
                    continue
        return cards


def winner(raw):
    _, _, prices = binary(raw, fast=True)
    if raw.get("closed") is True:
        if prices == [1, 0]:
            return "YES"
        if prices == [0, 1]:
            return "NO"
    return None
