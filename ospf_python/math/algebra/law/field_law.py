"""域公理验证 / Field law verification.

在环公理基础上增加乘法逆元验证。
Extends ring law verification with multiplicative
inverse.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ospf_python.math.algebra.law.ring_law import RingLaw


@runtime_checkable
class FieldLaw(RingLaw, Protocol):
    """域公理验证 / Field law verification.

    在环公理基础上验证非零元素的乘法逆元。
    Extends ring axioms with multiplicative inverse
    for nonzero elements.
    """

    def verify_multiplicative_inverse(
        self,
        *,
        a: object,
        inv_a: object,
        one: object,
    ) -> bool:
        """验证乘法逆元 / Verify multiplicative inverse.

        检查 a * (1/a) == 1（a 非零）。
        Checks a * (1/a) == 1 (for nonzero a).

        Args:
            a: 非零测试元素。Nonzero test element.
            inv_a: 候选乘法逆元。Candidate inverse.
            one: 单位元。Identity element.

        Returns:
            是否满足乘法逆元性质。
            Whether multiplicative inverse holds.
        """
