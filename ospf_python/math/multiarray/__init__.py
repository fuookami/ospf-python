"""数学层多维数组扩展模块。

Math-layer multi-array extensions module.
"""

from ospf_python.math.multiarray.fast_sum import fast_sum
from ospf_python.math.multiarray.multi_array_extensions import (
    dot,
    elementwise_add,
    elementwise_mul,
    matmul,
)

__all__ = [
    "dot",
    "elementwise_add",
    "elementwise_mul",
    "fast_sum",
    "matmul",
]
