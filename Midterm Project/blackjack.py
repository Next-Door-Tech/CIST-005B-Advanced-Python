from time import sleep
from typing import Generator, Any, cast
from common_lib.cards import *
from enum import Enum, IntEnum


class BlackjackHand(Hand):
    @staticmethod
    def card_value(card: Card) -> int:
        if card.rank in (Rank.JACK, Rank.QUEEN, Rank.KING):
            return 10
        elif card.rank is Rank.ACE:
            return 11
        else:
            return card.rank.value

    @property
    def value(self) -> int:
        tot = aces = 0
        for card in self.cards:
            tot += self.card_value(card)
            aces += card.rank is Rank.ACE
        while tot > 21 and aces > 0:
            tot -= 10
            aces -= 1
        return tot


class Player:
    hand: BlackjackHand
    chips: int
    _bet: int

    class Actions(Enum):
        HIT = "HIT"
        STAND = "STAND"

    def __init__(self, name: str, chips: int, deck: Deck) -> None:
        self.name: str = name
        self.chips: int = chips
        self.hand: BlackjackHand = BlackjackHand(deck)
        self._bet = 0

    def bet(self, amount: int) -> None:
        if amount < 0:
            raise ValueError("cannot bet a negative number of chips")
        if self.chips < amount:
            raise ValueError(f"player has only {self.chips} chips, cannot bet {amount}")
        else:
            self._bet += amount
            self.chips -= amount

    @property
    def current_bet(self) -> int:
        return self._bet

    def initial_deal(self) -> None:
        self.hand.draw(2, face_up=True)

    def hit(self) -> None:
        self.hand.draw(face_up=True)

    def stand(self) -> None:
        pass

    @property
    def has_busted(self) -> bool:
        return self.hand.value > 21

    @property
    def has_blackjack(self) -> bool:
        return len(self.hand) == 2 and self.hand.value == 21

    def take_turn(self) -> Generator[None, Actions, None]:
        if self.has_blackjack:
            return

        action = yield
        while action is self.Actions.HIT and not self.has_busted and not self.hand.value == 21:
            self.hit()
            action = yield

    def end_turn(self, dealer: Dealer) -> None:
        if self.has_busted:
            self.lose()
            return
        elif self.hand.value < dealer.hand.value:
            self.win()
            return

    def win(self) -> None:
        if self.has_blackjack:  # pays 3:2
            self.chips += (5 * self._bet) // 2
        else:  # pays 1:1
            self.chips += 2 * self._bet

        self._bet = 0

    def lose(self) -> None:
        self._bet = 0

    def cleanup(self) -> None:
        self._bet = 0
        self.hand.discard_all()


class Dealer(Player):

    def __init__(self, deck: Deck):
        super().__init__("Dealer", 0, deck)
        self.chips: float = float('infinity')  # type: ignore[assignment]

    def initial_deal(self):
        self.hand.draw(1, face_up=True)
        self.hand.draw(1, face_up=False)

    def bet(self, amount: int = 0):
        pass  # do nothing; dealer cannot make bets

    def take_turn(self) -> Generator[None, Any, None]:
        if self.has_blackjack:
            return

        while self.hand.value < 17:
            self.hit()
            yield


class BlackjackTable:
    class Phase(IntEnum):
        PRE_ROUND = 0
        BETTING = 1
        DEALING = 2
        PLAYER_TURN = 3
        DEALER_TURN = 4
        SCORING = 5
        PAYOUT = 6
        POST_ROUND = 7

    _phase: Phase

    @property
    def phase(self) -> Phase:
        return self._phase

    @phase.setter
    def phase(self, next_phase: Phase) -> None:
        next_phase = self.Phase(next_phase)
        if next_phase is self._phase or next_phase is self.Phase(self._phase + 1):
            self._phase = next_phase  # can re-enter same phase from itself, or enter next phase in order
        elif next_phase is self.Phase.PRE_ROUND and self._phase is self.Phase.POST_ROUND:
            self._phase = next_phase  # can enter PRE_ROUND from POST_ROUND
        elif next_phase is self.Phase.SCORING and self._phase is self.Phase.DEALING:
            self._phase = next_phase  # dealer has blackjack -> players lose, intermediate phases are skipped
        else:
            raise ValueError(f"cannot enter phase {next_phase.name} from phase {self._phase.name}")

    def __init__(self, player_seats: int = 3) -> None:
        self.deck: Deck = Shoe(8)
        self.deck.shuffle()
        self._dealer: Dealer = Dealer(self.deck)
        self._players: list[Player | None] = [self.dealer] + ([None] * player_seats)
        self._phase = self.Phase.PRE_ROUND

    @property
    def max_players(self) -> int:
        return len(self._players) - 1

    @property
    def dealer(self) -> Dealer:
        return self._dealer

    def player(self, seat: int) -> Player | None:
        """player seats are indexed from 1; player(0) is the dealer"""
        if 0 <= seat < len(self._players):
            return self._players[seat]
        else:
            raise IndexError(f"there is no seat {seat} at this table")

    @property
    def active_players(self) -> list[Player]:
        return [cast(Player, player) for player in self._players[1:] if player is not None and player.current_bet > 0]

    @property
    def present_players(self) -> list[Player]:
        return [player for player in self._players[1:] if player is not None]

    def join_table(self, seat: int, name: str = "Anonymous", chips: int = 0) -> None:
        if self.phase is not self.Phase.PRE_ROUND:
            raise RuntimeError(f"new players may not join the table in the middle of a round")

        if 1 <= seat < len(self._players) and self.player(seat) is None:
            self._players[seat] = Player(name, chips, self.deck)
        elif seat == 0:
            raise IndexError(f"player '{name}' cannot join at the dealer's seat")
        else:
            raise IndexError(f"there is no seat {seat} at this table")

    def leave_table(self, seat) -> None:
        if self.phase is not self.Phase.PRE_ROUND:
            raise RuntimeError(f"players may not leave the table in the middle of a round")

        if seat == 0:
            raise IndexError(f"the dealer may not leave the table")
        elif not 1 <= seat < len(self._players):
            raise IndexError(f"there is no seat {seat} at this table")
        elif self.player(seat) is not None:
            self._players[seat] = None
        else:
            raise ValueError(f"seat {seat} is already empty")

    def start_betting(self) -> None:
        self.phase = self.Phase.BETTING

    def start_round(self) -> None:
        for _ in self.initial_deal():
            print(self)
            sleep(1)

        self.take_turns()

        for player in self.active_players:
            if player.has_busted:
                print(player.name, "has busted (phrasing, genius)\n")
            elif player.hand.value > self.dealer.hand.value:
                print(player.name, f"wins against dealer, {player.hand.value} to {self.dealer.hand.value}")
            player.end_turn(self.dealer)

    def initial_deal(self) -> Generator[None, None, None]:
        self.phase = self.Phase.DEALING

        if len(self.dealer.hand) > 0 or any(len(player.hand) > 0 for player in self.active_players):
            raise RuntimeError(f"the initial deal has already started")

        self.dealer.hand.draw(face_up=True)
        yield

        for player in self.active_players:
            player.hand.draw(face_up=True)
            yield

        self.dealer.hand.draw(face_up=True)
        yield

        for player in self.active_players:
            player.hand.draw(face_up=True)
            yield

    def take_turns(self) -> None:
        self.phase = self.Phase.PLAYER_TURN
        for player in self.active_players:
            turn = player.take_turn()
            try:
                next(turn)
                print(self)
                while True:
                    turn.send(player.Actions(input(f"{player.name}, Hit or Stand: ").upper()))
                    print(self)
            except StopIteration:
                print(self)
                continue

        sleep(2)

        for _ in self.dealer.take_turn():
            print(self)
            sleep(2)

    def __str__(self) -> str:
        s = "Table:\n"
        s += "\tDealer: " + ", ".join(f"{card:s}" for card in self.dealer.hand.cards) + "\n"
        s += "\tPlayers:\n"
        for player in self.present_players:
            s += f"\t\t{player.name} (chips: {player.chips}, bet: {player.current_bet}): "
            s += ", ".join(f"{card:s}" for card in player.hand.cards)
            s += "\n"

        return s


table = BlackjackTable()

table.join_table(1, "Connor", 1000)

table.start_betting()

table.player(1).bet(100)

table.start_round()

print(table)
