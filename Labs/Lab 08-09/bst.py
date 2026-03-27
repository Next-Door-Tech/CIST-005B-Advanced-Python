from typing import Self


class BinarySearchTree[T]:
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

        def delete(self, value: T) -> None:
            if value == self.value:


    def __init__(self):
        self.root: Self | None = None

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
                else:
                    cur = cur.left
            else:
                if cur.right is None:
                    cur.right = self.Node(value)
                else:
                    cur = cur.right

    def delete(self, value: T) -> None:
        cur = None
        nxt = self.root

        while nxt is not None:
            if value == nxt.value:
                if cur is self.root:

                    while cur.left is not None:
                        cur.value = cur.right.value

                    if cur.

                    return

            elif value < nxt.value:
                cur = nxt
                nxt = cur.left
            else:
                cur = nxt
                nxt = cur.right

        raise KeyError
