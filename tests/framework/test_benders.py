"""Tests for Benders decomposition.

Benders 分解测试。
"""

from __future__ import annotations

import abc

import pytest

from ospf_python.framework.solver.benders_decomposition_solver import (
    BendersDecompositionSolver,
)

# -- BendersDecompositionSolver ABC ----------------------------------


class TestBendersDecompositionSolverABC:
    """Test BendersDecompositionSolver abstract interface."""

    def test_is_abstract(self) -> None:
        """是抽象类 / Is abstract class."""
        assert issubclass(BendersDecompositionSolver, abc.ABC)

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate."""
        with pytest.raises(TypeError):
            BendersDecompositionSolver()  # type: ignore[abstract]

    def test_has_initialize(self) -> None:
        """有 initialize 方法 / Has initialize method."""
        assert hasattr(BendersDecompositionSolver, "initialize")

    def test_has_solve_master_problem(self) -> None:
        """有 solve_master_problem / Has solve_master_problem."""
        assert hasattr(BendersDecompositionSolver, "solve_master_problem")

    def test_has_solve_sub_problem(self) -> None:
        """有 solve_sub_problem / Has solve_sub_problem."""
        assert hasattr(BendersDecompositionSolver, "solve_sub_problem")

    def test_has_add_cut(self) -> None:
        """有 add_cut 方法 / Has add_cut method."""
        assert hasattr(BendersDecompositionSolver, "add_cut")

    def test_has_is_optimal(self) -> None:
        """有 is_optimal 方法 / Has is_optimal method."""
        assert hasattr(BendersDecompositionSolver, "is_optimal")

    def test_has_cleanup(self) -> None:
        """有 cleanup 方法 / Has cleanup method."""
        assert hasattr(BendersDecompositionSolver, "cleanup")


# -- Concrete implementation test ------------------------------------


class TestConcreteBendersSolver:
    """Test a concrete BendersDecompositionSolver implementation."""

    def test_lifecycle(self) -> None:
        """完整生命周期 / Full lifecycle."""

        class MockBendersSolver(BendersDecompositionSolver):
            def __init__(self) -> None:
                self._initialized = False
                self._cuts = 0
                self._optimal = False

            def initialize(self) -> None:
                self._initialized = True
                self._cuts = 0

            def solve_master_problem(self) -> bool:
                return self._initialized

            def solve_sub_problem(self) -> bool:
                return self._initialized

            def add_cut(self) -> bool:
                if not self._initialized:
                    return False
                self._cuts += 1
                if self._cuts >= 3:
                    self._optimal = True
                return True

            def is_optimal(self) -> bool:
                return self._optimal

            def cleanup(self) -> None:
                self._initialized = False
                self._cuts = 0
                self._optimal = False

        solver = MockBendersSolver()
        solver.initialize()

        assert solver.solve_master_problem()
        assert solver.solve_sub_problem()

        # Add cuts until optimal
        assert solver.add_cut()
        assert not solver.is_optimal()
        assert solver.add_cut()
        assert not solver.is_optimal()
        assert solver.add_cut()
        assert solver.is_optimal()

        solver.cleanup()
        assert not solver.is_optimal()

    def test_add_cut_without_init(self) -> None:
        """未初始化时添加割 / Add cut without init."""

        class MockBendersSolver(BendersDecompositionSolver):
            def __init__(self) -> None:
                self._initialized = False

            def initialize(self) -> None:
                self._initialized = True

            def solve_master_problem(self) -> bool:
                return self._initialized

            def solve_sub_problem(self) -> bool:
                return self._initialized

            def add_cut(self) -> bool:
                return self._initialized

            def is_optimal(self) -> bool:
                return False

            def cleanup(self) -> None:
                pass

        solver = MockBendersSolver()
        assert not solver.add_cut()
