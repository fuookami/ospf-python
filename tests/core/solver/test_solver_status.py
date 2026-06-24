"""SolverStatus 测试。

测试求解器状态枚举的定义和值。
Tests SolverStatus enum definition and values.
"""

from __future__ import annotations

from ospf_python.core.solver.output.solver_status import (
    SolverStatus,
)
from ospf_python.core.solver.output.solving_status import (
    SolvingStatus,
)


class TestSolverStatus:
    """SolverStatus 枚举测试 / Enum tests."""

    def test_optimal_value(self) -> None:
        """OPTIMAL 值为 0。/ OPTIMAL is 0."""
        assert SolverStatus.OPTIMAL.value == 0

    def test_infeasible_value(self) -> None:
        """INFEASIBLE 值为 1。/ INFEASIBLE is 1."""
        assert SolverStatus.INFEASIBLE.value == 1

    def test_unbounded_value(self) -> None:
        """UNBOUNDED 值为 2。/ UNBOUNDED is 2."""
        assert SolverStatus.UNBOUNDED.value == 2

    def test_timeout_value(self) -> None:
        """TIMEOUT 值为 3。/ TIMEOUT is 3."""
        assert SolverStatus.TIMEOUT.value == 3

    def test_error_value(self) -> None:
        """ERROR 值为 4。/ ERROR is 4."""
        assert SolverStatus.ERROR.value == 4

    def test_unknown_value(self) -> None:
        """UNKNOWN 值为 5。/ UNKNOWN is 5."""
        assert SolverStatus.UNKNOWN.value == 5

    def test_member_count(self) -> None:
        """共 6 个成员。/ Has 6 members."""
        assert len(SolverStatus) == 6


class TestSolvingStatus:
    """SolvingStatus 枚举测试 / Enum tests."""

    def test_idle_value(self) -> None:
        """IDLE 值为 0。/ IDLE is 0."""
        assert SolvingStatus.IDLE.value == 0

    def test_completed_value(self) -> None:
        """COMPLETED 值为 4。/ COMPLETED is 4."""
        assert SolvingStatus.COMPLETED.value == 4

    def test_member_count(self) -> None:
        """共 6 个成员。/ Has 6 members."""
        assert len(SolvingStatus) == 6
