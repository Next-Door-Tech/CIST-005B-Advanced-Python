from typing import Self, overload
from collections.abc import MutableSequence, Iterable, Reversible, Container


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
        else:
            self._tail = node
            self._tail.forward = self

        # assert self._head >= self, "Sentinel chain is not closed after assignment."

    @head.deleter
    def head(self):
        if self.head is not self:
            self.head = self.head.traverse(1)
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


class LinkedList[T](MutableSequence[T]):
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

    def _check_index(self, index: int | slice) -> int | slice:
        match index:
            case slice():
                return index
            case int() if -len(self) <= index < len(self):
                return index
            case int():
                raise IndexError(f"{type(self)} index out of range")
            case _:
                raise TypeError(f"{type(self)} indices must be integers or slices, not '{type(index)}'")

    def _normalize_index_inclusive(self, index: int | slice) -> int | slice:
        match index:
            case slice():
                return index
            case int() if -len(self) <= index <= len(self):
                return index
            case int():
                raise IndexError(f"{type(self)} index out of range")
            case _:
                raise TypeError(f"{type(self)} indices must be integers or slices, not '{type(index)}'")

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
