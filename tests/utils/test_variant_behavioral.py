"""Behavioral tests for utils.functional.variant module.

Targets: Variant3, Variant4 match/index/value,
and V2Left/V2Right covered edge cases.
"""

from __future__ import annotations

import pytest

from ospf_python.utils.functional import (
    V3V1,
    V3V2,
    V3V3,
    V4V1,
    V4V2,
    V4V3,
    V4V4,
    V2Left,
    V2Right,
    Variant2,
    Variant3,
    Variant4,
)


class TestVariant2Deeper:
    """Variant2 深度行为测试。/ Variant2 deeper behavioral tests."""

    def test_v2left_frozen(self) -> None:
        """V2Left frozen dataclass 不可变。/ V2Left frozen dataclass."""
        v = V2Left(42)
        with pytest.raises(AttributeError):
            v._value = 99  # type: ignore[misc]

    def test_v2right_frozen(self) -> None:
        """V2Right frozen dataclass 不可变。/ V2Right frozen dataclass."""
        v = V2Right("hello")
        with pytest.raises(AttributeError):
            v._value = "bye"  # type: ignore[misc]

    def test_v2right_value(self) -> None:
        """V2Right.value 属性。/ V2Right.value property."""
        v: Variant2[int, str] = V2Right("world")
        assert v.value == "world"

    def test_v2left_value(self) -> None:
        """V2Left.value 属性。/ V2Left.value property."""
        v: Variant2[int, str] = V2Left(10)
        assert v.value == 10

    def test_match_returns_handler_result(self) -> None:
        """match 返回对应处理器结果。/ match returns handler result."""
        v: Variant2[int, str] = V2Left(3)
        assert v.match(lambda x: x * 10, lambda s: len(s)) == 30

    def test_match_right_branch(self) -> None:
        """match 右分支。/ match on right branch."""
        v: Variant2[int, str] = V2Right("abc")
        assert v.match(lambda x: x * 10, lambda s: len(s)) == 3


class TestVariant3:
    """Variant3 行为测试。/ Variant3 behavioral tests."""

    def test_v3v1_index(self) -> None:
        """V3V1 索引为 0。/ V3V1 index is 0."""
        v: Variant3[int, str, float] = V3V1(42)
        assert v.index() == 0
        assert v.value == 42

    def test_v3v2_index(self) -> None:
        """V3V2 索引为 1。/ V3V2 index is 1."""
        v: Variant3[int, str, float] = V3V2("hello")
        assert v.index() == 1
        assert v.value == "hello"

    def test_v3v3_index(self) -> None:
        """V3V3 索引为 2。/ V3V3 index is 2."""
        v: Variant3[int, str, float] = V3V3(3.14)
        assert v.index() == 2
        assert v.value == pytest.approx(3.14)

    def test_v3v1_match(self) -> None:
        """V3V1 match 分发到第一个处理器。/ V3V1 match dispatches to first handler."""
        v: Variant3[int, str, float] = V3V1(5)
        result = v.match(lambda x: x * 2, lambda s: len(s), lambda f: f"float:{f}")
        assert result == 10

    def test_v3v2_match(self) -> None:
        """V3V2 match 分发到第二个处理器。/ V3V2 match dispatches to second handler."""
        v: Variant3[int, str, float] = V3V2("abc")
        result = v.match(lambda x: x * 2, lambda s: len(s), lambda f: f"float:{f}")
        assert result == 3

    def test_v3v3_match(self) -> None:
        """V3V3 match 分发到第三个处理器。/ V3V3 match dispatches to third handler."""
        v: Variant3[int, str, float] = V3V3(2.5)
        result = v.match(lambda x: x * 2, lambda s: len(s), lambda f: f"float:{f}")
        assert result == "float:2.5"

    def test_v3_frozen(self) -> None:
        """V3 frozen dataclass 不可变。/ V3 frozen dataclass."""
        v = V3V1(1)
        with pytest.raises(AttributeError):
            v._value = 99  # type: ignore[misc]


class TestVariant4:
    """Variant4 行为测试。/ Variant4 behavioral tests."""

    def test_v4v1_index(self) -> None:
        """V4V1 索引为 0。/ V4V1 index is 0."""
        v: Variant4[int, str, float, bool] = V4V1(42)
        assert v.index() == 0
        assert v.value == 42

    def test_v4v2_index(self) -> None:
        """V4V2 索引为 1。/ V4V2 index is 1."""
        v: Variant4[int, str, float, bool] = V4V2("hello")
        assert v.index() == 1
        assert v.value == "hello"

    def test_v4v3_index(self) -> None:
        """V4V3 索引为 2。/ V4V3 index is 2."""
        v: Variant4[int, str, float, bool] = V4V3(3.14)
        assert v.index() == 2
        assert v.value == pytest.approx(3.14)

    def test_v4v4_index(self) -> None:
        """V4V4 索引为 3。/ V4V4 index is 3."""
        v: Variant4[int, str, float, bool] = V4V4(True)
        assert v.index() == 3
        assert v.value is True

    def test_v4v1_match(self) -> None:
        """V4V1 match 分发到第一个处理器。/ V4V1 match dispatches to first handler."""
        v: Variant4[int, str, float, bool] = V4V1(5)
        result = v.match(
            lambda x: f"int:{x}",
            lambda s: f"str:{s}",
            lambda f: f"float:{f}",
            lambda b: f"bool:{b}",
        )
        assert result == "int:5"

    def test_v4v2_match(self) -> None:
        """V4V2 match 分发到第二个处理器。/ V4V2 match dispatches to second handler."""
        v: Variant4[int, str, float, bool] = V4V2("test")
        result = v.match(
            lambda x: f"int:{x}",
            lambda s: f"str:{s}",
            lambda f: f"float:{f}",
            lambda b: f"bool:{b}",
        )
        assert result == "str:test"

    def test_v4v3_match(self) -> None:
        """V4V3 match 分发到第三个处理器。/ V4V3 match dispatches to third handler."""
        v: Variant4[int, str, float, bool] = V4V3(1.5)
        result = v.match(
            lambda x: f"int:{x}",
            lambda s: f"str:{s}",
            lambda f: f"float:{f}",
            lambda b: f"bool:{b}",
        )
        assert result == "float:1.5"

    def test_v4v4_match(self) -> None:
        """V4V4 match 分发到第四个处理器。/ V4V4 match dispatches to fourth handler."""
        v: Variant4[int, str, float, bool] = V4V4(False)
        result = v.match(
            lambda x: f"int:{x}",
            lambda s: f"str:{s}",
            lambda f: f"float:{f}",
            lambda b: f"bool:{b}",
        )
        assert result == "bool:False"

    def test_v4_frozen(self) -> None:
        """V4 frozen dataclass 不可变。/ V4 frozen dataclass."""
        v = V4V1(1)
        with pytest.raises(AttributeError):
            v._value = 99  # type: ignore[misc]
