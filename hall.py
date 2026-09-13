"""The doors are supplied by people; a stop enters a room."""
from room import Room as RoomWalk, _atomic_write
from roomkit import Declaration
import json
import random

DISCLOSURE = "The doors are the rooms people built. Which one she walks into is her stop."
DECLARATION = Declaration(
    name="the hall", path="/hall",
    cards={"source": "rooms whose doors are ready to open", "refresh_seconds": 2},
    commit_means="she enters that room",
    reward_source="The hall brings no sugar or shock; each room says where its own sugar and shock come from.",
    chosen=[DISCLOSURE, "twelve doors, shuffled every visit, six per room when two rooms are healthy",
            "The rooms are paper for now; the plan is to take them on-chain."],
    measured=["She stays on a door for two readings; a stop from her brain opens it after she has looked at another door.",
              "The page counts how often it pushes her out of an empty margin."],
    how=("twelve doors, shuffled every visit, six per room when two rooms are healthy.",
         "she needs readings from another door before a stop can open this one.",
         "entering a room brings her to that room's cards.",
         "every room leads back here, by her door or by the clock."))


class Hall(RoomWalk):
    declaration = DECLARATION
    disclosure = DISCLOSURE

    def __init__(self, *args, registry, **kwargs):
        self.registry = registry
        self.destination = None
        self._blind = 0
        self.entered = []
        super().__init__(*args, **kwargs)
        if self.public.exists():
            self.entered = json.loads(self.public.read_text(encoding="utf-8")).get("events", [])

    def board_source(self):
        def fetch():
            rooms = self.registry.healthy(self.http)
            cards = []
            for position, door in enumerate(rooms):
                count = 12 // len(rooms) + (position < 12 % len(rooms))
                previews = []
                try:
                    saved = json.loads((self.dir.parent / door["path"].strip("/") / "room.json").read_text(encoding="utf-8"))
                    for item in saved["cards"]:
                        if not isinstance(item, dict):
                            continue
                        if item.get("end_at", float("inf")) <= self._now():
                            continue
                        preview = (" / ".join(str(item[k]) for k in ("title", "artist") if item.get(k))
                                   if door["path"] == "/musicroom" else
                                   item.get("name", "") if door["path"] == "/paintroom" else item.get("question", ""))
                        if isinstance(preview, str) and preview and preview not in previews:
                            previews.append(preview)
                except (OSError, ValueError, KeyError, TypeError):
                    pass
                for index in range(count):
                    cards.append({**door, "token": f'{door["path"]}#{index}',
                                  "preview": previews[index % len(previews)] if previews else ""})
            return cards
        return fetch

    def remember(self, token, meta):
        self.meta[token] = dict(meta)

    def smell_of(self, token):
        preview = self.meta.get(token, {}).get("preview", "")
        return self.nose.smell(preview) if preview else None

    def board(self):
        board = super().board()
        board["order_seed"] = max(0, self.counters["visits"] - 1)
        cards = board["cards"]
        random.Random(board["order_seed"]).shuffle(cards)
        if self._now() - board["updated"] > 4:
            board["cards"] = []
        return board

    def _commit(self, img, cx, cy, seed, card, dwell, drive, smell):
        if self.destination is not None:
            return
        healthy = {d["path"] for d in self.registry.healthy(self.http)}
        doors = [d for d in self.board()["cards"] if d["path"] in healthy]
        door = next((d for d in doors if d["token"] == card["token"]), None)
        if door is None:
            return
        self.counters["commits"] += 1
        self._write_look(self._now(), img, cx, cy, seed, card, dwell, drive, smell)
        if drive is None:
            self._note_intent(self._now(), card["token"], "none", None, "no reference",
                              "the fly has looked at no other card in this visit")
            # Two blind stops lead her toward a card she has not seen.
            self._blind += 1
            if self._blind >= 2:
                unseen = [d["token"] for d in doors
                          if d["token"] != card["token"] and d["token"] not in self._seen]
                if unseen:
                    self.walk_to = unseen[0]
                self._blind = 0
            return
        self._blind = 0
        self.destination = door["path"]

    def record_entry(self, path):
        declaration, _ = self.registry.rooms[path]
        self.entered.append({"kind": "entered", "path": path, "at": self._now(),
                             "text": "entered " + declaration.name})
        self.entered = self.entered[-100:]
        _atomic_write(self.public, json.dumps(self.state(), indent=1).encode("utf-8"))

    async def enter(self, page):
        self.destination = None
        self._blind = 0
        await super().enter(page)

    def poll_events(self):
        self.refresh_board()

    def state(self):
        board = self.board()
        return {**super().state(), "events": self.entered,
                "doors": [{key: card[key] for key in ("name", "path", "preview")} for card in board["cards"]],
                "order_seed": board["order_seed"]}
