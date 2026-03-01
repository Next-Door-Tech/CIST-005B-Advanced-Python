import unicodedata as ucd
from enum import Enum
from itertools import product
from functools import cached_property
from dataclasses import dataclass, asdict, InitVar, KW_ONLY
from typing import Literal, ClassVar
import re


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


class Card:
    __slots__ = ("_rank", "_suit", "_face_up")

    class Rank(OrderedEnum):
        def __new__(cls, value, symbol: str, char_symbol: str = None):
            self = object.__new__(cls)
            self._value_ = value
            return self

        def __init__(self, value, symbol: str, char_symbol: str = None):
            self.string = self.name.title()
            self._add_alias_(self.string)
            self._add_value_alias_(self.string)

            self.symbol = symbol
            self._add_alias_(self.symbol)
            self._add_value_alias_(self.symbol)

            self.char_symbol = char_symbol or symbol
            self._add_alias_(self.char_symbol)
            self._add_value_alias_(self.char_symbol)

        ACE = 1, 'A'
        TWO = 2, '2'
        THREE = 3, '3'
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

    class Suit(OrderedEnum):
        def __new__(cls, value, symbol: str, char_symbol: str = None):
            self = object.__new__(cls)
            self._value_ = value
            return self

        def __init__(self, value, symbol: str, char_symbol=None):
            self.string = self.name.title()
            self._add_alias_(self.string)  # i.e. Spades
            self._add_alias_(self.string[:-1])  # i.e. Spade
            self._add_value_alias_(self.string)
            self._add_value_alias_(self.string[:-1])

            self.symbol = symbol
            self._add_alias_(self.symbol)
            self._add_value_alias_(self.symbol)

            self.char_symbol = char_symbol or symbol
            self._add_alias_(self.char_symbol)
            self._add_value_alias_(self.char_symbol)

        SPADES = 0, ucd.lookup('BLACK SPADE SUIT') + ucd.lookup('VS15'), 'S'
        HEARTS = 1, ucd.lookup('WHITE HEART SUIT') + ucd.lookup('VS15'), 'H'
        DIAMONDS = 2, ucd.lookup('WHITE DIAMOND SUIT') + ucd.lookup('VS15'), 'D'
        CLUBS = 3, ucd.lookup('BLACK CLUB SUIT') + ucd.lookup('VS15'), 'C'

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

    def __init__(self, rank: Rank, suit: Suit, face_up: bool = True):
        self._rank: Card.Rank = self.Rank(rank)
        self._suit: Card.Suit = self.Suit(suit)
        self._face_up: bool = face_up

    @property
    def suit(self):
        return self._suit

    @property
    def rank(self):
        return self._rank

    @property
    def face_up(self) -> bool:
        return self._face_up

    @face_up.setter
    def face_up(self, value: bool):
        self._face_up = value

    @property
    def face_down(self) -> bool:
        return not self._face_up

    @face_up.setter
    def face_up(self, value: bool):
        self._face_up = not value
        
    def flip(self):
        self._face_up = not self._face_up

    _symbols: dict[tuple[Rank, Suit], str] = {
        (rank, suit): ucd.lookup(f"PLAYING CARD {rank!s} OF {suit!s}") + ucd.lookup('VS15')
        for rank, suit in product(Rank, Suit)
    }
    _back_symbol = ucd.lookup("PLAYING CARD BACK") + ucd.lookup('VS15')

    @property
    def back_symbol(self):
        return self._back_symbol

    @cached_property
    def front_symbol(self):
        return self._symbols[self.rank, self.suit]

    @property
    def symbol(self):
        return self.front_symbol if self.face_up else self.back_symbol

    def __lt__(self, other):
        return self.rank < other.rank or (self.rank == other.rank and self.suit < other.suit)

    def __le__(self, other):
        return self.rank < other.rank or (self.rank == other.rank and self.suit <= other.suit)

    def __ge__(self, other):
        return self.rank > other.rank or (self.rank == other.rank and self.suit > other.suit)

    def __gt__(self, other):
        return self.rank > other.rank or (self.rank == other.rank and self.suit >= other.suit)

    def __eq__(self, other):
        return self.rank, self.suit == other.rank, other.suit

    def __ne__(self, other):
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
