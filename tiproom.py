"""Fixture wallets and fixture thanks, with no chain connection."""
import json
from pathlib import Path

from room import Room as RoomWalk
from roomkit import Declaration, TIP_DAILY_CAP_CENTS, TIP_ADDRESS_CAP_CENTS

FIXTURES = Path(__file__).parent / "tests" / "fixtures" / "tiproom"
DECLARATION = Declaration(
    name="the tipping room", path="/tiproom",
    cards={"source": "eight fixture wallets with holding days", "refresh_seconds": 30},
    commit_means="a tip of floor(abs(drive) times free paper balance in cents) to that wallet",
    reward_source="A fixture thanks event delivers sugar to the recorded cells; silence delivers nothing and there is no shock feed.",
    chosen=["People supplied eight fixture wallets; card area scales with holding days, capped at 365 days.",
            f"The daily cap is {TIP_DAILY_CAP_CENTS} cents and the lifetime per-address cap is {TIP_ADDRESS_CAP_CENTS} cents; the cap is the safe's lock, not her decision.",
            "This room is paper only. There is no smell mapping yet.",
            "a ten-minute room clock and a door in every room"],
    measured=["The stop and relative drive come from the brain; fixture thanks is not a measured human response.",
              "nudges: how often the page had to push her out of an empty margin"],
    how=("her eye settles on a wallet card for at least two rounds; this room adds no smell.",
         "her mushroom body supplies a drive, compared with the other cards she has seen in this visit.",
         "when she stops, either sign spends a share of her paper balance; zero spends nothing.",
         "the paper tipper rounds down to whole cents and refuses tips above its daily or wallet limit.",
         "a recorded fixture thanks brings sugar to the cells from that look; silence brings nothing.",
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
