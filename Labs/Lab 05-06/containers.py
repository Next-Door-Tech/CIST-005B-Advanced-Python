from typing import Self, overload
from collections.abc import MutableSequence, Iterable, Container, Collection
from copy import copy, deepcopy
from abc import ABC


class _CommonMethods(Collection, ABC):
    def _check_index(self, index: int | slice, *, int_only: bool = False) -> int | range:
        match index:
            case int() if -len(self) <= index < len(self):
                return index
            case int():
                raise IndexError(f"{type(self)} index out of range")
            case slice() if not int_only:
                return range(len(self))[index]
            case _ if not int_only:
                raise TypeError(f"{type(self)} indices must be integers or slices, not '{type(index)}'")
            case _:
                raise TypeError(f"{type(self)} indices must be integers, not '{type(index)}'")

    def _check_index_inclusive(self, index: int | slice, *, int_only: bool = False) -> int | range:
        match index:
            case int() if -len(self) <= index <= len(self):
                return index
            case _:
                return self._check_index(index, int_only=int_only)


class cirque[T](MutableSequence[T], _CommonMethods):  # noqa: N802
    """A circular queue, emulated in python."""

    def __new__(cls, max_len: int = 0, iterable: Iterable[T] = None) -> cirque[T]:
        match max_len:
            case int(max_len) if max_len >= 0:
                return super().__new__(cls)
            case int():
                raise ValueError(f"{cls.__name__} parameter max_len cannot be negative")
            case _:
                raise TypeError(f"{cls.__name__} parameter max_len must be an integer, not '{type(max_len)}'")

    def __init__(self, max_len: int = 0, iterable: Iterable[T] = None):

        self._array: list[T] = [None] * max_len
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
        self.__len = min(value, self.max_len)

    def _array_index(self, index: int) -> int:
        """Normalizes an index into self._array based on self._offset."""
        if self.max_len != 0:
            return self._offset + index % self.max_len
        else:
            raise IndexError(f"{type(self)} has max_len of 0; index out of range")

    @property
    def max_len(self) -> int:
        return len(self._array)

    @max_len.setter
    def max_len(self, value: int) -> None:
        """Resize the cirque to the specified size.

        The final size of the array must not be smaller than the current number of items."""
        try:
            value = int(value)
        except ValueError:
            raise TypeError(f"{self.__class__.__name__} property max_len must be an integer, not '{type(value)}'")

        if value < 0:
            raise ValueError(f"{self.__class__.__name__} property max_len cannot be negative")
        if value < len(self):
            raise ValueError(f"shortening {self.__class__.__name__} from {len(self)} to {value} would delete items")

        delta = value - self.max_len

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
            if self._offset + len(self) < self.max_len:
                tail = min(delta, max(self.max_len - len(self) - self._offset, 0))
                del self._array[-tail:]  # delete as many empty slots from the end as possible/needed
                delta -= tail
            del self._array[self._offset - delta:self._offset]
            self._offset -= delta

    def full(self) -> bool:
        return len(self) >= self.max_len

    @property
    def _offset(self) -> int:
        """The offset of the first filled data element in self._array."""
        return self.__offset

    @_offset.setter
    def _offset(self, value: int) -> None:
        """Allows naively setting _offset without checking if the new value would fall off the end of the array."""
        if self.max_len != 0:
            self.__offset = value % self.max_len
        else:
            self.__offset = 0

    def _wraps(self) -> bool:
        return self._offset + self._len > self.max_len

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
            for i in range(int(self.full()), index):  # last becomes first if full; do not overwrite last
                self._array[self._array_index(i - 1)] = self._array[self._array_index(i)]
            self._offset -= 1
            self._len += 1
        else:  # shifting self[index:] right is fastest
            for i in reversed(range(index, len(self))):
                self._array[self._array_index(i + 1)] = self._array[self._array_index(i)]
            self._len += 1

    def index(self, x: T, start: int = 0, stop: int = None, /) -> int:
        return super().index(x, start, stop)

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
        elif self.full():
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
    def __getitem__(self, index: slice) -> Self:
        ...

    def __getitem__(self, index: int | slice) -> T | list[T]:
        match self._check_index(index):
            case int(index):
                return self._array[self._array_index(index)]
            case range(indices):
                return [self._array[self._array_index(i)] for i in indices]

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
            case range(indices):
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

            case range(indices):
                if len(indices) == 0:
                    return

                elif len(indices) == len(self):
                    for i in range(len(self)):
                        self._array[self._array_index(i)] = None
                    self._len = 0
                    return

                elif abs(indices.step) == 1:  # slice is contiguous
                    count = len(indices)
                    if min(indices) < len(self) - (max(indices) + 1):  # head section is shortest
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
        return f"{self.__class__.__name__}(max_len={self.max_len}, [{", ".join(repr(i) for i in self)}])"


class Node[T](Iterable[T], Container[T]):
    __slots__ = ('_value', '_forward', '__weakref__')

    def __init__(self, value: T, forward: Self = None):
        self._value: T = value
        self._forward: Self = forward

    @property
    def value(self) -> T:
        return self._value

    @value.setter
    def value(self, value: T):
        self._value = value

    @property
    def forward(self) -> Self:
        return self._forward

    @forward.setter
    def forward(self, node: Self):
        self._forward = node

    @forward.deleter
    def forward(self):
        self.forward = self._forward.traverse(1)
        if hasattr(self._forward, 'tail'):  # if this is now a tail node
            self._forward.tail = self

    def traverse(self, count: int) -> Self:  # Recursive traverse
        if count == 0:
            return self

        elif count < 0:
            raise IndexError(f"{type(self)} does not support negative indices")

        elif self.forward is not None:
            return self.forward.traverse(count - 1)

        elif self.forward is None and count == 1:
            return None

        else:
            raise IndexError(f"End of Node chain reached with {count} indices remaining.")

    @classmethod
    def from_iterable(cls, iterable: Iterable[T]) -> Node[T]:
        i = iter(iterable)
        head = tail = Node(next(i))
        for value in i:
            tail.forward = Node(value)
            tail = tail.forward
        return head

    def __iter__(self):
        yield self
        if self.forward is None:
            raise StopIteration
        yield from self.forward

    def __contains__(self, item: T) -> bool:
        return self.value is item or self.value == item

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return f"<{self.__class__.__qualname__}: {repr(self.value)}> --> {repr(self.forward)}"

    def __gt__(self, other: Node) -> bool:
        """Returns whether other is eventually pointed to by self.forward"""
        if self.forward is other:
            return True
        elif self.forward is None:
            return False
        else:
            return self.forward > other

    def __ge__(self, other: Node) -> bool:
        """Returns whether other is self or is eventually pointed to by self.forward"""
        if self is other or self.forward is other:
            return True
        elif self.forward is None:
            return False
        else:
            return self.forward >= other

    def __lt__(self, other) -> bool:
        raise NotImplementedError

    def __le__(self, other) -> bool:
        raise NotImplementedError

    # def __copy__(self) -> Self:
    #     return Node(self.value, copy(self.forward))
    #
    # def __deepcopy__(self, memo) -> Self:
    #     return Node(deepcopy(self.value, memo), deepcopy(self.forward, memo))


class Sentinel(Node):
    # __slots__ = ('_head', '_tail')

    def __init__(self):
        super().__init__(value=None, forward=None)
        self._head: Node = self
        self._tail: Node = self

    @property
    def value(self):
        raise TypeError(f"{type(self)} cannot hold a value.")

    @value.setter
    def value(self, value):
        raise TypeError(f"{type(self)} cannot hold a value.")

    @property
    def head(self) -> Node:
        return self._head

    @head.setter
    def head(self, node: Node) -> None:
        if node is self:
            self._head = self._tail = self
        elif self._head is self and self._tail is self:
            self._head = self._tail = node
        elif node.forward is None or node.forward is self._head:
            node.forward = self._head
            self._head = node
        else:
            t = node
            while not (any(t.forward is x for x in (None, self._head, node))
                       or isinstance(t.forward, type(self))):
                t = t.forward

            t.forward = self._head
            self._head = node

            assert self._head >= self, "Sentinel chain is not closed after assignment."

    @head.deleter
    def head(self):
        if self.head is not self:
            self.head = self.head.traverse(1)  # call head.setter; performs checks
        else:
            raise IndexError(f"{type(self)} already points to an empty chain")

    forward = head

    @property
    def tail(self):
        return self._tail

    @tail.setter
    def tail(self, node: Node):
        if node is self:
            self._head = self._tail = self

        elif self._head is self and self._tail is self:
            self._head = self._tail = node
            self._tail.forward = self

        else:
            self._tail.forward = node
            self._tail = node
            self._tail.forward = self

        # assert self._head >= self, "Sentinel chain is not closed after assignment."

    def traverse(self, count: int) -> Node:  # Recursive traverse
        if count == 0:
            return self
        else:
            raise IndexError(f"{type(self)} reached with {count} indices remaining.")

    def __iter__(self):
        raise StopIteration

    def __reversed__(self):
        raise StopIteration

    def __repr__(self):
        return f"<{self.__class__.__qualname__}>"


class LinkedList[T](MutableSequence[T], _CommonMethods):
    __slots__ = ('_sentinel', '_count', "__weakref__")

    _sentinel: Sentinel
    _count: int

    def __init__(self, data: Iterable[T] = None):
        self._count = 0
        if not hasattr(self, '_sentinel'):
            self._sentinel = Sentinel()

        if data is not None:
            self.extend(data)

    @property
    def head(self) -> Node:
        return self._sentinel.head

    @head.setter
    def head(self, node: Node) -> None:
        self._sentinel.head = node

    @head.deleter
    def head(self) -> None:
        del self._sentinel.head
        self._count -= 1

    @property
    def tail(self) -> Node:
        return self._sentinel.tail

    @tail.setter
    def tail(self, node: Node) -> None:
        self._sentinel.tail = node

    @tail.deleter
    def tail(self) -> None:
        if len(self) == 1:
            del self.head
        else:
            del self.head.traverse(len(self) - 2).forward
        self._count -= 1

    def append(self, value: T) -> None:
        """Append value to the end of the list."""
        self.insert(len(self), value)

    def prepend(self, value: T) -> None:
        """Prepend value to the beginning of the list."""
        self.insert(0, value)

    append_left = prepend

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

    def insert(self, index: int, value: T) -> None:
        """Insert the value into the list before the given index.

        :param index:
        :param value:
        :return:
        """

        match index:
            case 0:
                self.head = Node(value, self.head.forward)
            case int() if index == len(self):
                self.tail = Node(value, self.tail.forward)
            case int() if -len(self) <= index < len(self):
                index %= len(self)
                cur = self.head.traverse(index - 1)
                cur.forward = Node(value, cur.forward)
            case int():
                raise IndexError(f"{type(self)} index out of range")
            case _:
                raise TypeError(f"{type(self)}.insert() indices must be integers, not '{type(index)}'")

        self._count += 1

    def inject(self, index: int, iterable: Iterable[T]) -> None:
        """Insert all members of iterable before the given index."""
        match index:
            case 0:
                cur = self.head
                for value in iterable:
                    cur.head = Node(value, self.head.forward)

            case int() if index == len(self):
                for value in iterable:
                    self.tail.forward = Node(value, self._sentinel)
                    self._count += 1

            case int() if -len(self) <= index < len(self):
                index %= len(self)
                cur = self.head.traverse(index - 1)
                for value in iterable:
                    cur.forward = Node(value, cur.forward)
                    cur = cur.forward
                    self._count += 1

            case int():
                raise IndexError(f"{type(self)} index out of range")

            case _:
                raise TypeError(f"{type(self)}.insert() indices must be integers, not '{type(index)}'")

    def pop(self, index: int = 0) -> T:
        val = super().pop(index)
        self._count -= 1
        return val

    def push(self, value: T) -> None:
        self.append(value)

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
        for node in self.head:
            if i >= stop:
                break

            if i >= start and value in node:
                return i

            i += 1

        raise ValueError

    def remove(self, value: T) -> None:
        for node in self.head:
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

        cursor = self.head.forward
        self.head.forward = self._sentinel

        while cursor is not self._sentinel:
            fwd = cursor.forward
            cursor.forward = self.head
            self.head = cursor
            cursor = fwd

    def __len__(self) -> int:
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
                return self.tail.value

            case int():
                return self.head.traverse(index % len(self)).value

            case slice():
                raise NotImplementedError  # TODO

    @overload
    def __setitem__(self, index: int, value: T) -> None:
        ...

    @overload
    def __setitem__(self, index: slice, value: Iterable[T]) -> None:
        ...

    def __setitem__(self, index: int | slice, value: T | Iterable[T]) -> None:
        match self._check_index(index):
            case int() if index == -1 or index == len(self) - 1:
                self.tail.value = value

            case int():
                self.head.traverse(index % len(self)).value = value

            case slice():
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
                del self.head
                self._count -= 1
            case int():
                del self.head.traverse(index - 1).forward
                self._count -= 1
            case slice():
                raise NotImplementedError  # TODO

    def __iter__(self):
        yield from self.head

    def __repr__(self):
        return f"<{type(self)}: {self.head!r}>"

    def __str__(self):
        return "[" + ", ".join(self) + "]"


class LinkedStack[T](LinkedList[T]):
    def push(self, value: T) -> None:
        self.prepend(value)

    def peek(self) -> T:
        return self.head.value

    def is_empty(self) -> bool:
        return len(self) == 0


class LinkedQueue[T](LinkedList[T]):
    def enqueue(self, item):
        self.append(item)

    def dequeue(self, item):
        self.pop(0)
