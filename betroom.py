"""The betting room supplies markets, bet meaning and market disclosure."""
from room import Room as RoomWalk, LoopbackHttp, answered_unbooked
from room import DWELL_MIN, BOARD_MAX_AGE_S, CHAIN_TIMEOUT_S, FOV_W, FOV_H, RECTS_JS
from roomkit import Declaration
from polymarket import Markets, DISCLOSURE

DECLARATION = Declaration(
    name="the betting room", path="/betroom",
    cards={"source": "Polymarket current binary markets", "refresh_seconds": 30},
    commit_means="a bet",
    reward_source="Resolved wins deliver sugar and losses shock; a sale teaches the sign of its profit. Every bet here is paper for now; the plan is to take the rooms on-chain.",
    chosen=[DISCLOSURE, "a six-minute room clock and a door in every room"],
    how=("her eye settles on a card; a decision only starts once she has stayed on it for two rounds.",
         "the card's question is turned into a smell, word by word, and fed to her olfactory neurons.",
         "her mushroom body remembers whether that smell brought sugar or shock before.",
         "while she stays, the drive it produces is summed; positive means YES, negative means NO, zero means she walks away.",
         "a held market records a look without another same-side bet; the opposite side still sells the position.",
         "the bookie takes the bet; a resolved win brings sugar and a loss brings shock, and she learns.",
         "she may leave by the door on any edge of the room; the house closes a room after six minutes either way."),
    measured=["Stops and relative drive come from the female brain; this does not establish predictive skill.",
              "nudges: how often the page had to push her out of an empty margin"])


class Room(RoomWalk):
    declaration = DECLARATION
    disclosure = DISCLOSURE
    event_token_key = "market_id"

    def reward_sign(self, ev):
        return ev["sign"] if ev["kind"] == "dopamine" else (1 if ev["side"] == ev["outcome"] else -1)

    def _apply_event(self, ev):
        if ev["kind"] == "settled":
            self._teach(ev)
            self._drop_ref(ev["market_id"], ev["look_id"])
        else:
            super()._apply_event(ev)
            if ev["kind"] == "fill" and ev.get("action") == "sell":
                self._drop_ref(ev["market_id"], ev["look_id"])

    def board_source(self):
        return Markets().board

    def smell_of(self, token):
        if token not in self._smell:
            self._smell[token] = self.nose.smell(self.meta.get(token, {}).get("question", ""))
        return self._smell[token]

    def can_commit(self, token, at):
        if token == "/hall":
            return True
        book = self.read_book()
        # Keep an unanswered intent closed while publication or event delivery catches up.
        pos = next((p for p in book.get("open_bets", []) if p["market_id"] == token), None)
        if self.refs.get(token) and (pos is None or any(
                look != pos.get("look_id") for look in self.refs[token])):
            return False
        if self.meta[token].get("end_at", float("inf")) <= at:
            return False
        return True

    def intent_body(self, token, drive, at, look_id):
        m = self.meta[token]
        side = "YES" if drive > 0 else "NO"
        body = {"market_id": token, "token_id": m["token_ids"][0 if drive > 0 else 1],
                "side": side, "drive": float(drive), "seen_at": at, "look_id": look_id}
        return body

    def allows_intent(self, token, drive):
        side = "YES" if drive > 0 else "NO"
        return token == "/hall" or not any(
            p["market_id"] == token and p["side"] == side
            for p in self.read_book().get("open_bets", []))
