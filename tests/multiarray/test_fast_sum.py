"""Fast sum 工具测试。

测试快速求和工具的功能。
Tests fast sum utility functionality.
"""

from __future__ import annotations

from ospf_python.multiarray.multi_array import MultiArray
from ospf_python.multiarray.shape import Shape1, Shape2


class TestFastSum:
    """快速求和测试 / Fast sum tests."""

    def test_sum_1d(self) -> None:
        """一维数组求和。/ 1D array sum."""
        arr = MultiArray.from_list(
            [1, 2, 3, 4, 5],
            Shape1(d0=5),
        )
        total = arr.reduce(lambda a, b: a + b)
        assert total == 15

    def test_sum_2d(self) -> None:
        """二维数组求和。/ 2D array sum."""
        arr = MultiArray.from_list(
            [1, 2, 3, 4, 5, 6],
            Shape2(d0=2, d1=3),
        )
        total = arr.reduce(lambda a, b: a + b)
        assert total == 21

    def test_sum_empty(self) -> None:
        """空数组求和。/ Empty array sum."""
        arr = MultiArray.zeros(Shape1(d0=1))
        total = arr.reduce(lambda a, b: a + b)
        assert total == 0.0
