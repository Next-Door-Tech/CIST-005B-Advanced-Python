from collections.abc import Iterable, Hashable
from typing import Protocol, runtime_checkable, Self
from abc import ABC, abstractmethod

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


class DiGraphABC[VertT: Hashable, EdgeT: Edge](GraphABC[VertT, EdgeT], ABC):
    """A Graph containing multiple Vertices connected via directed Edges."""

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
