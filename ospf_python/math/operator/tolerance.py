"""容差比较类型。

Tolerance comparison type.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Tolerance:
    """容差比较，用于近似相等判断。

    Tolerance comparison for approximate equality checks.

    Attributes:
        epsilon: 容差阈值。/ Tolerance threshold.
    """

    epsilon: float

    def is_close(
        self,
        a: float,
        b: float,
    ) -> bool:
        """判断两个值是否在容差范围内近似相等。

        Check whether two values are approximately
        equal within tolerance.

        Args:
            a: 第一个值。/ First value.
            b: 第二个值。/ Second value.

        Returns:
            是否近似相等。/ Whether approximately equal.
        """
        return math.isclose(
            a,
            b,
            abs_tol=self.epsilon,
        )
