from collections.abc import Collection, Iterable, Hashable
from typing import Protocol, Literal
from abc import abstractmethod


class Edge[VertT: Hashable](Protocol):
    """An edge in a Graph.
    Must contain two vertices as endpoints, though they may be identical for a loopback edge."""

    __slots__ = ()

    @abstractmethod
    def __contains__(self, vertex: VertT) -> bool:
        """Return True if vertex is either the start or end of this edge."""
        ...


class WEdge[VertT: Hashable](Edge[VertT], Protocol):
    """A weighted edge in a Graph.
    Must return the edge weight via the __len__ method."""

    __slots__ = ()

    @abstractmethod
    def __len__(self) -> int:
        """Return the weight of this edge."""
        ...


class DiEdge[VertT: Hashable](Edge[VertT], Protocol):
    """A directed edge in a Graph.
    Must contain two indexable vertices, though they may be identical for a loopback edge."""

    __slots__ = ()

    @abstractmethod
    def __getitem__(self, index: Literal[0, 1]) -> VertT:
        """Return the start vertex or end vertex of this graph."""
        ...


class WDiEdge[VertT: Hashable](WEdge[VertT], DiEdge[VertT], Protocol):
    """A weighted and directed edge."""

    __slots__ = ()
