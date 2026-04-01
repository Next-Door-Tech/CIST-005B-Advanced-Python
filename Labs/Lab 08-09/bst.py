from typing import Self, Optional
from collections.abc import MutableMapping, Generator


class BST[KT, VT](MutableMapping[KT, VT]):
    class Node(MutableMapping):
        __slots__ = ('key', 'value', 'left', 'right')

        def __init__(self, key: KT, value: VT, left: Self = None, right: Self = None) -> None:
            self.key = key
            self.value = value
            self.left = left
            self.right = right

        def is_leaf(self) -> bool:
            return self.left is None and self.right is None

        def __getitem__(self, key: KT, /) -> VT:
            if key is self.key or key == self.key:
                return self.value
            elif key < self.key and self.left is not None:
                return self.left[key]
            elif self.right is not None:
                return self.right[key]
            else:
                raise KeyError(key)

        def __setitem__(self, key: KT, value: VT) -> None:
            if key is self.key or key == self.key:
                self.value = value
            elif key < self.key:
                if self.left is not None:
                    self.left[key] = value
                else:
                    self.left = self.__class__(key, value)
            else:
                if self.right is not None:
                    self.right[key] = value
                else:
                    self.right = self.__class__(key, value)

        class NoRightChildError(LookupError):
            """Attempted to pop the least right child when the right child was None."""
            pass

        def pop_lrc(self) -> VT:
            """pop least right child"""

            if self.right is None:
                raise self.NoRightChildError
            else:
                cur = self
                nxt_attr = 'right'
                nxt = getattr(cur, nxt_attr)

                while nxt.left is not None:
                    cur = nxt
                    nxt_attr = 'left'
                    nxt = getattr(cur, nxt_attr)

                retval = nxt.value
                setattr(cur, nxt_attr, nxt.right)
                return retval

        def __delitem__(self, key: KT, /) -> None:
            if key is self.key or key == self.key:
                raise RuntimeError(f"del {self.__class__.__qualname__}[{key}] cannot be called from Node to be deleted")
            elif key < self.key and self.left is not None:
                if key is self.left.key or key == self.left.key:
                    try:
                        self.left.value = self.left.pop_lrc()
                    except self.NoRightChildError:
                        self.left = self.left.left
                else:
                    del self.left[key]
            elif self.right is not None:
                if key is self.right.key or key == self.right.key:
                    try:
                        self.right.value = self.right.pop_lrc()
                    except self.NoRightChildError:
                        self.right = self.right.left
                else:
                    del self.right[key]
            else:
                raise KeyError(key)

        def __len__(self) -> int:
            _len = 1
            if self.left is not None:
                _len += len(self.left)
            if self.right is not None:
                _len += len(self.right)
            return _len

        def __iter__(self) -> Generator[VT, None, None]:
            if self.left is not None:
                yield from self.left
            yield self.key
            if self.right is not None:
                yield from self.right

    root: Optional[Node]

    def __init__(self, root: Node = None) -> None:
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
            except self.root.NoRightChildError:
                self.root = self.root.left

        else:
            del self.root[key]

    def __len__(self) -> int:
        if self.root is not None:
            return len(self.root)
        else:
            return 0

    def __iter__(self) -> Generator[VT, None, None]:
        if self.root is not None:
            yield from self.root


class SimpleBST[T]:
    class Node:
        def __init__(self, value: T, left=None, right=None) -> None:
            self.value: T = value
            self.left: Self = left
            self.right: Self = right

    root: Node | None

    def __init__(self):
        self.root = None

    def search(self, value: T) -> T:
        cur = self.root
        while cur is not None:
            if value == cur.value:
                return cur.value
            elif value < cur.value:
                cur = cur.left
            else:
                cur = cur.right

        raise KeyError

    def insert(self, value: T) -> None:
        cur = self.root
        if cur is None:
            self.root = self.Node(value)
            return

        while True:
            if value < cur.value:
                if cur.left is None:
                    cur.left = self.Node(value)
                    return
                else:
                    cur = cur.left
            else:
                if cur.right is None:
                    cur.right = self.Node(value)
                    return
                else:
                    cur = cur.right

    def delete(self, value: T) -> None:
        class NodeRef:
            @property
            def ref(self) -> SimpleBST.Node:
                nonlocal cur, nxt_attr
                return getattr(cur, nxt_attr)

            @ref.setter
            def ref(self, node: SimpleBST.Node) -> None:
                nonlocal cur, nxt_attr
                setattr(cur, nxt_attr, node)

            @property
            def value(self) -> T:
                return self.ref.value

            @value.setter
            def value(self, value_: T) -> None:
                self.ref.value = value_

            @property
            def left(self) -> SimpleBST.Node:
                return self.ref.left

            @left.setter
            def left(self, node: SimpleBST.Node) -> None:
                self.ref.left = node

            @property
            def right(self) -> SimpleBST.Node:
                return self.ref.right

            @right.setter
            def right(self, node: SimpleBST.Node) -> None:
                self.ref.right = node

        cur = self
        nxt_attr = 'root'
        nxt = NodeRef()

        while nxt.ref is not None:
            if nxt.value == value:
                if nxt.right is None:
                    nxt.ref = nxt.left
                    return

                else:
                    cur = target = nxt.ref
                    nxt_attr = 'left'
                    while nxt.left is not None:
                        cur = nxt.ref
                    target.value = nxt.value
                    nxt.ref = nxt.right

                    return

            elif value < nxt.value:
                cur = nxt.ref
                nxt_attr = 'left'
            else:
                cur = nxt.ref
                nxt_attr = 'right'

        raise KeyError  # leaf node reached without finding value
