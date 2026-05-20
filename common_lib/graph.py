from collections.abc import Iterable, Hashable, Generator, Mapping, MutableMapping
from numbers import Real
from typing import Self, Any, NoReturn
from abc import ABC, abstractmethod

from weakref import WeakSet

import networkx as nx

from common_lib.hash_table import HashMap
from common_lib.graph_abc import *

__all__ = [
    "Graph",
    "DiGraph",
    "MultiGraph",
    "MultiDiGraph"
]


class _MappingProxy[KT: Hashable, VT](Mapping[KT, VT]):
    """A read-only mapping proxy view descriptor."""

    __slots__ = '_instance'

    _instance: Mapping[KT, VT]
    __objclass__: type[Mapping[KT, VT]]

    def __init__(self, instance: Mapping[KT, VT] | None = None, owner: type[Mapping[KT, VT]] | None = None) -> None:
        if instance is not None:
            self._instance = instance
        if owner is not None:
            self.__objclass__ = owner

    def __set_name__(self, owner: type[Mapping[KT, VT]], name: str) -> None:
        class _NamedMappingProxy(type(self)):
            """A read-only mapping proxy which has been assigned to a member of a class."""
            __doc__ = type(self).__doc__
            __name__ = name
            __qualname__ = f"{owner.__qualname__}.{type(self).__name__}"

        setattr(owner, name, _NamedMappingProxy(None, owner))

    def __get__(self, instance: Mapping[KT, VT], owner: type[Mapping[KT, VT]]) -> Self:
        if instance is None:
            return self
        else:
            class _BoundMappingProxy(type(self)):
                """A read-only mapping proxy which has been bound to an instance."""
                __doc__ = type(self).__doc__
                __qualname__ = f"{type(self).__qualname__}.{__name__}"

            return _BoundMappingProxy(instance, owner)

    def __set__(self, instance: Mapping[KT, VT], value) -> NoReturn:
        raise AttributeError

    def __delete__(self, instance: Mapping[KT, VT]) -> NoReturn:
        raise AttributeError

    def __getitem__(self, key: KT, /) -> VT:
        return self._instance.__getitem__(key)

    def __len__(self) -> int:
        return self._instance.__len__()

    def __iter__(self) -> Generator[KT]:
        yield from self._instance.keys()


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

    _Proxy = _MappingProxy()

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

    _Proxy = _MappingProxy[EdgeKT, EdgeT]()

    def __init__(self, graph: Graph) -> None:
        super().__init__()
        self._graph: Graph = graph

    @abstractmethod
    def add(self, head: NodeKT, tail: NodeKT, **data) -> None:
        ...

    @abstractmethod
    def remove(self, head: NodeKT, tail: NodeKT) -> None:
        ...

    @abstractmethod
    def discard(self, head: NodeKT, tail: NodeKT) -> None:
        ...


# noinspection PyProtectedMember
class _Edges[NodeKT: Hashable, DataKT: Hashable, DataVT](
    _EdgesABC[NodeKT, frozenset[NodeKT], _Edge[NodeKT, DataKT, DataVT]]
):
    """Internal container class for edges in simple graphs."""

    type KeyT = _Edge[NodeKT, DataKT, DataVT] | tuple[NodeKT, NodeKT] | frozenset[NodeKT]

    _Proxy = _MappingProxy()

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

    _Proxy = _MappingProxy()

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
    _EdgesABC[NodeKT, EdgeKT | tuple[NodeKT, NodeKT, MultiKT], EdgeT], ABC
):
    _Proxy = _MappingProxy()

    @abstractmethod
    def add(self, head: NodeKT, tail: NodeKT, key: MultiKT = None, **data) -> None: ...

    # noinspection PyMethodOverriding
    @abstractmethod
    def remove(self, head: NodeKT, tail: NodeKT, key: MultiKT) -> None: ...

    # noinspection PyMethodOverriding
    @abstractmethod
    def discard(self, head: NodeKT, tail: NodeKT, key: MultiKT) -> None: ...


# noinspection PyProtectedMember
class _MultiEdges[NodeKT: Hashable, EdgeKT: Hashable, DataKT: Hashable, DataVT](
    _MultiEdgesABC[NodeKT, EdgeKT, frozenset[NodeKT], _MultiEdge[NodeKT, EdgeKT, DataKT, DataVT]]
):
    """Internal container class for edges in multigraphs."""

    type KeyT = _Edge[NodeKT, DataKT, DataVT] | tuple[NodeKT, NodeKT] | frozenset[NodeKT]

    _Proxy = _MappingProxy()

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

    def remove(self, head: NodeKT, tail: NodeKT, key: EdgeKT) -> None:
        del self[head, tail][key]

    def discard(self, head: NodeKT, tail: NodeKT, key: EdgeKT) -> None:
        try:
            self.remove(head, tail, key)
        except KeyError:
            pass


# noinspection PyProtectedMember
class _MultiDiEdges[NodeKT: Hashable, EdgeKT: Hashable, DataKT: Hashable, DataVT](
    _MultiEdgesABC[NodeKT, EdgeKT, tuple[NodeKT, NodeKT], _MultiDiEdge[NodeKT, EdgeKT, DataKT, DataVT]]
):
    """Internal container class for edges in directed multigraphs."""

    type KeyT = _DiEdge[NodeKT, DataKT, DataVT] | tuple[NodeKT, NodeKT]

    _Proxy = _MappingProxy()

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


# noinspection PyProtectedMember
class _BaseGraph[NodeKT: Hashable, EdgeT: _Edge, EdgesT: _EdgesABC](GraphABC[_Node, EdgeT], ABC):
    """Base Methods for Graphs."""

    _nodes: _Nodes
    _edges: EdgesT

    def clear(self) -> None:
        self._edges.clear()
        self._nodes.clear()

    def clear_edges(self) -> None:
        self._edges.clear()

    def has_node(self, node: NodeKT) -> bool:
        return node in self._nodes

    @property
    def nodes(self) -> Mapping[NodeKT, MutableMapping]:
        return self._nodes._Proxy

    @property
    def edges(self) -> Mapping[Edge[NodeKT], MutableMapping]:
        return self._edges._Proxy

    def __len__(self) -> int:
        return len(self._nodes)

    def __copy__(self) -> Self:
        return type(self)(self._nodes, self._edges)


class Graph[NodeKT: Hashable,
            NodeDataKT: Hashable = str, NodeDataVT = Any,
            EdgeDataKT: Hashable = str, EdgeDataVT = Any](
    _BaseGraph[
        NodeKT,
        _Edge[NodeKT, EdgeDataKT, EdgeDataVT],
        _Edges[NodeKT, EdgeDataKT, EdgeDataVT]
    ]
):
    """An undirected graph with no duplicate edges."""

    def is_multigraph(self) -> bool:
        return False

    def is_directed(self) -> bool:
        return False

    _nodes: _Nodes[NodeKT, NodeDataKT, NodeDataVT]
    _edges: _Edges[NodeKT, EdgeDataKT, EdgeDataVT]

    def __new__(cls, *args, **kwargs) -> Self:
        self = object.__new__(cls)
        self._nodes = _Nodes(self)
        self._edges = _Edges(self)
        return self

    type InitNodes = Iterable[NodeKT] | Mapping[NodeKT, Mapping[str, NodeDataVT]] | None
    type InitEdges = Iterable[Iterable[NodeKT]] | Mapping[Iterable[NodeKT], Mapping[str, EdgeDataVT]] | None

    def __init__(self, nodes: InitNodes = None, edges: InitEdges = None) -> None:

        if nodes is None:
            pass
        elif hasattr(nodes, 'keys') and hasattr(nodes, '__getitem__'):
            nodes: Mapping
            for node in nodes.keys():
                self.add_node(node, **nodes[node])
        elif hasattr(nodes, '__iter__'):
            nodes: Iterable
            for node in nodes:
                self.add_node(node)
        else:
            raise TypeError(f"{type(self).__name__}: nodes == '{type(nodes)}'")

        if edges is None:
            pass
        elif hasattr(edges, 'keys') and hasattr(edges, '__getitem__'):
            edges: Mapping
            for edge in edges.keys():
                self.add_edge(*edge, **edges[edge])
        elif hasattr(edges, '__iter__'):
            edges: Iterable
            for edge in edges:
                self.add_edge(*edge)
        else:
            raise TypeError(f"{type(self).__name__}: edges == '{type(edges)}'")

    def add_node(self, node: NodeKT, /, **data) -> None:
        self._nodes.add(node, **data)

    def remove_node(self, node: NodeKT) -> None:  # TODO
        pass

    def discard_node(self, node: NodeKT) -> None:  # TODO
        pass

    def has_node(self, node: NodeKT) -> bool:  # TODO
        pass

    def has_edge(self, head: NodeKT, tail: NodeKT) -> bool:
        return (head, tail) in self._edges

    def add_edge(self, head: NodeKT, tail: NodeKT, /, **data) -> None:
        self._edges.add(head, tail, **data)

    def remove_edge(self, head: NodeKT, tail: NodeKT) -> None:
        try:
            self._edges.remove(head, tail)
        except KeyError:
            raise KeyError(f"No edge between {head!r} and {tail!r} exists.") from None

    def discard_edge(self, head: NodeKT, tail: NodeKT) -> None:
        self._edges.discard(head, tail)

    def get_edge_data(self, head, tail) -> _Edge:
        """Return the data dictionary associated with the edge from head to tail."""
        return self._edges[head, tail]

    def neighbors(self, node: NodeT) -> set[NodeT]:  # TODO
        return set.union(*(edge for edge in self._edges if node in edge)) - {node}

    def __iter__(self):
        pass


Graph.register(nx.Graph)


class DiGraph[NodeKT: Hashable = Hashable, NodeDataKT: Hashable = Hashable, NodeDataVT = Any,
              EdgeDataKT: Hashable = Hashable, EdgeDataVT = Any](
    Graph[NodeKT, NodeDataKT, NodeDataVT, EdgeDataKT, EdgeDataVT],
    _BaseGraph[
        NodeKT,
        _DiEdge[NodeKT, EdgeDataKT, EdgeDataVT],
        _DiEdges[NodeKT, EdgeDataKT, EdgeDataVT]
    ]
):
    """A simple directed graph (unweighted, no duplicate edges)."""

    _nodes: _Nodes[NodeKT, NodeDataKT, NodeDataVT]
    _edges: _DiEdges[NodeKT, EdgeDataKT, EdgeDataVT]

    def is_multigraph(self) -> bool:
        return False

    def is_directed(self) -> bool:
        return True

    def __new__(cls, *args, **kwargs) -> Self:
        self = object.__new__(cls)
        self._nodes = _Nodes(self)
        self._edges = _DiEdges(self)
        return self


DiGraph.register(nx.DiGraph)


class MultiGraph[NodeKT: Hashable, NodeDataKT: Hashable, NodeDataVT,
                 EdgeKT: Hashable, EdgeDataKT: Hashable, EdgeDataVT](
    Graph[NodeKT, NodeDataKT, NodeDataVT, EdgeDataKT, EdgeDataVT],
    _BaseGraph[
        NodeKT,
        _MultiEdge[NodeKT, EdgeKT, EdgeDataKT, EdgeDataVT],
        _MultiEdges[NodeKT, EdgeKT, EdgeDataKT, EdgeDataVT]
    ]
):
    """An undirected multigraph."""

    _nodes: _Nodes[NodeKT, NodeDataKT, NodeDataVT]
    _edges: _MultiEdges[NodeKT, EdgeKT, EdgeDataKT, EdgeDataVT]

    def is_multigraph(self) -> bool:
        return True

    def is_directed(self) -> bool:
        return False

    def __new__(cls, *args, **kwargs) -> Self:
        self = object.__new__(cls)
        self._nodes = _Nodes(self)
        self._edges = _MultiEdges(self)
        return self


MultiGraph.register(nx.MultiGraph)


class MultiDiGraph[NodeKT: Hashable, NodeDataKT: Hashable, NodeDataVT,
                   EdgeKT: Hashable, EdgeDataKT: Hashable, EdgeDataVT](
    Graph[NodeKT, NodeDataKT, NodeDataVT, EdgeDataKT, EdgeDataVT],
    _BaseGraph[
        NodeKT,
        _MultiDiEdge[NodeKT, EdgeKT, EdgeDataKT, EdgeDataVT],
        _MultiDiEdges[NodeKT, EdgeKT, EdgeDataKT, EdgeDataVT]
    ]
):
    """A directed multigraph."""

    _nodes: _Nodes[NodeKT, NodeDataKT, NodeDataVT]
    _edges: _MultiDiEdges[NodeKT, EdgeKT, EdgeDataKT, EdgeDataVT]

    def is_multigraph(self) -> bool:
        return True

    def is_directed(self) -> bool:
        return True

    def __new__(cls, *args, **kwargs) -> Self:
        self = object.__new__(cls)
        self._nodes = _Nodes(self)
        self._edges = _MultiDiEdges(self)
        return self


MultiDiGraph.register(nx.MultiDiGraph)
