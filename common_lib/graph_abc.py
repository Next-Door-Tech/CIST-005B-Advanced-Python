from collections.abc import Iterable, Hashable, Collection
from typing import Protocol, runtime_checkable, Self, overload
from abc import ABC, abstractmethod
import networkx as nx

__all__ = ("Weight", "Edge", "WeightedEdge", "GraphABC", "DiGraphABC")


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
    to represent directed edges, weights, etc.

    This may be a proxy type; no guarantees are made regarding how
    edges are internally represented in a graph."""

    __slots__ = ()

    @abstractmethod
    def __contains__(self, vertex: VertT) -> bool:
        """Return True if vertex is either the head or tail of this edge."""

    @abstractmethod
    def __eq__(self, other: Self | object) -> bool:
        """Return True if the edges are equal, i.e. both edges have
        the same endpoints and any additional values are equal."""


class WeightedEdge[VertT: Hashable](Edge[VertT], Protocol):
    """A weighted edge in a Graph."""

    __slots__ = ()

    @property
    @abstractmethod
    def weight(self) -> Weight:
        """Return the weight of this edge."""


class GraphABC[VertT: Hashable, EdgeT: Edge](Collection[VertT], ABC):
    """A Graph containing multiple Vertices connected via edges."""

    __slots__ = ()

    @overload
    @abstractmethod
    def __init__(self, /) -> None:
        """Create an empty Graph."""

    @overload
    @abstractmethod
    def __init__(self, /, edges: Iterable[EdgeT]) -> None:
        """Create a Graph with the specified edges, creating vertices based on supplied edge endpoints."""

    @overload
    @abstractmethod
    def __init__(self, edges: Iterable[EdgeT] = None, vertices: Iterable[VertT] = None, /, *,
                 strict: bool = True) -> None:
        """Create a graph with the provided set of vertices and edges between those vertices.
        :raises ValueError: strict is True and a provided edge's endpoints are not vertices in this Graph."""

    @abstractmethod
    def __init__(self, edges: Iterable[EdgeT] = None, vertices: Iterable[VertT] = None,
                 /, *, strict: bool = True) -> None:
        """Create a graph with the provided set of vertices and edges between those vertices.
        :raises ValueError: strict is True and a provided edge's endpoints are not vertices in this Graph."""

    def __contains__(self, vertex: VertT | object) -> bool:
        """Returns `True` if the Graph contains the specified vertex."""
        return vertex in self.vertices

    @property
    @abstractmethod
    def vertices(self) -> Iterable[VertT]:
        """Returns an Iterable of all vertices in the Graph."""

    @property
    @abstractmethod
    def edges(self) -> Iterable[EdgeT]:
        """Returns an Iterable of all edges in the Graph."""

    @abstractmethod
    def add_vertex(self, vertex: VertT) -> None:
        """Adds the specified vertex to the graph.

        Overrides may add additional arguments as necessary."""

    @abstractmethod
    def remove_vertex(self, vertex: VertT) -> None:
        """Removes the specified vertex from the graph. Also removes any attached edges.

        :raises KeyError: Specified vertex is not in the graph."""

    @abstractmethod
    def discard_vertex(self, vertex: VertT) -> None:
        """Removes the specified vertex from the graph. Also removes any attached edges.

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
    def is_multigraph(self) -> bool:
        """Return whether this graph is a multigraph."""

    @abstractmethod
    def is_directed(self) -> bool:
        """Return whether this graph is a multigraph."""

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
        """Returns `True` if there is an edge between `a` and `b`, regardless of direction."""
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


GraphABC.register(nx.Graph)


class DiGraphABC[VertT: Hashable, EdgeT: Edge](GraphABC[VertT, EdgeT], ABC):
    """A Graph containing multiple vertices connected via directed edges."""

    @abstractmethod
    def heads(self, vertex: VertT) -> Iterable[VertT]:
        """Returns an Iterable of vertices which are the head of an edge with this vertex as the tail."""

    def heads_to(self, head: VertT, tail: VertT) -> bool:
        """Returns whether there is a directed edge from `head` to `tail`."""
        return head in self.heads(tail)

    @abstractmethod
    def tails(self, vertex: VertT) -> Iterable[VertT]:
        """Returns an Iterable of vertices which are the tail of an edge with this vertex as the head."""

    def tails_from(self, tail: VertT, head: VertT) -> bool:
        """Returns whether there is a directed edge to `tail` from `head`."""
        return tail in self.tails(head)

    def is_directed(self) -> bool:
        """Return whether this graph is a multigraph."""
        return True


DiGraphABC.register(nx.DiGraph)
