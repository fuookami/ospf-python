"""多维数组视图，支持惰性映射。

Multi-dimensional array views with lazy mapping support.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from ospf_python._binding import shared_view as _shared_view
from ospf_python._binding.coordinate_materialization import materialize_coordinates
from ospf_python._binding.result import BindingResult  # noqa: TC001
from ospf_python._binding.shared_view import materialize_shared_view
from ospf_python.multiarray.multi_array import MultiArray
from ospf_python.multiarray.shape import DynShape, Shape

# T: 元素类型 / Element type
T = TypeVar("T")

# S: 形状类型 / Shape type
S = TypeVar("S", bound=Shape)

_DEFAULT_PROTOCOL = _shared_view._DEFAULT_PROTOCOL
_DEFAULT_MATERIALIZE = _shared_view._DEFAULT_MATERIALIZE
_DEFAULT_DYNSHAPE = DynShape


def _materialized_constructor() -> Callable[[Any, Any], MultiArray[Any, Any]]:
    """在复制完成后解析当前公共构造器 / Resolve the current public constructor after copying.

    Returns:
        当前数组构造器 / Current array constructor.
    """
    return MultiArray


class MultiArrayView:
    """多维数组视图，共享底层数据。

    Multi-dimensional array view sharing underlying data.

    视图不拥有数据，而是引用源数组并提供索引映射。
    A view does not own data; it references a source array
    and provides index mapping.

    Attributes:
        _source: 源数组。/ Source array.
        _offsets: 各维度偏移量。/ Offsets per dimension.
    """

    def __init__(
        self,
        source: MultiArray[Any, Any],
        *,
        offsets: tuple[int, ...] | None = None,
    ) -> None:
        """初始化数组视图。

        Initialize array view.

        Args:
            source: 源多维数组。/ Source multi-array.
            offsets: 各维度起始偏移。/ Starting offsets
                per dimension.
        """
        self._source = source
        self._offsets = offsets or (0,) * source.ndim

    @property
    def shape(self) -> Shape:
        """获取视图形状（与源数组相同）。

        Get view shape (same as source array).
        """
        return self._source.shape  # type: ignore[no-any-return]

    @property
    def ndim(self) -> int:
        """获取维度数。/ Get number of dimensions."""
        return self._source.ndim

    def get(self, *indices: int) -> T:  # type: ignore[type-var]
        """获取视图中指定索引处的元素。

        Get the element at the specified indices in the view.

        通过偏移量将视图索引映射到源数组索引。
        Maps view indices to source indices via offsets.

        Args:
            indices: 视图中的多维索引。
                Multi-dimensional indices in the view.

        Returns:
            指定位置的元素。/ Element at the position.
        """
        source_indices = tuple(
            vi + off for vi, off in zip(indices, self._offsets, strict=False)
        )
        return self._source.get(*source_indices)  # type: ignore[no-any-return]

    def map(self, f: Callable[[T], T]) -> MappedMultiArrayView:
        """对视图元素应用惰性映射。

        Apply a lazy mapping to view elements.

        Args:
            f: 映射函数。/ Mapping function.

        Returns:
            惰性映射视图。/ Lazy mapped view.
        """
        return MappedMultiArrayView(self, f=f)

    def materialize(self) -> BindingResult[MultiArray[Any, Any]]:
        """将视图物化为独立数组。

        Materialize the view into a standalone array.

        Returns:
            有效剩余区域副本或失败。/ Copy of the valid remaining region, or failure.
        """
        if (
            _shared_view._protocol is _DEFAULT_PROTOCOL
            and _shared_view.DynShape is _DEFAULT_DYNSHAPE
        ):
            try:
                return _DEFAULT_MATERIALIZE(
                    self, _DEFAULT_DYNSHAPE, _materialized_constructor
                )
            except Exception as error:
                return _shared_view.external_failure(error)
        return materialize_shared_view(self, _materialized_constructor)


class MappedMultiArrayView:
    """惰性映射的多维数组视图。

    Lazily mapped multi-dimensional array view.

    映射函数在每次访问时按需计算，不缓存结果。
    The mapping function is computed on each access;
    results are not cached.

    Attributes:
        _source: 源视图或数组。/ Source view or array.
        _f: 映射函数。/ Mapping function.
    """

    def __init__(
        self,
        source: MultiArrayView | MultiArray[Any, Any],
        *,
        f: Callable[[T], T],
    ) -> None:
        """初始化惰性映射视图。

        Initialize lazy mapped view.

        Args:
            source: 源视图或数组。/ Source view or array.
            f: 映射函数。/ Mapping function.
        """
        self._source = source
        self._f = f

    @property
    def shape(self) -> Shape:
        """获取视图形状。/ Get view shape."""
        return self._source.shape

    @property
    def ndim(self) -> int:
        """获取维度数。/ Get number of dimensions."""
        return self._source.ndim

    def get(self, *indices: int) -> T:  # type: ignore[type-var]
        """获取映射后的元素值。

        Get the mapped element value.

        Args:
            indices: 多维索引。/ Multi-dimensional indices.

        Returns:
            映射后的元素。/ Mapped element.
        """
        raw = self._source.get(*indices)
        return self._f(raw)  # type: ignore[return-value]

    def materialize(self) -> BindingResult[MultiArray[Any, Any]]:
        """将映射视图物化为独立数组。

        Materialize the mapped view into a standalone array.

        Returns:
            独立数组或保留外部异常的失败。/ Standalone array or failure retaining external exceptions.
        """
        return materialize_coordinates(
            owner=self, finish=lambda shape, data: MultiArray(shape, data)
        )


def view_of(
    source: MultiArray[Any, Any],
    *,
    offsets: tuple[int, ...] | None = None,
) -> MultiArrayView:
    """创建源数组的视图。

    Create a view of the source array.

    Args:
        source: 源多维数组。/ Source multi-array.
        offsets: 各维度起始偏移。/ Starting offsets
            per dimension.

    Returns:
        数组视图。/ Array view.
    """
    return MultiArrayView(source, offsets=offsets)
