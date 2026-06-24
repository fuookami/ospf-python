"""符号类别枚举测试。

Symbol category enumeration tests.

测试 Category 枚举的值和属性。
Tests Category enum values and properties.
"""

from __future__ import annotations

from ospf_python.math.symbol.category import Category

# ── Category enum ───────────────────────────────────────────────


class TestCategory:
    """符号类别测试。"""

    def test_values(self) -> None:
        """枚举值。/ Enum values."""
        assert Category.LINEAR.value == "linear"
        assert Category.QUADRATIC.value == "quadratic"
        assert Category.CANONICAL.value == "canonical"

    def test_is_linear(self) -> None:
        """线性类别检查。/ Linear category check."""
        assert Category.LINEAR.is_linear
        assert not Category.QUADRATIC.is_linear
        assert not Category.CANONICAL.is_linear

    def test_is_quadratic(self) -> None:
        """二次类别检查。/ Quadratic category check."""
        assert Category.QUADRATIC.is_quadratic
        assert not Category.LINEAR.is_quadratic
        assert not Category.CANONICAL.is_quadratic

    def test_is_canonical(self) -> None:
        """标准类别检查。/ Canonical category check."""
        assert Category.CANONICAL.is_canonical
        assert not Category.LINEAR.is_canonical
        assert not Category.QUADRATIC.is_canonical

    def test_unique_values(self) -> None:
        """值唯一。/ Values unique."""
        values = [e.value for e in Category]
        assert len(values) == len(set(values))
