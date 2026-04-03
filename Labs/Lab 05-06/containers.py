from typing import Self, NoReturn, Literal, Never, cast, overload
from collections import deque
from collections.abc import MutableSequence, Iterable, Collection, Generator
from copy import copy, deepcopy
from abc import ABC


class _CommonMethods[T](Collection[T], ABC):
    @overload
    def _check_index(self, index: int, *, int_only: bool = False) -> int:
        ...

    @overload
    def _check_index(self, index: slice, *, int_only: Literal[False]) -> range:
        ...

    @overload
    def _check_index(self, index: slice, *, int_only: Literal[True]) -> NoReturn:
        ...

    @overload
    def _check_index(self, index: slice, *, int_only: bool = False) -> range | NoReturn:
        ...

    def _check_index(self, index: int | slice, *, int_only: bool = False) -> int | range:
        match index:
            case int() if -len(self) <= index < len(self):
                return index
            case int():
                raise IndexError(f"{type(self)} index out of range")
            case _ if int_only:
                raise TypeError(f"{type(self)} indices must be integers, not '{type(index)}'")
            case slice():
                return range(len(self))[index]
            case _:
                raise TypeError(f"{type(self)} indices must be integers or slices, not '{type(index)}'")

    @overload
    def _check_index_inclusive(self, index: int, *, int_only: bool = False) -> int:
        ...

    @overload
    def _check_index_inclusive(self, index: slice, *, int_only: Literal[False]) -> range:
        ...

    @overload
    def _check_index_inclusive(self, index: slice, *, int_only: Literal[True]) -> NoReturn:
        ...

    @overload
    def _check_index_inclusive(self, index: slice, *, int_only: bool = False) -> range | NoReturn:
        ...

    def _check_index_inclusive(self, index: int | slice, *, int_only: bool = False) -> int | range:
        match index:
            case int() if -len(self) <= index <= len(self):
                return index
            case _:
                return self._check_index(index, int_only=int_only)


class cirque[T](MutableSequence[T], _CommonMethods[T], deque[T]):  # noqa: N802
    """A circular queue, emulated in python."""

    def __new__(cls, maxlen: int = 0, iterable: Iterable[T] = None) -> cirque[T]:
        match maxlen:
            case int(maxlen) if maxlen >= 0:
                return super().__new__(cls)
            case int():
                raise ValueError(f"{cls.__name__} parameter maxlen cannot be negative")
            case _:
                raise TypeError(f"{cls.__name__} parameter maxlen must be an integer, not '{type(maxlen)}'")

    def __init__(self, maxlen: int = 0, iterable: Iterable[T] = None):

        self._array: list[T | None] = [None] * maxlen
        self._len: int = 0
        self._offset: int = 0

        if iterable is not None:
            self.extend(iterable)

    def __len__(self) -> int:
        return self._len

    @property
    def _len(self) -> int:
        return self.__len

    @_len.setter
    def _len(self, value: int) -> None:
        self.__len = min(value, self.maxlen)

    def _array_index(self, index: int) -> int:
        """Normalizes an index into self._array based on self._offset."""
        if self.maxlen != 0:
            return self._offset + index % self.maxlen
        else:
            raise IndexError(f"{type(self)} has maxlen of 0; index out of range")

    @property
    def maxlen(self) -> int:
        return len(self._array)

    @maxlen.setter
    def maxlen(self, value: int) -> None:
        """Resize the cirque to the specified size.

        The final size of the array must not be smaller than the current number of items."""
        try:
            value = int(value)
        except ValueError:
            raise TypeError(f"{self.__class__.__name__} property maxlen must be an integer, not '{type(value)}'")

        if value < 0:
            raise ValueError(f"{self.__class__.__name__} property maxlen cannot be negative")
        if value < len(self):
            raise ValueError(f"shortening {self.__class__.__name__} from {len(self)} to {value} would delete items")

        delta = value - self.maxlen

        if delta == 0:  # do nothing
            return

        elif delta > 0:  # extending
            if not self._wraps:
                self._array += [None] * delta  # quick extend
            else:
                self._array[self._offset:self._offset] = [None] * delta
                self._offset += delta

        else:  # truncating
            delta *= -1
            if self._offset + len(self) < self.maxlen:
                tail = min(delta, max(self.maxlen - len(self) - self._offset, 0))
                del self._array[-tail:]  # delete as many empty slots from the end as possible/needed
                delta -= tail
            del self._array[self._offset - delta:self._offset]
            self._offset -= delta

    @property
    def full(self) -> bool:
        return len(self) >= self.maxlen

    @property
    def _offset(self) -> int:
        """The offset of the first filled data element in self._array."""
        return self.__offset

    @_offset.setter
    def _offset(self, value: int) -> None:
        """Allows naively setting _offset without checking if the new value would fall off the end of the array."""
        if self.maxlen != 0:
            self.__offset = value % self.maxlen
        else:
            self.__offset = 0

    @property
    def _wraps(self) -> bool:
        return self._offset + self._len > self.maxlen

    def append(self, value: T) -> None:
        """Insert value into the cirque after the current last element."""
        self._array[self._array_index(self._len)] = value
        self._len += 1

    def prepend(self, value: T) -> None:
        """Insert value into the cirque before the current first element."""
        self._array[self._array_index(-1)] = value
        self._offset -= 1
        self._len += 1

    appendleft = prepend  # alias to match naming convention of collections.deque

    def count(self, value: T) -> int:
        return super().count(value)

    def extend(self, iterable: Iterable[T]) -> None:
        """Extends the cirque by appending each value in iterable."""
        if iterable is self or iterable is self._array:
            iterable = list(iterable)
        for value in iterable:
            self.append(value)

    def extendleft(self, iterable: Iterable[T]) -> None:
        """Extends the cirque by prepending each value in iterable.

        Note that this effectively reverses the order of items in iterable.
        If this behavior is unwanted, use `cirque[:0] = list(iterable)` instead."""
        if iterable is self or iterable is self._array:
            iterable = list(iterable)
        for value in iterable:
            self.prepend(value)

    def insert(self, index: int, value: T) -> None:
        """Inserts value into self before index, as if by shifting self[index:] forward by 1 if necessary."""
        index = self._check_index_inclusive(index, int_only=True)

        if index == 0:
            self.prepend(value)
        elif index == self._len:
            self.append(value)
        elif index <= self._len // 2:  # shifting self[:index] left is fastest
            for i in range(int(self.full), index):  # last becomes first if full; do not overwrite last
                self._array[self._array_index(i - 1)] = self._array[self._array_index(i)]
            self._offset -= 1
            self._len += 1
        else:  # shifting self[index:] right is fastest
            for i in reversed(range(index, len(self))):
                self._array[self._array_index(i + 1)] = self._array[self._array_index(i)]
            self._len += 1

    def index(self, value: T, start: int = 0, stop: int = None, /) -> int:
        return super().index(value, start, stop)

    def remove(self, value: T) -> None:
        del self[self.index(value)]

    def pop(self, index: int = -1) -> T:
        value = self[index]
        del self[index]
        return value

    def popleft(self, index: int = 0) -> T:
        return self.pop(index)

    def rotate(self, count: int = 1) -> None:
        """Performs a rotation of the members of self."""
        if len(self) == 0:
            return  # rotating [] does nothing and x % 0 throws error

        count %= len(self)

        if count == 0:
            return
        elif self.full:
            self._offset += count
        elif count < len(self) // 2:  # rotate right
            for _ in range(count):
                self.prepend(self.pop(-1))  # move last item to before first
        else:  # rotate left
            for _ in range(len(self) - count):
                self.append(self.pop(0))  # move first item after last index

    def __lshift__(self, n: int) -> None:
        self.rotate(-n)

    def __rshift__(self, n: int) -> None:
        self.rotate(n)

    @overload
    def __getitem__(self, index: int) -> T:
        ...

    @overload
    def __getitem__(self, index: slice) -> list[T]:
        ...

    def __getitem__(self, index: int | slice) -> T | list[T]:
        match self._check_index(index):
            case int(index):
                return self._array[self._array_index(index)]
            case range() as indices:
                return [self._array[self._array_index(i)] for i in indices]

        raise RuntimeError("This point should be unreachable.")

    @overload
    def __setitem__(self, index: int, value: T) -> None:
        ...

    @overload
    def __setitem__(self, index: slice, value: Iterable[T]) -> None:
        ...

    def __setitem__(self, index: int | slice, value: T | Iterable[T]) -> None:
        match self._check_index(index):
            case int(index):
                self._array[self._array_index(index)] = value
            case range() as indices:
                start, stop, step = index.indices(len(self))
                if step == 1:
                    tail = self[stop:]
                    del self[start:]
                    self.extend(value)
                    self.extend(tail)

                else:  # extended slice, check that length of slice and iterable are the same
                    if not hasattr(value, '__len__') or value is self or value is self._array:
                        value = list(value)

                    if len(value) != len(indices):
                        raise ValueError(
                            f"attempt to assign sequence of size {len(value)} to extended slice of size {len(indices)}"
                        )
                    else:
                        for i, v in zip(indices, value):
                            self._array[self._array_index(i)] = v

    @overload
    def __delitem__(self, index: int) -> None:
        ...

    @overload
    def __delitem__(self, index: slice) -> None:
        ...

    def __delitem__(self, index) -> None:
        match self._check_index(index):
            case int(index):
                if index == 0:  # first item
                    self._array[self._offset] = None
                    self._offset += 1
                    self._len -= 1
                    return

                elif index == len(self) - 1:  # last item
                    self._array[self._array_index(index)] = None
                    self._len -= 1
                    return

                elif index <= self._len // 2:  # shifting self[1:index] right is fastest
                    for i in reversed(range(1, index)):
                        self._array[self._array_index(i)] = self._array[self._array_index(i - 1)]
                    self._array[self._offset] = None
                    self._offset += 1
                    self._len -= 1
                    return

                else:  # shifting self[index+1:] left is fastest
                    for i in range(index, len(self) - 1):
                        self._array[self._array_index(i)] = self._array[self._array_index(i + 1)]
                    self._array[self._array_index(len(self) - 1)] = None
                    self._len -= 1
                    return

            case range() as indices:
                if len(indices) == 0:
                    return

                elif len(indices) == len(self):
                    for i in range(len(self)):
                        self._array[self._array_index(i)] = None
                    self._len = 0
                    return

                elif abs(indices.step) == 1:  # slice is contiguous
                    count = len(indices)
                    if min(indices) < len(self) - (max(indices) + 1):  # _head section is shortest
                        for i in reversed(range(min(indices))):
                            self._array[self._array_index(i + count)] = self._array[self._array_index(i)]
                        for i in range(count):
                            self._array[self._array_index(i)] = None
                        self._offset += count
                        self._len -= count

                    else:  # tail section is shortest
                        for i in range(max(indices) + 1, len(self)):
                            self._array[self._array_index(i - count)] = self._array[self._array_index(i)]
                        for i in range(count):
                            self._array[len(self) - count + i] = None
                        self._len -= count

                else:
                    for i in indices:
                        del self[i]  # TODO optimize to minimize number of array shifts

    def copy(self) -> Self:
        return copy(self)

    def __iter__(self) -> Generator[T]:  # FIXME not safe if cirque is mutated during iteration
        for i in range(len(self)):
            yield self[i]

    def __copy__(self) -> Self:
        new = self.__class__()
        new._array = copy(self._array)
        new._len = self._len
        new._offset = self._offset

        return new

    def __deepcopy__(self, memo) -> Self:
        new = self.__class__(0)
        new._array = deepcopy(self._array, memo)
        new._len = self._len
        new._offset = self._offset

        return new

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(maxlen={self.maxlen}, [{", ".join(repr(i) for i in self)}])"


class LinkedList[T](MutableSequence[T], _CommonMethods[T]):
    class Node(Collection):
        __slots__ = '_value', '_forward', '__weakref__'

        type Node = LinkedList.Node

        _forward: Node

        def __init__(self, value: T, forward: Node = None):
            self._value: T = value
            self.forward = forward

        @property
        def value(self) -> T:
            return self._value

        @value.setter
        def value(self, value: T) -> None:
            self._value = value

        @property
        def forward(self) -> Node:
            return self._forward

        @forward.setter
        def forward(self, node: Node) -> None:
            self._forward = node
            if hasattr(node, 'tail'):  # if this is now a tail node
                node.tail = self

        @forward.deleter
        def forward(self) -> None:
            if self.forward is None:
                raise IndexError(f"{self.__class__.__qualname__} already points to None")
            self.forward = self.forward.traverse(1)

        def splice(self, chain_head: Node, chain_tail: Node = None) -> None:
            """Splices provided node chain in between self and self.forward.

            If node_chain has an infinite loop, the loop is first cut after the last unique node.
            If the tail node of the chain is already known, it may be supplied as an optimization.
            """
            if chain_tail is None:
                chain_tail = chain_head.get_tail()

            chain_tail.forward = self.forward
            self.forward = chain_head

        def insert(self, value: T) -> None:
            """Inserts value as a new node after this one."""
            self.forward = LinkedList.Node(value, self.forward)

        def inject(self, iterable: Iterable[T]) -> None:
            """Inserts the values in iterable as new nodes after this one.

            Roughly equivalent to calling self.splice(self.from_iterable(iterable))"""
            self.splice(*self.from_iterable(iterable, return_tail=True))

        def traverse(self, count: int) -> Node:  # Recursive traverse
            if count < 0:
                raise IndexError(f"{self.__class__.__qualname__} does not support negative indices")

            elif count == 0:
                return self

            elif self.forward is not None:
                return self.forward.traverse(count - 1)

            else:
                raise IndexError(f"End of forward reference chain reached with {count} indices remaining.")

        def get_tail(self) -> Node:
            """Returns the last regular node in the chain.
            If the node points to a circular loop, returns the last unique node found.
            Ignores a trailing sentinel node, if present."""
            tail = self
            memo = {id(self)}

            while tail.forward and id(tail.forward) not in memo:
                tail = tail.forward
                memo.add(id(tail))

            return tail

        @overload
        @classmethod
        def from_iterable(cls, iterable: Iterable[T], *, return_tail: Literal[False]) -> Node:
            ...

        @overload
        @classmethod
        def from_iterable(cls, iterable: Iterable[T], *, return_tail: Literal[True]) -> tuple[Node, Node]:
            ...

        @overload
        @classmethod
        def from_iterable(cls, iterable: Iterable[T], *, return_tail: bool = False) -> Node | tuple[Node, Node]:
            ...

        @classmethod
        def from_iterable(cls, iterable: Iterable[T], *, return_tail: bool = False) -> Node | tuple[Node, Node]:
            try:
                head = tail = cls(next(i := iter(iterable)))
            except StopIteration as e:
                raise ValueError(f'iterable raised StopIteration without returning at least one value') from e

            for value in i:
                tail.forward = cls(value)
                tail = tail.forward

            if return_tail:
                return head, tail
            else:
                return head

        def __iter__(self) -> Generator[Node]:
            yield self
            if self.forward is not None:
                yield from self.forward

        def __contains__(self, item: T) -> bool:
            return self.value is item or self.value == item

        def __str__(self) -> str:
            return f"<{self.__class__.__name__}({self.value!s})> --> {self.forward!s}"

        def __repr__(self) -> str:
            return f"{self.__class__.__qualname__}({self.value!r}, {self.forward!r})"

        def __len__(self, /, *, _memo: set[int] = None) -> int:
            if self.forward is None:
                return 1

            if _memo is None:
                _memo = {id(self)}
            else:
                _memo.add(id(self))

            if id(self.forward) in _memo:
                raise RecursionError(f"{self.__class__.__qualname__}: forward reference chain has an infinite loop.")
            else:
                return 1 + self.forward.__len__(_memo=_memo)

        def __bool__(self) -> bool:
            """Returns whether the node is normal and can be traversed."""
            return True

        def __gt__(self, other: Node | None, /, *, _memo: set[int] = None) -> bool:
            """Returns whether other is in this node's chain of forward references."""

            if self.forward is other:
                return True
            elif self.forward is None:
                return False  # if other is None, `self.forward is other` returns True first
            else:
                if _memo is None:
                    _memo = {id(self)}
                else:
                    _memo.add(id(self))

                if id(self.forward) in _memo:  # we have previously visited self.forward without finding other
                    return False  # do not enter infinite loop
                else:
                    return self.forward.__gt__(other, _memo=_memo)

        def __ge__(self, other: Node) -> bool:
            """Returns whether other is self or other is in this node's chain of forward references."""
            return other is self or self > other

        _shallow_copy_flag = object()

        def __copy__(self) -> Self:
            # uses deepcopy because nodes could theoretically link to themselves, as well as to handle Sentinel
            return deepcopy(self, memo={cast(int, self._shallow_copy_flag): True})

        def __deepcopy__(self, memo) -> Self:
            if id(self) in memo:
                return memo[id(self)]

            new = self.__class__(None)  # delay assignment of new.value
            memo[id(self)] = new

            if self._shallow_copy_flag in memo:
                new.value = self.value
            else:
                new.value = deepcopy(self.value, memo)

            new.forward = deepcopy(self.forward, memo)

            return new

    class Sentinel(Node):
        __slots__ = '_tail'

        type Node = LinkedList.Node
        _tail: Node

        def __init__(self) -> None:
            super().__init__(value=None, forward=self)
            self._forward = self
            self._tail = self

        value = property(doc=f"{__qualname__} cannot hold a value.")

        @property
        def head(self) -> Node:
            return self._forward

        @head.setter
        def head(self, node: Node) -> None:
            if node is self or node is None:
                self.clear()
                return

            if node.forward is None or node.forward is self._forward:
                if self._tail is self:
                    self._tail = node

                node.forward = self._forward
                self._forward = node
            else:
                chain_tail = node.get_tail()

                if chain_tail.forward is self:
                    self._forward = node
                else:
                    chain_tail.forward = self._forward
                    self._forward = node

            if self._tail is self:
                self._tail = node

        @head.deleter
        def head(self) -> None:
            if self.head is self:
                raise IndexError(f"{self.__class__.__qualname__} has an empty chain")
            else:
                self.head = self.head.traverse(1)

        forward = property(head.fget, head.fset, head.fdel, "Alias for head.")

        @property
        def tail(self) -> Node:
            return self._tail

        @tail.setter
        def tail(self, node: Node) -> None:
            """Splices node in at tail. If node is already part of the chain, do nothing.

            Note that if len(node) > 1, traversing the whole chain to check for the above condition is required."""
            if node is self or node is None:
                self.clear()

            elif node is self._tail:  # quick check for node already being in the chain
                return

            elif not node.forward:  # node.forward is none or is a sentinel
                self._tail.forward = node
                self._tail = node
                node.forward = self  # this recursively calls self.tail.setter, but `elif node is self._tail` catches it

            elif not self > node:  # expensive check that node is not already in chain
                chain_tail = node.get_tail()
                self._tail.forward = node
                self._tail = chain_tail
                chain_tail.forward = self

        def splice(self, node_chain: Node, chain_tail: Node = None) -> None:
            """Splices provided node chain in between self and self.head. chain_tail is ignored.

            If node_chain has an infinite loop, the loop is first cut after the last unique node."""
            self.head = node_chain

        def splice_tail(self, node_chain: Node) -> None:
            """Splices provided node chain in between self.tail and self.

            If node_chain has an infinite loop, the loop is first cut after the last unique node.
            If self > node_chain, this does nothing."""
            self.tail = node_chain

        def get_tail(self) -> Node:
            return self.tail

        def clear(self) -> None:
            self._forward = self
            self._tail = self

        def traverse(self, count: int, *, recursive_call: bool = True) -> Node:  # Recursive traverse
            if count == 0:
                return self
            elif recursive_call:
                raise IndexError(f"cannot traverse past {self.__class__.__name__} ({count} indices remaining)")
            else:
                return super().traverse(count)

        def __iter__(self) -> Generator[Never]:
            yield from ()  # stop iterating when sentinel is reached

        def __str__(self) -> str:
            return f"<{self.__class__.__name__}>"

        def __repr__(self) -> str:
            return f"{self.__class__.__qualname__}()"

        def __gt__(self, other: Node, /, *, _memo=None) -> bool:
            if _memo is not None:  # if we are calling __gt__ recursively, we have reached the end of the chain
                return False
            else:
                return super().__gt__(other, _memo=set())

        def __len__(self, /, *, _memo: set[int] = None) -> int:
            if self.head is self or _memo is not None:
                return 0  # if we are calling __len__ recursively, we have reached the end of the chain
            else:
                return self.head.__len__(_memo=set())

        def __bool__(self) -> bool:
            return False

        def __deepcopy__(self, memo) -> Self:
            if id(self) in memo:
                return memo[id(self)]

            new = self.__class__()
            memo[id(self)] = new

            if self.tail is self:
                new.tail = new
            else:
                new.tail = deepcopy(self.tail, memo)

            return new

    _sentinel: Sentinel
    _count: int

    def __init__(self, iterable: Iterable[T] = None) -> None:
        self._count = 0
        self._sentinel = self.Sentinel()

        if iterable is not None:
            self.extend(iterable)

    @property
    def _head(self) -> Node:
        return self._sentinel.head

    @_head.setter
    def _head(self, node: Node | None) -> None:
        """Splice the specified node chain in at _head."""
        if not isinstance(node, self.Node | None):
            raise TypeError(
                f"{self.__class__.__qualname__}._head must be '{type(self.Node).__qualname__}', not '{type(node)}'"
            )

        count = int(bool(node))  #
        if not (node >= self._head or node >= self._sentinel):
            for tail in node:

                if tail.next is None or tail.next is node:
                    tail.next = None
        self._head = node

    @_head.deleter
    def _head(self) -> None:
        try:
            del self._sentinel.head
            self._count -= 1
        except IndexError:
            raise IndexError(f"{self.__class__.__qualname__} is already empty")

    @property
    def _tail(self) -> Node:
        return self._sentinel.tail

    @_tail.setter
    def _tail(self, node: Node) -> None:
        self._sentinel.tail = node

    def append(self, value: T) -> None:
        """Append value to the end of the list."""
        self._tail.insert(value)
        self._count += 1

    def prepend(self, value: T) -> None:
        """Prepend value to the beginning of the list."""
        self._sentinel.insert(value)
        self._count += 1

    append_left = prepend

    def insert(self, index: int, value: T) -> None:
        """Insert the value into the list before the given index.

        :param index:
        :param value:
        :return:
        """
        self._check_index_inclusive(index, int_only=True)

        if index == 0 or index == -len(self):
            self.prepend(value)
        elif index == len(self):
            self.append(value)
        else:
            self._sentinel.traverse(index % len(self) - 1, recursive_call=False).insert(value)

        self._count += 1

    def extend(self, iterable: Iterable[T]) -> None:
        """Extend the list with the contents of iterable.

        This is the same as writing `for i in iterable: list.append(i)`.

        :param iterable: The iterable from which to extend the list.
        :return:
        """

        for item in iterable:
            self.append(item)

    def extend_left(self, iterable: Iterable[T]) -> None:
        """Extend the list with the contents of iterable before the beginning.

        This is the same as writing `for i in iterable: list.prepend(i)`.

        :param iterable: The iterable from which to extend the list.
        :return:
        """

        for item in iterable:
            self.prepend(item)

    def inject(self, index: int, iterable: Iterable[T]) -> None:
        """Insert all members of iterable before the given index."""
        self._check_index_inclusive(index, int_only=True)

        if index == 0 or index == -len(self):
            self._sentinel.inject(iterable)
        elif index == len(self):
            self._tail.inject(iterable)
        else:
            self._head.traverse(index % len(self) - 1).inject(iterable)

        self._count += 1

    def pop(self, index: int = 0) -> T:
        return super().pop(index)

    def index(self, value: T, start: int = 0, stop: int = None) -> int:
        """S.index(value, [start, [stop]]) -> int -- return first index of value.

        Raises ValueError if the value is not present.
        :param value: The value to search for.
        :param start: The index to start searching at. Defaults to 0.
        :param stop: The index to stop searching at. If not supplied, the search will stop at the end of the list.
        :return: The first index of value.
        """

        if start is not None and start < 0:
            start = max(len(self) + start, 0)

        if stop is not None and stop < 0:
            stop += len(self)
        elif stop is None:
            stop = len(self)

        i = 0
        for node in self._head:
            if i >= stop:
                break

            if i >= start and value in node:
                return i

            i += 1

        raise ValueError

    def remove(self, value: T) -> None:
        for node in self._head:
            if value in node.forward:
                del node.forward
                return

        raise ValueError(f"value {value!r} not found")

    def reverse(self) -> None:
        """
        Reverse the items of sequence in place.

        This method maintains economy of space when reversing a large sequence.
        To remind users that it operates by side effect, it returns None.

        :return:
        """

        cursor = self._head.forward
        self._head.forward = self._sentinel

        while cursor is not self._sentinel:
            fwd = cursor.forward
            cursor.forward = self._head
            self._head = cursor
            cursor = fwd

    def __len__(self) -> int:
        assert self._count == len(self._sentinel)
        return self._count

    @overload
    def __getitem__(self, index: int) -> T:
        ...

    @overload
    def __getitem__(self, index: slice) -> list:
        ...

    def __getitem__(self, index: int | slice) -> T | list:
        match self._check_index(index):
            case int() if index == -1 or index == len(self) - 1:
                return self._tail.value

            case int():
                return self._head.traverse(index % len(self)).value

            case range() as indices:
                indices: range  # type checker thinks indices is Never

                i = min(indices)
                cursor = self._head.traverse(i)

                retval = []

                while i <= max(indices):
                    retval.append(cursor.value)
                    cursor = cursor.traverse(abs(indices.step))
                    i += abs(indices.step)

                if index.step < 0:
                    retval.reverse()

                return retval

    @overload
    def __setitem__(self, index: int, value: T) -> None:
        ...

    @overload
    def __setitem__(self, index: slice, value: Iterable[T]) -> None:
        ...

    def __setitem__(self, index: int | slice, value: T | Iterable[T]) -> None:
        match self._check_index(index):
            case int() if index == -1 or index == len(self) - 1:
                self._tail.value = value

            case int():
                self._head.traverse(index % len(self)).value = value

            case range():
                raise NotImplementedError  # TODO

    @overload
    def __delitem__(self, index: int) -> None:
        ...

    @overload
    def __delitem__(self, index: slice) -> None:
        ...

    def __delitem__(self, index: int | slice) -> None:
        match self._check_index(index):
            case 0:
                del self._head
                self._count -= 1
            case int():
                del self._head.traverse(index - 1).forward
                self._count -= 1
            case range() as indices:
                if index.step == 1 or index.step == -1:
                    # TODO optimize for continuous ranges
                    pass

                else:
                    for i in sorted(indices, reverse=True):
                        del self[i]

    def __iter__(self) -> Generator[T]:
        for node in self._head:
            yield node.value

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}({self!s})"

    def __str__(self) -> str:
        return "[" + ", ".join(str(item) for item in self) + "]"


class LinkedStack[T](LinkedList[T]):
    def push(self, value: T) -> None:
        self.prepend(value)

    def peek(self) -> T:
        return self[0]

    def is_empty(self) -> bool:
        return len(self) == 0


class LinkedQueue[T](LinkedList[T]):
    def enqueue(self, item: T) -> None:
        self.append(item)

    def dequeue(self) -> T:
        return self.pop(0)

    def is_empty(self) -> bool:
        return len(self) == 0
