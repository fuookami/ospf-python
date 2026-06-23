"""Multi-dimensional array abstraction with numpy backend.

Provides a high-level interface for multi-dimensional arrays
with support for indexing, slicing, and mathematical operations.
"""

from __future__ import annotations

from typing import Any, TypeVar, Union

import numpy as np
from numpy.typing import NDArray

T = TypeVar("T")
Numeric = Union[int, float, np.integer, np.floating]


class MultiArray:
    """Multi-dimensional array wrapper around numpy.

    多维数组包装器，基于 numpy 实现。
    """

    __slots__ = ("_data",)

    def __init__(self, data: NDArray[Any]) -> None:
        """Initialize from numpy array.

        Args:
            data: Numpy array.
        """
        self._data = data

    @classmethod
    def from_list(cls, data: list[Any]) -> MultiArray:
        """Create from nested list.

        Args:
            data: Nested list of numbers.

        Returns:
            MultiArray instance.
        """
        return cls(np.array(data))

    @classmethod
    def zeros(cls, shape: tuple[int, ...]) -> MultiArray:
        """Create array of zeros.

        Args:
            shape: Array shape.

        Returns:
            MultiArray of zeros.
        """
        return cls(np.zeros(shape))

    @classmethod
    def ones(cls, shape: tuple[int, ...]) -> MultiArray:
        """Create array of ones.

        Args:
            shape: Array shape.

        Returns:
            MultiArray of ones.
        """
        return cls(np.ones(shape))

    @classmethod
    def full(cls, shape: tuple[int, ...], fill_value: Numeric) -> MultiArray:
        """Create array filled with value.

        Args:
            shape: Array shape.
            fill_value: Fill value.

        Returns:
            MultiArray filled with value.
        """
        return cls(np.full(shape, fill_value))

    @classmethod
    def arange(cls, *args: Any) -> MultiArray:
        """Create array with evenly spaced values.

        Args:
            *args: Arguments passed to np.arange.

        Returns:
            MultiArray with range values.
        """
        return cls(np.arange(*args))

    @classmethod
    def eye(cls, n: int) -> MultiArray:
        """Create identity matrix.

        Args:
            n: Matrix size.

        Returns:
            Identity matrix as MultiArray.
        """
        return cls(np.eye(n))

    @property
    def shape(self) -> tuple[int, ...]:
        """Get array shape."""
        return self._data.shape

    @property
    def ndim(self) -> int:
        """Get number of dimensions."""
        return self._data.ndim

    @property
    def size(self) -> int:
        """Get total number of elements."""
        return self._data.size

    @property
    def dtype(self) -> np.dtype[Any]:
        """Get data type."""
        return self._data.dtype

    @property
    def data(self) -> NDArray[Any]:
        """Get underlying numpy array."""
        return self._data

    def __getitem__(self, key: Any) -> MultiArray | Any:
        """Get item or slice.

        Args:
            key: Index or slice.

        Returns:
            MultiArray or scalar.
        """
        result = self._data[key]
        if isinstance(result, np.ndarray):
            return MultiArray(result)
        return result

    def __setitem__(self, key: Any, value: Any) -> None:
        """Set item or slice.

        Args:
            key: Index or slice.
            value: Value to set.
        """
        self._data[key] = value

    def __len__(self) -> int:
        """Get length of first dimension."""
        return len(self._data)

    def __add__(self, other: Any) -> MultiArray:
        """Add arrays or scalar."""
        if isinstance(other, MultiArray):
            return MultiArray(self._data + other._data)
        return MultiArray(self._data + other)

    def __radd__(self, other: Any) -> MultiArray:
        """Reverse add."""
        return MultiArray(other + self._data)

    def __sub__(self, other: Any) -> MultiArray:
        """Subtract arrays or scalar."""
        if isinstance(other, MultiArray):
            return MultiArray(self._data - other._data)
        return MultiArray(self._data - other)

    def __rsub__(self, other: Any) -> MultiArray:
        """Reverse subtract."""
        return MultiArray(other - self._data)

    def __mul__(self, other: Any) -> MultiArray:
        """Multiply arrays or scalar."""
        if isinstance(other, MultiArray):
            return MultiArray(self._data * other._data)
        return MultiArray(self._data * other)

    def __rmul__(self, other: Any) -> MultiArray:
        """Reverse multiply."""
        return MultiArray(other * self._data)

    def __truediv__(self, other: Any) -> MultiArray:
        """Divide arrays or scalar."""
        if isinstance(other, MultiArray):
            return MultiArray(self._data / other._data)
        return MultiArray(self._data / other)

    def __rtruediv__(self, other: Any) -> MultiArray:
        """Reverse divide."""
        return MultiArray(other / self._data)

    def __neg__(self) -> MultiArray:
        """Negate array."""
        return MultiArray(-self._data)

    def __eq__(self, other: object) -> MultiArray | bool:  # type: ignore[override]
        """Element-wise equality."""
        if isinstance(other, MultiArray):
            return MultiArray(self._data == other._data)
        result = self._data == other
        if isinstance(result, np.ndarray):
            return MultiArray(result)
        return bool(result)

    def __ne__(self, other: object) -> MultiArray | bool:  # type: ignore[override]
        """Element-wise inequality."""
        if isinstance(other, MultiArray):
            return MultiArray(self._data != other._data)
        result = self._data != other
        if isinstance(result, np.ndarray):
            return MultiArray(result)
        return bool(result)

    def __lt__(self, other: Any) -> MultiArray:
        """Element-wise less than."""
        if isinstance(other, MultiArray):
            return MultiArray(self._data < other._data)
        return MultiArray(self._data < other)

    def __le__(self, other: Any) -> MultiArray:
        """Element-wise less than or equal."""
        if isinstance(other, MultiArray):
            return MultiArray(self._data <= other._data)
        return MultiArray(self._data <= other)

    def __gt__(self, other: Any) -> MultiArray:
        """Element-wise greater than."""
        if isinstance(other, MultiArray):
            return MultiArray(self._data > other._data)
        return MultiArray(self._data > other)

    def __ge__(self, other: Any) -> MultiArray:
        """Element-wise greater than or equal."""
        if isinstance(other, MultiArray):
            return MultiArray(self._data >= other._data)
        return MultiArray(self._data >= other)

    def __repr__(self) -> str:
        """String representation."""
        return f"MultiArray({self._data!r})"

    def __str__(self) -> str:
        """String representation."""
        return str(self._data)

    def sum(self, axis: int | None = None) -> MultiArray | Any:
        """Sum along axis.

        Args:
            axis: Axis to sum along. None for all.

        Returns:
            Sum result.
        """
        result = self._data.sum(axis=axis)
        if isinstance(result, np.ndarray):
            return MultiArray(result)
        return result

    def mean(self, axis: int | None = None) -> MultiArray | Any:
        """Mean along axis.

        Args:
            axis: Axis to average along. None for all.

        Returns:
            Mean result.
        """
        result = self._data.mean(axis=axis)
        if isinstance(result, np.ndarray):
            return MultiArray(result)
        return result

    def min(self, axis: int | None = None) -> MultiArray | Any:
        """Minimum along axis.

        Args:
            axis: Axis to find min along. None for all.

        Returns:
            Minimum result.
        """
        result = self._data.min(axis=axis)
        if isinstance(result, np.ndarray):
            return MultiArray(result)
        return result

    def max(self, axis: int | None = None) -> MultiArray | Any:
        """Maximum along axis.

        Args:
            axis: Axis to find max along. None for all.

        Returns:
            Maximum result.
        """
        result = self._data.max(axis=axis)
        if isinstance(result, np.ndarray):
            return MultiArray(result)
        return result

    def reshape(self, shape: tuple[int, ...]) -> MultiArray:
        """Reshape array.

        Args:
            shape: New shape.

        Returns:
            Reshaped array.
        """
        return MultiArray(self._data.reshape(shape))

    def transpose(self, axes: tuple[int, ...] | None = None) -> MultiArray:
        """Transpose array.

        Args:
            axes: Axis permutation. None for reverse.

        Returns:
            Transposed array.
        """
        return MultiArray(self._data.transpose(axes))

    def flatten(self) -> MultiArray:
        """Flatten to 1D.

        Returns:
            Flattened array.
        """
        return MultiArray(self._data.flatten())

    def copy(self) -> MultiArray:
        """Copy array.

        Returns:
            Copy of array.
        """
        return MultiArray(self._data.copy())

    def dot(self, other: MultiArray) -> MultiArray:
        """Dot product.

        Args:
            other: Other array.

        Returns:
            Dot product result.
        """
        return MultiArray(np.dot(self._data, other._data))

    def matmul(self, other: MultiArray) -> MultiArray:
        """Matrix multiplication.

        Args:
            other: Other array.

        Returns:
            Matrix multiplication result.
        """
        return MultiArray(np.matmul(self._data, other._data))


def einsum(subscripts: str, *operands: MultiArray) -> MultiArray:
    """Einstein summation convention.

    Args:
        *args: Subscripts string followed by operands.

    Returns:
        Result of einsum.

    Examples:
        >>> a = MultiArray.from_list([[1, 2], [3, 4]])
        >>> b = MultiArray.from_list([[5, 6], [7, 8]])
        >>> einsum("ij,jk->ik", a, b)  # Matrix multiply
    """
    np_operands = [op._data for op in operands]
    return MultiArray(np.einsum(subscripts, *np_operands))
