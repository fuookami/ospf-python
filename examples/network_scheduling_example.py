"""网络排程示例 / Network scheduling example.

基本网络排程：最短路径和最大流。
Basic network scheduling: shortest path and max flow.
"""

from ospf_python.framework.network_scheduling.domain.edge.model.edge import Edge
from ospf_python.framework.network_scheduling.domain.flow.model.demand import Demand
from ospf_python.framework.network_scheduling.domain.node.model.node import Node
from ospf_python.framework.network_scheduling.domain.node.model.node_type import (
    NodeType,
)
from ospf_python.framework.network_scheduling.domain.service.flow_optimizer import (
    FlowOptimizer,
)
from ospf_python.framework.network_scheduling.domain.service.shortest_path import (
    ShortestPath,
)

nodes = (
    Node.create(node_key="A", name="Source", node_type=NodeType.SOURCE),
    Node.create(node_key="B", name="Transit", node_type=NodeType.TRANSIT),
    Node.create(node_key="C", name="Sink", node_type=NodeType.SINK),
)
edges = (
    Edge.create(edge_key="e1", from_node_key="A", to_node_key="B", cost=1.0),
    Edge.create(edge_key="e2", from_node_key="B", to_node_key="C", cost=2.0),
    Edge.create(edge_key="e3", from_node_key="A", to_node_key="C", cost=5.0),
)

# 最短路径 / Shortest path
path_result = ShortestPath.dijkstra(nodes=nodes, edges=edges, source_key="A", sink_key="C")
if path_result.is_ok():
    print(f"最短路径: {path_result.unwrap()}")  # 最短路径: ('A', 'B', 'C')

# 最大流 / Max flow
demands = (Demand.create(demand_key="d1", source_key="A", sink_key="C", amount=3.0),)
flow_result = FlowOptimizer.optimize(nodes=nodes, edges=edges, demands=demands)
if flow_result.is_ok():
    total = sum(f.amount for f in flow_result.unwrap())
    print(f"总流量: {total}")  # 总流量: 3.0
