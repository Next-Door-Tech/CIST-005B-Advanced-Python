from time import sleep
from typing import Generator, Any, cast
from common_lib.cards import *
from enum import Enum, IntEnum


def confirm(prompt: str = "Yes/no:", error: str = "I didn't understand that. Could you try again?") -> bool:
    tries = 0
    prompt = prompt.strip() + " "
    while not (response := input(prompt).lower().strip()).startswith(('y', 'n')):
        print(error)
        tries += 1
        if tries == 2:
            prompt += "(Yes or no) "

    print()
    return response.startswith('y')


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
        self._starting_chips: int = chips
        self.hand: BlackjackHand = BlackjackHand(deck)
        self._bet = 0

    @property
    def starting_chips(self) -> int:
        return self._starting_chips

    def bet(self, amount: int) -> None:
        if amount < -self.current_bet:  #
            raise ValueError("cannot bet a negative number of chips")

        if self.chips < amount:
            raise ValueError(f"{self.name} has only {self.chips} chips, cannot bet {amount}")
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
        """Creates a generator object which can be iterated over for the length of a player's turn."""
        if self.has_blackjack:
            return

        while not self.has_busted and not self.hand.value == 21:
            action = yield
            if action is not self.Actions.HIT:
                break
            self.hit()

    def end_turn(self, dealer: Dealer) -> None:
        if self.has_busted:
            self.lose()
            return
        elif self.hand.value > dealer.hand.value:
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
        PLAYING = 2
        POST_ROUND = 3

    _phase: Phase

    @property
    def phase(self) -> Phase:
        return self._phase

    @phase.setter
    def phase(self, next_phase: Phase) -> None:
        next_phase = self.Phase(next_phase)
        if next_phase is self._phase or next_phase == self.Phase(self._phase) + 1:
            self._phase = next_phase  # can re-enter same phase from itself, or enter next phase in order
        elif next_phase is self.Phase.PRE_ROUND and self._phase is self.Phase.POST_ROUND:
            self._phase = next_phase  # can enter PRE_ROUND from POST_ROUND
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

    @property
    def num_present_players(self) -> int:
        return sum(1 for player in self._players[1:] if player is not None)

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

    def pre_round(self) -> None:
        print(self)
        if self.num_present_players > 0 and confirm("Would anyone like to leave the table?"):
            for i in range(1, self.max_players):
                player = self.player(i)
                if player is not None and confirm(f"{player.name}, would you like to leave the table?"):
                    if player.chips > player.starting_chips:
                        print(f"Enjoy your winnings, {player.name}.")
                    else:
                        print(f"Have a good day, {player.name}.")
                    self.leave_table(i)
            print(self)

        else_ = ""
        while self.num_present_players < self.max_players and confirm(f"Would anyone {else_}like to join the table?"):
            else_ = "else "
            try:
                name = input("What is your name? ")
                seat = None
                chips = None

                while seat is None:
                    try:
                        seat = int(input(f"Which seat will you be taking, {name}? "))

                        if seat > self.max_players:
                            print("We don't have that many seats at this table.")
                            seat = None
                        elif seat < 1:
                            print("The seats are numbered starting at 1.")
                            seat = None
                        elif self.player(seat) is not None:
                            print(f"Sorry, {cast(Player, self.player(seat)).name} is already at that seat.")
                            seat = None
                    except ValueError:
                        print("I didn't understand that.")

                    if not seat and not confirm(f"Would you still like to join the table, {name}? "):
                        raise KeyboardInterrupt

                while chips is None:
                    try:
                        chips = int(input(f"How many chips do you have, {name}? "))

                        if chips == 0:
                            print("Just watching? I understand, but you won't be able to play.")
                        if chips < 0:
                            print("In debt already? Unfortunately I won't be able to let you join the table.")
                            raise KeyboardInterrupt

                    except ValueError:
                        print("I didn't understand that.")
                        if not confirm(f"Would you still like to join the table, {name}? "):
                            raise KeyboardInterrupt

                print(f"Welcome to the table, {name}.\n")
                self.join_table(seat, name, chips)

            except KeyboardInterrupt:
                print(self)
                continue

            print(self)

        if confirm("Is everyone ready to begin betting?"):
            self.phase = self.Phase.BETTING

    def start_betting(self) -> None:
        for player in self.present_players:
            success = False
            while not success:
                try:
                    bet = int(input(f"{player.name}, your bet? "))
                except ValueError:
                    print("I didn't understand that. Could you try again?")
                    continue

                try:
                    player.bet(bet)
                except ValueError:
                    print(f"Unfortunately I can't let you bet {bet} chips.")
                    continue

                success = True

            print(self)

        if confirm("Has everyone placed their bets? "):
            print("Bets are closed.")
            self.phase = self.Phase.PLAYING

    def start_round(self) -> None:
        for _ in self.initial_deal():
            print(self)
            sleep(1)

        if not self.dealer.has_blackjack:
            self.take_turns()

        self.phase = self.Phase.POST_ROUND
        return

    def post_round(self) -> None:
        if self.dealer.has_blackjack:
            print("Dealer has blackjack; everyone loses their bets.")
            for player in self.active_players:
                player.end_turn(self.dealer)

        else:
            for player in self.active_players:
                if player.has_busted:
                    print(player.name, "has busted (phrasing, genius).")
                elif player.has_blackjack and self.dealer.has_busted:
                    print(player.name, f"wins with blackjack against the dealer, who busted.")
                elif player.has_blackjack and player.hand.value > self.dealer.hand.value:
                    print(player.name, f"wins with blackjack against the dealer, who scored {self.dealer.hand.value}.")
                elif player.hand.value == self.dealer.hand.value:
                    print(player.name,
                          f"loses in a tie against dealer, {player.hand.value} to {self.dealer.hand.value}.")
                elif player.hand.value > self.dealer.hand.value:
                    print(player.name, f"wins against dealer, {player.hand.value} to {self.dealer.hand.value}.")
                else:
                    print(player.name, f"loses against dealer, {player.hand.value} to {self.dealer.hand.value}.")
                player.end_turn(self.dealer)

        print(self)
        while not confirm("May I clear the table so we can begin another round?"):
            print("Okay, I'll let you look at things once again.")
            print(self)

        for player in self.present_players:
            player.hand.discard_all()

        self.phase = self.Phase.PRE_ROUND

    def initial_deal(self) -> Generator[None, None, None]:

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
        self.phase = self.Phase.PLAYING
        for player in self.active_players:
            turn = player.take_turn()
            try:
                next(turn)
                print(self)
                while True:
                    try:
                        turn.send(player.Actions(input(f"{player.name}, Hit or Stand: ").upper()))
                    except ValueError:
                        print("Sorry, I didn't understand that.")
                        continue
                    print(self)
            except StopIteration:
                print(self)
                continue

        sleep(2)

        for _ in self.dealer.take_turn():
            print(self)
            sleep(2)

    def __str__(self) -> str:
        return '\n'.join((
            "Dealer:",
            "" if self.dealer.hand.value == 0
            else (f"    ({self.dealer.hand.value})" + ", ".join(f"{card:s}" for card in self.dealer.hand.cards)),

            *('\n'.join((
                f"Seat {i}: " + "Empty" if player is None
                else f"{player.name} (Chips: {player.chips}, Bet: {player.current_bet})",

                "" if player is None or len(player.hand) == 0
                else f"    ({player.hand.value}) {", ".join(f"{card:s}" for card in player.hand.cards)}"
            )) for i, player in enumerate(self._players[1:], 1)

            )))

    def loop(self) -> None:
        while True:
            match self.phase:
                case self.Phase.PRE_ROUND:
                    self.pre_round()
                case self.Phase.BETTING:
                    self.start_betting()
                case self.Phase.PLAYING:
                    self.start_round()
                case self.Phase.POST_ROUND:
                    self.post_round()


table = BlackjackTable()
table.loop()
