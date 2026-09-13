"""Fixture wallets and fixture thanks, with no chain connection."""
import json
from pathlib import Path

from room import Room as RoomWalk
from roomkit import Declaration

FIXTURES = Path(__file__).parent / "tests" / "fixtures" / "tiproom"
DECLARATION = Declaration(
    name="the tipping room", path="/tiproom",
    cards={"source": "eight fixture wallets with holding days", "refresh_seconds": 30},
    commit_means="She has a wallet of her own, where the creator fee from $HER accrues. A room is being prepared where she will be able to tip or airdrop holders at random, through a sugar-and-shock method we are keeping as a surprise for now. Until it opens, the room is closed and nothing moves.",
    reward_source="In rehearsal, a recorded practice thank-you brings sugar to the cells from her look; silence brings nothing, and this rehearsal brings no shock.",
    chosen=["People supply eight practice wallets; longer holding times make larger cards, up to three hundred and sixty-five days.",
            "People limit tips to two thousand five hundred cents a day and one thousand cents to each wallet over its lifetime; she does not choose these limits.",
            "This rehearsal uses paper (for now) money only and gives her no smells.",
            "People set a ten-minute room clock and put a door in every room."],
    measured=["Her brain supplies the stop and the drive compared with her other looks; the practice thanks is no human response.",
              "The page counts how often it pushes her out of an empty margin."],
    how=("in rehearsal, her eye settles on a fixture wallet card for at least two rounds; this room adds no smell.",
         "her mushroom body supplies a drive, compared with the other cards she has seen in this visit.",
         "her stop and drive set the share of free paper (for now) money she tips; either sign tips, zero does not.",
         "the room rounds her tip down to whole cents and refuses tips above its daily or wallet limit.",
         "a recorded practice thank-you brings sugar to the cells from that look; silence brings nothing.",
         "she may leave by the door at the bottom of the room; the house closes a room after ten minutes either way."))


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
