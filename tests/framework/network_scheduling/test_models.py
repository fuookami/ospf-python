"""网络排程模型测试。

Network scheduling model tests: nodes, edges, flows, demands.
"""

from __future__ import annotations

import pytest

from ospf_python.framework.network_scheduling.domain.edge.model.edge import Edge
from ospf_python.framework.network_scheduling.domain.flow.model.demand import Demand
from ospf_python.framework.network_scheduling.domain.flow.model.flow import Flow
from ospf_python.framework.network_scheduling.domain.node.model.node import Node
from ospf_python.framework.network_scheduling.domain.node.model.node_type import (
    NodeType,
)

# ============================================================
# Node
# ============================================================


class TestNode:
    """节点模型测试。/ Node model tests."""

    def test_create_source(self) -> None:
        """创建源节点。/ Create source node."""
        n = Node.create(node_key="s1", name="Source", node_type=NodeType.SOURCE)
        assert n.node_key == "s1"
        assert n.name == "Source"
        assert n.node_type == NodeType.SOURCE
        assert n.is_source

    def test_create_sink(self) -> None:
        """创建汇节点。/ Create sink node."""
        n = Node.create(node_key="t1", name="Sink", node_type=NodeType.SINK)
        assert n.node_type == NodeType.SINK
        assert n.is_sink

    def test_create_transit(self) -> None:
        """创建中间节点。/ Create transit node."""
        n = Node.create(node_key="v1", name="Transit", node_type=NodeType.TRANSIT)
        assert n.node_type == NodeType.TRANSIT
        assert n.is_transit

    def test_frozen(self) -> None:
        """frozen dataclass。/ frozen dataclass."""
        n = Node.create(node_key="s1", name="Source", node_type=NodeType.SOURCE)
        with pytest.raises(AttributeError):
            n.name = "changed"  # type: ignore[misc]

    def test_default_capacity_infinite(self) -> None:
        """默认容量为无穷大。/ Default capacity is infinity."""
        n = Node.create(node_key="v1", name="Transit", node_type=NodeType.TRANSIT)
        assert n.capacity == float("inf")

    def test_custom_capacity(self) -> None:
        """自定义容量。/ Custom capacity."""
        n = Node.create(node_key="v1", name="Transit", node_type=NodeType.TRANSIT, capacity=100.0)
        assert n.capacity == pytest.approx(100.0)

    def test_distance_to(self) -> None:
        """计算节点间欧氏距离。/ Compute Euclidean distance between nodes."""
        a = Node.create(node_key="A", name="A", x=0.0, y=0.0)
        b = Node.create(node_key="B", name="B", x=3.0, y=4.0)
        assert a.distance_to(b) == pytest.approx(5.0)

    def test_node_type_is_terminal(self) -> None:
        """终端节点判断。/ Terminal node check."""
        assert NodeType.SOURCE.is_terminal
        assert NodeType.SINK.is_terminal
        assert not NodeType.TRANSIT.is_terminal
        assert not NodeType.JUNCTION.is_terminal

    def test_node_type_can_route(self) -> None:
        """可路由节点判断。/ Routable node check."""
        assert NodeType.TRANSIT.can_route
        assert NodeType.JUNCTION.can_route
        assert not NodeType.SOURCE.can_route
        assert not NodeType.SINK.can_route


# ============================================================
# Edge
# ============================================================


class TestEdge:
    """边模型测试。/ Edge model tests."""

    def test_create_basic(self) -> None:
        """创建基本边。/ Create basic edge."""
        e = Edge.create(
            edge_key="e1",
            from_node_key="A",
            to_node_key="B",
            capacity=10.0,
            cost=1.0,
        )
        assert e.edge_key == "e1"
        assert e.from_node_key == "A"
        assert e.to_node_key == "B"
        assert e.capacity == pytest.approx(10.0)
        assert e.cost == pytest.approx(1.0)

    def test_default_capacity(self) -> None:
        """默认容量为无穷大。/ Default capacity is infinity."""
        e = Edge.create(
            edge_key="e1",
            from_node_key="A",
            to_node_key="B",
        )
        assert e.capacity == float("inf")

    def test_default_cost(self) -> None:
        """默认代价为 1.0。/ Default cost is 1.0."""
        e = Edge.create(
            edge_key="e1",
            from_node_key="A",
            to_node_key="B",
        )
        assert e.cost == pytest.approx(1.0)

    def test_reversed(self) -> None:
        """创建反向边。/ Create reversed edge."""
        e = Edge.create(edge_key="e1", from_node_key="A", to_node_key="B", capacity=10.0, cost=2.0)
        r = e.reversed()
        assert r.edge_key == "e1_rev"
        assert r.from_node_key == "B"
        assert r.to_node_key == "A"
        assert r.capacity == pytest.approx(10.0)
        assert r.cost == pytest.approx(2.0)

    def test_connects(self) -> None:
        """检查是否连接指定节点。/ Check if connects to a given node."""
        e = Edge.create(edge_key="e1", from_node_key="A", to_node_key="B")
        assert e.connects("A")
        assert e.connects("B")
        assert not e.connects("C")

    def test_is_reverse_possible(self) -> None:
        """有限容量边可创建反向边。/ Finite-capacity edge can be reversed."""
        e1 = Edge.create(edge_key="e1", from_node_key="A", to_node_key="B", capacity=10.0)
        assert e1.is_reverse_possible
        e2 = Edge.create(edge_key="e2", from_node_key="A", to_node_key="B")
        assert not e2.is_reverse_possible

    def test_effective_cost_within_capacity(self) -> None:
        """容量内流量代价不变。/ Cost unchanged within capacity."""
        e = Edge.create(edge_key="e1", from_node_key="A", to_node_key="B", capacity=10.0, cost=2.0)
        assert e.effective_cost(5.0) == pytest.approx(2.0)

    def test_effective_cost_over_capacity(self) -> None:
        """超容量流量代价按比例增加。/ Cost increases proportionally over capacity."""
        e = Edge.create(edge_key="e1", from_node_key="A", to_node_key="B", capacity=10.0, cost=2.0)
        # flow=20, capacity=10, overflow_ratio=2.0 → cost=4.0
        assert e.effective_cost(20.0) == pytest.approx(4.0)


# ============================================================
# Flow
# ============================================================


class TestFlow:
    """流模型测试。/ Flow model tests."""

    def test_create(self) -> None:
        """创建流。/ Create flow."""
        f = Flow.create(flow_key="f1", edge_key="e1", amount=5.0)
        assert f.flow_key == "f1"
        assert f.edge_key == "e1"
        assert f.amount == pytest.approx(5.0)

    def test_create_with_cost(self) -> None:
        """创建带代价的流。/ Create flow with cost."""
        f = Flow.create(flow_key="f1", edge_key="e1", amount=5.0, cost=10.0)
        assert f.cost == pytest.approx(10.0)

    def test_is_feasible_within_capacity(self) -> None:
        """流量在容量内可行。/ Flow within capacity is feasible."""
        f = Flow.create(flow_key="f1", edge_key="e1", amount=5.0)
        assert f.is_feasible(capacity=10.0)

    def test_is_feasible_exceeds_capacity(self) -> None:
        """流量超出容量不可行。/ Flow exceeding capacity is infeasible."""
        f = Flow.create(flow_key="f1", edge_key="e1", amount=15.0)
        assert not f.is_feasible(capacity=10.0)

    def test_is_feasible_infinite_capacity(self) -> None:
        """无限容量下非负流量可行。/ Non-negative flow feasible with infinite capacity."""
        f = Flow.create(flow_key="f1", edge_key="e1", amount=5.0)
        assert f.is_feasible(capacity=float("inf"))

    def test_with_amount(self) -> None:
        """创建不同流量值的流（代价按比例缩放）。/ Create flow with different amount, cost scaled."""
        f = Flow.create(flow_key="f1", edge_key="e1", amount=5.0, cost=10.0)
        f2 = f.with_amount(10.0)
        assert f2.amount == pytest.approx(10.0)
        assert f2.cost == pytest.approx(20.0)  # 10.0 * (10.0 / 5.0)
        assert f2.flow_key == "f1"
        assert f2.edge_key == "e1"

    def test_residual_capacity(self) -> None:
        """计算剩余容量。/ Calculate residual capacity."""
        f = Flow.create(flow_key="f1", edge_key="e1", amount=3.0)
        assert f.residual_capacity(edge_capacity=10.0) == pytest.approx(7.0)

    def test_residual_capacity_infinite(self) -> None:
        """无限边容量下剩余容量为无穷大。/ Residual is infinite with infinite edge capacity."""
        f = Flow.create(flow_key="f1", edge_key="e1", amount=3.0)
        assert f.residual_capacity(edge_capacity=float("inf")) == float("inf")


# ============================================================
# Demand
# ============================================================


class TestDemand:
    """需求模型测试。/ Demand model tests."""

    def test_create(self) -> None:
        """创建需求。/ Create demand."""
        d = Demand.create(demand_key="d1", source_key="A", sink_key="B", amount=5.0)
        assert d.demand_key == "d1"
        assert d.source_key == "A"
        assert d.sink_key == "B"
        assert d.amount == pytest.approx(5.0)

    def test_default_priority(self) -> None:
        """默认优先级为 0。/ Default priority is 0."""
        d = Demand.create(demand_key="d1", source_key="A", sink_key="B", amount=5.0)
        assert d.priority == 0

    def test_custom_priority(self) -> None:
        """自定义优先级。/ Custom priority."""
        d = Demand.create(demand_key="d1", source_key="A", sink_key="B", amount=5.0, priority=10)
        assert d.priority == 10

    def test_is_satisfied_zero(self) -> None:
        """零需求已满足。/ Zero demand is satisfied."""
        d = Demand.create(demand_key="d1", source_key="A", sink_key="B", amount=0.0)
        assert d.is_satisfied

    def test_is_satisfied_positive(self) -> None:
        """正需求未满足。/ Positive demand is not satisfied."""
        d = Demand.create(demand_key="d1", source_key="A", sink_key="B", amount=5.0)
        assert not d.is_satisfied

    def test_with_amount(self) -> None:
        """创建不同需求量的需求。/ Create demand with different amount."""
        d = Demand.create(demand_key="d1", source_key="A", sink_key="B", amount=5.0, priority=3)
        d2 = d.with_amount(10.0)
        assert d2.amount == pytest.approx(10.0)
        assert d2.priority == 3

    def test_is_satisfied_by(self) -> None:
        """检查流量是否满足需求。/ Check if flow amount satisfies demand."""
        d = Demand.create(demand_key="d1", source_key="A", sink_key="B", amount=5.0)
        assert d.is_satisfied_by(5.0)
        assert d.is_satisfied_by(6.0)
        assert not d.is_satisfied_by(4.0)
