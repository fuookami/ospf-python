"""多维数组模块。

Multi-dimensional array module.
"""

from __future__ import annotations

from importlib import import_module as _import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.multiarray.access_order import (
        AccessOrder,
        IteratorPosition,
        MultiIndexIterator,
        MultiIndexSequence,
    )
    from ospf_python.multiarray.block_multi_array import (
        BlockMultiArray,
        IndexKey,
    )
    from ospf_python.multiarray.data_frame import (
        DataFrame,
        DataFrameBuilder,
        NullableValue,
    )
    from ospf_python.multiarray.list import (
        chunk_list,
        flatten_list,
        transpose_list,
    )
    from ospf_python.multiarray.map import (
        group_by_to_array,
        map_to_matrix,
    )
    from ospf_python.multiarray.multi_array import (
        AbstractMultiArray,
        MultiArray,
        MutableMultiArray,
    )
    from ospf_python.multiarray.multi_array_view import (
        MappedMultiArrayView,
        MultiArrayView,
        view_of,
    )
    from ospf_python.multiarray.shape import (
        DimensionMismatchingException,
        DynShape,
        OutOfShapeException,
        Shape,
        Shape1,
        Shape2,
        Shape3,
        Shape4,
        StorageOrder,
    )
    from ospf_python.multiarray.vector import (
        DummyIndex,
        DummyIndexIterator,
        DummyIndexRange,
        IdentityMapIndex,
        MapIndex,
        OffsetMapIndex,
        SimpleDummyIndex,
        SimpleDummyIndexIterator,
        Vector,
    )

__all__ = [
    # access_order
    "AccessOrder",
    "IteratorPosition",
    "MultiIndexIterator",
    "MultiIndexSequence",
    # block_multi_array
    "BlockMultiArray",
    "IndexKey",
    # data_frame
    "DataFrame",
    "DataFrameBuilder",
    "NullableValue",
    # list
    "chunk_list",
    "flatten_list",
    "transpose_list",
    # map
    "group_by_to_array",
    "map_to_matrix",
    # multi_array
    "AbstractMultiArray",
    "MultiArray",
    "MutableMultiArray",
    # multi_array_view
    "MappedMultiArrayView",
    "MultiArrayView",
    "view_of",
    # shape
    "DimensionMismatchingException",
    "DynShape",
    "OutOfShapeException",
    "Shape",
    "Shape1",
    "Shape2",
    "Shape3",
    "Shape4",
    "StorageOrder",
    # vector
    "DummyIndex",
    "DummyIndexIterator",
    "DummyIndexRange",
    "IdentityMapIndex",
    "MapIndex",
    "OffsetMapIndex",
    "SimpleDummyIndex",
    "SimpleDummyIndexIterator",
    "Vector",
]

_EXPORTS = {
    "AccessOrder": "ospf_python.multiarray.access_order",
    "IteratorPosition": "ospf_python.multiarray.access_order",
    "MultiIndexIterator": "ospf_python.multiarray.access_order",
    "MultiIndexSequence": "ospf_python.multiarray.access_order",
    "BlockMultiArray": "ospf_python.multiarray.block_multi_array",
    "IndexKey": "ospf_python.multiarray.block_multi_array",
    "DataFrame": "ospf_python.multiarray.data_frame",
    "DataFrameBuilder": "ospf_python.multiarray.data_frame",
    "NullableValue": "ospf_python.multiarray.data_frame",
    "chunk_list": "ospf_python.multiarray.list",
    "flatten_list": "ospf_python.multiarray.list",
    "transpose_list": "ospf_python.multiarray.list",
    "group_by_to_array": "ospf_python.multiarray.map",
    "map_to_matrix": "ospf_python.multiarray.map",
    "AbstractMultiArray": "ospf_python.multiarray.multi_array",
    "MultiArray": "ospf_python.multiarray.multi_array",
    "MutableMultiArray": "ospf_python.multiarray.multi_array",
    "MappedMultiArrayView": "ospf_python.multiarray.multi_array_view",
    "MultiArrayView": "ospf_python.multiarray.multi_array_view",
    "view_of": "ospf_python.multiarray.multi_array_view",
    "DimensionMismatchingException": "ospf_python.multiarray.shape",
    "DynShape": "ospf_python.multiarray.shape",
    "OutOfShapeException": "ospf_python.multiarray.shape",
    "Shape": "ospf_python.multiarray.shape",
    "Shape1": "ospf_python.multiarray.shape",
    "Shape2": "ospf_python.multiarray.shape",
    "Shape3": "ospf_python.multiarray.shape",
    "Shape4": "ospf_python.multiarray.shape",
    "StorageOrder": "ospf_python.multiarray.shape",
    "DummyIndex": "ospf_python.multiarray.vector",
    "DummyIndexIterator": "ospf_python.multiarray.vector",
    "DummyIndexRange": "ospf_python.multiarray.vector",
    "IdentityMapIndex": "ospf_python.multiarray.vector",
    "MapIndex": "ospf_python.multiarray.vector",
    "OffsetMapIndex": "ospf_python.multiarray.vector",
    "SimpleDummyIndex": "ospf_python.multiarray.vector",
    "SimpleDummyIndexIterator": "ospf_python.multiarray.vector",
    "Vector": "ospf_python.multiarray.vector",
}


def __getattr__(name: str) -> object:
    """按需加载自然导出，避免底层形状反向初始化消费者 / Load natural exports lazily without initializing shape consumers.

    Args:
        name: 导出名称 / Export name.

    Returns:
        与原模块相同的对象 / The original module object.
    """
    module = _EXPORTS.get(name)
    if module is None:
        raise AttributeError(
            f"模块 {__name__!r} 没有属性 {name!r}"
            f" / module {__name__!r} has no attribute {name!r}"
        )
    value: object = getattr(_import_module(module), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """未加载的公开入口同样可发现 / Keep unloaded public exports discoverable."""
    return sorted(set(globals()) | set(__all__))
