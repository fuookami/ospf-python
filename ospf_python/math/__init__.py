"""ospf-python math module.

Provides algebraic structures, number types, and mathematical functions.
"""

from ospf_python.math.algebra.number import Float64, Int64, RealNumber, V
from ospf_python.math.algebra.value_range import (
    ClosedTypedValueRange,
    TypedValueRange,
    create_closed_range,
    create_range,
)

__all__ = [
    # Number types
    "RealNumber",
    "Float64",
    "Int64",
    "V",
    # Value range types
    "TypedValueRange",
    "ClosedTypedValueRange",
    "create_range",
    "create_closed_range",
]
