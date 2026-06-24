"""环协议 / Ring protocol.

环是加法构成交换群、乘法构成幺半群的代数结构。
A ring is an algebraic structure where addition forms an abelian group
and multiplication forms a monoid.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ospf_python.math.algebra.concept.abelian_group import AbelianGroup
from ospf_python.math.algebra.concept.multiplicative_monoid import (
    MultiplicativeMonoid,
)


@runtime_checkable
class Ring(AbelianGroup, MultiplicativeMonoid, Protocol):
    """环协议 / Ring protocol.

    加法构成交换群，乘法构成幺半群，乘法对加法满足分配律。
    Addition forms an abelian group, multiplication forms a monoid,
    and multiplication distributes over addition.
    """
