"""域协议 / Field protocol.

域是非零元素对乘法构成交换群的交换环。
A field is a commutative ring where nonzero elements form
a multiplicative abelian group.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ospf_python.math.algebra.concept.commutative_ring import CommutativeRing
from ospf_python.math.algebra.concept.multiplicative_group import (
    MultiplicativeGroup,
)


@runtime_checkable
class Field(CommutativeRing, MultiplicativeGroup, Protocol):
    """域协议 / Field protocol.

    在交换环基础上，非零元素对乘法构成群。
    Extends commutative ring: nonzero elements form a
    multiplicative group.
    """
