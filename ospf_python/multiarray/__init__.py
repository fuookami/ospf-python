"""ospf-python multi-dimensional array module.

Provides MultiArray abstraction with numpy backend and einsum support.
"""

from ospf_python.multiarray.array import MultiArray, einsum

__all__ = [
    "MultiArray",
    "einsum",
]
