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
