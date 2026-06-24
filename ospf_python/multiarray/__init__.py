"""多维数组模块。

Multi-dimensional array module.
"""

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
