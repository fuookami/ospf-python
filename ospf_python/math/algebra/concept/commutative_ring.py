"""交换环协议 / Commutative ring protocol.

交换环是乘法满足交换律的环。
A commutative ring is a ring where multiplication is commutative.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ospf_python.math.algebra.concept.ring import Ring


@runtime_checkable
class CommutativeRing(Ring, Protocol):
    """交换环协议 / Commutative ring protocol.

    在环基础上乘法满足交换律: a * b == b * a。
    Extends ring with multiplicative commutativity: a * b == b * a.
    """
