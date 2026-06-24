"""多维数组形状定义。

Multi-dimensional array shape definitions.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


class StorageOrder(enum.Enum):
    """存储顺序 / Storage order.

    ROW_MAJOR: 行优先存储（C 顺序）。
        Row-major storage (C order).
    COLUMN_MAJOR: 列优先存储（Fortran 顺序）。
        Column-major storage (Fortran order).
    """

    ROW_MAJOR = enum.auto()
    COLUMN_MAJOR = enum.auto()


@runtime_checkable
class Shape(Protocol):
    """形状协议 / Shape protocol.

    所有形状类型的公共接口。
    Common interface for all shape types.
    """

    @property
    def ndim(self) -> int:
        """维度数。/ Number of dimensions."""
        ...

    @property
    def size(self) -> int:
        """元素总数。/ Total number of elements."""
        ...

    @property
    def dims(self) -> tuple[int, ...]:
        """各维度大小。/ Size of each dimension."""
        ...

    @property
    def storage_order(self) -> StorageOrder:
        """存储顺序。/ Storage order."""
        ...

    def strides(self) -> tuple[int, ...]:
        """各维度步长。/ Stride of each dimension."""
        ...

    def flat_index(self, *indices: int) -> int:
        """将多维索引转换为扁平索引。

        Convert multi-dimensional indices to flat index.
        """
        ...


def _compute_strides(
    dims: tuple[int, ...],
    storage_order: StorageOrder,
) -> tuple[int, ...]:
    """计算步长元组。/ Compute strides tuple.

    Args:
        dims: 各维度大小。/ Size of each dimension.
        storage_order: 存储顺序。/ Storage order.

    Returns:
        步长元组。/ Strides tuple.
    """
    ndim = len(dims)
    if ndim == 0:
        return ()
    strides = [0] * ndim
    if storage_order == StorageOrder.ROW_MAJOR:
        # C 阶段：最后维度步长为 1
        # C-order: last dimension has stride 1
        strides[ndim - 1] = 1
        for i in range(ndim - 2, -1, -1):
            strides[i] = strides[i + 1] * dims[i + 1]
    else:
        # F 阶段：第一维度步长为 1
        # F-order: first dimension has stride 1
        strides[0] = 1
        for i in range(1, ndim):
            strides[i] = strides[i - 1] * dims[i - 1]
    return tuple(strides)


def _compute_flat_index(
    dims: tuple[int, ...],
    strides: tuple[int, ...],
    indices: tuple[int, ...],
) -> int:
    """计算扁平索引。/ Compute flat index.

    Args:
        dims: 各维度大小。/ Size of each dimension.
        strides: 各维度步长。/ Stride of each dimension.
        indices: 多维索引。/ Multi-dimensional indices.

    Returns:
        扁平索引。/ Flat index.
    """
    return sum(s * i for s, i in zip(strides, indices, strict=False))


@dataclass(frozen=True)
class Shape1:
    """一维形状 / 1-D shape.

    Attributes:
        d0: 第一维度大小。/ First dimension size.
        storage_order: 存储顺序。/ Storage order.
    """

    d0: int
    storage_order: StorageOrder = StorageOrder.ROW_MAJOR

    def __post_init__(self) -> None:
        """校验维度为正整数。/ Validate dimensions are positive."""
        if self.d0 <= 0:
            raise DimensionMismatchingException(
                f"维度必须为正整数，实际为 {self.d0}"
                f" / Dimension must be positive, got {self.d0}"
            )

    @classmethod
    def of(cls, dim0: int) -> Shape1:
        """工厂方法，使用默认行优先顺序。

        Factory method with default row-major order.

        Args:
            dim0: 第一维度大小。/ First dimension size.

        Returns:
            新的 Shape1 实例。/ New Shape1 instance.
        """
        return cls(d0=dim0)

    @property
    def ndim(self) -> int:
        """维度数。/ Number of dimensions."""
        return 1

    @property
    def size(self) -> int:
        """元素总数。/ Total number of elements."""
        return self.d0

    @property
    def dims(self) -> tuple[int, ...]:
        """各维度大小元组。/ Size of each dimension tuple."""
        return (self.d0,)

    def strides(self) -> tuple[int, ...]:
        """各维度步长。/ Stride of each dimension."""
        return _compute_strides(self.dims, self.storage_order)

    def flat_index(self, *indices: int) -> int:
        """将多维索引转换为扁平索引。

        Convert multi-dimensional indices to flat index.
        """
        return _compute_flat_index(self.dims, self.strides(), indices)


@dataclass(frozen=True)
class Shape2:
    """二维形状 / 2-D shape.

    Attributes:
        d0: 第一维度大小（行数）。/ First dimension size (rows).
        d1: 第二维度大小（列数）。/ Second dimension size (cols).
        storage_order: 存储顺序。/ Storage order.
    """

    d0: int
    d1: int
    storage_order: StorageOrder = StorageOrder.ROW_MAJOR

    def __post_init__(self) -> None:
        """校验维度为正整数。/ Validate dimensions are positive."""
        if self.d0 <= 0 or self.d1 <= 0:
            raise DimensionMismatchingException(
                f"维度必须为正整数，实际为 ({self.d0}, {self.d1})"
                f" / Dimensions must be positive, "
                f"got ({self.d0}, {self.d1})"
            )

    @classmethod
    def of(cls, dim0: int, dim1: int) -> Shape2:
        """工厂方法，使用默认行优先顺序。

        Factory method with default row-major order.

        Args:
            dim0: 第一维度大小。/ First dimension size.
            dim1: 第二维度大小。/ Second dimension size.

        Returns:
            新的 Shape2 实例。/ New Shape2 instance.
        """
        return cls(d0=dim0, d1=dim1)

    @property
    def ndim(self) -> int:
        """维度数。/ Number of dimensions."""
        return 2

    @property
    def size(self) -> int:
        """元素总数。/ Total number of elements."""
        return self.d0 * self.d1

    @property
    def dims(self) -> tuple[int, ...]:
        """各维度大小元组。/ Size of each dimension tuple."""
        return (self.d0, self.d1)

    def strides(self) -> tuple[int, ...]:
        """各维度步长。/ Stride of each dimension."""
        return _compute_strides(self.dims, self.storage_order)

    def flat_index(self, *indices: int) -> int:
        """将多维索引转换为扁平索引。

        Convert multi-dimensional indices to flat index.
        """
        return _compute_flat_index(self.dims, self.strides(), indices)


@dataclass(frozen=True)
class Shape3:
    """三维形状 / 3-D shape.

    Attributes:
        d0: 第一维度大小。/ First dimension size.
        d1: 第二维度大小。/ Second dimension size.
        d2: 第三维度大小。/ Third dimension size.
        storage_order: 存储顺序。/ Storage order.
    """

    d0: int
    d1: int
    d2: int
    storage_order: StorageOrder = StorageOrder.ROW_MAJOR

    def __post_init__(self) -> None:
        """校验维度为正整数。/ Validate dimensions are positive."""
        if self.d0 <= 0 or self.d1 <= 0 or self.d2 <= 0:
            raise DimensionMismatchingException(
                f"维度必须为正整数，实际为 "
                f"({self.d0}, {self.d1}, {self.d2})"
                f" / Dimensions must be positive, got "
                f"({self.d0}, {self.d1}, {self.d2})"
            )

    @classmethod
    def of(cls, dim0: int, dim1: int, dim2: int) -> Shape3:
        """工厂方法，使用默认行优先顺序。

        Factory method with default row-major order.

        Args:
            dim0: 第一维度大小。/ First dimension size.
            dim1: 第二维度大小。/ Second dimension size.
            dim2: 第三维度大小。/ Third dimension size.

        Returns:
            新的 Shape3 实例。/ New Shape3 instance.
        """
        return cls(d0=dim0, d1=dim1, d2=dim2)

    @property
    def ndim(self) -> int:
        """维度数。/ Number of dimensions."""
        return 3

    @property
    def size(self) -> int:
        """元素总数。/ Total number of elements."""
        return self.d0 * self.d1 * self.d2

    @property
    def dims(self) -> tuple[int, ...]:
        """各维度大小元组。/ Size of each dimension tuple."""
        return (self.d0, self.d1, self.d2)

    def strides(self) -> tuple[int, ...]:
        """各维度步长。/ Stride of each dimension."""
        return _compute_strides(self.dims, self.storage_order)

    def flat_index(self, *indices: int) -> int:
        """将多维索引转换为扁平索引。

        Convert multi-dimensional indices to flat index.
        """
        return _compute_flat_index(self.dims, self.strides(), indices)


@dataclass(frozen=True)
class Shape4:
    """四维形状 / 4-D shape.

    Attributes:
        d0: 第一维度大小。/ First dimension size.
        d1: 第二维度大小。/ Second dimension size.
        d2: 第三维度大小。/ Third dimension size.
        d3: 第四维度大小。/ Fourth dimension size.
        storage_order: 存储顺序。/ Storage order.
    """

    d0: int
    d1: int
    d2: int
    d3: int
    storage_order: StorageOrder = StorageOrder.ROW_MAJOR

    def __post_init__(self) -> None:
        """校验维度为正整数。/ Validate dimensions are positive."""
        if self.d0 <= 0 or self.d1 <= 0 or self.d2 <= 0 or self.d3 <= 0:
            raise DimensionMismatchingException(
                f"维度必须为正整数，实际为 "
                f"({self.d0}, {self.d1}, {self.d2}, {self.d3})"
                f" / Dimensions must be positive, got "
                f"({self.d0}, {self.d1}, {self.d2}, {self.d3})"
            )

    @classmethod
    def of(cls, dim0: int, dim1: int, dim2: int, dim3: int) -> Shape4:
        """工厂方法，使用默认行优先顺序。

        Factory method with default row-major order.

        Args:
            dim0: 第一维度大小。/ First dimension size.
            dim1: 第二维度大小。/ Second dimension size.
            dim2: 第三维度大小。/ Third dimension size.
            dim3: 第四维度大小。/ Fourth dimension size.

        Returns:
            新的 Shape4 实例。/ New Shape4 instance.
        """
        return cls(d0=dim0, d1=dim1, d2=dim2, d3=dim3)

    @property
    def ndim(self) -> int:
        """维度数。/ Number of dimensions."""
        return 4

    @property
    def size(self) -> int:
        """元素总数。/ Total number of elements."""
        return self.d0 * self.d1 * self.d2 * self.d3

    @property
    def dims(self) -> tuple[int, ...]:
        """各维度大小元组。/ Size of each dimension tuple."""
        return (self.d0, self.d1, self.d2, self.d3)

    def strides(self) -> tuple[int, ...]:
        """各维度步长。/ Stride of each dimension."""
        return _compute_strides(self.dims, self.storage_order)

    def flat_index(self, *indices: int) -> int:
        """将多维索引转换为扁平索引。

        Convert multi-dimensional indices to flat index.
        """
        return _compute_flat_index(self.dims, self.strides(), indices)


@dataclass(frozen=True)
class DynShape:
    """动态 N 维形状 / Dynamic N-D shape.

    支持任意维度数量的形状。
    Shape supporting an arbitrary number of dimensions.

    Attributes:
        dims: 各维度大小。/ Size of each dimension.
        storage_order: 存储顺序。/ Storage order.
    """

    dims: tuple[int, ...]
    storage_order: StorageOrder = StorageOrder.ROW_MAJOR

    def __post_init__(self) -> None:
        """校验维度为正整数。/ Validate dimensions are positive."""
        if any(d <= 0 for d in self.dims):
            raise DimensionMismatchingException(
                f"维度必须为正整数，实际为 {self.dims}"
                f" / Dimensions must be positive, got {self.dims}"
            )

    @property
    def ndim(self) -> int:
        """维度数。/ Number of dimensions."""
        return len(self.dims)

    @property
    def size(self) -> int:
        """元素总数。/ Total number of elements."""
        result = 1
        for d in self.dims:
            result *= d
        return result

    def strides(self) -> tuple[int, ...]:
        """各维度步长。/ Stride of each dimension."""
        return _compute_strides(self.dims, self.storage_order)

    def flat_index(self, *indices: int) -> int:
        """将多维索引转换为扁平索引。

        Convert multi-dimensional indices to flat index.
        """
        return _compute_flat_index(self.dims, self.strides(), indices)


# ==================== 异常类型 ====================
# ==================== Exception types ====================


class DimensionMismatchingException(Exception):
    """维度不匹配异常。

    Raised when dimensions do not match expected values.
    """

    def __init__(self, message: str = "") -> None:
        """初始化维度不匹配异常。

        Initialize dimension mismatching exception.

        Args:
            message: 错误信息。/ Error message.
        """
        super().__init__(message)


class OutOfShapeException(Exception):
    """索引越界异常。

    Raised when indices are out of the shape bounds.
    """

    def __init__(self, message: str = "") -> None:
        """初始化索引越界异常。

        Initialize out-of-shape exception.

        Args:
            message: 错误信息。/ Error message.
        """
        super().__init__(message)
