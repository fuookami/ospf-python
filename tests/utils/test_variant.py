"""Variant 类型测试。

测试 Variant2..Variant7 的 match、index 等操作。
"""

from __future__ import annotations

from ospf_python.utils.functional import V2Left, V2Right, Variant2


class TestVariant2:
    """Variant2 二元变体测试。"""

    def test_first_variant(self) -> None:
        v: Variant2[int, str] = V2Left(42)
        assert v.index() == 0
        assert v.value == 42

    def test_second_variant(self) -> None:
        v: Variant2[int, str] = V2Right("hello")
        assert v.index() == 1
        assert v.value == "hello"

    def test_match_on_first(self) -> None:
        v: Variant2[int, str] = V2Left(10)
        result = v.match(
            lambda x: x * 2,
            lambda s: len(s),
        )
        assert result == 20

    def test_match_on_second(self) -> None:
        v: Variant2[int, str] = V2Right("abc")
        result = v.match(
            lambda x: x * 2,
            lambda s: len(s),
        )
        assert result == 3

    def test_variant_mixed_types(self) -> None:
        v1: Variant2[int, str] = V2Left(1)
        v2: Variant2[int, str] = V2Right("two")
        assert v1.index() != v2.index()
