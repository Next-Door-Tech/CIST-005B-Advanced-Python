import unicodedata as ucd
from enum import Enum
from itertools import product, chain
from typing import overload, Self, TypeVar, Protocol
from collections import deque
from collections.abc import MutableSequence, MutableSet, Iterable, Callable
from identityset import IdentitySet
from formatspec import FormatSpec

__all__ = ["Card", "Deck", "Shoe", "Hand"]

_non_emoji = ucd.lookup('VS15')  # Unicode modifier preventing use of emoji versions of characters


class OrderedEnum(Enum):  # From python docs
    def __ge__(self, other):
        return self.value >= other.value if self.__class__ is other.__class__ else NotImplemented

    def __gt__(self, other):
        return self.value > other.value if self.__class__ is other.__class__ else NotImplemented

    def __le__(self, other):
        return self.value <= other.value if self.__class__ is other.__class__ else NotImplemented

    def __lt__(self, other):
        return self.value < other.value if self.__class__ is other.__class__ else NotImplemented


class Rank(OrderedEnum):
    """The rank of a card. {Ace, Two - Ten, Jack, Queen, King}"""

    def __new__(cls, value, symbol: str, char_symbol: str = None, *aliases):
        self = object.__new__(cls)
        self._value_ = value
        return self

    def __init__(self, value, symbol: str, char_symbol: str = None, *aliases):
        self._add_value_alias_(self.name)

        self.string = self.name.title()
        self._add_value_alias_(self.string)

        self.symbol = symbol
        self._add_value_alias_(self.symbol)

        self.char_symbol = char_symbol or symbol
        self._add_value_alias_(self.char_symbol)

        for alias in aliases:
            if isinstance(alias, str):
                self._add_alias_(alias.upper())
            self._add_value_alias_(alias)
            if hasattr(alias, "upper"):
                self._add_value_alias_(alias.upper())

    ACE = 1, 'A'
    TWO = 2, '2', None, "DEUCE"
    THREE = 3, '3', None, "TREY"
    FOUR = 4, '4'
    FIVE = 5, '5'
    SIX = 6, '6'
    SEVEN = 7, '7'
    EIGHT = 8, '8'
    NINE = 9, '9'
    TEN = 10, '10', 'X'
    JACK = 11, 'J'
    QUEEN = 12, 'Q'
    KING = 13, 'K'

    def _add_value_alias_(self, value):
        super()._add_value_alias_(value)
        if hasattr(value, "upper"):
            super()._add_value_alias_(value.upper())

    @classmethod
    def _missing_(cls, value: str):
        if hasattr(value, "upper") and value.upper() in cls:
            return cls(value.upper())
        else:
            return None

    def __str__(self):
        return self.string

    def __format__(self, format_spec):
        spec = FormatSpec(format_spec)

        match spec.type, spec.alt:
            case 'c', None:
                spec.type = 's'
                return format(self.symbol, str(spec))
            case 'c', '#':
                spec.type = 's'
                spec.alt = None
                return format(self.char_symbol, str(spec))
            case _:
                return format(self.string, format_spec)


class Color(Enum):
    """The color of a card. {Black, Red}"""

    def __new__(cls, value, *aliases):
        self = object.__new__(cls)
        self._value_ = value
        return self

    def __init__(self, value, *aliases):
        self._add_value_alias_(self.name)

        for alias in aliases:
            self._add_value_alias_(alias)

    def _add_value_alias_(self, value):
        super()._add_value_alias_(value)
        if hasattr(value, "upper"):
            super()._add_value_alias_(value.upper())

    @classmethod
    def _missing_(cls, value: str):
        if hasattr(value, "upper") and value.upper() in cls:
            return cls(value.upper())

        try:
            if Suit(value) in cls:
                return cls(Suit(value))
        except ValueError:
            pass
        else:
            return None

        return None

    BLACK = "Black", "Clubs", "Spades"
    RED = "Red", "Diamonds", "Hearts"


class Suit(OrderedEnum):
    """The suit of a card. {Clubs, Diamonds, Hearts, Spades}"""

    def __new__(cls, value, symbol: str, char_symbol: str = None, solid_symbol=None):
        self = object.__new__(cls)
        self._value_ = value
        return self

    def __init__(self, value, symbol: str, char_symbol=None, solid_symbol=None):
        self._add_value_alias_(self.name)

        self.string = self.name.title()
        self._add_value_alias_(self.string)  # i.e. Spades
        self._add_value_alias_(self.string[:-1])  # i.e. Spade

        self.symbol = symbol
        self._add_value_alias_(self.symbol)

        self.char_symbol = char_symbol or symbol
        self._add_value_alias_(self.char_symbol)

        self.solid_symbol = solid_symbol or symbol
        self._add_value_alias_(self.solid_symbol)

        self.color = Color(self.name)
        # noinspection PyProtectedMember
        Color(self.name)._add_value_alias_(self)

    SPADES = 0, ucd.lookup('BLACK SPADE SUIT') + _non_emoji, 'S'
    HEARTS = 1, ucd.lookup('WHITE HEART SUIT') + _non_emoji, 'H', ucd.lookup('BLACK HEART SUIT') + _non_emoji
    DIAMONDS = 2, ucd.lookup('WHITE DIAMOND SUIT') + _non_emoji, 'D', ucd.lookup('BLACK DIAMOND SUIT') + _non_emoji
    CLUBS = 3, ucd.lookup('BLACK CLUB SUIT') + _non_emoji, 'C'

    def _add_value_alias_(self, value):
        super()._add_value_alias_(value)
        if hasattr(value, "upper"):
            super()._add_value_alias_(value.upper())

    @classmethod
    def _missing_(cls, value: str):
        if hasattr(value, "upper") and value.upper() in cls:
            return cls(value.upper())
        else:
            return None

    def __str__(self):
        return self.string

    def __format__(self, format_spec):
        spec = FormatSpec(format_spec)

        match spec.type, spec.alt:
            case 'c', None:
                spec.type = 's'
                return format(self.symbol, str(spec))
            case 'c', '#':
                spec.type = 's'
                spec.alt = None
                return format(self.char_symbol, str(spec))
            case _:
                return format(self.string, format_spec)


class Kind(OrderedEnum):
    """The kind of card; its face value in a 52-card deck."""

    _ignore_ = ["r", "s"]

    def __new__(cls, rank: Rank = None, suit: Suit = None):
        self = object.__new__(cls)
        self._value_ = (Rank(rank), Suit(suit))
        return self

    def __init__(self, rank: Rank = None, suit: Suit = None):
        self.rank: Rank = Rank(rank)
        self.suit: Suit = Suit(suit)
        self.symbol: str = ucd.lookup(f"PLAYING CARD {rank!s} OF {suit!s}") + _non_emoji
        self.back_symbol: str = ucd.lookup("PLAYING CARD BACK") + _non_emoji
        self.color: Color = self.suit.color

        self._add_value_alias_((str(self.rank), str(self.suit)))

    for r, s in product(Rank, Suit):  # Generate types from product(Rank, Suit)
        locals()[f"{r.name}_{s.name}"] = (r, s)

    def __lt__(self, other):
        return self.rank < other.rank or (self.rank == other.rank and self.suit < other.suit)

    def __le__(self, other):
        return self.rank < other.rank or (self.rank == other.rank and self.suit <= other.suit)

    def __ge__(self, other):
        return self.rank > other.rank or (self.rank == other.rank and self.suit > other.suit)

    def __gt__(self, other):
        return self.rank > other.rank or (self.rank == other.rank and self.suit >= other.suit)

    @classmethod
    def _missing_(cls, value):
        match value:
            case (Rank(rank) | str(rank), Suit(suit) | str(suit)) if (Rank(rank), Suit(suit)) in cls:
                return cls(Rank(rank), Suit(suit))
            case (Suit(suit), Rank(rank) | str(rank)) if (Rank(rank), Suit(suit)) in cls:
                return cls(Rank(rank), Suit(suit))
            case (Suit(suit) | str(suit), Rank(rank)) if (Rank(rank), Suit(suit)) in cls:
                return cls(Rank(rank), Suit(suit))
            case str() if value.upper() in cls:
                return cls(value.upper())
            case str():  # TODO add search matching for names of rank and suit
                raise NotImplementedError
            case _:
                return None

        return None  # Should be unreachable, but just in case.

    def _add_value_alias_(self, value):
        super()._add_value_alias_(value)
        if hasattr(value, "upper"):
            super()._add_value_alias_(value.upper())
        if isinstance(value, tuple | list):
            super()._add_value_alias_((item.upper() if hasattr(item, "upper") else item for item in value))


class Card:
    __slots__ = ("_kind", "_face_up", "__weakref__")

    Ranks: Rank = staticmethod(Rank)
    Suits: Suit = staticmethod(Suit)
    Colors: Color = staticmethod(Color)
    Kinds: Kind = staticmethod(Kind)

    @overload
    def __init__(self, rank: Card.Ranks, suit: Card.Suits, *, face_up: bool = False):
        self._kind: Card.Kinds = self.Kinds(rank, suit)
        self._face_up: bool = face_up

    @overload
    def __init__(self, kind: Card.Kinds, *, face_up: bool = False):
        self._kind: Card.Kinds = kind
        self._face_up: bool = face_up

    def __init__(self, *args, face_up: bool = False, **kwargs):
        if len(args) == 1:
            self._kind: Card.Kinds = self.Kinds(args[0])
        else:  # len(args) == 2
            self._kind: Card.Kinds = self.Kinds(*args[0:1])
        self._face_up: bool = face_up

    @property
    def kind(self) -> Card.Kinds:
        """The kind of the card, i.e. its rank and suit."""
        return self._kind

    @property
    def rank(self) -> Card.Ranks:
        """The rank of the card."""
        return self._kind.rank

    @property
    def suit(self) -> Card.Suits:
        """The suit of the card."""
        return self._kind.suit

    @property
    def color(self) -> Card.Colors:
        """The color of the card."""
        return self._kind.color

    @property
    def face_up(self) -> bool:
        """Whether the card is face up."""
        return self._face_up

    @face_up.setter
    def face_up(self, value: bool) -> None:
        self._face_up = value

    @property
    def face_down(self) -> bool:
        """Whether the card is face down."""
        return not self._face_up

    @face_up.setter
    def face_up(self, value: bool) -> None:
        self._face_up = not value

    def flip(self) -> None:
        """Flips whether the card is face up or face down."""
        self._face_up = not self._face_up

    @property
    def front_symbol(self):
        """The symbol representing the front of the card."""
        return self._kind.symbol

    @property
    def back_symbol(self):
        """The symbol representing the back of the card."""
        return self._kind.back_symbol

    @property
    def symbol(self):
        """The symbol representing the front or back of the card, as it is currently flipped."""
        return self.front_symbol if self.face_up else self.back_symbol

    def __lt__(self, other: Self) -> bool:
        return self._kind < other._kind

    def __le__(self, other: Self) -> bool:
        return self._kind <= other._kind

    def __ge__(self, other: Self) -> bool:
        return self._kind >= other._kind

    def __gt__(self, other: Self) -> bool:
        return self._kind > other._kind

    def __eq__(self, other: Self) -> bool:
        return self._kind == other._kind

    def __ne__(self, other: Self) -> bool:
        return self._kind != other.kind

    def __str__(self):
        return f"[{self.rank!s} of {self.suit!s}]" if self.face_up else "[A face down card.]"

    def __repr__(self):
        return f"Card('{self.rank.name}', '{self.suit.name}', face_up = {self.face_up})"

    def __format__(self, format_spec):
        spec = FormatSpec(format_spec)
        match spec.type, spec.alt:
            case 'c', None:
                spec.type = 's'
                return format(self.symbol, str(spec))

            case 'c', '#':
                spec.type = 's'
                spec.alt = None
                return format(self.rank.char_symbol + self.suit.char_symbol, str(spec))

            case 's' | None, '#':
                spec.alt = None
                if self.face_up:
                    return format(self.rank.symbol + self.suit.symbol, str(spec))
                else:
                    return format("XX", str(spec))

            case _:
                return format(str(self), format_spec)


class SortAlgorithm[T](Protocol):
    def __call__(self, iterable: Iterable[T], key: Callable[[T, T], bool] = None, reverse: bool = None) -> list[T]: ...


class ComparisonKey[T](Protocol):
    def __call__(self, left: T, right: T) -> bool: ...


class Deck(MutableSequence[Card], IdentitySet[Card]):
    """A standard 52-card deck.

    Contains a draw pile and a discard pile.

    Ideally, there should be only one Deck per game. If you are implementing a
    game which uses multiple decks of cards, see Shoe instead.

    Once created, Cards always belong to their parent Deck unless they are explicitly deleted with del().
    Likewise, new Cards can be inserted into the deck using insert().

    Cards can be moved from the deck into a hand, but once removed from a hand
    they are automatically returned to the deck's discard pile.
    """

    _new_deck_order: tuple[Kind] = tuple(chain(
        (Kind(rank, Card.Suits.SPADES) for rank in Card.Ranks),
        (Kind(rank, Card.Suits.DIAMONDS) for rank in Card.Ranks),
        reversed([Kind(rank, Card.Suits.HEARTS) for rank in Card.Ranks]),
        reversed([Kind(rank, Card.Suits.CLUBS) for rank in Card.Ranks])
    ))
    _sort_key: ComparisonKey[Card] = None
    _sort_algorithm: SortAlgorithm[Card] = sorted  # Override in subclass for HW assignment

    def __init__(self, *, sort_key: ComparisonKey[Card] = None,
                 sort_algorithm: SortAlgorithm[Card] = None):
        """Initialize a deck in new deck order.

        If subclassing, call super().__init__() after initializing
        self._draw_pile and self._discard_pile, if non-standard sizes are desired.

        sort_key, if supplied, must compare two Cards by their Kind.
        sort_algorithm, if supplied, must match the signature and behavior of sorted().
        """
        super().__init__()

        # Allow subclasses to define their own deque sizes and deck orders
        if not hasattr(self, '_draw_pile'):
            self._draw_pile = deque[Card](maxlen=52)
        if len(self._draw_pile) == 0:
            self._draw_pile.extend(Card(kind) for kind in self._new_deck_order)

        if not hasattr(self, '_discard_pile'):
            self._discard_pile = deque[Card](maxlen=52)

        self._owned_cards: IdentitySet[Card] = IdentitySet(self._draw_pile)

        if sort_algorithm is not None:
            self._sort_algorithm = sort_algorithm
        if sort_key is not None:
            self._sort_key = sort_key

    @property
    def draw_pile(self) -> list[Card]:
        return list(self._draw_pile)

    @property
    def discard_pile(self) -> list[Card]:
        return list(self._discard_pile)

    def sort_draw(self):
        temp = self._sort_algorithm(self._draw_pile, key=self._sort_key, reverse=False)
        self._draw_pile.clear()
        self._draw_pile.extend(temp)

    def sort_discard(self):
        temp = self._sort_algorithm(self._discard_pile, key=self._sort_key, reverse=False)
        self._discard_pile.clear()
        self._discard_pile.extend(temp)

    def sort(self):
        """Alias for sort_draw()."""
        self.sort_draw()

    def re_sort(self):
        """Return all cards from the discard pile to the draw pile, and re-sort the deck."""
        self._draw_pile.extend(self._discard_pile)
        self._discard_pile.clear()
        self.sort()

    def shuffle_draw(self):  # TODO
        ...

    def shuffle_discard(self):  # TODO
        ...

    def shuffle(self):
        """Alias for shuffle_draw()."""
        self.shuffle_draw()

    def re_shuffle(self):  # TODO
        """Return all cards from the discard pile to the draw pile, and reshuffle."""
        ...

    def return_top(self):  # TODO
        """Return all cards from the discard pile to the top of the draw pile."""
        ...

    def return_bottom(self):  # TODO
        """Return all cards from the discard pile to the bottom of the draw pile."""
        ...

    @overload
    def __contains__(self, card: Card) -> bool:
        """Return whether the deck owns this exact card (by id)."""
        ...

    @overload
    def __contains__(self, card: Kind) -> bool:
        """Return whether the deck owns a card of this kind."""
        ...

    def __contains__(self, card: Card | Kind) -> bool:
        if isinstance(card, Card):
            return card in self._owned_cards
        elif isinstance(card, Kind):
            return card in (member.type for member in self._owned_cards)
        else:
            raise ValueError

    # @overload
    # @abstractmethod
    # def __getitem__(self, index: int) -> Card:
    #     ...
    #
    # @overload
    # @abstractmethod
    # def __getitem__(self, index: slice) -> Hand:
    #     ...
    #
    # def __getitem__(self, index):
    #     return self._draw_pile[index]
    #
    # @overload
    # @abstractmethod
    # def __delitem__(self, index: int) -> None: ...
    #
    # @overload
    # @abstractmethod
    # def __delitem__(self, index: slice) -> None: ...
    #
    # def __delitem__(self, index):
    #     pass
    #
    # def __setitem__(self, key, value):
    #     pass
    #
    # def insert(self, index, value):
    #     pass
    #
    # def __len__(self):
    #     pass


class Shoe(Deck):
    """A grouping of multiple 52-card decks treated as one."""

    def __init__(self, num_decks: int, *, sort_key: Callable[[Card, Card], bool] = None):
        self._deck = deque[Card](maxlen=52 * num_decks)
        self._discard = deque[Card](maxlen=52 * num_decks)
        for i in range(num_decks):
            self._deck.extend(Card(kind) for kind in self._new_deck_order)

        super().__init__(sort_key=sort_key)


class Hand(MutableSequence[Card]):
    """A hand of cards. Must be a subset of a Deck or Shoe."""

    def __init__(self):
        pass

    def add(self, value):
        pass

    def discard(self, value):
        pass

    def __contains__(self, x):
        pass

    def __len__(self):
        pass

    def __iter__(self):
        pass
