"""Csp1dSchedule tests.

Test scheduling assignments to machines.
测试将分配排程到机器。
"""

from __future__ import annotations

from ospf_python.framework.csp1d.application.model.csp1d_assignment import (
    Csp1dAssignment,
)
from ospf_python.framework.csp1d.application.model.csp1d_solution import (
    Csp1dSolution,
)
from ospf_python.framework.csp1d.application.service.csp1d_schedule import (
    Csp1dSchedule,
)
from ospf_python.framework.csp1d.domain.material.model.machine import (
    Machine,
)


class TestCsp1dSchedule:
    """Csp1dSchedule tests."""

    def _make_machine(self, name: str) -> Machine:
        """Helper to create a machine. / 创建机器辅助方法。"""
        return Machine(name=name, max_width=200.0, cut_loss=2.0)

    def test_schedule_empty_solution(self) -> None:
        """Schedule empty solution. / 排程空解决方案。"""
        machine = self._make_machine("C1")
        scheduler = Csp1dSchedule((machine,))
        solution = Csp1dSolution(assignments=(), total_waste=0.0, utilization=1.0)
        result = scheduler.schedule(solution)
        assert result == ()

    def test_schedule_no_machines(self) -> None:
        """Schedule with no machines returns empty. / 无机器返回空。"""
        scheduler = Csp1dSchedule(())
        assignment = Csp1dAssignment(
            material="Steel",
            cutting_plan="plan-1",
            quantity=2,
            waste=5.0,
        )
        solution = Csp1dSolution(
            assignments=(assignment,),
            total_waste=5.0,
            utilization=0.9,
        )
        result = scheduler.schedule(solution)
        assert result == ()

    def test_schedule_round_robin(self) -> None:
        """Schedule uses round-robin across machines. / 轮询排程。"""
        m1 = self._make_machine("C1")
        m2 = self._make_machine("C2")
        scheduler = Csp1dSchedule((m1, m2))
        assignment = Csp1dAssignment(
            material="Steel",
            cutting_plan="plan-1",
            quantity=4,
            waste=10.0,
        )
        solution = Csp1dSolution(
            assignments=(assignment,),
            total_waste=10.0,
            utilization=0.9,
        )
        result = scheduler.schedule(solution)
        assert len(result) == 4
        # Round-robin: C1, C2, C1, C2
        assert result[0][0].name == "C1"
        assert result[1][0].name == "C2"
        assert result[2][0].name == "C1"
        assert result[3][0].name == "C2"

    def test_schedule_multiple_assignments(self) -> None:
        """Schedule multiple assignments. / 排程多个分配。"""
        m1 = self._make_machine("C1")
        scheduler = Csp1dSchedule((m1,))
        a1 = Csp1dAssignment(
            material="Steel",
            cutting_plan="plan-1",
            quantity=2,
            waste=5.0,
        )
        a2 = Csp1dAssignment(
            material="Steel",
            cutting_plan="plan-2",
            quantity=1,
            waste=3.0,
        )
        solution = Csp1dSolution(
            assignments=(a1, a2),
            total_waste=8.0,
            utilization=0.85,
        )
        result = scheduler.schedule(solution)
        assert len(result) == 3

    def test_machines_property(self) -> None:
        """Machines property returns tuple. / machines 属性返回元组。"""
        m1 = self._make_machine("C1")
        m2 = self._make_machine("C2")
        scheduler = Csp1dSchedule((m1, m2))
        assert len(scheduler.machines) == 2
