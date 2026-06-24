"""阿贝尔群协议 / Abelian group protocol.

阿贝尔群是满足交换律的群。
An abelian group is a group that satisfies commutativity.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ospf_python.math.algebra.concept.group import Group


@runtime_checkable
class AbelianGroup(Group, Protocol):
    """阿贝尔群协议 / Abelian group protocol.

    在群基础上满足交换律: a + b == b + a。
    Extends group with commutativity: a + b == b + a.
    """
