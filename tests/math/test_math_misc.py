"""数学杂项模块测试。

Tests for miscellaneous math modules: range_to,
Tolerance, FltXPowerStrategy, collection_aliases,
QuadraticInequality, and collection extensions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from ospf_python.math.collection_aliases import FloatList, IntList, NumberList

# ============================================================
# range_to
# ============================================================


class TestRangeTo:
    """range_to 测试。/ range_to tests."""

    def test_basic_range(self) -> None:
        """基本范围。/ Basic range."""
        from ospf_python.math.operator.range_to import range_to

        result = range_to(0, 5)
        assert isinstance(result, range)
        assert list(result) == [0, 1, 2, 3, 4]

    def test_empty_range(self) -> None:
        """空范围。/ Empty range."""
        from ospf_python.math.operator.range_to import range_to

        result = range_to(5, 5)
        assert list(result) == []

    def test_negative_range(self) -> None:
        """反向范围。/ Reverse range."""
        from ospf_python.math.operator.range_to import range_to

        result = range_to(5, 3)
        assert list(result) == []


# ============================================================
# Tolerance
# ============================================================


class TestTolerance:
    """Tolerance 测试。/ Tolerance tests."""

    def test_is_close_true(self) -> None:
        """近似相等。/ Approximately equal."""
        from ospf_python.math.operator.tolerance import Tolerance

        t = Tolerance(epsilon=0.01)
        assert t.is_close(1.0, 1.005) is True

    def test_is_close_false(self) -> None:
        """不近似相等。/ Not approximately equal."""
        from ospf_python.math.operator.tolerance import Tolerance

        t = Tolerance(epsilon=0.01)
        assert t.is_close(1.0, 1.1) is False

    def test_exact_match(self) -> None:
        """精确匹配。/ Exact match."""
        from ospf_python.math.operator.tolerance import Tolerance

        t = Tolerance(epsilon=0.0)
        assert t.is_close(5.0, 5.0) is True

    def test_frozen(self) -> None:
        """frozen dataclass。/ frozen dataclass."""
        from ospf_python.math.operator.tolerance import Tolerance

        t = Tolerance(epsilon=0.01)
        with pytest.raises(AttributeError):
            t.epsilon = 0.1  # type: ignore[misc]


# ============================================================
# FltXPowerStrategy
# ============================================================


class TestFltXPowerStrategy:
    """FltXPowerStrategy 测试。/ FltXPowerStrategy tests."""

    def test_fast_value(self) -> None:
        """FAST 枚举值。/ FAST enum value."""
        from ospf_python.math.ordinary.flt_x_power_strategy import (
            FltXPowerStrategy,
        )

        assert FltXPowerStrategy.FAST.value == "fast"

    def test_precise_value(self) -> None:
        """PRECISE 枚举值。/ PRECISE enum value."""
        from ospf_python.math.ordinary.flt_x_power_strategy import (
            FltXPowerStrategy,
        )

        assert FltXPowerStrategy.PRECISE.value == "precise"

    def test_members(self) -> None:
        """枚举成员数量。/ Enum member count."""
        from ospf_python.math.ordinary.flt_x_power_strategy import (
            FltXPowerStrategy,
        )

        assert len(FltXPowerStrategy) == 2


# ============================================================
# collection_aliases
# ============================================================


class TestCollectionAliases:
    """collection_aliases 测试。/ collection_aliases tests."""

    def test_int_list_type(self) -> None:
        """IntList 类型别名。/ IntList type alias."""

        x: IntList = [1, 2, 3]
        assert isinstance(x, list)

    def test_float_list_type(self) -> None:
        """FloatList 类型别名。/ FloatList type alias."""

        x: FloatList = [1.0, 2.0]
        assert isinstance(x, list)

    def test_number_list_type(self) -> None:
        """NumberList 类型别名。/ NumberList type alias."""

        x: NumberList = [1, 2.5, 3]
        assert isinstance(x, list)


# ============================================================
# collection_extensions (math/utils/functional)
# ============================================================


class TestCollectionExtensions:
    """collection_extensions 测试。/ Collection extensions tests."""

    def test_sum_by(self) -> None:
        """sum_by 求和。/ sum_by summation."""
        from ospf_python.math.utils.functional.collection_extensions import (
            sum_by,
        )

        items = [("a", 1), ("b", 2), ("c", 3)]
        result = sum_by(items, selector=lambda x: x[1])
        assert result == 6.0

    def test_sum_by_empty(self) -> None:
        """空列表 sum_by 为 0。/ Empty sum_by is 0."""
        from ospf_python.math.utils.functional.collection_extensions import (
            sum_by,
        )

        result = sum_by([], selector=lambda x: x)
        assert result == 0.0

    def test_product(self) -> None:
        """product 乘积。/ product multiplication."""
        from ospf_python.math.utils.functional.collection_extensions import (
            product,
        )

        result = product([2.0, 3.0, 4.0])
        assert result == pytest.approx(24.0)

    def test_product_empty(self) -> None:
        """空列表 product 为 1。/ Empty product is 1."""
        from ospf_python.math.utils.functional.collection_extensions import (
            product,
        )

        result = product([])
        assert result == pytest.approx(1.0)

    def test_product_single(self) -> None:
        """单元素 product。/ Single element product."""
        from ospf_python.math.utils.functional.collection_extensions import (
            product,
        )

        result = product([5.0])
        assert result == pytest.approx(5.0)


# ============================================================
# QuadraticInequality
# ============================================================


class TestQuadraticInequality:
    """QuadraticInequality 测试。/ QuadraticInequality tests."""

    def test_import(self) -> None:
        """导入 QuadraticInequality。/ Import QuadraticInequality."""
        from ospf_python.math.symbol.inequality.quadratic_inequality import (
            QuadraticInequality,
        )

        assert QuadraticInequality is not None


# ============================================================
# math/utils/parallel/fold (math layer)
# ============================================================


class TestMathParallelFold:
    """数学层并行折叠测试。/ Math-layer parallel fold tests."""

    def test_import(self) -> None:
        """导入 fold_parallel。/ Import fold_parallel."""
        from ospf_python.math.utils.parallel.fold import fold_parallel

        assert callable(fold_parallel)
