from collections.abc import Iterable, Hashable, Mapping
from typing import Self
from abc import ABC
from graph_abc import *


class BaseGraph[VertT: Hashable, EdgeT: Edge](GraphABC[VertT, EdgeT], ABC):
    """Base Methods for Graphs"""

    _vertices: set[VertT]
    _edges: set[EdgeT]

    def __init__(self, vertices: Iterable[VertT] | None = None, edges: Iterable[Iterable[VertT]] | None = None) -> None:
        if vertices is not None:
            self._vertices = set(vertices)
        else:
            self._vertices = set()

        self._edges = set()
        if edges is not None:
            for i, e in enumerate(edges):
                try:
                    self.add_edge(*e)
                except (KeyError, TypeError, ValueError) as exc:
                    raise ValueError(f"Failed to add edges[{i}] == {e!r}") from exc

    @property
    def vertices(self) -> frozenset[VertT]:
        return frozenset(self._vertices)

    @property
    def edges(self) -> frozenset[EdgeT]:
        return frozenset(self._edges)

    def add_vertex(self, vertex: VertT) -> None:
        self._vertices.add(vertex)

    def remove_vertex(self, vertex: VertT) -> None:
        self._vertices.remove(vertex)

    def discard_vertex(self, vertex: VertT) -> None:
        self._vertices.discard(vertex)

    def clear(self) -> None:
        self._vertices.clear()
        self._edges.clear()

    def clear_edges(self) -> None:
        self._edges.clear()

    def __and__(self, other: Self) -> Self:
        if not isinstance(other, type(self)):
            return NotImplemented
        else:
            return type(self)(self.vertices & other.vertices, self.edges & other.edges)

    def __iand__(self, other: Self) -> Self:
        if not isinstance(other, type(self)):
            return NotImplemented
        else:
            self._vertices &= other.vertices
            self._edges &= other.edges
            return self

    def __or__(self, other: Self) -> Self:
        if not isinstance(other, type(self)):
            return NotImplemented
        else:
            return type(self)(self._vertices | other._vertices, self._edges | other._edges)

    def __ior__(self, other: Self) -> Self:
        if not isinstance(other, type(self)):
            return NotImplemented
        else:
            self._vertices |= other.vertices
            self._edges |= other.edges
            return self

    def __copy__(self) -> Self:
        return type(self)(self._vertices, self._edges)


class SimpleGraph[VertT: Hashable](BaseGraph[VertT, frozenset[VertT]]):
    """A simple graph (undirected, unweighted, no duplicate edges)."""

    type EdgeT = frozenset[VertT]

    def add_edge(self, a: VertT, b: VertT) -> None:
        edge = frozenset((a, b))
        if not edge <= self._vertices:
            s = "Provided vertices are not present in this Graph:"
            if a not in self._vertices:
                s += f" a: {a!r}"
            if b not in self._vertices:
                s += f" b: {b!r}"
            raise KeyError(s)
        if len(edge) < 2:
            raise ValueError(
                f"{type(self).__name__} endpoints must be distinct, got hash({a!r}) == hash({b!r}).")
        self._edges.add(edge)

    def remove_edge(self, a: VertT, b: VertT) -> None:
        try:
            self._edges.remove(frozenset((a, b)))
        except KeyError:
            raise KeyError(f"No edge between {a!r} and {b!r}") from None

    def discard_edge(self, a: VertT, b: VertT) -> None:
        self._edges.discard(frozenset((a, b)))

    def neighbors(self, vertex: VertT) -> set[VertT]:
        return set.union(*(edge for edge in self._edges if vertex in edge)) - {vertex}

    def __sub__(self, other: Self) -> Self:
        if not isinstance(other, type(self)):
            return NotImplemented
        else:
            vertices = self.vertices - other.vertices
            edges = {e for e in self.edges - other.edges if e <= vertices}

            return type(self)(vertices, edges)

    def __rsub__(self, other: Self) -> Self:
        if not isinstance(other, type(self)):
            return NotImplemented
        else:
            vertices = other.vertices - self.vertices
            edges = {e for e in other.edges - self.edges if e <= vertices}

            return type(self)(vertices, edges)

    def __isub__(self, other: Self) -> Self:
        if not isinstance(other, type(self)):
            return NotImplemented
        else:
            self._vertices -= other.vertices
            self._edges -= other.edges
            for e in self._edges:
                if not e <= self._vertices:
                    self._edges.remove(e)
            return self


class DiGraph[VertT: Hashable](BaseGraph[VertT, tuple[VertT, VertT]], DiGraphABC[VertT, tuple[VertT, VertT]]):
    """A simple directed graph (unweighted, no duplicate edges)."""

    type EdgeT = tuple[VertT, VertT]

    _vertices: set[VertT]
    _edges: set[EdgeT]

    def add_edge(self, head: VertT, tail: VertT) -> None:
        edge_set = frozenset((head, tail))
        if not edge_set <= self._vertices:
            s = "Provided vertices are not present in this Graph:"
            if head not in self._vertices:
                s += f" head: {head!r}"
            if tail not in self._vertices:
                s += f" tail: {tail!r}"
            raise KeyError(s)
        if len(edge_set) < 2:
            raise ValueError(
                f"{type(self).__name__}: head and tail must be distinct, got hash({head!r}) == hash({tail!r})")
        self._edges.add((head, tail))

    def remove_edge(self, head: VertT, tail: VertT) -> None:
        try:
            self._edges.remove((head, tail))
        except KeyError:
            raise KeyError(f"No edge between {head!r} and {tail!r}") from None

    def discard_edge(self, head: VertT, tail: VertT) -> None:
        self._edges.discard((head, tail))

    def neighbors(self, vertex: VertT) -> set[VertT]:
        return set(e[1] for e in self.edges if vertex is e[0] or vertex == e[0])

    def __sub__(self, other: Self) -> Self:
        if not isinstance(other, type(self)):
            return NotImplemented
        else:
            vertices = self.vertices - other.vertices
            edges = {e for e in self.edges - other.edges if all(v in vertices for v in e)}

            return type(self)(vertices, edges)

    def __rsub__(self, other: Self) -> Self:
        if not isinstance(other, type(self)):
            return NotImplemented
        else:
            vertices = other.vertices - self.vertices
            edges = {e for e in other.edges - self.edges if all(v in vertices for v in e)}

            return type(self)(vertices, edges)

    def __isub__(self, other: Self) -> Self:
        if not isinstance(other, type(self)):
            return NotImplemented
        else:
            self._vertices -= other.vertices
            self._edges -= other.edges
            for e in self._edges:
                if not all(v in self._vertices for v in e):
                    self._edges.remove(e)
            return self
