"""A small shelf of music, with the same clock for her ear and the page."""
import json
from pathlib import Path

from room import Room as RoomWalk
from roomkit import Declaration

CATALOGUE = "data/music/catalog.json"
DECLARATION = Declaration(
    name="music room", path="/musicroom",
    cards={"source": "a small catalogue of Creative Commons music from Wikimedia Commons, each card names its license",
           "refresh_seconds": 60},
    commit_means="she plays the track on the card she settled on",
    reward_source="listeners: sugar and shock reactions written to the room's reactions file (paper; the stream will carry them later)",
    chosen=["People chose the catalogue search terms, the 30-second minimum and the six-card board."],
    measured=["Her dwell, her mushroom-body drive and her Johnston-organ hearing rates while a track plays are measured.",
              "nudges: how often the page had to push her out of an empty margin"],
    how=("her eye settles on a music card for at least two rounds before she can choose it.",
         "the title and artist become a smell; her mushroom body compares its drive with the other cards she has seen.",
         "when she stops with a nonzero drive, the paper DJ starts that track; either sign can play it.",
         "she stays with a track for at least thirty seconds and cannot restart it while it is playing.",
         "the sound file feeds her Johnston organs, the hearing cells in her antennae, while the page plays it.",
         "a listener's sugar or shock teaches the cells recorded when she chose that play."))


def catalogue(path=CATALOGUE):
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("the music catalogue must be a list")
    # The Commons catalogue writes page ids as numbers; a track id travels as text.
    for row in rows:
        row["id"] = str(row["id"])
    return rows


class Room(RoomWalk):
    declaration = DECLARATION
    disclosure = " ".join(DECLARATION.chosen + DECLARATION.measured)
    event_token_key = "track_id"

    def __init__(self, *args, ear=None, catalogue_path=CATALOGUE, **kwargs):
        self.ear, self.catalogue_path = ear, Path(catalogue_path)
        self.now_playing = None
        self._tables = {}
        super().__init__(*args, **kwargs)

    def board_source(self):
        def fetch():
            rows = catalogue(self.catalogue_path)
            if not rows:
                return []
            start = int(self._now() // 3600) % len(rows)
            return [{**rows[(start + slot) % len(rows)],
                     "token": rows[(start + slot) % len(rows)]["id"],
                     "name": rows[(start + slot) % len(rows)]["title"],
                     "slot": slot, "room": DECLARATION.public()} for slot in range(6)]
        return fetch

    def refresh_board(self, force=False):
        self.now_playing = self.read_book().get("now_playing")
        return super().refresh_board(force)

    def smell_of(self, token):
        if token not in self._smell:
            card = self.meta.get(token, {})
            self._smell[token] = self.nose.smell(f"{card.get('title', '')} {card.get('artist', '')}")
        return self._smell[token]

    def can_commit(self, token, at):
        self.now_playing = self.read_book().get("now_playing")
        playing = self.now_playing
        return not playing or (at - playing["started_at"] >= 30 and playing["track_id"] != token)

    def intent_body(self, token, drive, at, look_id):
        return {"track_id": token, "drive": float(drive), "seen_at": at, "look_id": look_id}

    def extra_drive(self, smell):
        drive = super().extra_drive(smell)
        playing = self.now_playing
        if self.ear is None or not playing:
            return drive
        t = self._now() - playing["started_at"]
        if not 0 <= t < playing["duration"]:
            return drive
        token = playing["track_id"]
        if token not in self._tables:
            from ear import analyse
            track = next(row for row in catalogue(self.catalogue_path) if row["id"] == token)
            self._tables[token] = analyse(track["file"])
        merged = dict(drive or {})
        t = self._now() - playing["started_at"]
        if not 0 <= t < playing["duration"]:
            return drive
        for key, rate in self.ear.drive(self._tables[token], t).items():
            if key in merged:
                raise ValueError("extra_drive overlaps the nose's own input")
            merged[key] = rate
        return merged
