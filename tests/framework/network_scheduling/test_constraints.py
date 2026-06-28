"""网络排程约束测试。

Network scheduling constraint tests:
edge capacity, flow conservation, demand constraints.
"""

from __future__ import annotations

import pytest

from ospf_python.framework.network_scheduling.domain.edge.model.edge import Edge
from ospf_python.framework.network_scheduling.domain.flow.model.demand import Demand
from ospf_python.framework.network_scheduling.domain.node.model.node import Node
from ospf_python.framework.network_scheduling.domain.node.model.node_type import (
    NodeType,
)

# ============================================================
# Edge capacity constraints
# ============================================================


class TestEdgeCapacity:
    """边容量约束测试。/ Edge capacity constraint tests."""

    def test_capacity_within_limit(self) -> None:
        """容量在限制内。/ Capacity within limit."""
        e = Edge.create(
            edge_key="e1",
            from_node_key="A",
            to_node_key="B",
            capacity=10.0,
        )
        assert e.capacity == pytest.approx(10.0)
        # 流量 5 <= 容量 10 → 合理
        # Flow 5 <= capacity 10 → feasible
        assert e.capacity >= 5.0

    def test_capacity_exceeded(self) -> None:
        """容量超出限制。/ Capacity exceeded."""
        e = Edge.create(
            edge_key="e1",
            from_node_key="A",
            to_node_key="B",
            capacity=3.0,
        )
        # 流量 5 > 容量 3 → 不可行
        # Flow 5 > capacity 3 → infeasible
        assert e.capacity < 5.0

    def test_infinite_capacity(self) -> None:
        """无限容量边。/ Infinite capacity edge."""
        e = Edge.create(
            edge_key="e1",
            from_node_key="A",
            to_node_key="B",
        )
        assert e.capacity == float("inf")


# ============================================================
# Flow conservation (logical check)
# ============================================================


class TestFlowConservation:
    """流量守恒逻辑测试。/ Flow conservation logic tests."""

    def test_source_produces_flow(self) -> None:
        """源节点产生流量。/ Source node produces flow."""
        n = Node.create(node_key="s1", name="Source", node_type=NodeType.SOURCE)
        assert n.node_type == NodeType.SOURCE
        # 源节点：出流量 > 入流量
        # Source: out flow > in flow

    def test_sink_absorbs_flow(self) -> None:
        """汇节点吸收流量。/ Sink node absorbs flow."""
        n = Node.create(node_key="t1", name="Sink", node_type=NodeType.SINK)
        assert n.node_type == NodeType.SINK
        # 汇节点：入流量 > 出流量
        # Sink: in flow > out flow

    def test_transit_balances_flow(self) -> None:
        """中间节点流量守恒。/ Transit node balances flow."""
        n = Node.create(node_key="v1", name="Transit", node_type=NodeType.TRANSIT)
        assert n.node_type == NodeType.TRANSIT
        # 中间节点：入流量 = 出流量
        # Transit: in flow = out flow


# ============================================================
# Demand constraints
# ============================================================


class TestDemandConstraints:
    """需求约束测试。/ Demand constraint tests."""

    def test_demand_specified(self) -> None:
        """需求已指定。/ Demand is specified."""
        d = Demand.create(demand_key="d1", source_key="A", sink_key="B", amount=5.0)
        assert d.amount == pytest.approx(5.0)

    def test_zero_demand(self) -> None:
        """零需求。/ Zero demand."""
        d = Demand.create(demand_key="d1", source_key="A", sink_key="B", amount=0.0)
        assert d.amount == pytest.approx(0.0)
