from abc import ABC, abstractmethod
from typing import Self, Protocol, runtime_checkable, Optional, cast, overload, Literal
from collections.abc import Collection, Sequence, MutableSet, MutableMapping, Generator, Iterable, Mapping
from itertools import chain
from copy import copy, deepcopy

from common_lib.containers import _CommonMethods

__all__ = ['BSTSeq', 'BSTSet', 'BSTMap', 'AVLSeq', 'AVLSet', 'AVLMap']


@runtime_checkable
class Comparable(Protocol):
    def __lt__[T](self: T, other: T) -> bool:
        ...

    def __eq__[T](self: T, other: T) -> bool:
        ...


class MissingChildError(AttributeError):
    """Attempted to access a child node which is not set."""


class NoRightChildError(MissingChildError):
    """Node has no right child."""


class NoLeftChildError(MissingChildError):
    """Node has no left child."""


LeafNodeError = ExceptionGroup("Node has no children.", [NoLeftChildError(), NoRightChildError()])


class BSTNodeBase[T: Comparable](Collection[T], ABC):
    __slots__ = 'key', '_left', '_right', '_len', '_depth', '_skew'

    key: T

    _len: int
    _depth: int
    _skew: int

    _left: Self
    _right: Self

    class DeleteMe(Exception):
        """Signals to the parent node that this node should be deleted upon return."""
        pass

    def __init__(self, key: T, left: Optional[Self] = None, right: Optional[Self] = None) -> None:
        self.key: T = key
        if left is not None:
            self.left = left
        if right is not None:
            self.right = right

    @property
    def has_left(self) -> bool:
        return hasattr(self, '_left')

    @property
    def left(self) -> Self:
        if hasattr(self, '_left'):
            return self._left
        raise NoLeftChildError

    @left.setter
    def left(self, node: Self) -> None:
        self._left = node
        self._clear_cache()

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
        return hasattr(self, '_right')

    @property
    def right(self) -> Self:
        if hasattr(self, '_right'):
            return self._right
        raise NoRightChildError

    @right.setter
    def right(self, node: Self) -> None:
        self._right = node
        self._clear_cache()

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
            try:
                left = self.left.depth
            except NoLeftChildError:
                left = -1

            try:
                right = self.right.depth
            except NoRightChildError:
                right = -1

            self._depth = 1 + max(left, right)

        return self._depth

    @depth.deleter
    def depth(self) -> None:
        del self._depth

    @property
    def skew(self) -> int:
        if not hasattr(self, '_skew'):
            try:
                left = self.left.depth
            except NoLeftChildError:
                left = -1

            try:
                right = self.right.depth
            except NoRightChildError:
                right = -1

            self._skew = left - right

        return self._skew

    @skew.deleter
    def skew(self) -> None:
        del self._skew

    @property
    def len(self) -> int:
        if not hasattr(self, '_len'):
            self._len = 1 + (self.has_left and len(self.left)) + (self.has_right and len(self.right))

        return self._len

    @len.deleter
    def len(self) -> None:
        del self._len

    def _clear_cache(self) -> None:
        if hasattr(self, '_len'):
            del self._len
        if hasattr(self, '_depth'):
            del self._depth
        if hasattr(self, '_skew'):
            del self._skew

    @property
    def _has_cache(self) -> bool:
        return hasattr(self, '_depth') or hasattr(self, '_skew') or hasattr(self, '_len')

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
        return self.len

    def __iter__(self) -> Generator[Self, None, None]:
        if self.has_left:
            yield from self.left
        yield self
        if self.has_right:
            yield from self.right

    def __reversed__(self) -> Generator[Self, None, None]:
        if self.has_right:
            yield from reversed(self.right)
        yield self
        if self.has_left:
            yield from reversed(self.left)

    def __str__(self) -> str:
        left = f"{self.left!s} <-- " if self.has_left else ""
        right = f" --> {self.right!s}" if self.right else ""
        return f"({left}{self.key}{right})"

    def __repr__(self) -> str:
        left = f", left={self.left!r}" if self.has_left else ""
        right = f", right={self.right!r}" if self.has_right else ""
        return f"{type(self).__qualname__}({self.key!r}{left}{right})"

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


class BSTBase[T: Comparable](Collection[T], ABC):
    @abstractmethod
    class Node[T_](BSTNodeBase[T_]):
        ...

    _root: Node

    @classmethod
    def from_node(cls, node: Node) -> Self:
        new = cls()
        new._root = node
        return new

    @property
    def has_root(self) -> bool:
        return hasattr(self, '_root')

    @property
    def root(self) -> Node[T]:
        return self._root

    @root.setter
    def root(self, node: Node[T]) -> None:
        self._root = node

    @root.deleter
    def root(self) -> None:
        try:
            if not self.root.has_right:
                self.root = self.root.left
            else:
                self.root = self.root.pop_lrc()
        except* MissingChildError:
            del self._root

    def __len__(self) -> int:
        if self.has_root:
            return len(self.root)
        else:
            return 0

    def __iter__(self) -> Generator[T, None, None]:
        if self.has_root:
            for node in self.root:
                yield node.key

    def __reversed__(self) -> Generator[T, None, None]:
        if self.has_root:
            for node in reversed(self.root):
                yield node.key

    def __contains__(self, key: object) -> bool:
        return self.has_root and key in self.root

    @property
    def depth(self) -> int:
        if self.has_root:
            return self.root.depth
        else:
            return -1

    @property
    def skew(self) -> int:
        if self.has_root:
            return self.root.skew
        else:
            return 0


class BSTSeq[T: Comparable](BSTBase[T], _CommonMethods[T], Sequence[T]):
    class Node[T_: Comparable](BSTNodeBase[T_], _CommonMethods[T_], Sequence[T_]):
        @property
        def value(self) -> T_:
            return self.key

        @value.setter
        def value(self, value: T_) -> None:
            self.key = value

        @property
        def node_index(self) -> int:
            return getattr(self.left, 'len', 0)

        @overload
        def __getitem__(self, index: int, /, *, recursive: bool = False) -> T_:
            ...

        @overload
        def __getitem__(self, index: slice, /, *, recursive: Literal[False] = False) -> list[T_]:  # noqa
            ...

        @overload
        def __getitem__(self, index: slice, /, *, recursive: Literal[True]) -> Iterable[T_]:  # noqa
            ...

        @overload
        def __getitem__(self, index: int | slice, /, *, recursive: Literal[False] = False) -> T_ | list[T_]:
            ...

        def __getitem__(self, index: int | slice, /, *, recursive: bool = False) -> T_ | list[T_] | Iterable[T_]:
            if not recursive:
                self._check_index(index)
                if isinstance(index, int):
                    index %= len(self)

            match index:
                case int(i):
                    if i < self.node_index:
                        return self.left.__getitem__(i, recursive=True)
                    elif i == self.node_index:
                        return self.key
                    else:
                        return self.right.__getitem__(i - self.node_index, recursive=True)
                case slice() as s:
                    if not recursive:
                        return list(self.__getitem__(s, recursive=True))

                    indices = range(len(self))[s]

                    if not indices:
                        return ()

                    s = slice(indices.start, indices.stop, indices.step)

                    if range(self.node_index)[s] and self.has_left:
                        left = self.left.__getitem__(s, recursive=True)
                    else:
                        left = ()

                    if self.node_index in indices:
                        center = (self.key,)
                    else:
                        center = ()

                    if self.has_right:
                        r = range(-self.node_index - 1, len(self.right))[s]
                        right = self.right.__getitem__(slice(r.start, r.stop, r.step), recursive=True)
                    else:
                        right = ()

                    if s.step > 0:
                        return chain(left, center, right)
                    else:
                        return chain(right, center, left)

        def __delitem__(self, index: int | slice, /, *, recursive: bool = False) -> None:
            if not recursive:
                self._check_index(index)
                if isinstance(index, int):
                    index %= len(self)

            match index:
                case int(i):
                    if i == self.node_index:
                        raise self.DeleteMe
                    elif i < self.node_index:
                        try:
                            self.left.__delitem__(i, recursive=True)
                        except self.DeleteMe:
                            del self.left
                    else:
                        try:
                            self.right.__delitem__(i - self.node_index, recursive=True)
                        except self.DeleteMe:
                            del self.right
                case slice() as s:
                    if s.step < 0:
                        indices = range(len(self))[s][::-1]
                    else:
                        indices = range(len(self))[s]

                    if not indices:
                        return

                    s = slice(indices.start, indices.stop, indices.step)

                    if range(self.node_index)[s] and self.has_left:
                        try:
                            self.left.__delitem__(s, recursive=True)
                        except self.DeleteMe:
                            del self.left

                    if self.has_right:
                        r = range(-self.node_index - 1, len(self.right))[s]
                        try:
                            self.right.__delitem__(slice(r.start, r.stop, r.step), recursive=True)
                        except self.DeleteMe:
                            del self.right

                    self._clear_cache()

                    if self.node_index in indices:
                        raise self.DeleteMe

        def add(self, value: T_) -> None:
            if value == self.value:
                return
            elif value < self.value:
                if self.has_left:
                    self.left.add(value)
                else:
                    self.left = type(self)(value)

                if not self.left._has_cache:
                    self._clear_cache()
            else:
                if self.has_right:
                    self.right.add(value)
                else:
                    self.right = type(self)(value)

                if not self.right._has_cache:
                    self._clear_cache()

        def discard(self, value: T_) -> None:
            """Remove a member. Do not raise an exception if absent."""
            if value == self.value:
                raise self.DeleteMe

            elif value < self.value:
                if self.has_left:
                    try:
                        self.left.discard(value)
                        if not self.left._has_cache:
                            self._clear_cache()
                    except self.DeleteMe:
                        del self.left
                        self._clear_cache()
            else:
                if self.has_right:
                    try:
                        self.right.discard(value)
                        if not self.right._has_cache:
                            self._clear_cache()
                    except self.DeleteMe:
                        del self.right
                        self._clear_cache()

        def remove(self, value: T_) -> None:
            """Remove a member. Do raise ValueError if absent."""
            if value == self.value:
                raise self.DeleteMe

            elif value < self.value:
                if self.has_left:
                    try:
                        self.left.discard(value)
                        if not self.left._has_cache:
                            self._clear_cache()
                    except self.DeleteMe:
                        del self.left
                        self._clear_cache()
                else:
                    raise ValueError

            else:
                if self.has_right:
                    try:
                        self.right.discard(value)
                        if not self.right._has_cache:
                            self._clear_cache()
                    except self.DeleteMe:
                        del self.right
                        self._clear_cache()
                else:
                    raise ValueError

        def index(self, value: T_, start: Optional[int] = 0, stop: Optional[int] = None) -> int:
            if start is None:
                start = 0
            start: int  # type hint
            if start < 0:
                start = max(len(self) + start, 0)

            if stop is not None and stop < 0:
                stop += len(self)
                if stop < 0:
                    raise ValueError

            i = self.node_index

            try:
                if value < self.value:
                    if start >= i:
                        raise ValueError
                    else:
                        return self.left.index(value, start, stop)

                elif value == self.value:
                    if start > i or (stop is not None and stop <= i):
                        raise ValueError
                    else:
                        return i

                else:
                    if stop is not None and stop <= i:
                        raise ValueError
                    else:
                        return i + self.right.index(value, start - i, stop and stop - i)

            except AttributeError:
                raise ValueError from None

        def count(self, value: T_) -> int:
            return int(value in self)

        def clear(self) -> None:
            if self.has_left:
                del self._left
            if self.has_right:
                del self._right

            raise self.DeleteMe

        def pop(self, index: int = 0) -> T_:
            self._check_index(index, int_only=True)
            if index < 0:
                index += len(self)

            if index == self.node_index:
                raise self.DeleteMe

            elif index < self.node_index:
                try:
                    retval = self.left.pop(index)
                except self.DeleteMe:
                    retval = self.left.value
                    del self.left

                self._clear_cache()
                return retval

            else:
                try:
                    retval = self.right.pop(index)
                except self.DeleteMe:
                    retval = self.right.value
                    del self.right

                self._clear_cache()
                return retval

    def __init__(self, iterable: Iterable[T] = None) -> None:
        if iterable is not None:
            for value in iterable:
                self.add(value)

    @property
    def has_root(self) -> bool:
        return hasattr(self, 'root')

    @property
    def root(self) -> Node[T]:
        return self._root

    @root.setter
    def root(self, node: Node[T]) -> None:
        self._root = node

    @root.deleter
    def root(self) -> None:
        try:
            if not self.root.has_right:
                self.root = self.root.left
            else:
                self.root = self.root.pop_lrc()
        except* MissingChildError:
            del self._root

    @overload
    def __getitem__(self, index: int) -> T:
        ...

    @overload
    def __getitem__(self, index: slice) -> list[T]:
        ...

    def __getitem__(self, index: int | slice) -> T | list[T]:
        self._check_index(index)
        return self.root[index]

    def __delitem__(self, index: int | slice) -> None:
        try:
            del self.root[index]
        except self.Node.DeleteMe:
            del self.root

    def __len__(self) -> int:
        if self.has_root:
            return len(self.root)
        else:
            return 0

    def __contains__(self, key: object) -> bool:
        return hasattr(self, 'root') and key in self.root

    def add(self, value: T) -> None:
        try:
            self.root.add(value)
        except AttributeError:
            self.root = self.Node(value)

    def discard(self, value: T) -> None:
        try:
            self.root.discard(value)
        except AttributeError:
            pass
        except self.Node.DeleteMe:
            del self.root

    def remove(self, value: T) -> None:
        try:
            self.root.remove(value)
        except AttributeError:
            raise ValueError from None
        except self.Node.DeleteMe:
            del self.root

    def index(self, value: T, start: Optional[int] = 0, stop: Optional[int] = None) -> int:
        try:
            return self.root.index(value, start, stop)
        except AttributeError:
            raise ValueError from None

    def count(self, value: T) -> int:
        return int(value in self)

    def clear(self) -> None:
        try:
            del self._root
        except AttributeError:
            pass

    def pop(self, index: int = 0) -> T:
        try:
            return self.root.pop(index)
        except AttributeError:
            raise IndexError from None

    def __str__(self) -> str:
        return f"[{', '.join(str(val) for val in self)}]"

    def __repr__(self) -> str:
        if len(self):
            return f"{type(self).__name__}([{', '.join(repr(val) for val in self)}])"
        else:
            return f"{type(self).__name__}()"


class BSTMap[KT: Comparable, VT](BSTBase[KT], MutableMapping[KT, VT]):
    class Node[KT_: Comparable, VT_](BSTNodeBase[KT_], MutableMapping[KT_, VT_]):
        __slots__ = 'value'

        _len: int
        _depth: int

        def __init__(self, key: KT_, value: VT_, left: Optional[Self] = None, right: Optional[Self] = None) -> None:
            super().__init__(key, left, right)
            self.value: VT_ = value

        def __getitem__(self, key: KT_, /) -> VT_:
            if key is self.key or key == self.key:
                return self.value
            elif key < self.key and self.has_left:
                return self.left[key]
            elif self.has_right:
                return self.right[key]
            else:
                raise KeyError(key)

        def __setitem__(self, key: KT_, value: VT_) -> None:
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

        def __delitem__(self, key: KT_, /) -> None:
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

        def __str__(self) -> str:
            left = f"{self.left!s} <-- " if self.has_left else ""
            right = f" --> {self.right!s}" if self.right else ""
            return f"({left}({self.key}: {self.value}){right})"

        def __repr__(self) -> str:
            left = f", left={self.left!r}" if self.has_left else ""
            right = f", right={self.right!r}" if self.has_right else ""
            return f"{type(self).__qualname__}({self.key!r}, {self.value!r}{left}{right})"

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

    def __init__(self, mapping_or_iterable: Mapping[KT, VT] | Iterable[tuple[KT, VT]] = None, /, **kwargs) -> None:
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

    @property
    def has_root(self) -> bool:
        return hasattr(self, 'root')

    @property
    def root(self) -> Node[KT, VT]:
        return self._root

    @root.setter
    def root(self, node: Node[KT, VT]) -> None:
        self._root = node

    @root.deleter
    def root(self) -> None:
        try:
            if not self.root.has_right:
                self.root = self.root.left
            else:
                self.root = self.root.pop_lrc()
        except* MissingChildError:
            del self._root

    def __getitem__(self, key: KT, /) -> VT:
        if self.has_root:
            return self.root[key]
        else:
            raise KeyError(key)

    def __setitem__(self, key: KT, value: VT, /) -> None:
        if self.has_root:
            self.root[key] = value
        else:
            self.root = self.Node(key, value)

    def __delitem__(self, key: KT, /) -> None:
        if not self.has_root:
            raise KeyError(key)
        elif key is self.root.key or key == self.root.key:
            try:
                self.root = self.root.pop_lrc()
            except NoRightChildError:
                self.root = self.root.left
        else:
            del self.root[key]

    def __len__(self) -> int:
        if self.has_root:
            return len(self.root)
        else:
            return 0

    def __str__(self) -> str:
        return '{' + ', '.join(f'{key!s}: {self[key]!s}' for key in self) + '}'

    def __repr__(self) -> str:
        if len(self):
            return f"{type(self).__name__}({'{' + ', '.join(f'{key!r}: {self[key]!r}' for key in self) + '}'})"
        else:
            return f"{type(self).__name__}()"


class AVLNodeBase[T: Comparable](BSTNodeBase[T]):
    __slots__ = ()

    def __rshift__(self, n: int) -> Self:
        """Performs a right rotation at this node n times. Returns the new root node."""
        if n == 0:
            return self
        elif n < 0:
            return self << -n
        elif not self.has_left:
            raise ValueError(f"{n} right rotations remaining, but Node has no left child.")
        else:
            if self.skew * self.left.skew < 0:
                self.left >>= 1
            root = self.left
            try:
                self.left = self.left.right
            except NoRightChildError:
                del self._left
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
        elif not self.has_right:
            raise ValueError(f"{n} left rotations remaining, but Node has no right child.")
        else:
            if self.skew * self.right.skew < 0:
                self.right <<= 1
            root = self.right
            try:
                self.right = self.right.left
            except NoLeftChildError:
                del self._right
            root.left = self
            self._clear_cache()
            root._clear_cache()
            return root << n - 1

    def rebalance_left(self) -> None:
        skew = getattr(self.left, 'skew', 0)

        if skew < -1:
            self.left <<= -1 - self.left.skew
        elif skew > 1:
            self.left >>= self.left.skew - 1

    def rebalance_right(self) -> None:
        skew = getattr(self.right, 'skew', 0)

        if skew < -1:
            self.right <<= -1 - self.right.skew
        elif skew > 1:
            self.right >>= self.right.skew - 1

    def rebalance_on_key(self, key) -> None:
        if key < self.key:
            self.rebalance_left()
        elif key != self.key:
            self.rebalance_right()


class AVLBase[T](BSTBase[T]):
    @abstractmethod
    class Node[T_](AVLNodeBase[T_]):
        ...

    def rebalance(self) -> None:
        skew = getattr(self.root, 'skew', 0)

        if skew < -1:
            self.root <<= -1 - self.root.skew
        elif skew > 1:
            self.root >>= self.root.skew - 1


class AVLSeq[T](AVLBase[T], BSTSeq[T]):
    class Node[T_](AVLNodeBase[T_], BSTSeq.Node[T_]):
        __slots__ = ()

    def __delitem__(self, index: int | slice) -> None:
        super().__delitem__(index)
        self.rebalance()

    def add(self, value: T) -> None:
        super().add(value)
        self.rebalance()

    def discard(self, value: T) -> None:
        super().discard(value)
        self.rebalance()

    def remove(self, value: T) -> None:
        super().remove(value)
        self.rebalance()

    def pop(self, index: int = 0) -> T:
        retval = super().pop(index)
        self.rebalance()
        return retval


class AVLMap[KT: Comparable, VT](AVLBase[KT], BSTMap[KT, VT]):
    class Node[KT_: Comparable, VT_](AVLNodeBase[KT_], BSTMap.Node[KT_, VT_]):
        __slots__ = ()

        def __setitem__(self, key: KT_, value: VT_) -> None:
            super().__setitem__(key, value)

            if key < self.key:
                self.rebalance_left()
            elif key > self.key:
                self.rebalance_right()

        def __delitem__(self, key: KT_, /) -> None:
            super().__delitem__(key)

            if key < self.key:
                self.rebalance_left()
            elif key > self.key:
                self.rebalance_right()

    root: Node[KT, VT]

    def __setitem__(self, key: KT, value: VT, /) -> None:
        super().__setitem__(key, value)
        self.rebalance()

    def __delitem__(self, key: KT, /) -> None:
        super().__delitem__(key)
        self.rebalance()

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
