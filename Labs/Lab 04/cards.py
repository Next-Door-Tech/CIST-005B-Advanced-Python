import unicodedata as ucd
from abc import abstractmethod
from enum import Enum
from itertools import product, chain
from functools import singledispatchmethod
from dataclasses import dataclass, asdict, InitVar, KW_ONLY
from typing import Literal, ClassVar, overload, Self, Callable
from collections import deque
from collections.abc import MutableSequence, Set, MutableSet
import re

__all__ = ["Card", "Deck", "Shoe", "Hand"]

_non_emoji = ucd.lookup('VS15')  # Unicode modifier preventing use of emoji versions of characters


@dataclass
class FormatSpec:  # Adapted from https://stackoverflow.com/a/78351366/2565329
    """Parsed variant of the Format Specification Mini-Language."""

    format_spec: InitVar[str | None] = None

    _: KW_ONLY
    fill: str | None = None
    align: Literal["<", ">", "=", "^"] | None = None
    sign: Literal["+", "-", " "] | None = None
    pos_zero: Literal["z"] | None = None
    alt: Literal["#"] | None = None
    zero_padding: Literal["0"] | None = None
    width_str: str | None = None
    grouping: Literal["_", ","] | None = None
    decimal: Literal["."] | None = None
    precision_str: str | None = None
    type: Literal["b", "c", "d", "e", "E", "f", "F", "g", "G", "n", "o", "s", "x", "X", "%"] | None = None

    RE_FORMAT_SPEC: ClassVar[re.Pattern] = re.compile(
        r'(?:(?P<fill>[\s\S])?(?P<align>[<>=^]))?'
        r'(?P<sign>[- +])?'
        r'(?P<pos_zero>z)?'
        r'(?P<alt>#)?'
        r'(?P<zero_padding>0)?'
        r'(?P<width_str>\d+)?'
        r'(?P<grouping>[_,])?'
        r'(?:(?P<decimal>\.)(?P<precision_str>\d+))?'
        r'(?P<type>[bcdeEfFgGnosxX%])?'
    )

    def __post_init__(self, format_spec: str | None):
        if format_spec is not None:
            if not isinstance(format_spec, str):
                raise TypeError(f"Could not parse unexpected format_spec: {format_spec!r}")

            spec_match = FormatSpec.RE_FORMAT_SPEC.fullmatch(format_spec)
            if spec_match:
                for key, value in spec_match.groupdict().items():
                    if value is not None:
                        setattr(self, key, value)
            else:
                raise ValueError(f"Could not parse format_spec string: {format_spec!r}")

    @property
    def width(self) -> int:
        return int(self.width_str) if self.width_str else 0

    @width.setter
    def width(self, val: int):
        if val is None:
            self.width_str = None
        else:
            self.width_str = str(val)

    @property
    def precision(self) -> int:
        return int(self.precision_str) if self.precision_str else 0

    @precision.setter
    def precision(self, val: int | None):
        if val is None:
            self.precision_str = val
        else:
            self.precision_str = str(val)

    def __str__(self) -> str:
        return "".join(v for v in asdict(self).values() if v is not None)


class OrderedEnum(Enum):  # From python docs
    def __ge__(self, other):
        return self.value >= other.value if self.__class__ is other.__class__ else NotImplemented

    def __gt__(self, other):
        return self.value > other.value if self.__class__ is other.__class__ else NotImplemented

    def __le__(self, other):
        return self.value <= other.value if self.__class__ is other.__class__ else NotImplemented

    def __lt__(self, other):
        return self.value < other.value if self.__class__ is other.__class__ else NotImplemented


class FrozenIdentitySet[T](Set[T]):  # Adapted from https://stackoverflow.com/a/17039643/2565329
    """A functional frozenset() implementation allowing for mutable members by using `id()` instead of `==`."""

    __key = id

    def __init__(self, iterable=()):
        self.__map = {}
        self.__map |= zip(map(self.__key, iterable), iterable)

    def __len__(self):
        return len(self.__map)

    def __contains__(self, x):
        return self.__key(x) in self.__map

    def __iter__(self):
        return iter(self.__map.values())

    def __repr__(self):
        if not self:
            return f"{self.__class__.__name__!s}"
        return f"{self.__class__.__name__!s}({list(self)!r})"


class IdentitySet[T](MutableSet[T]):  # Adapted from https://stackoverflow.com/a/17039643/2565329
    """A functional set() implementation allowing for mutable members by using `id()` instead of `==`."""

    __key = id

    def __init__(self, iterable=()):
        self.__map = {}
        self.__map |= zip(map(self.__key, iterable), iterable)

    def __len__(self):
        return len(self.__map)

    def __contains__(self, x):
        return self.__key(x) in self.__map

    def __iter__(self):
        return iter(self.__map.values())

    def add(self, value):
        """Add an element."""
        self.__map[self.__key(value)] = value

    def discard(self, value):
        """Remove an element.  Do not raise an exception if absent."""
        self.__map.pop(self.__key(value), None)

    def __repr__(self):
        if not self:
            return f"{self.__class__.__name__!s}"
        return f"{self.__class__.__name__!s}({list(self)!r})"


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
        self.rank = Rank(rank)
        self.suit = Suit(suit)
        self.symbol = ucd.lookup(f"PLAYING CARD {rank!s} OF {suit!s}") + _non_emoji
        self.back_symbol = ucd.lookup("PLAYING CARD BACK") + _non_emoji

        match suit:  # Determine Color
            case Suit.CLUBS | Suit.SPADES:
                self.color = Color.BLACK
            case Suit.HEARTS | Suit.DIAMONDS:
                self.color = Color.RED

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


class Card:
    __slots__ = ("_kind", "_face_up", "__weakref__")

    Ranks = Rank
    Suits = Suit
    Colors = Color
    Kinds = Kind

    @singledispatchmethod
    def __init__(self, rank: Card.Ranks, suit: Card.Suits, face_up: bool = False):
        self._kind: Card.Kinds = Card.Kinds(rank, suit)
        self._face_up: bool = face_up

    @singledispatchmethod
    def __init__(self, kind: Card.Kinds, face_up: bool = False):
        self._kind: Card.Kinds = kind
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
        return not self == other

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


class Deck(MutableSequence[Card], FrozenIdentitySet[Card]):
    """A standard 52-card deck.

    Contains a draw pile and a discard pile.

    Once created, Cards always belong to their parent Deck unless they are explicitly deleted with del().

    Cards can be moved from the deck into a hand, but once removed from a hand
    they are automatically returned to the deck's discard pile.

    """

    _new_deck_order: tuple[Kind]  # TODO implement

    # TODO implement overloading __init__ for Kind and Rank, Suit
    # @overload
    # def __init__(self, kind: Kind, face_up: bool = False):
    #     ...
    #
    # @overload
    # def __init__(self, rank: Rank, suit: Suit):
    #     ...
    #
    # def __init__(self, rank: Rank = None, suit: Suit = None, kind: Kind = None):
    #     if rank in Kind:
    #         kind = rank
    #         rank = kind.rank
    #         suit = kind.suit
    #     else:

    _sort_algorithm = sorted  # Override in subclass for HW assignment
    _sort_key =

    def __init__(self, *, sort_key: Callable[[Card, Card], bool]):  # TODO fix sorting function
        """Initialize a deck in new deck order."""
        self._deck = deque[Card](maxlen=52)
        self._discard = deque[Card](maxlen=52)
        self._deck.extend([Card(rank, Card.Suits.SPADES) for rank in Card.Ranks])
        self._deck.extend([Card(rank, Card.Suits.DIAMONDS) for rank in Card.Ranks])
        self._deck.extend(reversed([Card(rank, Card.Suits.HEARTS) for rank in Card.Ranks]))
        self._deck.extend(reversed([Card(rank, Card.Suits.CLUBS) for rank in Card.Ranks]))

        self._all_cards: frozenset[Card] = frozenset(self._all_cards)

    @property
    def cards(self) -> frozenset[Card]:
        return self._cards

    @overload
    @abstractmethod
    def __getitem__(self, index: int) -> Card:
        ...

    @overload
    @abstractmethod
    def __getitem__(self, index: slice) -> Hand:
        ...

    def __getitem__(self, index):
        return self._deck[index]

    @overload
    @abstractmethod
    def __delitem__(self, index: int) -> None: ...

    @overload
    @abstractmethod
    def __delitem__(self, index: slice) -> None: ...

    def __delitem__(self, index):
        pass

    def __setitem__(self, key, value):
        pass

    def insert(self, index, value):
        pass

    def __len__(self):
        pass


class Shoe(Deck):
    """A grouping of multiple 52-card decks treated as one."""

    def __init__(self, num_decks: int):
        super().__init__()
        for i in range(num_decks - 1):
            pass


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
