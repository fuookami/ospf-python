"""SolveValue 测试。

测试求解值的创建、获取和验证。
Tests SolveValue creation, access, and validation.
"""

from __future__ import annotations

import pytest

from ospf_python.core.solver.value.solve_value import SolveValue
from ospf_python.core.solver.value.solve_value_validation import (
    SolveValueValidation,
)


class TestSolveValueCreation:
    """创建测试 / Creation tests."""

    def test_frozen(self) -> None:
        """实例不可变。/ Instance is frozen."""
        sv = SolveValue(values={"x": 1.0})
        with pytest.raises(AttributeError):
            sv.values = {}  # type: ignore[misc]

    def test_empty(self) -> None:
        """默认为空。/ Default is empty."""
        sv = SolveValue()
        assert sv.is_empty is True


class TestSolveValueAccess:
    """访问测试 / Access tests."""

    def test_get_existing(self) -> None:
        """获取存在的变量。/ Get existing variable."""
        sv = SolveValue(values={"x": 3.14, "y": 2.0})
        assert sv.get("x") == 3.14

    def test_get_missing_uses_default(self) -> None:
        """缺失变量返回默认值。/ Missing returns default."""
        sv = SolveValue(values={"x": 1.0})
        assert sv.get("z", default=99.0) == 99.0

    def test_variable_names(self) -> None:
        """变量名元组。/ Variable name tuple."""
        sv = SolveValue(values={"a": 1.0, "b": 2.0})
        assert set(sv.variable_names) == {"a", "b"}


class TestSolveValueValidation:
    """验证测试 / Validation tests."""

    def test_valid_values(self) -> None:
        """正常值通过验证。/ Normal values pass."""
        sv = SolveValue(values={"x": 1.0, "y": 2.0})
        result = SolveValueValidation.validate(sv)
        assert result.is_valid is True
        assert len(result.issues) == 0

    def test_nan_detected(self) -> None:
        """NaN 值被检测。/ NaN detected."""
        sv = SolveValue(values={"x": float("nan")})
        result = SolveValueValidation.validate(sv)
        assert result.is_valid is False
        assert len(result.issues) == 1

    def test_inf_detected(self) -> None:
        """Inf 值被检测。/ Inf detected."""
        sv = SolveValue(values={"x": float("inf")})
        result = SolveValueValidation.validate(sv)
        assert result.is_valid is False

    def test_nan_allowed(self) -> None:
        """允许 NaN。/ NaN allowed."""
        sv = SolveValue(values={"x": float("nan")})
        result = SolveValueValidation.validate(
            sv,
            allow_nan=True,
        )
        assert result.is_valid is True

    def test_inf_allowed(self) -> None:
        """允许 Inf。/ Inf allowed."""
        sv = SolveValue(values={"x": float("inf")})
        result = SolveValueValidation.validate(
            sv,
            allow_inf=True,
        )
        assert result.is_valid is True
