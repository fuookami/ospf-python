"""网络排程端到端测试。

Network scheduling e2e tests:
full pipeline from network creation to flow optimization.
"""

from __future__ import annotations

import pytest

from ospf_python.framework.network_scheduling.domain.edge.model.edge import Edge
from ospf_python.framework.network_scheduling.domain.flow.model.demand import Demand
from ospf_python.framework.network_scheduling.domain.network_context import (
    NetworkContext,
)
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

# ============================================================
# Full pipeline: shortest path
# ============================================================


class TestShortestPathE2e:
    """最短路径端到端测试。/ Shortest path e2e tests."""

    def test_full_pipeline_shortest_path(self) -> None:
        """最短路径完整流程。/ Shortest path full pipeline."""
        # 1. 创建网络 / Create network
        ctx = NetworkContext.create(
            network_key="net_1",
            name="Test Network",
            description="E2E shortest path test",
        )
        assert ctx.network_key == "net_1"

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

        # 2. 运行最短路径 / Run shortest path
        result = ShortestPath.dijkstra(
            nodes=nodes, edges=edges, source_key="A", sink_key="C",
        )

        # 3. 验证结果 / Verify results
        assert result.is_ok()
        path = result.unwrap()
        assert path == ("A", "B", "C")  # A→B→C = 3, A→C = 5

    def test_shortest_path_cost_objective(self) -> None:
        """最短路径代价目标。/ Shortest path cost objective."""
        nodes = (
            Node.create(node_key="A", name="Source", node_type=NodeType.SOURCE),
            Node.create(node_key="B", name="Transit", node_type=NodeType.TRANSIT),
            Node.create(node_key="C", name="Sink", node_type=NodeType.SINK),
        )
        edges = (
            Edge.create(edge_key="e1", from_node_key="A", to_node_key="B", cost=10.0),
            Edge.create(edge_key="e2", from_node_key="B", to_node_key="C", cost=10.0),
            Edge.create(edge_key="e3", from_node_key="A", to_node_key="C", cost=15.0),
        )

        result = ShortestPath.dijkstra(
            nodes=nodes, edges=edges, source_key="A", sink_key="C",
        )
        assert result.is_ok()
        path = result.unwrap()
        # A→C = 15 < A→B→C = 20 → direct is cheaper
        assert path == ("A", "C")


# ============================================================
# Full pipeline: max flow
# ============================================================


class TestMaxFlowE2e:
    """最大流端到端测试。/ Max flow e2e tests."""

    def test_full_pipeline_max_flow(self) -> None:
        """最大流完整流程。/ Max flow full pipeline."""
        # 1. 创建网络 / Create network
        nodes = (
            Node.create(node_key="S", name="Source", node_type=NodeType.SOURCE),
            Node.create(node_key="A", name="Transit-A", node_type=NodeType.TRANSIT),
            Node.create(node_key="B", name="Transit-B", node_type=NodeType.TRANSIT),
            Node.create(node_key="T", name="Sink", node_type=NodeType.SINK),
        )
        edges = (
            Edge.create(edge_key="e1", from_node_key="S", to_node_key="A", capacity=10.0, cost=1.0),
            Edge.create(edge_key="e2", from_node_key="S", to_node_key="B", capacity=8.0, cost=2.0),
            Edge.create(edge_key="e3", from_node_key="A", to_node_key="T", capacity=7.0, cost=1.0),
            Edge.create(edge_key="e4", from_node_key="B", to_node_key="T", capacity=10.0, cost=1.0),
        )
        demands = (
            Demand.create(demand_key="d1", source_key="S", sink_key="T", amount=15.0),
        )

        # 2. 运行流优化 / Run flow optimization
        result = FlowOptimizer.optimize(nodes=nodes, edges=edges, demands=demands)

        # 3. 验证结果 / Verify results
        assert result.is_ok()
        flows = result.unwrap()
        total_flow = sum(f.amount for f in flows)
        # S→A (cap 10) + S→B (cap 8) = 18, A→T (cap 7) + B→T (cap 10) = 17
        # Min cut = 17, but demand is 15 which is ≤ 17
        assert total_flow == pytest.approx(15.0)

    def test_capacity_insufficient_e2e(self) -> None:
        """容量不足不可行端到端。/ Capacity insufficient e2e."""
        nodes = (
            Node.create(node_key="S", name="Source", node_type=NodeType.SOURCE),
            Node.create(node_key="T", name="Sink", node_type=NodeType.SINK),
        )
        edges = (
            Edge.create(edge_key="e1", from_node_key="S", to_node_key="T", capacity=5.0, cost=1.0),
        )
        demands = (
            Demand.create(demand_key="d1", source_key="S", sink_key="T", amount=100.0),
        )

        result = FlowOptimizer.optimize(nodes=nodes, edges=edges, demands=demands)
        # 容量 5 < 需求 100 → 不可行
        assert result.is_failed()

    def test_unreachable_network_e2e(self) -> None:
        """不可达网络端到端。/ Unreachable network e2e."""
        nodes = (
            Node.create(node_key="S", name="Source", node_type=NodeType.SOURCE),
            Node.create(node_key="A", name="Island", node_type=NodeType.TRANSIT),
            Node.create(node_key="T", name="Sink", node_type=NodeType.SINK),
        )
        edges = (
            Edge.create(edge_key="e1", from_node_key="S", to_node_key="A", capacity=10.0, cost=1.0),
            # No edge from A to T or S to T
        )
        demands = (
            Demand.create(demand_key="d1", source_key="S", sink_key="T", amount=1.0),
        )

        result = FlowOptimizer.optimize(nodes=nodes, edges=edges, demands=demands)
        assert result.is_failed()


# ============================================================
# Full pipeline: network context wiring
# ============================================================


class TestNetworkContextWiring:
    """网络上下文连接测试。/ Network context wiring tests."""

    def test_context_creation_and_properties(self) -> None:
        """上下文创建和属性。/ Context creation and properties."""
        ctx = NetworkContext.create(
            network_key="net_1",
            name="Test Network",
            description="Wiring test",
        )
        assert ctx.network_key == "net_1"
        assert ctx.name == "Test Network"
        assert ctx.description == "Wiring test"

    def test_context_default_description(self) -> None:
        """上下文默认描述。/ Context default description."""
        ctx = NetworkContext.create(
            network_key="net_2",
            name="Minimal",
        )
        assert ctx.description == ""

    def test_full_wiring_with_context(self) -> None:
        """带上下文的完整连接。/ Full wiring with context."""
        # 创建上下文 / Create context
        ctx = NetworkContext.create(
            network_key="supply_chain",
            name="Supply Chain Network",
        )
        assert ctx.network_key == "supply_chain"

        # 创建节点和边 / Create nodes and edges
        nodes = (
            Node.create(node_key="factory", name="Factory", node_type=NodeType.SOURCE),
            Node.create(node_key="warehouse", name="Warehouse", node_type=NodeType.TRANSIT),
            Node.create(node_key="store", name="Store", node_type=NodeType.SINK),
        )
        edges = (
            Edge.create(edge_key="e1", from_node_key="factory", to_node_key="warehouse", capacity=100.0, cost=1.0),
            Edge.create(edge_key="e2", from_node_key="warehouse", to_node_key="store", capacity=50.0, cost=2.0),
        )

        # 创建需求 / Create demands
        demands = (
            Demand.create(demand_key="d1", source_key="factory", sink_key="store", amount=30.0, priority=1),
        )

        # 先检查最短路径 / Check shortest path first
        sp_result = ShortestPath.dijkstra(
            nodes=nodes, edges=edges, source_key="factory", sink_key="store",
        )
        assert sp_result.is_ok()

        # 再运行流优化 / Run flow optimization
        flow_result = FlowOptimizer.optimize(nodes=nodes, edges=edges, demands=demands)
        assert flow_result.is_ok()
        flows = flow_result.unwrap()
        total = sum(f.amount for f in flows)
        assert total == pytest.approx(30.0)
