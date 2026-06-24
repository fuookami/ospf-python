"""缩放因子。

Scale factor.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Scale:
    """缩放因子。

    Scale factor for value transformation.

    Attributes:
        factor: 缩放系数。/ Scale factor.
    """

    factor: float

    def apply(self, value: float) -> float:
        """应用缩放到值。

        Apply scale to a value.

        Args:
            value: 待缩放的值。/ Value to scale.

        Returns:
            缩放后的值。/ Scaled value.
        """
        return value * self.factor

    def inverse(self) -> Scale:
        """获取逆缩放。

        Get inverse scale.

        Returns:
            系数为 1/factor 的新 Scale。/ New Scale with 1/factor.
        """
        return Scale(factor=1.0 / self.factor)
