"""群公理验证 / Group law verification.

验证群的三条公理：结合律、单位元、逆元。
Verifies the three group axioms: associativity,
identity, and inverse.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class GroupLaw(Protocol):
    """群公理验证 / Group law verification.

    提供方法验证群的三条公理。
    Provides methods to verify the three group axioms.
    """

    def verify_associativity(
        self,
        *,
        a: object,
        b: object,
        c: object,
    ) -> bool:
        """验证结合律 / Verify associativity.

        检查 (a + b) + c == a + (b + c)。
        Checks (a + b) + c == a + (b + c).

        Args:
            a: 第一个操作数。First operand.
            b: 第二个操作数。Second operand.
            c: 第三个操作数。Third operand.

        Returns:
            是否满足结合律。Whether associativity holds.
        """

    def verify_identity(
        self,
        *,
        a: object,
        zero: object,
    ) -> bool:
        """验证单位元 / Verify identity.

        检查 a + 0 == 0 + a == a。
        Checks a + 0 == 0 + a == a.

        Args:
            a: 测试元素。Test element.
            zero: 候选零元。Candidate zero element.

        Returns:
            是否满足单位元性质。
            Whether identity property holds.
        """

    def verify_inverse(
        self,
        *,
        a: object,
        neg_a: object,
        zero: object,
    ) -> bool:
        """验证逆元 / Verify inverse.

        检查 a + (-a) == 0。
        Checks a + (-a) == 0.

        Args:
            a: 测试元素。Test element.
            neg_a: 候选逆元。Candidate inverse.
            zero: 零元。Zero element.

        Returns:
            是否满足逆元性质。
            Whether inverse property holds.
        """
