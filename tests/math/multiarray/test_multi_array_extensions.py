"""多维数组运算扩展测试。

Multi-array extension tests.

测试 dot、matmul、elementwise_add、elementwise_mul。
Tests dot, matmul, elementwise_add, elementwise_mul.
"""

from __future__ import annotations

import numpy as np
import pytest

from ospf_python.multiarray.multi_array import MultiArray
from ospf_python.multiarray.shape import DynShape

try:
    from ospf_python.math.multiarray.multi_array_extensions import (
        dot,
        elementwise_add,
        elementwise_mul,
        matmul,
    )

    HAS_EXTENSIONS = True
except ImportError:
    HAS_EXTENSIONS = False


pytestmark = pytest.mark.skipif(
    not HAS_EXTENSIONS,
    reason="multi_array_extensions not available",
)


# ── dot ─────────────────────────────────────────────────────────


class TestDot:
    """点积测试。"""

    def test_1d_dot(self) -> None:
        """一维点积。/ 1D dot product."""
        shape = DynShape(dims=(3,))
        a = MultiArray(shape, np.array([1.0, 2.0, 3.0]))
        b = MultiArray(shape, np.array([4.0, 5.0, 6.0]))
        result = dot(a, b)
        assert abs(float(result) - 32.0) < 1e-10

    def test_2d_matmul(self) -> None:
        """二维矩阵乘法。/ 2D matrix multiplication."""
        shape = DynShape(dims=(2, 2))
        a = MultiArray(shape, np.array([1.0, 2.0, 3.0, 4.0]))
        b = MultiArray(shape, np.array([5.0, 6.0, 7.0, 8.0]))
        result = dot(a, b)
        expected = np.array([19.0, 22.0, 43.0, 50.0])
        np.testing.assert_allclose(
            result._data.reshape(result.shape.dims),
            expected.reshape(2, 2),
        )


# ── matmul ──────────────────────────────────────────────────────


class TestMatmul:
    """矩阵乘法测试。"""

    def test_2x2_matmul(self) -> None:
        """2x2 矩阵乘法。/ 2x2 matrix multiplication."""
        shape = DynShape(dims=(2, 2))
        a = MultiArray(shape, np.array([1.0, 2.0, 3.0, 4.0]))
        b = MultiArray(shape, np.array([5.0, 6.0, 7.0, 8.0]))
        result = matmul(a, b)
        expected = np.array([19.0, 22.0, 43.0, 50.0])
        np.testing.assert_allclose(
            result._data.reshape(result.shape.dims),
            expected.reshape(2, 2),
        )


# ── elementwise_add ─────────────────────────────────────────────


class TestElementwiseAdd:
    """逐元素加法测试。"""

    def test_1d_add(self) -> None:
        """一维逐元素加法。/ 1D element-wise addition."""
        shape = DynShape(dims=(3,))
        a = MultiArray(shape, np.array([1.0, 2.0, 3.0]))
        b = MultiArray(shape, np.array([4.0, 5.0, 6.0]))
        result = elementwise_add(a, b)
        expected = np.array([5.0, 7.0, 9.0])
        np.testing.assert_allclose(
            result._data.reshape(result.shape.dims),
            expected,
        )


# ── elementwise_mul ─────────────────────────────────────────────


class TestElementwiseMul:
    """逐元素乘法测试。"""

    def test_1d_mul(self) -> None:
        """一维逐元素乘法。/ 1D element-wise multiplication."""
        shape = DynShape(dims=(3,))
        a = MultiArray(shape, np.array([1.0, 2.0, 3.0]))
        b = MultiArray(shape, np.array([4.0, 5.0, 6.0]))
        result = elementwise_mul(a, b)
        expected = np.array([4.0, 10.0, 18.0])
        np.testing.assert_allclose(
            result._data.reshape(result.shape.dims),
            expected,
        )
