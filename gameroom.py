"""Twelve smells and a taste that changes every two hours, with no rule in her eye."""
import random

from room import Room as RoomWalk
from roomkit import Declaration

RULE_S = 7200   # the sweet draw changes every two hours, the same rhythm as the paint room canvas
WORDS = ("apple", "lemon", "rain", "moon", "salt", "honey", "iron", "moss", "sand", "wine", "snow", "smoke")
DECLARATION = Declaration(
    name="the game room", path="/gameroom",
    cards={"source": "twelve plain words with distinct smells", "refresh_seconds": 60},
    commit_means="she picks that card and tastes it",
    reward_source="The game itself: a sweet card is sugar and a sour card is shock, on the room's own rule. The rule is drawn every two hours and written on this page; she is never told it. Paper for now.",
    chosen=["The sweet card game: twelve words, four sweet for two hours, shuffled every minute.",
            "One pick per ten seconds; a picked card rests sixty seconds.",
            "a four-minute room clock and a door in every room"],
    measured=["picks, sweet, sour and hit rate per two-hour rule", "time in room", "nudges"],
    how=("she stays on a card for two readings before choosing.",
         "the word becomes a smell through her olfactory neurons.",
         "when she stops, she tastes the card.",
         "sweet is sugar, sour is shock, and her mushroom body keeps the taste.",
         "four of twelve are sweet for two hours, and the draw is written here for people to see.",
         "a picked card rests a minute; she can pick at most once every ten seconds.",
         "she may leave by the door; the room closes after the four-minute clock."))


def sweet_words(hour):
    return tuple(random.Random(int(hour)).sample(WORDS, 4))


class Room(RoomWalk):
    declaration = DECLARATION
    disclosure = " ".join(DECLARATION.chosen + DECLARATION.measured)
    event_token_key = "market_id"

    def board_source(self):
        def fetch():
            words = list(WORDS)
            random.Random(int(self._now() // 60)).shuffle(words)
            return [{"token": word, "name": word, "question": word, "slot": i}
                    for i, word in enumerate(words)]
        return fetch

    def board(self):
        board = super().board()
        resting = self.read_book().get("resting_until", {})
        board["cards"] = [{**card, "resting": self._now() < resting.get(card["token"], 0)}
                          for card in board["cards"]]
        return board

    def smell_of(self, token):
        if token not in self._smell:
            self._smell[token] = self.nose.smell(self.meta.get(token, {}).get("question", ""))
        return self._smell[token]

    def can_commit(self, token, at):
        return token == "/hall" or (super().can_commit(token, at) and
                                    at >= self.read_book().get("resting_until", {}).get(token, 0))

    def intent_body(self, token, drive, at, look_id):
        return {"card_id": token, "drive": float(drive), "seen_at": at, "look_id": look_id}

