from typing import overload
from common_lib.containers import LinkedList
from collections.abc import MutableMapping, Hashable, Generator
from math import log2, ceil


class HashTable[KT: Hashable, VT](MutableMapping[KT, VT]):
    class Node:
        __slots__ = ('_occupied', '_key', '_value', '_floated')

        _occupied: bool
        _key: KT
        _value: VT
        _floated: int

        @overload
        def __init__(self, key: KT, value: VT, *, floated: int = 0) -> None:
            ...

        @overload
        def __init__(self, /, *, floated: int = 0) -> None:
            ...

        __nothing = object()  # argument sentinel; None is a valid key and value

        def __init__(self, key: KT = __nothing, value: VT = __nothing, *, floated: int = 0) -> None:
            self.floated = floated
            if key is self.__nothing and value is self.__nothing:
                self._key = None
                self._value = None
                self._occupied = False
            elif key is not self.__nothing and value is not self.__nothing:
                self._key = key
                self._value = value
                self._occupied = True
            else:
                raise TypeError("expected 0 or 2 positional arguments")

        @property
        def key(self) -> KT:
            return self._key

        @property
        def value(self) -> VT:
            return self._value

        @value.setter
        def value(self, value: VT) -> None:
            self._value = value
            self._occupied = True

        def set(self, key: KT, value: VT) -> None:
            self._key = key
            self._value = value
            self._occupied = True

        def clear(self) -> None:
            self._key = None
            self._value = None
            self._occupied = False

        @property
        def floated(self) -> int:
            return self._floated

        @floated.setter
        def floated(self, value) -> None:
            if value < 0:
                raise ValueError("HashTable.Node.floated cannot be negative")
            self._floated = value

        @property
        def occupied(self) -> bool:
            return self._occupied

        def __bool__(self) -> bool:
            return self._occupied or self._floated > 0

        def __contains__(self, key: KT) -> bool:
            """Returns whether this Node corresponds to key."""
            return self._occupied and (self._key is key or self._key == key)

    _table: list[Node]
    _history: LinkedList[KT]

    def __init__(self, *args, **kwargs) -> None:
        temp = dict(*args, **kwargs)  # used only for parsing arguments

        self._history: LinkedList[KT] = LinkedList()  # needed to keep insert order history like dict

        if len(temp) > 0:  # if parsed arguments result in a non-empty dict, initialize
            self._maxlen = len(temp)
            for key in temp.keys():
                self[key] = temp[key]

    def _hash(self, key: KT) -> int:
        try:
            return hash(key) % self._maxlen
        except TypeError as e:
            raise TypeError(f"cannot use '{type(key).__name__}' as a {self.__class__.__name__} key ({str(e)})") from e

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
            buffer = [(key, self[key]) for key in self]
            self._table = [self.Node() for _ in range(maxlen)]
            for key, value in buffer:
                self[key] = value

    def _get_node(self, index: int) -> Node:
        return self._table[index % self._maxlen]

    def _find_node(self, key: KT) -> int:
        """Returns the index of the node matching key if found, or the index of the first empty node if not found.
        Guaranteed to return an index >= self._hash(key); does not wrap.

        Also performs a cleanup step if a found node can be moved closer to its hash index."""
        start = self._hash(key)

        target: None | int = None  # first passed empty node
        for i in range(start, start + self._maxlen):
            n = self._get_node(i)

            if key in n:  # node found
                if target is None:  # no need to reshuffle
                    return i
                else:  # node can be moved closer to its hash value
                    self._get_node(target).set(n.key, n.value)
                    n.clear()
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

    def __getitem__(self, key: KT, /) -> VT:
        n = self._get_node(self._find_node(key))

        if key in n:
            return n.value
        else:
            raise KeyError(key)

    def __setitem__(self, key: KT, value: VT, /) -> None:
        if self.impacted:
            self._maxlen *= 2

        start = self._hash(key)
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
        start = self._hash(key)
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
