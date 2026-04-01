from typing import Self

class SimpleBST[T]:
    class Node:
        def __init__(self, value: T, left=None, right=None) -> None:
            self.value: T = value
            self.left: Self = left
            self.right: Self = right

        def search(self, value: T) -> T:
            if value == self.value:
                return self.value
            elif value < self.value:
                if self.left is not None:
                    return self.left.search(value)
                else:
                    raise KeyError
            else:
                if self.right is not None:
                    return self.right.search(value)
                else:
                    raise KeyError

        def insert(self, value: T) -> None:
            if value < self.value:
                if self.left is not None:
                    self.left.insert(value)
                else:
                    self.left = self.__class__(value)
            else:
                if self.right is not None:
                    self.right.insert(value)
                else:
                    self.right = self.__class__(value)

        # def delete(self, value: T) -> None:
        #     if value == self.value:
        #         if self.left is None:
        #             self = self.right

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

                elif nxt.left is None:
                    nxt.ref = nxt.right
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
