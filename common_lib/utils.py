from typing import Any


class SliceInfo:
    """Prints information about the current slice.

    Usage: SliceInfo[slice](length)"""

    def __init__(self, s: slice, length: int = None) -> None:
        self.s = s
        if length is not None:
            self(length)

    def __class_getitem__(cls, s: slice) -> SliceInfo:
        return SliceInfo(s)

    def __getitem__(self, s: slice) -> SliceInfo:
        self.s = s
        return self

    def __call__(self, length: int) -> None:
        """Prints information about the current slice.

        Usage: SliceInfo[slice](length)"""
        print(f"{self.__class__.__name__}:",
              f"slice: {self.s!r}",
              f"length: {length}",
              f"slice.indices: {self.s.indices(length)}",
              f"indices: {range(length)[self.s]}",
              f"index list: [{", ".join(str(i) for i in range(length)[self.s])}]",
              f"index count: {len(range(length)[self.s])}",
              sep="\n\t", end="\n\n")


class SubscriptInfo:
    def __class_getitem__(cls, item) -> Any:
        return item
