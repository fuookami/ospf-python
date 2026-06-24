"""多维数组快速求和测试。

Fast sum tests for multi-arrays.

测试 fast_sum 函数的全轴和沿轴求和。
Tests fast_sum full-axis and along-axis summation.
"""

from __future__ import annotations

import numpy as np
import pytest

from ospf_python.multiarray.multi_array import MultiArray
from ospf_python.multiarray.shape import DynShape

try:
    from ospf_python.math.multiarray.fast_sum import fast_sum

    HAS_FAST_SUM = True
except ImportError:
    HAS_FAST_SUM = False


pytestmark = pytest.mark.skipif(
    not HAS_FAST_SUM,
    reason="fast_sum not available",
)


# ── fast_sum ────────────────────────────────────────────────────


class TestFastSum:
    """快速求和测试。"""

    def test_sum_all_elements(self) -> None:
        """对所有元素求和。/ Sum all elements."""
        shape = DynShape(dims=(3,))
        arr = MultiArray(shape, np.array([1.0, 2.0, 3.0]))
        result = fast_sum(arr)
        assert abs(float(result) - 6.0) < 1e-10

    def test_sum_2d_all(self) -> None:
        """二维数组全部求和。/ 2D array sum all."""
        shape = DynShape(dims=(2, 2))
        arr = MultiArray(shape, np.array([1.0, 2.0, 3.0, 4.0]))
        result = fast_sum(arr)
        assert abs(float(result) - 10.0) < 1e-10

    def test_sum_along_axis(self) -> None:
        """沿轴求和。/ Sum along axis."""
        shape = DynShape(dims=(2, 3))
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        arr = MultiArray(shape, data)
        result = fast_sum(arr, axis=0)
        expected = np.array([5.0, 7.0, 9.0])
        np.testing.assert_allclose(
            result._data.reshape(result.shape.dims),
            expected,
        )

    def test_sum_empty_axis(self) -> None:
        """沿轴 1 求和。/ Sum along axis 1."""
        shape = DynShape(dims=(2, 3))
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        arr = MultiArray(shape, data)
        result = fast_sum(arr, axis=1)
        expected = np.array([6.0, 15.0])
        np.testing.assert_allclose(
            result._data.reshape(result.shape.dims),
            expected,
        )
