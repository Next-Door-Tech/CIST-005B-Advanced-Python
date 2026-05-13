from collections.abc import Iterable, Hashable, Set
from typing import Protocol, runtime_checkable, Self
from abc import ABC, abstractmethod


@runtime_checkable
class Weight(Protocol):
    """Must support comparison, addition, and negation/subtraction with other Weight types."""

    @abstractmethod
    def __eq__(self, other: Weight | object) -> bool:
        """self == other"""

    def __ne__(self, other: Weight | object) -> bool:
        """self != other"""

    @abstractmethod
    def __lt__(self, other: Weight) -> bool:
        """self < other"""

    @abstractmethod
    def __le__(self, other: Weight) -> bool:
        """self <= other"""

    @abstractmethod
    def __gt__(self, other: Weight) -> bool:
        """self > other"""

    @abstractmethod
    def __ge__(self, other: Weight) -> bool:
        """self >= other"""

    @abstractmethod
    def __add__(self, other: Weight) -> Weight:
        """self + other"""

    @abstractmethod
    def __radd__(self, other: Weight) -> Weight:
        """other + self"""

    @abstractmethod
    def __neg__(self) -> Weight:
        """-self"""

    @abstractmethod
    def __sub__(self, other: Weight) -> Weight:
        """self - other"""

    @abstractmethod
    def __rsub__(self, other) -> Weight:
        """other - self"""


class Edge[VertT: Hashable](Protocol):
    """An edge in a Graph. Must contain two vertices as endpoints,
    though they may be identical for a loopback edge.
    Additional information may be assigned to an edge
    to represent directed edges, weights, etc."""

    __slots__ = ()

    @abstractmethod
    def __contains__(self, vertex: VertT) -> bool:
        """Return True if vertex is either the start or end of this edge."""

    @abstractmethod
    def __eq__(self, other: Self | object) -> bool:
        """Return True if the edges are equal, i.e. both edges have
        the same endpoints and any additional values are equal."""


class WeightedEdge[VertT: Hashable](Edge[VertT], Protocol):
    """A weighted edge in a Graph.
    Must return the edge weight via the __len__ method."""

    __slots__ = ()

    @abstractmethod
    @property
    def weight(self) -> Weight:
        """Return the weight of this edge."""

    @abstractmethod
    def __len__(self) -> Weight:
        """Return the weight of this edge."""


class GraphABC[VertT: Hashable, EdgeT: Edge](ABC):
    """A Graph containing multiple Vertices connected via Edges."""

    __slots__ = ()

    @abstractmethod
    def __init__(self, vertices: Iterable[VertT] | None = None, edges: Iterable[EdgeT] | None = None) -> None:
        """Create a Graph with the provided set of Vertices and Edges between those Vertices.
        :raises ValueError: A provided Edge's endpoints are not Vertices in this Graph."""

    def __contains__(self, vertex: VertT | object) -> bool:
        """Returns `True` if the Graph contains the specified Vertex."""
        return vertex in self.vertices

    @abstractmethod
    @property
    def vertices(self) -> Iterable[VertT]:
        """Returns an Iterable of all vertices in the Graph."""

    @abstractmethod
    @property
    def edges(self) -> Iterable[EdgeT]:
        """Returns an Iterable of all edges in the Graph."""

    @abstractmethod
    def add_vertex(self, vertex: VertT) -> None:
        """Adds the specified vertex to the graph.

        Overrides may add additional arguments as necessary."""

    @abstractmethod
    def remove_vertex(self, vertex: VertT) -> None:
        """Removes the specified vertex from the graph.

        :raises KeyError: Specified vertex is not in the graph."""

    @abstractmethod
    def discard_vertex(self, vertex: VertT) -> None:
        """Removes the specified vertex from the graph.

        Does not raise an error if the vertex is not present."""

    @abstractmethod
    def add_edge(self, head: VertT, tail: VertT) -> None:
        """Adds an edge between the specified vertices.

        Overrides may add additional arguments as necessary."""

    @abstractmethod
    def remove_edge(self, head: VertT, tail: VertT) -> None:
        """Removes the specified edge from the graph.

        :raises KeyError: Specified edge is not in the graph."""

    @abstractmethod
    def discard_edge(self, head: VertT, tail: VertT) -> None:
        """Removes the specified edge from the graph.

        Does not raise an error if the edge is not present."""

    @abstractmethod
    def clear(self) -> None:
        """Removes all vertices and edges from the graph."""

    @abstractmethod
    def clear_edges(self) -> None:
        """Removes all edges from the graph."""

    @abstractmethod
    def neighbors(self, vertex: VertT) -> Iterable[VertT]:
        """Returns an Iterable of vertices which share an edge with this vertex, regardless of direction."""

    def connected(self, a: VertT, b: VertT) -> bool:
        """Returns `True` if there is an Edge between `a` and `b`, regardless of direction."""
        return b in self.neighbors(a)

    def __lt__(self, other: Self) -> bool:
        """Returns whether `self` is a proper subgraph of `other`."""
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.edges < other.edges and self.vertices < other.vertices

    def __le__(self, other: Self) -> bool:
        """Returns whether `self` is an improper subgraph of `other`."""
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.edges <= other.edges and self.vertices <= other.vertices

    def __eq__(self, other: Self | object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return other is self or (self.vertices == other.vertices and self.edges == other.edges)

    def __ge__(self, other: Self) -> bool:
        """Returns whether `self` is an improper supergraph of `other`."""
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.edges >= other.edges and self.vertices >= other.vertices

    def __gt__(self, other: Self) -> bool:
        """Returns whether `self` is a proper supergraph of `other`."""
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.edges > other.edges and self.vertices > other.vertices

    @abstractmethod
    def __and__(self, other: Self) -> Self:
        """Return the intersection of the two Graphs."""
        raise NotImplementedError

    @abstractmethod
    def __iand__(self, other: Self) -> Self:
        """Update `self` to the intersection of `self` and `other` in-place."""
        raise NotImplementedError

    @abstractmethod
    def __or__(self, other: Self) -> Self:
        """Return the union of the two Graphs."""
        raise NotImplementedError

    @abstractmethod
    def __ior__(self, other: Self) -> Self:
        """Update `self` to the union of `self` and `other` in-place."""
        raise NotImplementedError

    @abstractmethod
    def __sub__(self, other: Self) -> Self:
        """Return the difference of the two graphs."""
        raise NotImplementedError

    @abstractmethod
    def __rsub__(self, other: Self) -> Self:
        """Return the difference of the two graphs."""
        raise NotImplementedError

    @abstractmethod
    def __isub__(self, other: Self) -> Self:
        """Update `self` to the difference of `self` and `other` in-place."""
        raise NotImplementedError

    @abstractmethod
    def __copy__(self) -> Self:
        raise NotImplementedError


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


class DiGraph[VertT: Hashable](BaseGraph[VertT, tuple[VertT, VertT]]):
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
