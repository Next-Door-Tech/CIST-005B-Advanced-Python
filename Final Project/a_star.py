from collections.abc import Callable
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Hashable

import networkx as nx
import matplotlib.pyplot as plt
import osmnx as ox

import heapq
import random

# from common_lib.containers import LinkedQueue
# from common_lib.graph import DiGraph

place = "West Valley College, Saratoga, California, USA"

G = ox.graph_from_place(place, network_type="all")
ox.plot_graph(G)
plt.show()


def a_star[NodeT: Hashable](
        graph: nx.DiGraph[NodeT], source: NodeT, target: NodeT,
        weight: str | Callable[[NodeT, NodeT], float] = "weight",
        heuristic: Callable[[NodeT, NodeT], float] = lambda s, e: 0
) -> list[NodeT]:
    parent: dict[NodeT, NodeT] = {}

    if isinstance(weight, str):
        weight_attr = weight

        if G.is_multigraph():
            def weight(src: NodeT, dest: NodeT) -> float:
                return min(edge.get(weight_attr, 1) for edge in G.get_edge_data(src, dest).values())
        else:
            def weight(src: NodeT, dest: NodeT, ) -> float:
                return G.get_edge_data(src, dest).get(weight_attr, 1)

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
            weight: float = field(compare=True)

            def __init__(self, item: NodeT_, weight: float = None) -> None:
                self.item = item
                if weight is None:
                    self.weight = score(item)
                else:
                    self.weight = weight

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

    while queue:
        current = queue.pop()

        if current is target or current == target:
            path = [current]
            while current in parent and current is not source and current != source:
                current = parent[current]
                path.append(current)

            path.reverse()
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


random.seed(0)
for _ in range(10):
    targets = random.sample(list(G.nodes), 2)
    print(targets[0], "->", targets[1])
    print('\t', "Heuristic = 0")
    print('\t', nx.astar_path(G, *targets, weight="length"))
    print('\t', a_star(G, *targets, weight="length"))
    print()
