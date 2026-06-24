"""Tests for column generation lifecycle.

列生成生命周期测试。
"""

from __future__ import annotations

import abc

import pytest

from ospf_python.framework.solver.column_generation_solver import (
    ColumnGenerationSolver,
)

# -- ColumnGenerationSolver ABC --------------------------------------


class TestColumnGenerationSolverABC:
    """Test ColumnGenerationSolver abstract interface."""

    def test_is_abstract(self) -> None:
        """是抽象类 / Is abstract class."""
        assert issubclass(ColumnGenerationSolver, abc.ABC)

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate."""
        with pytest.raises(TypeError):
            ColumnGenerationSolver()  # type: ignore[abstract]

    def test_has_initialize(self) -> None:
        """有 initialize 方法 / Has initialize method."""
        assert hasattr(ColumnGenerationSolver, "initialize")

    def test_has_solve_master_problem(self) -> None:
        """有 solve_master_problem 方法 / Has solve_master_problem."""
        assert hasattr(ColumnGenerationSolver, "solve_master_problem")

    def test_has_solve_sub_problem(self) -> None:
        """有 solve_sub_problem 方法 / Has solve_sub_problem."""
        assert hasattr(ColumnGenerationSolver, "solve_sub_problem")

    def test_has_is_optimal(self) -> None:
        """有 is_optimal 方法 / Has is_optimal method."""
        assert hasattr(ColumnGenerationSolver, "is_optimal")

    def test_has_cleanup(self) -> None:
        """有 cleanup 方法 / Has cleanup method."""
        assert hasattr(ColumnGenerationSolver, "cleanup")


# -- Concrete implementation test ------------------------------------


class TestConcreteColumnGenerationSolver:
    """Test a concrete ColumnGenerationSolver implementation."""

    def test_lifecycle(self) -> None:
        """完整生命周期 / Full lifecycle."""

        class MockCGSolver(ColumnGenerationSolver):
            def __init__(self) -> None:
                self._initialized = False
                self._optimal = False

            def initialize(self) -> None:
                self._initialized = True

            def solve_master_problem(self) -> bool:
                return self._initialized

            def solve_sub_problem(self) -> bool:
                return self._initialized

            def is_optimal(self) -> bool:
                return self._optimal

            def cleanup(self) -> None:
                self._initialized = False

        solver = MockCGSolver()
        assert not solver.is_optimal()

        solver.initialize()
        assert solver.solve_master_problem()
        assert solver.solve_sub_problem()

        solver.cleanup()
        assert not solver.solve_master_problem()
