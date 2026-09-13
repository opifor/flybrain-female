"""The doors are supplied by people; a stop enters a room."""
from room import Room as RoomWalk, _atomic_write
from roomkit import Declaration
import json

DISCLOSURE = "The doors are the rooms people built. Which one she walks into is her stop."
DECLARATION = Declaration(
    name="the hall", path="/hall",
    cards={"source": "rooms whose doors are ready to open", "refresh_seconds": 2},
    commit_means="she enters that room",
    reward_source="The hall brings no sugar or shock; each room says where its own sugar and shock come from.",
    chosen=[DISCLOSURE, "door order rotates every visit so no door owns the left"],
    measured=["She stays on a door for two readings; a stop from her brain opens it after she has looked at another door.",
              "The page counts how often it pushes her out of an empty margin."],
    how=("door order rotates every visit so no door owns the left.",
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
        return lambda: self.registry.healthy(self.http)

    def board(self):
        board = super().board()
        board["order_seed"] = max(0, self.counters["visits"] - 1)
        cards = board["cards"]
        if cards:
            offset = board["order_seed"] % len(cards)
            board["cards"] = cards[offset:] + cards[:offset]
        if self._now() - board["updated"] > 4:
            board["cards"] = []
        return board

    def _commit(self, img, cx, cy, seed, card, dwell, drive, smell):
        if self.destination is not None:
            return
        doors = self.registry.healthy(self.http)
        door = next((d for d in doors if d["token"] == card["token"]), None)
        if door is None:
            return
        self.counters["commits"] += 1
        self._write_look(self._now(), img, cx, cy, seed, card, dwell, drive, smell)
        if drive is None:
            self._note_intent(self._now(), card["token"], "none", None, "no reference",
                              "the fly has looked at no other card in this visit")
            # Two blind stops on the same door: the hall walks her to a door she
            # has not looked at, so the choice is made between doors, not by habit.
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
        await super().enter(page)

    def poll_events(self):
        self.refresh_board()

    def state(self):
        board = self.board()
        return {**super().state(), "events": self.entered,
                "doors": [{"name": card["name"], "path": card["path"]} for card in board["cards"]],
                "order_seed": board["order_seed"]}
