from collections.abc import Callable, Generator
from dataclasses import dataclass, field
from typing import Hashable, Literal, overload

import networkx as nx
import matplotlib.pyplot as plt
import osmnx as ox

import heapq
import random

from common_lib.graph import *
from common_lib.hash_table import HashMap, HashSet
from common_lib.containers import LinkedStack

place = "West Valley College, Saratoga, California, USA"

nxG = ox.graph_from_place(place, network_type="all")


# ox.plot_graph(nxG)
# plt.show()


# G = MultiDiGraph(nxG.nodes, nxG.edges)


def a_star[NodeT: Hashable](
        graph: Graph[NodeT], source: NodeT, target: NodeT,
        weight: str | Callable[[NodeT, NodeT], float] = "weight",
        heuristic: Callable[[NodeT, NodeT], float] = lambda s, e: 0,
        logging: bool = False
) -> list[NodeT]:
    parent: HashMap[NodeT, NodeT] = HashMap()

    if isinstance(weight, str):
        weight_attr = weight

        if graph.is_multigraph():
            def weight(src: NodeT, dest: NodeT) -> float:
                nonlocal graph
                return min(edge.get(weight_attr, 1) for edge in graph.get_edge_data(src, dest).values())
        else:
            def weight(src: NodeT, dest: NodeT) -> float:
                nonlocal graph
                return graph.get_edge_data(src, dest).get(weight_attr, 1)

    def distance(node: NodeT) -> float:
        nonlocal source
        if node is source or node == source:
            return 0

        if node not in parent:
            return float('inf')

        dist = 0
        while node in parent:
            dist += weight(parent[node], node)
            node = parent[node]
        return dist

    def score(node: NodeT) -> float:
        nonlocal target
        return heuristic(node, target) + distance(node)

    class HeuristicQueue[NodeT_](list[NodeT_]):
        @dataclass(order=True, repr=True)
        class Item:
            item: NodeT_ = field(compare=False)
            heuristic: float = field(compare=True)

            def __init__(self, item: NodeT_, heuristic_: float | None = None) -> None:
                self.item = item
                if heuristic_ is None:
                    self.heuristic = score(item)
                else:
                    self.heuristic = heuristic_

        heapify = heapq.heapify

        def push(self, item: NodeT_, /) -> None:
            """ Push item onto heap, maintaining the heap invariant. """
            heapq.heappush(self, self.Item(item))

        # noinspection PyMethodOverriding
        def pop(self, /) -> NodeT_:
            """ Pop the smallest item off the heap, maintaining the heap invariant. """
            return heapq.heappop(self).item

        def push_pop(self, item: NodeT_, /) -> NodeT_:
            """
            Push item on the heap, then pop and return the smallest item from the heap.

            The combined action runs more efficiently than heappush() followed by
            a separate call to heappop().
            """
            return heapq.heappushpop(self, self.Item(item)).item

        def replace(self, item: NodeT_, /) -> NodeT_:
            """
            Pop and return the current smallest value, and add the new item.

            This is more efficient than heappop() followed by heappush(), and can be
            more appropriate when using a fixed-size heap.  Note that the value
            returned may be larger than item!  That constrains reasonable uses of
            this routine unless written as part of a conditional replacement:

                if item > heap[0]:
                    item = heapreplace(heap, item)
            """

            return heapq.heapreplace(self, self.Item(item)).item

    queue: HeuristicQueue[NodeT] = HeuristicQueue()
    queue.push(source)

    if logging:
        node_log = []

    while queue:
        current = queue.pop()

        if logging:
            node_log.append(current)

        if current is target or current == target:
            path = [current]
            while current in parent and current is not source and current != source:
                current = parent[current]
                path.append(current)

            path.reverse()

            if logging:
                print('\t\tSteps:', node_log)
                print('\t\tCount:', len(node_log))

            return path

        cur_dist = distance(current)

        for neighbor in graph.neighbors(current):
            wgt = weight(current, neighbor)
            if wgt < 0:
                raise ValueError(f"Edge weight between {current} and {neighbor} is negative.")

            if cur_dist + wgt < distance(neighbor):
                parent[neighbor] = current
                queue.push(neighbor)

    else:
        raise ValueError(f"No path from {source} to {target} exists.")


def dfs[NodeT: Hashable](graph: Graph[NodeT],
                         source: NodeT, target: NodeT = None,
                         logging: bool = False) -> list[NodeT]:
    visited = HashSet()
    stack = LinkedStack()


def bfs[NodeT: Hashable](graph: Graph[NodeT],
                         source: NodeT, target: NodeT = None,
                         logging: bool = False) -> list[NodeT]:
    return a_star(graph, source, target, weight=lambda *_, **__: 1)


def dijkstra[NodeT: Hashable](graph: Graph[NodeT],
                              source: NodeT, target: NodeT = None,
                              logging: bool = False) -> list[NodeT]:
    return a_star(graph, source, target)


def gps_distance[NodeT](graph: Graph, node1: NodeT, node2: NodeT) -> float:
    latlong1 = graph.nodes[node1]['y'], graph.nodes[node1]['x']
    latlong2 = graph.nodes[node2]['y'], graph.nodes[node2]['x']
    return ox.distance.great_circle(*latlong1, *latlong2)


targets = random.sample(list(nxG.nodes), 2)
print()
print(targets[0], "->", targets[1])
print('\tNetworkX:', nx.astar_path(nxG, *targets, weight="length"))
print()
print("\tAlgorithm: Dijkstra using current path length only")
print('\tMy Graph:', a_star(nxG, *targets, weight="length", logging=True))  # A* with h = 0 is simply Dijkstra.
print()
print('\tAlgorithm: A* using GPS Distance and current path length')
print('\tMy Graph:',
      a_star(nxG, *targets, weight="length", heuristic=lambda a, b: gps_distance(nxG, a, b), logging=True))

ox.plot_graph_route(nxG, a_star(nxG, *targets, weight="length", heuristic=lambda a, b: gps_distance(nxG, a, b)))
