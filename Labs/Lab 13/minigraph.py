from collections.abc import Iterable, Mapping
from typing import Hashable

from common_lib.hash_table import HashMap, HashSet
from common_lib.containers import LinkedStack, LinkedQueue


class GraphAdjMatrix[T: Hashable]:
    def __init__(self, iterable: Iterable[T] | None = None) -> None:
        self.vertices: HashMap[T, int] = HashMap()
        self.edges: list[list[bool]] = []
        offset = 0
        for i, key in enumerate(iterable if iterable is not None else ()):
            if key not in self.vertices:
                self.vertices[key] = i + offset
            else:
                offset -= 1

        for i in range(len(self.vertices)):
            self.edges.append([False] * len(self.vertices))

    def add_vertex(self, key) -> None:
        if key not in self.vertices:
            self.vertices[key] = len(self.vertices)
            for row in self.edges:
                row.append(False)
            self.edges.append([False] * len(self.vertices))

    def add_edge(self, source, destination) -> None:
        if source not in self.vertices or destination not in self.vertices:
            raise KeyError

        self.edges[self.vertices[source]][self.vertices[destination]] = True


class GraphAdjSet[T: Hashable]:
    def __init__(self, vertices: Iterable[T] | None = None, edges: Iterable[tuple[T, T]] | None = None) -> None:
        self.vertices: HashSet[T] = HashSet(vertices)
        self.edges: HashSet[tuple[T, T]] = HashSet(edges)

    def add_vertex(self, key: T) -> None:
        self.vertices.add(key)

    def add_edge(self, source: T, destination: T) -> None:
        if source not in self.vertices or destination not in self.vertices:
            raise KeyError
        self.edges.add((source, destination))

    def breadth_first_traversal(self, start_vertex: T) -> list[T]:
        if start_vertex not in self.vertices:
            raise KeyError

        queue = LinkedQueue([start_vertex])
        visited = HashSet({start_vertex})
        result = []

        while queue:
            cur = queue.dequeue()
            result.append(cur)
            for dest in self.vertices - visited:
                if (cur, dest) in self.edges:
                    queue.enqueue(dest)
                    visited.add(dest)

        return result

    def depth_first_traversal(self, start_vertex: T) -> list[T]:
        if start_vertex not in self.vertices:
            raise KeyError

        stack = LinkedStack([start_vertex])
        visited = HashSet({start_vertex})
        result = []

        while stack:
            cur = stack.pop()
            result.append(cur)
            for dest in self.vertices - visited:
                if (cur, dest) in self.edges:
                    stack.push(dest)
                    visited.add(dest)

        return result


class WeightedGraphAdjHashMap[T: Hashable](GraphAdjSet[T]):
    def __init__(self, vertices: Iterable[T] | None = None, edges: Mapping[tuple[T, T], float] | None = None) -> None:
        super().__init__()
        self.vertices: HashSet[T] = HashSet(vertices)
        self.edges: HashMap[tuple[T, T], float] = HashMap(edges)

    def add_edge(self, source: T, destination: T, weight: float) -> None:
        if source not in self.vertices or destination not in self.vertices:
            raise KeyError
        self.edges.add((source, destination))
