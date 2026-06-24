"""环公理验证 / Ring law verification.

在群公理基础上增加分配律验证。
Extends group law verification with distributivity.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ospf_python.math.algebra.law.group_law import GroupLaw


@runtime_checkable
class RingLaw(GroupLaw, Protocol):
    """环公理验证 / Ring law verification.

    在群公理基础上验证乘法对加法的分配律。
    Extends group axioms with multiplicative
    distributivity over addition.
    """

    def verify_distributivity(
        self,
        *,
        a: object,
        b: object,
        c: object,
    ) -> bool:
        """验证分配律 / Verify distributivity.

        检查 a * (b + c) == a * b + a * c。
        Checks a * (b + c) == a * b + a * c.

        Args:
            a: 第一个操作数。First operand.
            b: 第二个操作数。Second operand.
            c: 第三个操作数。Third operand.

        Returns:
            是否满足分配律。
            Whether distributivity holds.
        """
