"""SolveOptions 测试。

测试求解选项的创建、默认值和不可变方法。
Tests SolveOptions creation, defaults, and immutable methods.
"""

from __future__ import annotations

import pytest

from ospf_python.core.solver.solve_options import SolveOptions


class TestSolveOptionsDefaults:
    """默认值测试 / Default value tests."""

    def test_default_time_limit(self) -> None:
        """默认时间限制为无穷。/ Default time limit is inf."""
        opts = SolveOptions()
        assert opts.time_limit == float("inf")

    def test_default_gap_tolerance(self) -> None:
        """默认间隙容差。/ Default gap tolerance."""
        opts = SolveOptions()
        assert opts.gap_tolerance == 1e-4

    def test_default_verbose(self) -> None:
        """默认不详细输出。/ Default verbose is False."""
        opts = SolveOptions()
        assert opts.verbose is False

    def test_default_threads(self) -> None:
        """默认线程数为 1。/ Default threads is 1."""
        opts = SolveOptions()
        assert opts.threads == 1

    def test_default_seed(self) -> None:
        """默认随机种子。/ Default random seed."""
        opts = SolveOptions()
        assert opts.seed == 42


class TestSolveOptionsFrozen:
    """不可变性测试 / Immutability tests."""

    def test_frozen(self) -> None:
        """实例不可变。/ Instance is frozen."""
        opts = SolveOptions()
        with pytest.raises(AttributeError):
            opts.time_limit = 10.0  # type: ignore[misc]


class TestSolveOptionsWithMethods:
    """with 方法测试 / With-method tests."""

    def test_with_time_limit(self) -> None:
        """创建带新时间限制的副本。/ Copy with new time limit."""
        opts = SolveOptions()
        new_opts = opts.with_time_limit(60.0)
        assert new_opts.time_limit == 60.0
        assert opts.time_limit == float("inf")

    def test_with_verbose(self) -> None:
        """创建带新日志设置的副本。/ Copy with verbose."""
        opts = SolveOptions()
        new_opts = opts.with_verbose(True)
        assert new_opts.verbose is True
        assert opts.verbose is False

    def test_chaining(self) -> None:
        """链式调用。/ Method chaining."""
        opts = SolveOptions()
        new_opts = opts.with_time_limit(30.0).with_verbose(True)
        assert new_opts.time_limit == 30.0
        assert new_opts.verbose is True
