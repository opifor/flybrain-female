"""Twelve colours and brushes leave a lasting record of her stops."""
import random

from room import Room as RoomWalk
from roomkit import Declaration

COLOURS = {"rose": "#ff79b0", "white": "#ffffff", "amber": "#ffbf00",
           "ice blue": "#99ddff", "moss": "#779955", "crimson": "#dc143c",
           "violet": "#9955dd", "charcoal": "#36454f"}
BRUSHES = ("dot", "stroke", "ring", "rest")
DECLARATION = Declaration(
    name="the paint room", path="/paintroom",
    cards={"source": "eight colours and four brushes", "refresh_seconds": 60},
    commit_means="she paints one mark on the canvas with the card she settled on",
    reward_source="Painting brings no sugar or shock of its own. Listener reactions to a mark or to a canvas will teach her through the stream chat later; the room is paper for now.",
    chosen=["People choose eight colours, four brushes, a twelve-card board and a two-hour canvas.",
            "Mark size grows from 6 to 40 pixels with dwell; rose and dot are the first colour and brush."],
    measured=["marks", "colour distribution", "canvas coverage percent", "rests", "time in room", "nudges"],
    how=("She takes two readings before choosing a card.",
         "The card's name becomes a smell.",
         "One mark lands where she stands, using the last chosen colour and brush.",
         "The canvas keeps every mark for two hours, then goes to the gallery.",
         "Nothing is ever erased; rest paints nothing.",
         "She can take the door on any edge, and the room clock closes her visit after six minutes."))


class Room(RoomWalk):
    declaration = DECLARATION
    disclosure = " ".join(DECLARATION.chosen + DECLARATION.measured)

    def board_source(self):
        self.refresh_count = -1
        def fetch():
            self.refresh_count += 1
            names = list(COLOURS) + list(BRUSHES)
            random.Random(self.refresh_count).shuffle(names)
            return [dict(token=name, name=name, colour=COLOURS.get(name), slot=i,
                         room=DECLARATION.public()) for i, name in enumerate(names)]
        return fetch

    def board(self):
        return {**super().board(), "order_seed": getattr(self, "refresh_count", 0)}

    def smell_of(self, token):
        if token not in self._smell:
            self._smell[token] = self.nose.smell(token)
        return self._smell[token]

    def can_commit(self, token, at):
        return True

    def _commit(self, img, cx, cy, seed, card, dwell, drive, smell):
        self.mark_position = (float(cx), float(cy), min(40, 6 + 2 * max(0, dwell["steps"] - 2)))
        return super()._commit(img, cx, cy, seed, card, dwell, drive, smell)

    def intent_body(self, token, drive, at, look_id):
        x, y, size = self.mark_position
        return dict(card_id=token, drive=float(drive), seen_at=at, look_id=look_id, x=x, y=y, size=size)

    def _apply_event(self, ev):
        if ev["kind"] == "fill":
            super()._apply_event(ev)
            self._drop_ref(ev.get("card_id"), ev.get("look_id"))

    def leave(self):
        if self.in_room and self.entered_at is not None:
            self.counters["time_in_room"] = self.counters.get("time_in_room", 0) + self._now() - self.entered_at
        super().leave()

    def state(self):
        seconds = self.counters.get("time_in_room", 0)
        if self.in_room and self.entered_at is not None:
            seconds += self._now() - self.entered_at
        return {**super().state(), "time_in_room": seconds}
