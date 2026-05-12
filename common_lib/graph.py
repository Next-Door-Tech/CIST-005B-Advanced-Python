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
    def vertices(self) -> Set[VertT]:
        """Returns a (possibly immutable) `Set` of all vertices in the Graph."""

    @abstractmethod
    @property
    def edges(self) -> Set[EdgeT]:
        """Returns a (possibly immutable) `Set` of all edges in the Graph."""

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
    def add_edge(self, source: VertT, dest: VertT) -> None:
        """Adds an edge between the specified vertices.

        Overrides may add additional arguments as necessary."""

    @abstractmethod
    def remove_edge(self, source: VertT, dest: VertT) -> None:
        """Removes the specified edge from the graph.

        :raises KeyError: Specified edge is not in the graph."""

    @abstractmethod
    def discard_edge(self, source: VertT, dest: VertT) -> None:
        """Removes the specified edge from the graph.

        Does not raise an error if the edge is not present."""

    @abstractmethod
    def neighbors(self, vertex: VertT) -> Set[VertT]:
        """Returns a Set of vertices which are the destination of an edge starting at the supplied vertex."""

    def connected(self, source: VertT, dest: VertT) -> bool:
        """Returns `True` if there is an Edge from `source` to `dest`."""
        return dest in self.neighbors(source)

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
        return self.vertices == other.vertices and self.edges == other.edges

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
    """A simple graph (undirected, unweighted, no duplicate edges)."""

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

    def add_edge(self, source: VertT, dest: VertT) -> None:
        edge = frozenset((source, dest))
        if not edge <= self._vertices:
            s = "Provided vertices are not present in this Graph:"
            if source not in self._vertices:
                s += f" source: {source!r}"
            if dest not in self._vertices:
                s += f" dest: {dest!r}"
            raise KeyError(s)
        if len(edge) < 2:
            raise ValueError(
                f"Source and dest must be distinct in a {type(self).__name__}, got ({source!r}, {dest!r}).")
        self._edges.add(edge)

    def remove_edge(self, source: VertT, dest: VertT) -> None:
        try:
            self._edges.remove(frozenset((source, dest)))
        except KeyError:
            raise KeyError(f"No edge between {source!r} and {dest!r}") from None

    def discard_edge(self, source: VertT, dest: VertT) -> None:
        self._edges.discard(frozenset((source, dest)))

    def neighbors(self, vertex: VertT) -> Set[VertT]:
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

