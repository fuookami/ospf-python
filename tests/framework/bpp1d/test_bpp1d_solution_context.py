"""BPP1D 解上下文行为测试 / BPP1D solution context behavioral tests.

测试 SolutionContext 的创建、注册和查询。
Test SolutionContext creation, registration, and lookup.
"""

from __future__ import annotations

from ospf_python.framework.bpp1d.domain.solution.model.solution import Solution
from ospf_python.framework.bpp1d.domain.solution.solution_context import (
    SolutionContext,
)


class TestSolutionContextBehavioral:
    """解上下文行为测试 / Solution context behavioral tests."""

    def test_create_with_initial_solutions(self) -> None:
        """创建带初始解的上下文 / Create context with initial solutions."""
        sol = Solution.create(solution_key="s1", objective_value=5.0)
        ctx = SolutionContext.create(solutions={"s1": sol})
        assert ctx.count == 1
        assert ctx.get("s1") is not None

    def test_create_with_none_solutions(self) -> None:
        """创建无初始解的上下文 / Create context with None solutions."""
        ctx = SolutionContext.create(solutions=None)
        assert ctx.count == 0

    def test_register_returns_new_context(self) -> None:
        """注册返回新上下文 / Register returns new context."""
        ctx = SolutionContext.create()
        sol = Solution.create(solution_key="s1", objective_value=5.0)
        new_ctx = ctx.register(sol)
        assert ctx.count == 0  # Original unchanged (immutable)
        assert new_ctx.count == 1

    def test_get_returns_none_for_missing(self) -> None:
        """查询不存在的解返回 None / Get returns None for missing."""
        ctx = SolutionContext.create()
        assert ctx.get("nonexistent") is None

    def test_get_best_empty_context(self) -> None:
        """空上下文最优解为 None / Best solution is None for empty context."""
        ctx = SolutionContext.create()
        assert ctx.get_best() is None

    def test_get_best_returns_minimum_objective(self) -> None:
        """最优解为目标值最小的解 / Best solution has minimum objective value."""
        sol_a = Solution.create(solution_key="s1", objective_value=5.0)
        sol_b = Solution.create(solution_key="s2", objective_value=2.0)
        sol_c = Solution.create(solution_key="s3", objective_value=8.0)
        ctx = (
            SolutionContext.create()
            .register(sol_a)
            .register(sol_b)
            .register(sol_c)
        )
        best = ctx.get_best()
        assert best is not None
        assert best.solution_key == "s2"
        assert best.objective_value == 2.0

    def test_get_all(self) -> None:
        """获取所有解 / Get all solutions."""
        sol_a = Solution.create(solution_key="s1", objective_value=3.0)
        sol_b = Solution.create(solution_key="s2", objective_value=1.0)
        ctx = SolutionContext.create().register(sol_a).register(sol_b)
        all_solutions = ctx.get_all()
        assert len(all_solutions) == 2

    def test_count_property(self) -> None:
        """解数量属性 / Solution count property."""
        ctx = SolutionContext.create()
        assert ctx.count == 0
        sol = Solution.create(solution_key="s1", objective_value=1.0)
        ctx = ctx.register(sol)
        assert ctx.count == 1
