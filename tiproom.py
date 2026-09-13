"""Fixture wallets and fixture thanks, with no chain connection."""
import json
from pathlib import Path

from room import Room as RoomWalk
from roomkit import Declaration

FIXTURES = Path(__file__).parent / "tests" / "fixtures" / "tiproom"
DECLARATION = Declaration(
    name="the tipping room", path="/tiproom",
    cards={"source": "wallets shared by people who post about her; eight practice wallets in rehearsal", "refresh_seconds": 30},
    commit_means="She has a wallet of her own, and the creator fee from $HER accrues in it. The room being prepared works like this: post about her on X with $HER, or say something in the Kick chat, and share a wallet; your card may drop into this room, and if she happens upon it, she may tip it. Within limits, on her terms, at random. The details stay open until the room opens; until then nothing moves.",
    reward_source="What people say about her is the sugar and the shock of this room, through a line we have not wired yet. In rehearsal, a recorded practice thank-you brings sugar to the cells from her look; silence brings nothing. Every tip here is paper for now; the plan is to take the rooms on-chain.",
    chosen=["People will decide which posts and comments put a card in the room, and the limits that keep her wallet safe; none of that is chosen yet.",
            "In rehearsal, people supply eight practice wallets and no smells.",
            "People set a six-minute room clock and put a door in every room."],
    measured=["Her brain supplies the stop and the drive compared with her other looks; the practice thanks is no human response.",
              "The page counts how often it pushes her out of an empty margin."],
    how=("in rehearsal, her eye settles on a wallet card for at least two rounds; this room adds no smell.",
         "her mushroom body supplies a drive, compared with the other cards she has seen in this visit.",
         "when she stops, her drive sets a paper tip to that wallet; either sign tips, zero does not.",
         "a recorded practice thank-you brings sugar to the cells from that look; silence brings nothing.",
         "when the room opens, the cards will be wallets people shared by posting about her; their words, her sugar and shock.",
         "she may leave by the door on any edge of the room; the house closes a room after six minutes either way."))


def wallets():
    rows = json.loads((FIXTURES / "wallets.json").read_text(encoding="utf-8"))
    return [{**row, "token": row["address"], "name": row["address"],
             "area_scale": 0.35 + 0.65 * min(365, max(0, row["holding_days"])) / 365}
            for row in rows]


class Room(RoomWalk):
    declaration = DECLARATION
    disclosure = " ".join(DECLARATION.chosen + DECLARATION.measured)
    event_token_key = "address"

    def board_source(self):
        return wallets

    def intent_body(self, token, drive, at, look_id):
        return {"address": token, "drive": float(drive), "seen_at": at, "look_id": look_id}

    def can_commit(self, token, at):
        if token == "/hall":
            return True
        booked = {e["look_id"] for e in self.read_book().get("tips", [])}
        return all(look in booked for look in self.refs.get(token, []))
