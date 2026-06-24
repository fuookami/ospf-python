"""Tests for framework solver orchestration.

框架求解器编排测试。
"""

from __future__ import annotations

import pytest

from ospf_python.framework.solver.framework_async import (
    gather_with_limit,
    run_with_timeout,
)
from ospf_python.framework.solver.framework_solve_options import (
    FrameworkSolveOptions,
)

# -- FrameworkSolveOptions extra tests --------------------------------


class TestFrameworkSolveOptionsExtra:
    """Test FrameworkSolveOptions edge cases."""

    def test_defaults(self) -> None:
        """默认值 / Default values."""
        opts = FrameworkSolveOptions()
        assert opts.timeout_seconds == pytest.approx(3600.0)
        assert opts.tolerance == pytest.approx(1e-6)
        assert opts.max_iterations == 10000
        assert opts.verbose is False

    def test_custom_timeout(self) -> None:
        """自定义超时 / Custom timeout."""
        opts = FrameworkSolveOptions(timeout_seconds=60.0)
        assert opts.timeout_seconds == pytest.approx(60.0)

    def test_custom_tolerance(self) -> None:
        """自定义容差 / Custom tolerance."""
        opts = FrameworkSolveOptions(tolerance=1e-4)
        assert opts.tolerance == pytest.approx(1e-4)

    def test_verbose_mode(self) -> None:
        """详细模式 / Verbose mode."""
        opts = FrameworkSolveOptions(verbose=True)
        assert opts.verbose is True

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        opts = FrameworkSolveOptions()
        with pytest.raises(AttributeError):
            opts.verbose = True  # type: ignore[misc]

    def test_custom_iterations(self) -> None:
        """自定义迭代次数 / Custom iterations."""
        opts = FrameworkSolveOptions(max_iterations=500)
        assert opts.max_iterations == 500


# -- Async utilities extra tests -------------------------------------


class TestFrameworkAsyncExtra:
    """Test async utility edge cases."""

    @pytest.mark.asyncio
    async def test_run_with_timeout_returns_value(self) -> None:
        """超时内返回值 / Returns value within timeout."""
        result = await run_with_timeout(
            _async_return(99),
            timeout_seconds=5.0,
        )
        assert result == 99

    @pytest.mark.asyncio
    async def test_gather_preserves_order(self) -> None:
        """有限并发保持顺序 / Gather preserves order."""
        coros = [_async_return(i) for i in range(10)]
        results = await gather_with_limit(*coros, limit=3)
        assert results == list(range(10))

    @pytest.mark.asyncio
    async def test_gather_single_coroutine(self) -> None:
        """单协程 / Single coroutine."""
        results = await gather_with_limit(_async_return(42), limit=5)
        assert results == [42]


async def _async_return(value: object) -> object:
    """辅助异步返回函数 / Helper async return function."""
    return value
