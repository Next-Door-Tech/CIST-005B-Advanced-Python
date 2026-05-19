from collections.abc import Iterable, Hashable, Collection
from typing import Protocol, Self, overload
from numbers import Real
from abc import ABC, abstractmethod

import networkx as nx

__all__ = ("Edge", "WeightedEdge", "GraphABC", "DiGraphABC")


class Edge[NodeT: Hashable](Protocol):
    """An edge in a Graph. Must contain two nodes as endpoints,
    though they may be identical for a loopback edge.

    Additional information may be assigned to an edge
    to represent directed edges, weights, etc.

    This may be a proxy type; no guarantees are made regarding how
    edges are internally represented in a graph."""

    __slots__ = ()

    @abstractmethod
    def __contains__(self, node: NodeT) -> bool:
        """Return True if node is either the head or tail of this edge."""
        raise NotImplementedError

    @abstractmethod
    def __eq__(self, other: Self | object) -> bool:
        """Return True if the edges are equal, i.e. both edges have
        the same endpoints and direction."""
        raise NotImplementedError


class WeightedEdge[NodeT: Hashable](Edge[NodeT], Protocol):
    """A weighted edge in a Graph."""

    __slots__ = ()

    @property
    @abstractmethod
    def weight(self) -> Real:
        """Return the weight of this edge."""
        raise NotImplementedError


class GraphABC[NodeT: Hashable, EdgeT: Edge](Collection[NodeT], ABC):
    """A Graph containing multiple nodes connected via edges."""

    __slots__ = ()

    @overload
    @abstractmethod
    def __init__(self, /) -> None:
        """Create an empty Graph."""

    @overload
    @abstractmethod
    def __init__(self, /, edges: Iterable[EdgeT]) -> None:
        """Create a Graph with the specified edges, creating nodes based on supplied edge endpoints."""

    @overload
    @abstractmethod
    def __init__(self, edges: Iterable[EdgeT] | None = None, nodes: Iterable[NodeT] | None = None, /, *,
                 strict: bool = True) -> None:
        """Create a graph with the provided set of nodes and edges between those nodes.
        :raises ValueError: strict is True and a provided edge's endpoints are not nodes in this Graph."""

    @abstractmethod
    def __init__(self, edges: Iterable[EdgeT] | None = None, nodes: Iterable[NodeT] | None = None,
                 /, *, strict: bool = True) -> None:
        """Create a graph with the provided set of nodes and edges between those nodes.
        :raises ValueError: strict is True and a provided edge's endpoints are not nodes in this Graph."""
        raise NotImplementedError

    def __contains__(self, node: NodeT | object) -> bool:
        """Returns `True` if the Graph contains the specified node."""
        return node in self.nodes

    @abstractmethod
    def __len__(self) -> int:
        """Returns the number of nodes in the graph."""
        raise NotImplementedError

    @property
    @abstractmethod
    def nodes(self) -> Iterable[NodeT]:
        """Returns an Iterable of all nodes in the Graph."""
        raise NotImplementedError

    @abstractmethod
    def add_node(self, node: NodeT) -> None:
        """Adds the specified node to the graph.

        Overrides may add additional arguments as necessary."""
        raise NotImplementedError

    @abstractmethod
    def remove_node(self, node: NodeT) -> None:
        """Removes the specified node from the graph. Also removes any attached edges.

        :raises KeyError: Specified node is not in the graph."""
        raise NotImplementedError

    @abstractmethod
    def discard_node(self, node: NodeT) -> None:
        """Removes the specified node from the graph. Also removes any attached edges.

        Does not raise an error if the node is not present."""
        raise NotImplementedError

    @abstractmethod
    def has_node(self, node: NodeT) -> bool:
        """Returns whether the graph has a given node."""
        raise NotImplementedError

    @property
    @abstractmethod
    def edges(self) -> Iterable[EdgeT]:
        """Returns an Iterable of all edges in the Graph."""
        raise NotImplementedError

    @abstractmethod
    def add_edge(self, head: NodeT, tail: NodeT) -> None:
        """Adds an edge between the specified nodes.

        Overrides may add additional arguments as necessary."""
        raise NotImplementedError

    @abstractmethod
    def remove_edge(self, head: NodeT, tail: NodeT) -> None:
        """Removes the specified edge from the graph.

        :raises KeyError: Specified edge is not in the graph."""
        raise NotImplementedError

    @abstractmethod
    def discard_edge(self, head: NodeT, tail: NodeT) -> None:
        """Removes the specified edge from the graph.

        Does not raise an error if the edge is not present."""
        raise NotImplementedError

    @abstractmethod
    def has_edge(self, head: NodeT, tail: NodeT) -> bool:
        """Returns whether the graph has an edge from head to tail."""
        raise NotImplementedError

    @abstractmethod
    def is_multigraph(self) -> bool:
        """Return whether this graph is a multigraph."""
        raise NotImplementedError

    @abstractmethod
    def is_directed(self) -> bool:
        """Return whether this graph is a multigraph."""
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        """Removes all nodes and edges from the graph."""
        raise NotImplementedError

    @abstractmethod
    def clear_edges(self) -> None:
        """Removes all edges from the graph."""
        raise NotImplementedError

    @abstractmethod
    def neighbors(self, node: NodeT) -> Iterable[NodeT]:
        """Returns an Iterable of nodes which share an edge with this node, regardless of direction."""

    def connected(self, a: NodeT, b: NodeT) -> bool:
        """Returns `True` if there is an edge between `a` and `b`, regardless of direction."""
        return b in self.neighbors(a)

    def __lt__(self, other: Self) -> bool:
        """Returns whether `self` is a proper subgraph of `other`."""
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.edges < other.edges and self.nodes < other.nodes

    def __le__(self, other: Self) -> bool:
        """Returns whether `self` is an improper subgraph of `other`."""
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.edges <= other.edges and self.nodes <= other.nodes

    def __eq__(self, other: Self | object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return other is self or (self.nodes == other.nodes and self.edges == other.edges)

    def __ge__(self, other: Self) -> bool:
        """Returns whether `self` is an improper supergraph of `other`."""
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.edges >= other.edges and self.nodes >= other.nodes

    def __gt__(self, other: Self) -> bool:
        """Returns whether `self` is a proper supergraph of `other`."""
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.edges > other.edges and self.nodes > other.nodes

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


class DiGraphABC[NodeT: Hashable, EdgeT: Edge](GraphABC[NodeT, EdgeT], ABC):
    """A Graph containing multiple nodes connected via directed edges."""

    @abstractmethod
    def successors(self, node: NodeT) -> Iterable[NodeT]:
        """Returns an Iterable of nodes which are the tail of an edge with this node as the head."""

    def has_successor(self, head: NodeT, tail: NodeT) -> bool:
        """Returns whether there is a directed edge from `head` to `tail`. (head->tail)"""
        return tail in self.successors(head)

    @abstractmethod
    def predecessors(self, node: NodeT) -> Iterable[NodeT]:
        """Returns an Iterable of nodes which are the head of an edge with this node as the tail."""

    def has_predecessor(self, tail: NodeT, head: NodeT) -> bool:
        """Returns whether there is a directed edge to `tail` from `head`. (tail<-head)"""
        return tail in self.successors(head)

    def is_directed(self) -> bool:
        """Return whether this graph is a multigraph."""
        return True


DiGraphABC.register(nx.DiGraph)
