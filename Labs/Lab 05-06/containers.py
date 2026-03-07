from functools import singledispatchmethod
from typing import *
from collections.abc import MutableSequence, Iterable


class LinkedList[T](MutableSequence[T]):
    __slots__ = ['_head', '_tail', '_count']

    class Node:
        __slots__ = ("data", "fwd", "__weakref__")

        def __init__(self, data: T, fwd: Self = None):
            self.data: T = data
            self.fwd: Self = fwd

        def __str__(self):
            return self.data.__str__()

        def __repr__(self):
            return f"<{self.__class__.__qualname__}: {repr(self.data)}> --> {repr(self.fwd)}"

    def __init__(self, data: Iterable[T] = None):
        self._count = 0
        self._head: LinkedList.Node | None = None
        self._tail: LinkedList.Node | None = None

        if data is not None:
            try:
                self.extend(data)
            except TypeError:
                self.insert(0, data)

    def __len__(self):
        return self._count

    def append(self, data):
        self.insert(-1, data)
        # if self.__len__() == 0:
        #     self._head = self._tail = self.Node(data)
        #
        # else:
        #     self._tail.link = self.Node(data)
        #
        # self._count += 1

    def prepend(self, value):
        self.insert(0, value)
        # if self.__len__() == 0:
        #     self._head = self._tail = self.Node(value)
        #
        # else:
        #     self._head = self.Node(value, self._head)
        #
        # self._count += 1

    def insert(self, index, value):
        pass

    @overload
    def __getitem__(self, index: int) -> T:
        ...

    @overload
    def __getitem__(self, index: slice) -> MutableSequence[T]:
        ...

    @singledispatchmethod
    def __getitem__(self, index):
        raise ValueError

    @__getitem__.register
    def _(self, index: int) -> T:
        if -len(self) < index <= len(self):
            raise IndexError

        if index < 0:
            index += len(self)

    @__getitem__.register
    def _(self, index: slice) -> MutableSequence[T]:
        pass

    @overload
    def __setitem__(self, index: int, value: T) -> None:
        ...

    @overload
    def __setitem__(self, index: slice, value: Iterable[T]) -> None:
        ...

    def __setitem__(self, index, value):
        pass

    @overload
    def __delitem__(self, index: int) -> None:
        ...

    @overload
    def __delitem__(self, index: slice) -> None:
        ...

    def __delitem__(self, index):
        pass


LinkedList.Node(3)
