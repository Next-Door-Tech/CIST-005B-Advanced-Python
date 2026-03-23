from common_lib.cards import *


def card_value(card):
    if card.rank in (Rank.JACK, Rank.QUEEN, Rank.KING):
        return 10
    elif card.rank is Rank.ACE:
        return 11
    else:
        return card.rank.value


class BlackjackHand(Hand):

    @property
    def value(self) -> int:
        tot = sum(card_value(card) for card in self.cards)
        aces = sum(1 for card in self.cards if card.rank is Rank.ACE)
        while aces > 0 and tot > 21:
            tot -= 10
            aces -= 1
        return tot


class Player:
    hand: BlackjackHand
    chips: int
    _bet: int

    def __init__(self, name: str, chips: int, deck: Deck):
        self.name: str = name
        self.chips: int = chips
        self.hand: BlackjackHand = BlackjackHand(deck)

    def bet(self, amount: int):
        if amount < 0:
            raise ValueError("cannot bet a negative number of chips")
        if self.chips < amount:
            raise ValueError(f"player has only {self.chips} chips, cannot bet {amount}")
        else:
            self._bet += amount
            self.chips -= amount

    @property
    def busted(self):
        return self.hand.value > 21

    @property
    def has_blackjack(self):
        return len(self.hand) == 2 and self.hand.value == 21

    def bust(self):
        self._bet = 0

    def win(self):
        self.chips += 2 * self._bet

    def lose(self):
        self._bet = 0

    def start_turn(self):
        self.hand.draw(2, face_up=True)

    def hit(self):
        self.hand.draw(face_up=True)
        if self.busted:
            self.bust()

    def cleanup(self):
        self._bet = 0
        self.hand.discard_all()


class Dealer(Player):

    def __init__(self, deck: Deck):
        super().__init__("Dealer", 0, deck)
        self.chips: float = float('infinity')

    def start_turn(self):
        self.hand.draw(1, face_up=True)
        self.hand.draw(1, face_up=False)

    def bet(self, amount: int = 0):
        super().bet(0)

    def
