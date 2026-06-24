"""量纲测试。/ Dimension tests.

测试量纲创建、运算、导出量和量域。
Tests dimension creation, operations,
derived quantity, and quantity domain.
"""

from __future__ import annotations

import pytest

from ospf_python.quantities.dimension.derived_quantity import (
    DerivedQuantity,
)
from ospf_python.quantities.dimension.dimensions import (
    Dimensions,
)
from ospf_python.quantities.dimension.fundamental_quantity import (
    FundamentalQuantity,
)
from ospf_python.quantities.dimension.quantity_domain import (
    QuantityDomain,
)

# ── 量纲创建 ─────────────────────────────────────────────────────


class TestDimensionsCreation:
    """量纲创建测试。"""

    def test_default_dimensionless(self) -> None:
        """默认无量纲。/ Default dimensionless."""
        d = Dimensions()
        assert d.mass == 0.0
        assert d.length == 0.0
        assert d.time == 0.0

    def test_create_with_values(self) -> None:
        """指定值创建。/ Create with specified values."""
        d = Dimensions(mass=1, length=2, time=-2)
        assert d.mass == 1.0
        assert d.length == 2.0
        assert d.time == -2.0

    def test_create_all_seven(self) -> None:
        """七个基本量纲。/ All seven fundamentals."""
        d = Dimensions(
            mass=1,
            length=2,
            time=-2,
            current=0,
            temperature=0,
            amount=0,
            luminous_intensity=0,
        )
        assert d.mass == 1.0
        assert d.length == 2.0
        assert d.time == -2.0
        assert d.current == 0.0


# ── 量纲运算 ─────────────────────────────────────────────────────


class TestDimensionsOperations:
    """量纲运算测试。"""

    def test_multiply(self) -> None:
        """量纲相乘（指数相加）。
        Dimension multiply (exponents add).
        """
        d1 = Dimensions(length=1)
        d2 = Dimensions(length=1)
        result = d1 * d2
        assert result.length == 2.0

    def test_divide(self) -> None:
        """量纲相除（指数相减）。
        Dimension divide (exponents subtract).
        """
        d1 = Dimensions(length=2)
        d2 = Dimensions(length=1)
        result = d1 / d2
        assert result.length == 1.0

    def test_power(self) -> None:
        """量纲乘方。/ Dimension power."""
        d = Dimensions(length=1, time=-1)
        result = d**2
        assert result.length == 2.0
        assert result.time == -2.0

    def test_is_dimensionless(self) -> None:
        """无量纲检查。/ Dimensionless check."""
        d = Dimensions()
        assert d.is_dimensionless()

    def test_not_dimensionless(self) -> None:
        """有量纲检查。/ Not dimensionless check."""
        d = Dimensions(length=1)
        assert not d.is_dimensionless()

    def test_multiply_complex(self) -> None:
        """复合量纲乘法。/ Complex dimension multiply."""
        force = Dimensions(mass=1, length=1, time=-2)
        length = Dimensions(length=1)
        work = force * length
        assert work.mass == 1.0
        assert work.length == 2.0
        assert work.time == -2.0


# ── 基本量纲枚举 ─────────────────────────────────────────────────


class TestFundamentalQuantity:
    """基本量纲枚举测试。"""

    def test_enum_values(self) -> None:
        """枚举值。/ Enum values."""
        assert FundamentalQuantity.MASS.value == "mass"
        assert FundamentalQuantity.LENGTH.value == "length"
        assert FundamentalQuantity.TIME.value == "time"

    def test_enum_count(self) -> None:
        """枚举数量。/ Enum count."""
        assert len(FundamentalQuantity) == 7

    def test_get_exponent(self) -> None:
        """获取基本量纲指数。/ Get fundamental exponent."""
        d = Dimensions(mass=1, length=2, time=-2)
        assert d.get(FundamentalQuantity.MASS) == 1.0
        assert d.get(FundamentalQuantity.LENGTH) == 2.0
        assert d.get(FundamentalQuantity.TIME) == -2.0
        assert d.get(FundamentalQuantity.CURRENT) == 0.0


# ── 导出量 ───────────────────────────────────────────────────────


class TestDerivedQuantity:
    """导出量测试。"""

    def test_create(self) -> None:
        """创建导出量。/ Create derived quantity."""
        d = Dimensions(length=2)
        q = DerivedQuantity(name="area", dimensions=d)
        assert q.name == "area"
        assert q.dimensions.length == 2.0

    def test_frozen(self) -> None:
        """不可变性。/ Immutability."""
        d = Dimensions(length=1)
        q = DerivedQuantity(name="length", dimensions=d)
        with pytest.raises(AttributeError):
            q.name = "other"  # type: ignore[misc]


# ── 量域 ─────────────────────────────────────────────────────────


class TestQuantityDomain:
    """量域测试。"""

    def test_empty_domain(self) -> None:
        """空量域。/ Empty domain."""
        domain = QuantityDomain(name="mechanics")
        assert domain.name == "mechanics"
        assert len(domain.quantities) == 0

    def test_domain_with_quantities(self) -> None:
        """带导出量的量域。/ Domain with quantities."""
        length = DerivedQuantity(
            name="length",
            dimensions=Dimensions(length=1),
        )
        area = DerivedQuantity(
            name="area",
            dimensions=Dimensions(length=2),
        )
        domain = QuantityDomain(
            name="geometry",
            quantities=(length, area),
        )
        assert len(domain.quantities) == 2
        assert domain.quantities[0].name == "length"
