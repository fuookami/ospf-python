"""Test SSP solver — 测试 SSP 求解器。"""

from __future__ import annotations

from examples.framework_demo.demo1.interface import Demo1Interface


def test_ssp_basic_routing() -> None:
    """Test basic SSP routing."""
    iface = Demo1Interface()
    result = iface.create_and_solve(
        nodes=["A", "B", "C"],
        edges=[
            ("e1", "A", "B", 10.0),
            ("e2", "B", "C", 8.0),
            ("e3", "A", "C", 15.0),
        ],
        services=[("s1", "A", "C", 2.0)],
    )
    assert result.feasible is True
    assert "s1" in result.routes
    assert result.total_cost < float("inf")


def test_ssp_bandwidth_constraint() -> None:
    """Test SSP with bandwidth constraints."""
    iface = Demo1Interface()
    result = iface.create_and_solve(
        nodes=["A", "B"],
        edges=[("e1", "A", "B", 5.0)],
        services=[
            ("s1", "A", "B", 3.0),
            ("s2", "A", "B", 4.0),
        ],
    )
    # Second service should fail due to bandwidth
    assert result.feasible is False


def test_ssp_multiple_services() -> None:
    """Test SSP with multiple services on different paths."""
    iface = Demo1Interface()
    result = iface.create_and_solve(
        nodes=["A", "B", "C", "D"],
        edges=[
            ("e1", "A", "B", 10.0),
            ("e2", "B", "D", 10.0),
            ("e3", "A", "C", 10.0),
            ("e4", "C", "D", 10.0),
        ],
        services=[
            ("s1", "A", "D", 3.0),
            ("s2", "A", "D", 2.0),
        ],
    )
    assert result.feasible is True
    assert len(result.routes) == 2
