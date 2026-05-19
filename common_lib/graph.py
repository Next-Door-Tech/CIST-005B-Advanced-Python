from collections.abc import Iterable, Hashable, Generator
from typing import Self, Any, MutableMapping
from abc import ABC

from dataclasses import dataclass, field

from common_lib.hash_table import HashSet, HashMap
from common_lib.graph_abc import *

__all__ = [
    "Graph",
    "DiGraph",
    "MultiGraph",
    "MultiDiGraph"
]


class _Node[NodeKT: Hashable, DataKT: Hashable, DataVT](MutableMapping[DataKT, DataVT]):
    __slots__ = '_graph', '_key', '_data', '_edges', '__weakref__'

    _graph: Graph
    _key: NodeKT
    _data: HashMap[DataKT, DataVT]
    _edges: HashSet[_Edge]

    def __init__(self, graph: Graph, key: NodeKT, /, **data) -> None:
        self._graph = graph
        self._key = key
        self._data = HashMap(**data)
        self._edges = HashSet[_Edge]()

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


class _Edge[NodeKT: Hashable, DataKT: Hashable, DataVT](Edge[NodeKT], MutableMapping[DataKT, DataVT]):
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
        else:
            return NotImplemented

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

    def __contains__(self, node: NodeKT) -> bool:
        return node in self._nodes


class _DiEdge[NodeKT: Hashable, DataKT: Hashable, DataVT](_Edge[NodeKT, DataKT, DataVT]):
    __slots__ = ()

    def __init__(self, graph: Graph, head: NodeKT, tail: NodeKT, _=None, /, **data) -> None:
        super().__init__(graph, head, tail, **data)
        self._nodes = (head, tail)

    @property
    def head(self) -> NodeKT:
        return self._nodes[0]

    @property
    def tail(self) -> NodeKT:
        return self._nodes[1]


class _MultiEdge[NodeKT: Hashable, EdgeKT: Hashable, DataKT: Hashable, DataVT](_Edge[NodeKT, DataKT, DataVT]):
    __slots__ = '_key',

    _key: EdgeKT

    def __init__(self, graph: Graph, head: NodeKT, tail: NodeKT, key: EdgeKT, /, **data) -> None:
        super().__init__(graph, head, tail, key, **data)
        self._key = key

    def __hash__(self) -> int:
        return hash((self._nodes, self._key))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        else:
            return (self._nodes, self._key) == (other._nodes, other._key)


class _MultiDiEdge[NodeKT: Hashable, EdgeKT: Hashable, DataKT: Hashable, DataVT] \
            (_DiEdge[NodeKT, DataKT, DataVT], _MultiEdge[NodeKT, EdgeKT, DataKT, DataVT]):
    __slots__ = ()

    def __init__(self, graph: Graph, head: NodeKT, tail: NodeKT, key: EdgeKT, /, **data) -> None:
        super().__init__(graph, head, tail, key, **data)
        self._key = key


class _BaseGraph[NodeKT: Hashable, NodeDataKT: Hashable = Hashable, NodeDataVT = Any,
                 EdgeT: Edge = Edge[NodeKT], EdgeDataKT: Hashable = Hashable, EdgeDataVT = Any] \
            (GraphABC[_Node[NodeKT, NodeDataKT, NodeDataVT], _Edge[EdgeT, EdgeDataKT, EdgeDataVT]], ABC):
    """Base Methods for Graphs."""

    @dataclass(slots=True, weakref_slot=True)
    class _Vertex[T: Hashable, K: Hashable, V]:
        edges: HashSet[NodeKT]
        neighbors: HashSet[NodeKT] = field(default_factory=HashSet)
        data: HashMap[K, V] = field(default_factory=HashMap)

    _vertices: HashMap[NodeKT, _Vertex]  # fixme
    _edges: set[EdgeT]

    _neighbors: dict[NodeKT, set[EdgeT]]  # maps nodes to their neighbors

    def __init__(self, nodes: Iterable[NodeKT] | None = None, edges: Iterable[Iterable[NodeKT]] | None = None) -> None:
        if nodes is not None:
            self._vertices = set(nodes)  # fixme
            self._endpoints = {v: set() for v in nodes}
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
    def nodes(self) -> frozenset[NodeKT]:
        return frozenset(self._vertices)

    @property
    def edges(self) -> frozenset[EdgeT]:
        return frozenset(self._edges)

    def add_node(self, node: NodeKT) -> None:
        self._vertices.add(node)

    def remove_node(self, node: NodeKT) -> None:
        self._vertices.remove(node)
        self._neighbors.pop(node)

    def discard_node(self, node: NodeKT) -> None:
        self._vertices.discard(node)
        self._neighbors.pop(node)

    def clear(self) -> None:
        self._edges.clear()
        self._vertices.clear()

    def clear_edges(self) -> None:
        self._edges.clear()

    def __and__(self, other: Self) -> Self:
        if not isinstance(other, type(self)):
            return NotImplemented
        else:
            return type(self)(self.nodes & other.nodes, self.edges & other.edges)

    def __iand__(self, other: Self) -> Self:
        if not isinstance(other, type(self)):
            return NotImplemented
        else:
            self._vertices &= other.nodes
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
            self._vertices |= other.nodes
            self._edges |= other.edges
            return self

    def __copy__(self) -> Self:
        return type(self)(self._vertices, self._edges)

    def __iter__(self) -> Generator[NodeKT]:
        yield from self._nodes


class Graph[NodeT: Hashable](_BaseGraph[NodeT, frozenset[NodeT]]):
    """An undirected graph with no duplicate edges."""

    type EdgeT = frozenset[NodeT]

    def add_edge(self, a: NodeT, b: NodeT) -> None:
        edge = frozenset((a, b))
        if not edge <= self._vertices:
            s = "Provided nodes are not present in this Graph:"
            if a not in self._vertices:
                s += f" a: {a!r}"
            if b not in self._vertices:
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
            self._vertices -= other.nodes
            self._edges -= other.edges
            for e in self._edges:
                if not e <= self._vertices:
                    self._edges.remove(e)
            return self

    def get_edge_data(self, head, tail) -> dict:
        """Return the data dictionary associated with the edge from head to tail."""


class DiGraph[NodeT: Hashable](_BaseGraph[NodeT, tuple[NodeT, NodeT]], DiGraphABC[NodeT, tuple[NodeT, NodeT]]):
    """A simple directed graph (unweighted, no duplicate edges)."""

    type EdgeT = tuple[NodeT, NodeT]

    _vertices: set[NodeT]
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


class MultiGraph[VertKT: Hashable](Graph[VertKT]):
    """An undirected multigraph."""


class MultiDiGraph[VertKT: Hashable, VertVT](MultiGraph, DiGraph):
    """A directed multigraph."""
