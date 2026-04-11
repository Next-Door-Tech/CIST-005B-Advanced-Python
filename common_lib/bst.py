from abc import ABC, abstractmethod
from typing import Self, Protocol, runtime_checkable, Optional, cast, overload, Literal
from collections.abc import Collection, Sequence, MutableSet, MutableMapping, Generator, Iterable
from itertools import chain
from copy import copy, deepcopy

__all__ = ['BSTList', 'BSTMap', 'AVLList', 'AVLMap']


@runtime_checkable
class Comparable(Protocol):
    def __lt__[T](self: T, other: T) -> bool:
        ...


class MissingChildError(AttributeError):
    """Attempted to access a child node which is not set."""


class NoRightChildError(MissingChildError):
    """Node has no right child."""


class NoLeftChildError(MissingChildError):
    """Node has no left child."""


LeafNodeError = ExceptionGroup("Node has no children.", [NoLeftChildError(), NoRightChildError()])


class BSTNode[T: Comparable](Collection[T]):
    __slots__ = 'key', '_left', '_right', '_len', '_depth'

    _len: int
    _depth: int

    _left: Self
    _right: Self

    def __init__(self, key: T, left: Optional[Self] = None, right: Optional[Self] = None) -> None:
        self.key: T = key
        if left is not None:
            self.left = left
        if right is not None:
            self.right = right

    @property
    def has_left(self) -> bool:
        return hasattr(self, 'left')

    @property
    def left(self) -> Self:
        if hasattr(self, '_left'):
            return self._left
        raise NoLeftChildError

    @left.setter
    def left(self, node: Self) -> None:
        self._left = node

    @left.deleter
    def left(self) -> None:
        try:
            if not self.left.has_right:
                self.left = self.left.left
            else:
                self.left = self.left.pop_lrc()
        except* MissingChildError:
            del self._left

        self._clear_cache()

    @property
    def has_right(self) -> bool:
        return hasattr(self, 'right')

    @property
    def right(self) -> Self:
        if hasattr(self, '_right'):
            return self._right
        raise NoRightChildError

    @right.setter
    def right(self, node: Self) -> None:
        self._right = node

    @right.deleter
    def right(self) -> None:
        try:
            if not self.right.has_right:
                self.right = self.right.left
            else:
                self.right = self.right.pop_lrc()
        except* MissingChildError:
            del self._right

        self._clear_cache()

    def pop_lrc(self) -> Self:
        """Return the least right child of this node, extracting it from the tree."""
        if self.has_right:
            cur = self
            nxt_attr = 'right'

            while (nxt := getattr(cur, nxt_attr)).has_left:
                cur._clear_cache()
                cur = nxt
                nxt_attr = 'left'

            retval = nxt

            try:
                setattr(cur, nxt_attr, nxt.right)
            except NoRightChildError:
                delattr(cur, nxt_attr)

            try:
                retval.left = self.left
            except NoLeftChildError:
                if retval.has_left:
                    del retval._left  # noqa: do not call deleter again, just zap it

            try:
                retval.right = self.right
            except NoRightChildError:
                if retval.has_right:
                    del retval._right  # noqa: do not call deleter again, just zap it

            return retval

        elif self.has_left:  # and not self.has_right
            return self.left

        else:
            raise LeafNodeError

    @property
    def depth(self) -> int:
        if not hasattr(self, '_depth'):
            self._depth = 1 + max(getattr(self.left, 'depth', -1), getattr(self.right, 'depth', -1))

        return self._depth

    @depth.deleter
    def depth(self) -> None:
        del self._depth

    @property
    def _has_cache(self) -> bool:
        return hasattr(self, '_depth') or hasattr(self, '_len')

    def _clear_cache(self) -> None:
        if hasattr(self, '_len'):
            del self._len
        if hasattr(self, '_depth'):
            del self._depth

    @property
    def is_leaf(self) -> bool:
        return self.left is None and self.right is None

    def __contains__(self, key: object) -> bool:
        if self.key is key or self.key == key:
            return True
        elif not isinstance(key, Comparable):
            return False
        elif key < self.key:
            return self.has_left and key in self.left
        else:
            return self.has_right and key in self.right

    def __len__(self) -> int:
        if not hasattr(self, '_len'):
            self._len = 1 + (self.has_left and len(self.left)) + (self.has_right and len(self.right))

        return self._len

    def __iter__(self) -> Generator[T, None, None]:
        if self.has_left:
            yield from self.left
        yield self.key
        if self.has_right:
            yield from self.right

    def __reversed__(self) -> Generator[T, None, None]:
        if self.has_right:
            yield from reversed(self.right)
        yield self.key
        if self.has_left:
            yield from reversed(self.left)

    def __copy__(self) -> Self:
        new: Self = object.__new__(type(self))

        for cls in type(self).__mro__:
            try:
                slots = cls.__slots__
                if isinstance(slots, str):
                    slots = cls.__slots__.split()
                for attr in slots:
                    try:
                        setattr(new, attr, getattr(self, attr))
                    except AttributeError:
                        continue
            except AttributeError:
                continue

        if new.has_left:
            new._left = copy(new.left)
        if new.has_right:
            new._right = copy(new.right)

        return new

    def __deepcopy__(self, memo) -> Self:
        if id(self) in memo:
            return memo[id(self)]

        new: Self = object.__new__(type(self))

        memo[id(self)] = new
        for cls in type(self).__mro__:
            try:
                slots = cls.__slots__
                if isinstance(slots, str):
                    slots = cls.__slots__.split()
                for attr in slots:
                    try:
                        setattr(new, attr, deepcopy(getattr(self, attr), memo))
                    except AttributeError:
                        continue
            except AttributeError:
                continue
        return new






class BSTMapNode[KT: Comparable, VT](MutableMapping[KT, VT], BSTNode[KT]):
    __slots__ = 'value'

    _len: int
    _depth: int

    def __init__(self, key: KT, value: VT, left: Optional[Self] = None, right: Optional[Self] = None) -> None:
        super().__init__(key, left, right)
        self.value: VT = value

    def __getitem__(self, key: KT, /) -> VT:
        if key is self.key or key == self.key:
            return self.value
        elif key < self.key and self.has_left:
            return self.left[key]
        elif self.has_right:
            return self.right[key]
        else:
            raise KeyError(key)

    def __setitem__(self, key: KT, value: VT) -> None:
        if key is self.key or key == self.key:
            self.value = value
        else:
            if key < self.key:
                if self.has_left:
                    self.left[key] = value
                    if not self.left._has_cache:
                        self._clear_cache()
                else:
                    self.left = cast(Self, type(self)(key, value))
                    self._clear_cache()
            else:
                if self.has_right:
                    self.right[key] = value
                    if not self.right._has_cache:
                        self._clear_cache()
                else:
                    self.right = cast(Self, type(self)(key, value))
                    self._clear_cache()

    def __delitem__(self, key: KT, /) -> None:
        if key is self.key or key == self.key:
            raise RuntimeError(
                f"del {self.__class__.__qualname__}[{key}] cannot be called from Node to be deleted")
        elif key < self.key and self.has_left:
            if key is self.left.key or key == self.left.key:
                del self.left
            else:
                del self.left[key]
        elif self.has_right:
            if key is self.right.key or key == self.right.key:
                del self.right
            else:
                del self.right[key]
        else:
            raise KeyError(key)

        self._clear_cache()


class BSTMap[KT: Comparable, VT](MutableMapping[KT, VT]):
    Node: type = BSTMapNode

    root: BSTMapNode[KT, VT] | None

    def __init__(self, root: BSTMapNode[KT, VT] = None) -> None:
        self.root = root

    def __getitem__(self, key: KT, /) -> VT:
        if self.root is None:
            raise KeyError(key)
        else:
            return self.root[key]

    def __setitem__(self, key: KT, value: VT, /) -> None:
        if self.root is None:
            self.root = self.Node(key, value)
        else:
            self.root[key] = value

    def __delitem__(self, key: KT, /) -> None:
        if self.root is None:
            raise KeyError(key)
        elif key is self.root.key or key == self.root.key:
            try:
                self.root.value = self.root.pop_lrc()
            except NoRightChildError:
                self.root = self.root.left
        else:
            del self.root[key]

    def __len__(self) -> int:
        if self.root is not None:
            return len(self.root)
        else:
            return 0

    def __iter__(self) -> Generator[KT, None, None]:
        if self.root is not None:
            yield from self.root

    def __reversed__(self) -> Generator[KT, None, None]:
        if self.root is not None:
            yield from reversed(self.root)


class AVLMapNode[KT: Comparable, VT](BSTMapNode[KT, VT]):
    __slots__ = '_skew'

    _skew: int

    @property
    def skew(self) -> int:
        if not hasattr(self, '_skew'):
            self._skew = getattr(self.left, 'depth', -1) - getattr(self.right, 'depth', -1)

        return self._skew

    @skew.deleter
    def skew(self) -> None:
        del self._skew

    def _clear_cache(self) -> None:
        if hasattr(self, '_len'):
            del self._len
        if hasattr(self, '_dep'):
            del self._dep
        if hasattr(self, '_skew'):
            del self._skew

    @property
    def _has_cache(self) -> bool:
        return hasattr(self, '_skew') or hasattr(self, '_depth') or hasattr(self, '_len')

    def __rshift__(self, n: int) -> Self:
        """Performs a right rotation at this node n times. Returns the new root node."""
        if n == 0:
            return self
        elif n < 0:
            return self << -n
        elif self.left is None:
            raise ValueError(f"{n} right rotations remaining, but Node has no left child.")
        else:
            if self.skew * self.left.skew < 0:
                self.left >>= 1
            root = self.left
            self.left = self.left.right
            root.right = self
            self._clear_cache()
            root._clear_cache()
            return root >> n - 1

    def __lshift__(self, n: int) -> Self:
        """Performs a left rotation at this node n times. Returns the new root node."""
        if n == 0:
            return self
        elif n < 0:
            return self >> -n
        elif self.right is None:
            raise ValueError(f"{n} left rotations remaining, but Node has no right child.")
        else:
            if self.skew * self.right.skew < 0:
                self.right <<= 1
            root = self.right
            self.right = self.right.left
            root.left = self
            self._clear_cache()
            root._clear_cache()
            return root << n - 1

    def rebalance_left(self) -> None:
        skew = getattr(self.left, 'skew', 0)

        if skew < -1:
            self.left >>= -1 - self.left.skew  # type: ignore
            self._clear_cache()
        elif skew > 1:
            self.left <<= self.left.skew - 1  # type: ignore
            self._clear_cache()

    def rebalance_right(self) -> None:
        skew = getattr(self.right, 'skew', 0)

        if skew < -1:
            self.right >>= -1 - self.right.skew  # type: ignore
            self._clear_cache()
        elif skew > 1:
            self.right <<= self.right.skew - 1  # type: ignore
            self._clear_cache()

    def __setitem__(self, key: KT, value: VT) -> None:
        super().__setitem__(key, value)

        if key < self.key:
            self.rebalance_left()
        elif key > self.key:
            self.rebalance_right()

    def __delitem__(self, key: KT, /) -> None:
        super().__delitem__(key)

        if key < self.key:
            self.rebalance_left()
        elif key > self.key:
            self.rebalance_right()


class AVLMap[KT: Comparable, VT](BSTMap[KT, VT]):
    Node: type = AVLMapNode

    def __setitem__(self, key: KT, value: VT, /) -> None:
        super().__setitem__(key, value)
        skew = getattr(self.root, 'skew', 0)

        if skew < -1:
            self.root >>= -1 - skew  # type: ignore
        elif skew > 1:
            self.root <<= skew - 1  # type: ignore

    def __delitem__(self, key: KT, /) -> None:
        super().__delitem__(key)


# class SimpleNode[T: Comparable]:
#     def __init__(self, value: T, left: Self | None = None, right: Self | None = None) -> None:
#         self.value: T = value
#         self.left: Self | None = left
#         self.right: Self | None = right
#
#
# class SimpleBST[T: Comparable]:
#     Node: ClassVar[type[SimpleNode]] = SimpleNode[T]
#
#     root: SimpleNode[T] | None
#
#     def __init__(self):
#         self.root = None
#
#     def search(self, value: T) -> T:
#         cur = self.root
#         while cur is not None:
#             if value == cur.value:
#                 return cur.value
#             elif value < cur.value:
#                 cur = cur.left
#             else:
#                 cur = cur.right
#
#         raise KeyError
#
#     def insert(self, value: T) -> None:
#         if self.root is None:
#             self.root = SimpleNode(value)
#             return
#
#         cur: SimpleNode[T] = self.root
#         if cur is None:
#
#         while True:
#             if value < cur.value:
#                 if cur.left is None:
#                     cur.left = SimpleNode(value)
#                     return
#                 else:
#                     cur = cur.left
#             else:
#                 if cur.right is None:
#                     cur.right = SimpleNode(value)
#                     return
#                 else:
#                     cur = cur.right
#
#     def delete(self: Self, value: T) -> None:
#         cur: Self | SimpleNode[T] = self
#         nxt_attr = 'root'
#
#         class NodeRef:
#             @property
#             def ref(self) -> SimpleNode[T]:
#                 nonlocal cur, nxt_attr
#                 return getattr(cur, nxt_attr)
#
#             @ref.setter
#             def ref(self, node: SimpleNode[T]) -> None:
#                 nonlocal cur, nxt_attr
#                 setattr(cur, nxt_attr, node)
#
#             @property
#             def value(self) -> T:
#                 return self.ref.value
#
#             @value.setter
#             def value(self, value_: T) -> None:
#                 self.ref.value = value_
#
#             @property
#             def left(self) -> SimpleNode[T]:
#                 return self.ref.left
#
#             @left.setter
#             def left(self, node: SimpleNode[T]) -> None:
#                 self.ref.left = node
#
#             @property
#             def right(self) -> SimpleNode[T]:
#                 return self.ref.right
#
#             @right.setter
#             def right(self, node: SimpleNode[T]) -> None:
#                 self.ref.right = node
#
#         nxt = NodeRef()
#
#         while nxt.ref is not None:
#             if nxt.value == value:
#                 if nxt.right is None:
#                     nxt.ref = nxt.left
#                     return
#
#                 else:
#                     cur = target = nxt.ref
#                     nxt_attr = 'left'
#                     while nxt.left is not None:
#                         cur = nxt.ref
#                     target.value = nxt.value
#                     nxt.ref = nxt.right
#
#                     return
#
#             elif value < nxt.value:
#                 cur = nxt.ref
#                 nxt_attr = 'left'
#             else:
#                 cur = nxt.ref
#                 nxt_attr = 'right'
#
#         raise KeyError  # leaf node reached without finding value
