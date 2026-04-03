from collections.abc import Set, MutableSet


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
