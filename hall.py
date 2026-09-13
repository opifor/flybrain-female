"""The doors are supplied by people; a stop enters a room."""
from room import Room as RoomWalk, _atomic_write
from roomkit import Declaration
import json

DISCLOSURE = "The doors are the rooms people built. Which one she walks into is her stop."
DECLARATION = Declaration(
    name="the hall", path="/hall",
    cards={"source": "registered rooms with healthy loopback executors", "refresh_seconds": 2},
    commit_means="entering that room",
    reward_source="The hall delivers no sugar or shock; the entered room declares its own reward source.",
    chosen=[DISCLOSURE], measured=["Two readings and a descending-neuron stop open a door."])


class Hall(RoomWalk):
    declaration = DECLARATION
    disclosure = DISCLOSURE

    def __init__(self, *args, registry, **kwargs):
        self.registry = registry
        self.destination = None
        self.entered = []
        super().__init__(*args, **kwargs)
        if self.public.exists():
            self.entered = json.loads(self.public.read_text(encoding="utf-8")).get("events", [])

    def board_source(self):
        return lambda: self.registry.healthy(self.http)

    def board(self):
        board = super().board()
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
            return
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
        return {**super().state(), "events": self.entered}
