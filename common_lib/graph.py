from collections.abc import Iterable, Hashable, Generator, Mapping, MutableMapping
from numbers import Real
from typing import Self, NoReturn, overload, Unpack, Any
from abc import ABC, abstractmethod

from dataclasses import dataclass, field
from weakref import WeakSet

from common_lib.hash_table import HashSet, HashMap
from common_lib.graph_abc import *

__all__ = [
    "Graph",
    "DiGraph",
    "MultiGraph",
    "MultiDiGraph"
]


class _Node[NodeKT: Hashable, DataKT: Hashable, DataVT](MutableMapping[DataKT, DataVT]):
    """Internal representation for nodes."""

    __slots__ = '_graph', '_key', '_data', '_edges', '__weakref__'

    _graph: Graph
    _key: NodeKT
    _data: HashMap[DataKT, DataVT]
    _edges: WeakSet[_Edge]

    def __init__(self, graph: Graph, key: NodeKT, /, **data) -> None:
        self._graph = graph
        self._key = key
        self._data = HashMap(**data)
        self._edges = WeakSet()

    def __getitem__(self, key: DataKT, /) -> DataVT:
        return self._data[key]

    def __setitem__(self, key: DataKT, value: DataVT, /) -> None:
        self._data[key] = value

    def __delitem__(self, key: DataKT, /) -> None:
        del self._data[key]

    def __len__(self) -> int:
        return self._data.__len__()

    def __iter__(self) -> Generator[DataKT]:
        return self._data.__iter__()

    def __hash__(self) -> int:
        return hash(self._key)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        else:
            return self._key is other._key or self._key == other._key


# noinspection PyProtectedMember
class _Nodes[NodeKT: Hashable, DataKT: Hashable, DataVT](HashMap[NodeKT, _Node[NodeKT, DataKT, DataVT]]):
    """Internal container class for nodes."""

    def __init__(self, graph: Graph) -> None:
        super().__init__()
        self._graph: Graph = graph

    def add(self, node: NodeKT, **data) -> None:
        if node not in self:
            self[node] = _Node(self._graph, node, **data)
        else:
            self[node]._data.update(**data)

    def remove(self, node: NodeKT) -> None:
        node = self.pop(node)
        for edge in node._edges:
            self._graph._edges.discard(*edge._nodes)

    def discard(self, node: NodeKT) -> None:
        try:
            self.remove(node)
        except KeyError:
            pass


class _Edge[NodeKT: Hashable, DataKT: Hashable, DataVT](Edge[NodeKT], MutableMapping[DataKT, DataVT]):
    """Internal representation for edges in simple graphs."""

    __slots__ = '_graph', '_nodes', '_data', '__weakref__'

    _graph: Graph
    _nodes: frozenset[NodeKT]
    _data: HashMap[DataKT, DataVT]

    def __init__(self, graph: Graph, head: NodeKT, tail: NodeKT, _=None, /, **data) -> None:
        self._graph = graph
        self._nodes = frozenset({head, tail})
        self._data = HashMap(**data)

    def __hash__(self) -> int:
        return hash(self._nodes)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, type(self)):
            return self._nodes == other._nodes
        elif isinstance(other, set | frozenset):
            return self._nodes == other
        else:
            return NotImplemented

    def __getitem__(self, key: DataKT, /) -> DataVT:
        return self._data[key]

    def __setitem__(self, key: DataKT, value: DataVT, /) -> None:
        self._data[key] = value

    def __delitem__(self, key: DataKT, /) -> None:
        del self._data[key]

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Generator[DataKT]:
        return iter(self._data)

    def __contains__(self, node: NodeKT) -> bool:
        return node in self._nodes


class _DiEdge[NodeKT: Hashable, DataKT: Hashable, DataVT](_Edge[NodeKT, DataKT, DataVT]):
    """Internal representation for edges in directed graphs."""

    __slots__ = ()

    def __init__(self, graph: Graph, head: NodeKT, tail: NodeKT, _=None, /, **data) -> None:
        super().__init__(graph, head, tail, **data)
        self._nodes = (head, tail)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, type(self)):
            return self._nodes == other._nodes
        elif isinstance(other, tuple):
            return self._nodes == other
        else:
            return NotImplemented

    @property
    def head(self) -> NodeKT:
        return self._nodes[0]

    @property
    def tail(self) -> NodeKT:
        return self._nodes[1]


class _MultiEdge[NodeKT: Hashable, EdgeKT: Hashable, DataKT: Hashable, DataVT](_Edge[NodeKT, DataKT, DataVT]):
    """Internal representation for edges in multigraphs."""

    __slots__ = '_key',

    _key: EdgeKT

    def __init__(self, graph: Graph, head: NodeKT, tail: NodeKT, key: EdgeKT, /, **data) -> None:
        super().__init__(graph, head, tail, key, **data)
        self._key = key

    def __hash__(self) -> int:
        return hash((self._nodes, self._key))


class _MultiDiEdge[NodeKT: Hashable, EdgeKT: Hashable, DataKT: Hashable, DataVT] \
            (_DiEdge[NodeKT, DataKT, DataVT], _MultiEdge[NodeKT, EdgeKT, DataKT, DataVT]):
    """Internal representation for edges in directed multigraphs."""

    __slots__ = ()

    def __init__(self, graph: Graph, head: NodeKT, tail: NodeKT, key: EdgeKT, /, **data) -> None:
        super().__init__(graph, head, tail, key, **data)
        self._key = key


class _EdgesABC[NodeKT: Hashable, EdgeKT: Hashable, EdgeT: _Edge](HashMap[EdgeKT, EdgeT], ABC):
    _graph: Graph

    def __init__(self, graph: Graph) -> None:
        super().__init__()
        self._graph: Graph = graph

    @abstractmethod
    def add(self, head: NodeKT, tail: NodeKT, **data) -> None: ...

    @abstractmethod
    def remove(self, head: NodeKT, tail: NodeKT) -> None: ...

    @abstractmethod
    def discard(self, head: NodeKT, tail: NodeKT) -> None: ...


# noinspection PyProtectedMember
class _Edges[NodeKT: Hashable, DataKT: Hashable, DataVT](
    _EdgesABC[NodeKT, frozenset[NodeKT], _Edge[NodeKT, DataKT, DataVT]]
):
    """Internal container class for edges in simple graphs."""

    type KeyT = _Edge[NodeKT, DataKT, DataVT] | tuple[NodeKT, NodeKT] | frozenset[NodeKT]

    def __getitem__(self, edge: KeyT) -> _Edge[NodeKT, DataKT, DataVT]:
        if isinstance(edge, _Edge):
            return super().__getitem__(frozenset(edge._nodes))
        else:
            return super().__getitem__(frozenset(edge))

    def __delitem__(self, edge: KeyT) -> None:
        if isinstance(edge, _Edge):
            super().__delitem__(frozenset(edge._nodes))
        else:
            super().__delitem__(frozenset(edge))

    def __contains__(self, edge: KeyT) -> bool:
        if isinstance(edge, _Edge):
            return super().__contains__(frozenset(edge._nodes))
        else:
            return super().__contains__(frozenset(edge))

    def add(self, head: NodeKT, tail: NodeKT, **data) -> None:
        edge = frozenset((head, tail))
        if edge not in self:
            if head not in self._graph or tail not in self._graph:
                raise KeyError
            self[edge] = _Edge(self._graph, head, tail, **data)
            self._graph._nodes[head]._edges.add(self[edge])
            self._graph._nodes[tail]._edges.add(self[edge])
        else:
            self[edge]._data.update(**data)

    def remove(self, head: NodeKT, tail: NodeKT) -> None:
        del self[head, tail]

    def discard(self, head: NodeKT, tail: NodeKT) -> None:
        try:
            self.remove(head, tail)
        except KeyError:
            pass


# noinspection PyProtectedMember
class _DiEdges[NodeKT: Hashable, DataKT: Hashable, DataVT](
    _EdgesABC[NodeKT, tuple[NodeKT, NodeKT], _DiEdge[NodeKT, DataKT, DataVT]]
):
    """Internal container class for edges in directed graphs."""

    type KeyT = _DiEdge[NodeKT, DataKT, DataVT] | tuple[NodeKT, NodeKT]

    def __getitem__(self, edge: KeyT) -> _Edge[NodeKT, DataKT, DataVT]:
        if isinstance(edge, _DiEdge):
            return super().__getitem__(edge._nodes)
        else:
            return super().__getitem__(edge)

    def __delitem__(self, edge: KeyT) -> None:
        if isinstance(edge, _DiEdge):
            super().__delitem__(edge._nodes)
        else:
            super().__delitem__(edge)

    def __contains__(self, edge: KeyT) -> bool:
        if isinstance(edge, _DiEdge):
            return super().__contains__(edge._nodes)
        else:
            return super().__contains__(edge)

    def add(self, head: NodeKT, tail: NodeKT, **data) -> None:
        edge = head, tail
        if edge not in self:
            if head not in self._graph or tail not in self._graph:
                raise KeyError
            self[edge] = _DiEdge(self._graph, head, tail, **data)
            self._graph._nodes[head]._edges.add(self[edge])
            self._graph._nodes[tail]._edges.add(self[edge])
        else:
            self[edge]._data.update(**data)

    def remove(self, head: NodeKT, tail: NodeKT) -> None:
        del self[head, tail]

    def discard(self, head: NodeKT, tail: NodeKT) -> None:
        try:
            self.remove(head, tail)
        except KeyError:
            pass


class _MultiEdgesABC[NodeKT: Hashable, EdgeKT: Hashable, MultiKT: Hashable, EdgeT: _MultiEdge](
    HashMap[EdgeKT | tuple[NodeKT, NodeKT, MultiKT], EdgeT],
    _EdgesABC[NodeKT, EdgeKT | tuple[NodeKT, NodeKT, MultiKT], EdgeT],
    ABC
):

    @abstractmethod
    def add(self, head: NodeKT, tail: NodeKT, key: MultiKT = None, **data) -> None: ...

    @abstractmethod
    def remove(self, head: NodeKT, tail: NodeKT, key: MultiKT) -> None: ...

    @abstractmethod
    def discard(self, head: NodeKT, tail: NodeKT, key: MultiKT) -> None: ...


# noinspection PyProtectedMember
class _MultiEdges[NodeKT: Hashable, EdgeKT: Hashable, DataKT: Hashable, DataVT](
    _MultiEdgesABC[NodeKT, EdgeKT, frozenset[NodeKT], _MultiEdge[NodeKT, EdgeKT, DataKT, DataVT]]
):
    """Internal container class for edges in multigraphs."""

    type KeyT = _Edge[NodeKT, DataKT, DataVT] | tuple[NodeKT, NodeKT] | frozenset[NodeKT]

    def __getitem__(self, edge: KeyT) -> HashMap[EdgeKT, _MultiEdge[NodeKT, EdgeKT, DataKT, DataVT]]:
        if isinstance(edge, _Edge):
            return super().__getitem__(frozenset(edge._nodes))
        else:
            return super().__getitem__(frozenset(edge))

    def __delitem__(self, edge: KeyT) -> None:
        if isinstance(edge, _Edge):
            super().__delitem__(frozenset(edge._nodes))
        else:
            super().__delitem__(frozenset(edge))

    def __contains__(self, edge: KeyT) -> bool:
        if isinstance(edge, _Edge):
            return super().__contains__(frozenset(edge._nodes))
        else:
            return super().__contains__(frozenset(edge))

    def add(self, head: NodeKT, tail: NodeKT, key: EdgeKT = None, **data) -> None:
        edge = frozenset((head, tail))
        if edge not in self:
            if head not in self._graph or tail not in self._graph:
                raise KeyError

            if key is None:
                key = 0

            self[edge] = HashMap()

        if key is None:
            key = int(max((-1, *(key for key in self[edge] if isinstance(key, Real))))) + 1

        if key in self[edge]:
            self[edge][key].update(**data)
        else:
            self[edge][key] = _MultiEdge(self._graph, head, tail, key, **data)
            self._graph._nodes[head]._edges.add(self[edge][key])
            self._graph._nodes[tail]._edges.add(self[edge][key])

    def remove(self, head: NodeKT, tail: NodeKT) -> None:
        del self[head, tail]

    def discard(self, head: NodeKT, tail: NodeKT) -> None:
        try:
            self.remove(head, tail)
        except KeyError:
            pass


# noinspection PyProtectedMember
class _MultiDiEdges[NodeKT: Hashable, EdgeKT: Hashable, DataKT: Hashable, DataVT](
    _MultiEdgesABC[NodeKT, EdgeKT, tuple[NodeKT, NodeKT], _MultiDiEdge[NodeKT, EdgeKT, DataKT, DataVT]]
):
    """Internal container class for edges in directed multigraphs."""

    type KeyT = _DiEdge[NodeKT, DataKT, DataVT] | tuple[NodeKT, NodeKT]

    def __getitem__(self, edge: KeyT) -> HashMap[EdgeKT, _MultiDiEdge[NodeKT, EdgeKT, DataKT, DataVT]]:
        if isinstance(edge, _DiEdge):
            return super().__getitem__(edge._nodes)
        else:
            return super().__getitem__(edge)

    def __delitem__(self, edge: KeyT) -> None:
        if isinstance(edge, _DiEdge):
            super().__delitem__(edge._nodes)
        else:
            super().__delitem__(edge)

    def __contains__(self, edge: KeyT) -> bool:
        if isinstance(edge, _DiEdge):
            return super().__contains__(edge._nodes)
        else:
            return super().__contains__(edge)

    def add(self, head: NodeKT, tail: NodeKT, key: EdgeKT = None, **data) -> None:
        edge = head, tail
        if edge not in self:
            if head not in self._graph or tail not in self._graph:
                raise KeyError

            if key is None:
                key = 0

            self[edge] = HashMap()

        if key is None:
            key = int(max((-1, *(key for key in self[edge] if isinstance(key, Real))))) + 1

        if key in self[edge]:
            self[edge][key].update(**data)
        else:
            self[edge][key] = _MultiDiEdge(self._graph, head, tail, key, **data)
            self._graph._nodes[head]._edges.add(self[edge][key])
            self._graph._nodes[tail]._edges.add(self[edge][key])

    def remove(self, head: NodeKT, tail: NodeKT) -> None:
        del self[head, tail]

    def discard(self, head: NodeKT, tail: NodeKT) -> None:
        try:
            self.remove(head, tail)
        except KeyError:
            pass


class _BaseGraph[NodeKT: Hashable, NodeT: _Node, EdgeT: _Edge](GraphABC[NodeT, EdgeT], ABC):
    """Base Methods for Graphs."""

    _nodes: _Nodes[NodeKT, NodeT]
    _edges: _EdgesABC

    #
    # _neighbors: dict[NodeKT, set[EdgeT]]  # maps nodes to their neighbors

    # def __init__(self, nodes: Mapping[NodeKT, NodeT] | None = None, edges: Iterable[Iterable[NodeKT]] | None = None) -> None:
    #     if nodes is not None:
    #         self._nodes = set(nodes)  # fixme
    #         self._endpoints = {v: set() for v in nodes}
    #     else:
    #         self._nodes = set()
    #
    #     self._edges = set()
    #     if edges is not None:
    #         for i, e in enumerate(edges):
    #             try:
    #                 self.add_edge(*e)
    #             except (KeyError, TypeError, ValueError) as exc:
    #                 raise ValueError(f"Failed to add edges[{i}] == {e!r}") from exc
    #
    # @property
    # def nodes(self) -> frozenset[NodeKT]:
    #     return frozenset(self._nodes)
    #
    # @property
    # def edges(self) -> frozenset[EdgeT]:
    #     return frozenset(self._edges)
    #
    # def add_node(self, node: NodeKT) -> None:
    #     self._nodes.add(node)
    #
    # def remove_node(self, node: NodeKT) -> None:
    #     self._nodes.remove(node)
    #     self._neighbors.pop(node)
    #
    # def discard_node(self, node: NodeKT) -> None:
    #     self._nodes.discard(node)
    #     self._neighbors.pop(node)

    def clear(self) -> None:
        self._edges.clear()
        self._nodes.clear()

    def clear_edges(self) -> None:
        self._edges.clear()

    # def __and__(self, other: Self) -> Self:
    #     if not isinstance(other, type(self)):
    #         return NotImplemented
    #     else:
    #         return type(self)(self.nodes & other.nodes, self.edges & other.edges)
    #
    # def __iand__(self, other: Self) -> Self:
    #     if not isinstance(other, type(self)):
    #         return NotImplemented
    #     else:
    #         self._nodes &= other.nodes
    #         self._edges &= other.edges
    #         return self
    #
    # def __or__(self, other: Self) -> Self:
    #     if not isinstance(other, type(self)):
    #         return NotImplemented
    #     else:
    #         return type(self)(self._nodes | other._nodes, self._edges | other._edges)
    #
    # def __ior__(self, other: Self) -> Self:
    #     if not isinstance(other, type(self)):
    #         return NotImplemented
    #     else:
    #         self._nodes |= other.nodes
    #         self._edges |= other.edges
    #         return self
    #
    # def __copy__(self) -> Self:
    #     return type(self)(self._nodes, self._edges)
    #
    # def __iter__(self) -> Generator[NodeKT]:
    #     yield from self._nodes


class Graph[NodeKT: Hashable, NodeDataKT: Hashable, NodeDataVT, EdgeDataKT: Hashable, EdgeDataVT](
    _BaseGraph[NodeKT, _Node[NodeKT, NodeDataKT, NodeDataVT], _Edge[NodeKT, EdgeDataKT, EdgeDataVT]]
):
    """An undirected graph with no duplicate edges."""

    def add_node(self, node: NodeKT) -> None:
        self._nodes.add(node)

    def add_edge(self, a: NodeKT, b: NodeKT) -> None:
        edge = frozenset((a, b))
        if not edge <= self._nodes:
            s = "Provided nodes are not present in this Graph:"
            if a not in self._nodes:
                s += f" a: {a!r}"
            if b not in self._nodes:
                s += f" b: {b!r}"
            raise KeyError(s)
        if len(edge) < 2:
            raise ValueError(
                f"{type(self).__name__} endpoints must be distinct, got hash({a!r}) == hash({b!r}).")
        self._edges.add(edge)

    def remove_edge(self, a: NodeT, b: NodeT) -> None:
        try:
            self._edges.remove(frozenset((a, b)))
        except KeyError:
            raise KeyError(f"No edge between {a!r} and {b!r}") from None

    def discard_edge(self, a: NodeT, b: NodeT) -> None:
        self._edges.discard(frozenset((a, b)))

    def is_multigraph(self) -> bool:
        return False

    def is_directed(self) -> bool:
        return False

    def neighbors(self, node: NodeT) -> set[NodeT]:
        return set.union(*(edge for edge in self._edges if node in edge)) - {node}

    def __sub__(self, other: Self) -> Self:
        if not isinstance(other, type(self)):
            return NotImplemented
        else:
            vertices = self.nodes - other.nodes
            edges = {e for e in self.edges - other.edges if e <= vertices}

            return type(self)(vertices, edges)

    def __rsub__(self, other: Self) -> Self:
        if not isinstance(other, type(self)):
            return NotImplemented
        else:
            vertices = other.nodes - self.nodes
            edges = {e for e in other.edges - self.edges if e <= vertices}

            return type(self)(vertices, edges)

    def __isub__(self, other: Self) -> Self:
        if not isinstance(other, type(self)):
            return NotImplemented
        else:
            self._nodes -= other.nodes
            self._edges -= other.edges
            for e in self._edges:
                if not e <= self._nodes:
                    self._edges.remove(e)
            return self

    def get_edge_data(self, head, tail) -> dict:
        """Return the data dictionary associated with the edge from head to tail."""


class DiGraph[NodeKT: Hashable = Hashable, NodeDataKT: Hashable = Hashable, NodeDataVT = Any,
              EdgeDataKT: Hashable = Hashable, EdgeDataVT = Any](
    Graph[NodeKT, NodeDataKT, NodeDataVT, EdgeDataKT, EdgeDataVT],
    _BaseGraph[NodeKT, _Node[NodeKT, NodeDataKT, NodeDataVT], _DiEdge[NodeKT, EdgeDataKT, EdgeDataVT]]
):
    """A simple directed graph (unweighted, no duplicate edges)."""

    type EdgeT = tuple[NodeT, NodeT]

    _nodes: set[NodeT]
    _edges: set[EdgeT]

    def add_edge(self, head: NodeT, tail: NodeT) -> None:
        edge_set = frozenset((head, tail))
        if not edge_set <= self._vertices:
            s = "Provided nodes are not present in this Graph:"
            if head not in self._vertices:
                s += f" head: {head!r}"
            if tail not in self._vertices:
                s += f" tail: {tail!r}"
            raise KeyError(s)
        if len(edge_set) < 2:
            raise ValueError(
                f"{type(self).__name__}: head and tail must be distinct, got hash({head!r}) == hash({tail!r})")
        self._edges.add((head, tail))

    def remove_edge(self, head: NodeT, tail: NodeT) -> None:
        try:
            self._edges.remove((head, tail))
        except KeyError:
            raise KeyError(f"No edge between {head!r} and {tail!r}") from None

    def discard_edge(self, head: NodeT, tail: NodeT) -> None:
        self._edges.discard((head, tail))

    def is_multigraph(self) -> bool:
        return False

    def is_directed(self) -> bool:
        return True

    def neighbors(self, node: NodeT) -> set[NodeT]:
        return set(e[1] for e in self.edges if node is e[0] or node == e[0])

    def __sub__(self, other: Self) -> Self:
        if not isinstance(other, type(self)):
            return NotImplemented
        else:
            vertices = self.nodes - other.nodes
            edges = {e for e in self.edges - other.edges if all(v in vertices for v in e)}

            return type(self)(vertices, edges)

    def __rsub__(self, other: Self) -> Self:
        if not isinstance(other, type(self)):
            return NotImplemented
        else:
            vertices = other.nodes - self.nodes
            edges = {e for e in other.edges - self.edges if all(v in vertices for v in e)}

            return type(self)(vertices, edges)

    def __isub__(self, other: Self) -> Self:
        if not isinstance(other, type(self)):
            return NotImplemented
        else:
            self._vertices -= other.nodes
            self._edges -= other.edges
            for e in self._edges:
                if not all(v in self._vertices for v in e):
                    self._edges.remove(e)
            return self


class MultiGraph[NodeKT: Hashable, NodeDataKT: Hashable, NodeDataVT,
                 EdgeKT: Hashable, EdgeDataKT: Hashable, EdgeDataVT](
    Graph[NodeKT, NodeDataKT, NodeDataVT, EdgeDataKT, EdgeDataVT],
    _BaseGraph[NodeKT, _Node[NodeKT, NodeDataKT, NodeDataVT], _MultiEdge[NodeKT, EdgeKT, EdgeDataKT, EdgeDataVT]]
):
    """An undirected multigraph."""


class MultiDiGraph[NodeKT: Hashable, NodeDataKT: Hashable, NodeDataVT,
                   EdgeKT: Hashable, EdgeDataKT: Hashable, EdgeDataVT](
    Graph[NodeKT, NodeDataKT, NodeDataVT, EdgeDataKT, EdgeDataVT],
    _BaseGraph[NodeKT, _Node[NodeKT, NodeDataKT, NodeDataVT], _MultiDiEdge[NodeKT, EdgeKT, EdgeDataKT, EdgeDataVT]]
):
    """A directed multigraph."""
