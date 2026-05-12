from collections.abc import Collection, Iterable, Hashable, Set
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

    @property
    def weight(self) -> Weight:

    @abstractmethod
    def __len__(self) -> int:
        """Return the weight of this edge."""
        ...


class GraphABC[VertT: Hashable, EdgeT: Edge](Collection[VertT], ABC):
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
    def add_vertex(self, vertex: VertT, *args, **kwargs) -> None:
        """Adds the specified vertex to the graph. Overrides may add additional arguments as necessary."""

    @abstractmethod
    def add_edge(self, source: VertT, dest: VertT, *args, **kwargs) -> None:
        """Adds an edge between the specified vertices. Overrides may add additional arguments as necessary."""

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
