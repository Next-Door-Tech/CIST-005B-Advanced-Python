from typing import overload
from collections.abc import Hashable, Iterable, MutableSet, Mapping, MutableMapping, Generator
from math import log2, ceil
from .containers import LinkedList


# noinspection PyPep8Naming
class _MISSING_TYPE:
    """A sentinel object to detect if a parameter is supplied or not."""
    pass


_MISSING = _MISSING_TYPE()


class HashTable[T: Hashable]:
    """A hash table which does not implement any 'public' insert/remove API.
    Intended for use as a base class for other HashTable types.
    """

    class Node[U]:
        __slots__ = ('_occupied', '_key', '_floated')

        _occupied: bool
        _key: U
        _floated: int

        @overload
        def __init__(self, key: U, *, floated: int = 0) -> None:
            ...

        @overload
        def __init__(self, /, *, floated: int = 0) -> None:
            ...

        def __init__(self, key: U = _MISSING, *, floated: int = 0) -> None:
            self.floated = floated
            if key is _MISSING:
                self._key = None
                self._occupied = False
            else:
                self._key = key
                self._occupied = True

        @property
        def key(self) -> U:
            return self._key

        def set(self, key: U) -> None:
            """Set the data in the node to the specified state."""
            self._key = key
            self._occupied = True

        def peek(self) -> tuple[U]:
            """Return a tuple which can be unpacked into Node.set() to relocate stored data."""
            return (self._key,)

        def pop(self) -> tuple[U]:
            """Clear the node and return a tuple which can be unpacked into Node.set() to relocate stored data."""
            retval = (self._key,)
            self.clear()
            return retval

        def clear(self) -> None:
            self._key = None
            self._occupied = False

        @property
        def floated(self) -> int:
            return self._floated

        @floated.setter
        def floated(self, value: int) -> None:
            if value < 0:
                raise ValueError(f"{type(self).__qualname__}.floated cannot be negative")
            self._floated = value

        @property
        def occupied(self) -> bool:
            return self._occupied

        def __bool__(self) -> bool:
            return self._occupied or self._floated > 0

        def __contains__(self, key: U) -> bool:
            """Returns whether this Node corresponds to key."""
            return self._occupied and (self._key is key or self._key == key)

    _table: list[Node[T]]

    def __init__(self) -> None:
        self._table = []

    def _hash_key(self, key: T) -> int:
        try:
            return hash(key) % self._maxlen
        except TypeError as e:
            raise TypeError(f"cannot use '{type(key).__name__}' as a {type(self).__name__} key ({e!s})") from e

    @property
    def load_factor(self) -> float:
        if self._maxlen == 0:
            return float('inf')
        else:
            return len(self) / self._maxlen

    @property
    def impacted(self) -> bool:
        return self.load_factor > 0.7

    @property
    def _maxlen(self) -> int:
        if not hasattr(self, '_table'):
            return 0
        return len(self._table)

    @_maxlen.setter
    def _maxlen(self, maxlen: int) -> None:
        maxlen = max(maxlen, len(self), 1)  # disallow setting maxlen to 0 or shrinking below current size
        maxlen = 4 << ceil(log2(maxlen))  # round up to next power of 2 at least 4 times greater than specified

        if maxlen == self._maxlen:
            return
        else:
            self._resize(maxlen)

    def _resize(self, maxlen: int) -> None:
        """Resize self._table to the specified maxlen."""
        buf = (n for n in self._table if n.occupied)  # save reference to original table in generator
        self._table = [self.Node() for _ in range(maxlen)]

        for node in buf:
            start = self._hash_key(node.key)
            hit = self._find_node(node.key)

            self._get_node(hit).set(*(node.peek()))

            for i in range(start, hit):
                self._get_node(i).floated += 1

    def _find_node(self, key: T) -> int:
        """Returns the index of the node matching key if found,
        or the index of the first empty node if not found.

        Guaranteed to return an index >= self._hash_key(key); does not wrap.

        Also performs a cleanup step if a found node can be moved closer to its hash index."""
        start = self._hash_key(key)

        target: None | int = None  # first passed empty node
        for i in range(start, start + self._maxlen):
            n = self._get_node(i)

            if key in n:  # node found
                if target is None:  # no need to reshuffle
                    return i
                else:  # node can be moved closer to its hash value
                    self._get_node(target).set(*(n.pop()))
                    for j in range(target, i):
                        self._get_node(j).floated -= 1
                    return target

            elif not n:  # n is empty and nothing has floated past this node
                return i if target is None else target

            elif not n.occupied and target is None:  # empty node found but need to keep searching
                target = i

        # iterated through all indices without returning, i.e. self._table is full
        if target is not None:
            return target
        else:
            raise KeyError(key)

    def _get_node(self, index: int) -> Node[T]:
        """Returns the Node with the specified index"""
        return self._table[index % self._maxlen]

    def __len__(self) -> int:
        return sum(1 for n in self._table if n.occupied)

    def __iter__(self) -> Generator[T]:
        yield from (n.key for n in self._table if n.occupied)

    def __contains__(self, key: object) -> bool:
        try:
            return key == self._get_node(self._find_node(key)).key
        except (TypeError, ZeroDivisionError):
            return False


class HashSet[T: Hashable](HashTable[T], MutableSet[T]):
    class Node[U](HashTable.Node[U]):
        __slots__ = ()
        pass

    _table: list[Node[T]]

    def __init__(self, iterable: Iterable[T] | None = None) -> None:
        super().__init__()

        self._count: int = 0

        if iterable is not None:
            temp = [*iterable]
            self._maxlen = len(temp)
            for i in iterable:
                self.add(i)

    def add(self, value: T) -> None:
        if self.impacted:
            self._maxlen *= 2

        start = self._hash_key(value)
        hit = self._find_node(value)
        node = self._get_node(hit)

        if value not in node:
            node.set(value)
            for i in range(start, hit):
                self._get_node(i).floated += 1
            self._count += 1

    def remove(self, value: T) -> None:
        start = self._hash_key(value)
        hit = self._find_node(value)
        node = self._get_node(hit)

        if value in node:
            node.clear()
            for i in range(start, hit):
                self._get_node(i).floated -= 1
            self._count -= 1

        else:
            raise KeyError(value)

    def discard(self, value: T) -> None:
        try:
            self.remove(value)
        except KeyError:
            pass

    def clear(self) -> None:
        self._table = []
        self._count = 0

    def __len__(self) -> int:
        return self._count

    def __str__(self) -> str:
        if len(self) > 0:
            return '{' + ', '.join(f'{key!r}' for key in self) + '}'
        else:
            return 'set()'

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({', '.join(f'{key!r}' for key in self)})"


class HashMap[KT: Hashable, VT](HashTable[KT], MutableMapping[KT, VT]):
    class Node[KU: Hashable, VU](HashTable.Node[KU]):
        __slots__ = ('_value',)

        _value: VU

        @overload
        def __init__(self, key: KU, value: VU, *, floated: int = 0) -> None:
            ...

        @overload
        def __init__(self, /, *, floated: int = 0) -> None:
            ...

        def __init__(self, key: KU = _MISSING, value: VU = _MISSING, *, floated: int = 0) -> None:
            self.floated = floated
            if key is _MISSING and value is _MISSING:
                self._key = None
                self._value = None
                self._occupied = False
            elif key is not _MISSING and value is not _MISSING:
                self._key = key
                self._value = value
                self._occupied = True
            else:
                raise TypeError("expected 0 or 2 positional arguments")

        @property
        def key(self) -> KU:
            return self._key

        @property
        def value(self) -> VU:
            return self._value

        @value.setter
        def value(self, value: VU) -> None:
            self._value = value
            self._occupied = True

        # noinspection PyMethodOverriding
        def set(self, key: KU, value: VU) -> None:
            self._key = key
            self._value = value
            self._occupied = True

        def peek(self) -> tuple[KU, VU]:
            """Return a tuple which can be unpacked into Node.set() to relocate stored data."""
            return self._key, self._value

        def pop(self) -> tuple[KU, VU]:
            """Clear the node and return a tuple which can be unpacked into Node.set() to relocate stored data."""
            retval = self._key, self._value
            self.clear()
            return retval

        def clear(self) -> None:
            self._key = None
            self._value = None
            self._occupied = False

    _table: list[Node[KT, VT]]
    _history: LinkedList[KT]

    @overload
    def __init__(self, /) -> None:
        ...

    @overload
    def __init__(self, /, **kwargs: VT) -> None:
        ...

    @overload
    def __init__(self, mapping: Mapping[KT, VT], /, **kwargs: VT) -> None:
        ...

    @overload
    def __init__(self, iterable: Iterable[tuple[KT, VT]], /, **kwargs: VT) -> None:
        ...

    def __init__(self, mapping_or_iterable: Mapping[KT, VT] | Iterable[tuple[KT, VT]] | None = None, /,
                 **kwargs) -> None:
        super().__init__()
        self._history: LinkedList[KT] = LinkedList()  # needed to keep insert order history like dict

        if mapping_or_iterable is None:
            pass
        elif hasattr(mapping_or_iterable, 'keys') and hasattr(mapping_or_iterable, '__getitem__'):
            mapping_or_iterable: Mapping
            for key in mapping_or_iterable.keys():
                self[key] = mapping_or_iterable[key]
        elif hasattr(mapping_or_iterable, '__iter__'):
            mapping_or_iterable: Iterable
            try:
                for i, (key, value) in enumerate(mapping_or_iterable):
                    self[key] = value
            except ValueError as e:
                try:
                    # noinspection PyUnboundLocalVariable
                    i
                except NameError:
                    i = 0

                try:
                    if "values to unpack" in e.args[0]:
                        raise ValueError(f"Iterable element #{i} has incorrect length; 2 is required") from e
                except AttributeError:
                    raise e from None
                else:
                    raise e from None
        else:
            raise TypeError(f"{type(self).__name__} expected a Mapping or Iterable of (key, value) pairs, "
                            f"got '{type(mapping_or_iterable)}'")

        for arg in kwargs:
            self[arg] = kwargs[arg]

    def _resize(self, maxlen: int) -> None:
        buffer = [(key, self[key]) for key in self]
        self._table = [self.Node() for _ in range(maxlen)]
        for key, value in buffer:
            self[key] = value

    def _get_node(self, index: int) -> Node[KT, VT]:  # override return type
        """Returns the Node with the specified index"""
        return self._table[index % self._maxlen]

    def clear(self) -> None:
        self._table = []
        self._history = LinkedList()

    def __getitem__(self, key: KT, /) -> VT:
        n = self._get_node(self._find_node(key))

        if key in n:
            return n.value
        else:
            raise KeyError(key)

    def __setitem__(self, key: KT, value: VT, /) -> None:
        if self.impacted:
            self._maxlen *= 2

        start = self._hash_key(key)
        hit = self._find_node(key)
        node = self._get_node(hit)

        if key in node:
            node.value = value

        else:
            node.set(key, value)
            for i in range(start, hit):
                self._get_node(i).floated += 1
            self._history.append(key)

    def __delitem__(self, key: KT, /) -> None:
        start = self._hash_key(key)
        hit = self._find_node(key)
        node = self._get_node(hit)

        if key in node:
            node.clear()
            for i in range(start, hit):
                self._get_node(i).floated -= 1
            self._history.remove(key)

        else:
            raise KeyError(key)

    def __len__(self) -> int:
        return len(self._history)

    def __iter__(self) -> Generator[KT]:
        yield from self._history

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({', '.join(f'{key!r}: {self[key]!r}' for key in self)})"
