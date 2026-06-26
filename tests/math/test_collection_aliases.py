"""集合类型别名测试。

Collection type alias tests.

测试 IntList、FloatList、NumberList 类型别名。
Tests IntList, FloatList, NumberList type aliases.
"""

from __future__ import annotations

from ospf_python.math.collection_aliases import (  # noqa: F401, TC001
    FloatList,
    IntList,
    NumberList,
)

# ── IntList ─────────────────────────────────────────────────────


class TestIntList:
    """整数列表别名测试。"""

    def test_empty_list(self) -> None:
        """空整数列表。/ Empty int list."""
        lst: IntList = []
        assert len(lst) == 0

    def test_single_element(self) -> None:
        """单元素列表。/ Single element list."""
        lst: IntList = [42]
        assert lst[0] == 42

    def test_multiple_elements(self) -> None:
        """多元素列表。/ Multiple element list."""
        lst: IntList = [1, 2, 3, 4, 5]
        assert len(lst) == 5

    def test_negative_values(self) -> None:
        """负值列表。/ Negative values list."""
        lst: IntList = [-1, -2, -3]
        assert all(v < 0 for v in lst)

    def test_is_list_type(self) -> None:
        """类型为 list。/ Type is list."""
        lst: IntList = [1, 2, 3]
        assert isinstance(lst, list)


# ── FloatList ───────────────────────────────────────────────────


class TestFloatList:
    """浮点数列表别名测试。"""

    def test_empty_list(self) -> None:
        """空浮点列表。/ Empty float list."""
        lst: FloatList = []
        assert len(lst) == 0

    def test_single_element(self) -> None:
        """单元素列表。/ Single element list."""
        lst: FloatList = [3.14]
        assert abs(lst[0] - 3.14) < 1e-10

    def test_multiple_elements(self) -> None:
        """多元素列表。/ Multiple element list."""
        lst: FloatList = [1.0, 2.0, 3.0]
        assert len(lst) == 3

    def test_contains_float(self) -> None:
        """包含浮点值。/ Contains float values."""
        lst: FloatList = [0.5, 1.5, 2.5]
        assert all(isinstance(v, float) for v in lst)


# ── NumberList ──────────────────────────────────────────────────


class TestNumberList:
    """数值列表别名测试。"""

    def test_mixed_types(self) -> None:
        """混合类型列表。/ Mixed type list."""
        lst: NumberList = [1, 2.5, 3, 4.0]
        assert len(lst) == 4

    def test_all_ints(self) -> None:
        """全整数列表。/ All int list."""
        lst: NumberList = [1, 2, 3]
        assert all(isinstance(v, int) for v in lst)

    def test_all_floats(self) -> None:
        """全浮点列表。/ All float list."""
        lst: NumberList = [1.0, 2.0, 3.0]
        assert all(isinstance(v, float) for v in lst)

    def test_empty_list(self) -> None:
        """空数值列表。/ Empty number list."""
        lst: NumberList = []
        assert len(lst) == 0
