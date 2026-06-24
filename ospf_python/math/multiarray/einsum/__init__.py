"""爱因斯坦求和模块。

Einstein summation module.
"""

from ospf_python.math.multiarray.einsum.einsum import einsum
from ospf_python.math.multiarray.einsum.einsum_error import EinsumError
from ospf_python.math.multiarray.einsum.einsum_parser import parse_einsum
from ospf_python.math.multiarray.einsum.index_label import IndexLabel
from ospf_python.math.multiarray.einsum.operations import (
    diagonal,
    tensordot,
    trace,
)
from ospf_python.math.multiarray.einsum.tensor_expr import TensorExpr

__all__ = [
    "EinsumError",
    "IndexLabel",
    "TensorExpr",
    "diagonal",
    "einsum",
    "parse_einsum",
    "tensordot",
    "trace",
]
