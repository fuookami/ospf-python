"""Condition 和 ListFindResult 测试。

测试条件求值与列表查找结果类型。
"""

from __future__ import annotations

from ospf_python.utils.functional import Condition, ListFindResult


class TestCondition:
    """Condition 条件求值测试。"""

    def test_condition_true(self) -> None:
        c = Condition(_predicate=lambda x: x > 0)
        assert c(5) is True

    def test_condition_false(self) -> None:
        c = Condition(_predicate=lambda x: x > 0)
        assert c(-1) is False

    def test_condition_predicate_property(self) -> None:
        pred = lambda x: x > 0  # noqa: E731
        c = Condition(_predicate=pred)
        assert c.predicate is pred

    def test_condition_call(self) -> None:
        c = Condition(_predicate=lambda x: x % 2 == 0)
        assert c(4) is True
        assert c(3) is False


class TestListFindResult:
    """ListFindResult 列表查找结果测试。"""

    def test_found_result(self) -> None:
        r = ListFindResult(_index=2, _value=42)
        assert r.index == 2
        assert r.value == 42

    def test_not_found_result(self) -> None:
        r = ListFindResult(_index=-1, _value=None)
        assert r.index == -1
        assert r.value is None

    def test_found_map(self) -> None:
        r = ListFindResult(_index=0, _value=10)
        assert r.value == 10
        assert r.index == 0

    def test_not_found_map(self) -> None:
        r: ListFindResult[int] = ListFindResult(_index=-1, _value=0)
        assert r.index == -1

    def test_found_or_else_returns_value(self) -> None:
        r = ListFindResult(_index=1, _value=5)
        assert r.value == 5

    def test_not_found_or_else_returns_default(self) -> None:
        r: ListFindResult[int] = ListFindResult(_index=-1, _value=99)
        assert r.value == 99
