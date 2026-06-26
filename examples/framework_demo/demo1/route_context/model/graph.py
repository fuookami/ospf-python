"""Graph model — 网络拓扑图。

定义网络图结构，包含节点与边，支持邻接查询。
Defines the network graph structure with nodes, edges,
and adjacency lookup.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .assignment import Edge


@dataclass(frozen=True)
class Graph:
    """网络拓扑图 / Network topology graph.

    表示由节点和有向边组成的网络拓扑。提供邻接表查询
    以便高效地进行路径搜索。
    Represents a network topology composed of nodes and
    directed edges. Provides adjacency-list lookup for
    efficient path search.

    Attributes:
        nodes: 节点标识元组 / Tuple of node identifiers.
        edges: 有向边元组 / Tuple of directed edges.
    """

    nodes: tuple[str, ...] = ()
    edges: tuple[Edge, ...] = ()

    @property
    def node_set(self) -> frozenset[str]:
        """节点集合 / Set of nodes."""
        return frozenset(self.nodes)

    def adjacency(self) -> dict[str, list[Edge]]:
        """构建邻接表。

        Build the adjacency list.

        将边按源节点分组，返回每个节点的出边列表。
        Groups edges by source node, returning the outgoing
        edge list for each node.

        Returns:
            邻接字典，键为源节点，值为出边列表。
            Adjacency dict mapping source node to outgoing edges.
        """
        adj: dict[str, list[Edge]] = {n: [] for n in self.nodes}
        for edge in self.edges:
            if edge.source in adj:
                adj[edge.source].append(edge)
        return adj

    def neighbors(self, node: str) -> tuple[str, ...]:
        """获取节点的邻居。

        Get the neighbors of a node.

        Args:
            node: 节点标识 / Node identifier.

        Returns:
            邻居节点标识元组 / Tuple of neighbor node identifiers.
        """
        return tuple(edge.target for edge in self.edges if edge.source == node)

    def has_node(self, node: str) -> bool:
        """检查节点是否存在。

        Check whether a node exists.

        Args:
            node: 节点标识 / Node identifier.

        Returns:
            存在返回 True / True if node exists.
        """
        return node in self.node_set

    def edge_between(self, source: str, target: str) -> Edge | None:
        """查找两节点间的边。

        Find the edge between two nodes.

        Args:
            source: 源节点 / Source node.
            target: 目标节点 / Target node.

        Returns:
            匹配的边，不存在时返回 None。
            Matching edge, or None if not found.
        """
        for edge in self.edges:
            if edge.source == source and edge.target == target:
                return edge
        return None
