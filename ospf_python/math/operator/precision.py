"""精度控制类型。

Precision control type.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Precision:
    """精度控制，用于四舍五入到指定小数位。

    Precision control for rounding to specified decimal places.

    Attributes:
        digits: 保留的小数位数。/ Number of decimal places.
    """

    digits: int

    def round_to(self, x: float) -> float:
        """按精度四舍五入。

        Round to the configured precision.

        Args:
            x: 输入值。/ Input value.

        Returns:
            四舍五入后的值。/ Rounded value.
        """
        return round(x, self.digits)
