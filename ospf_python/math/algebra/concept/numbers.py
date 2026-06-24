"""数值协议 / Number protocols.

Number / RealNumber，数值类型层次结构。
Number / RealNumber, numeric type hierarchy.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ospf_python.math.algebra.concept.arithmetic import Arithmetic
from ospf_python.utils.functional.ord import Ord


@runtime_checkable
class Number(Arithmetic, Protocol):
    """数值协议 / Number protocol.

    所有数值类型的基础协议。
    Base protocol for all numeric types.
    """


@runtime_checkable
class RealNumber(Number, Ord, Protocol):
    """实数协议 / Real number protocol.

    实数支持全序比较。
    Real numbers support total ordering.
    """
