"""二维坐标轴排列。

Two-dimensional axis permutation.
"""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.math.geometry.axis2 import Axis2


@dataclass(frozen=True)
class AxisPermutation2:
    """二维坐标轴排列，映射源轴到目标轴。

    Two-dimensional axis permutation mapping
    source axes to target axes.

    Attributes:
        x: X 轴映射目标。/ X axis target.
        y: Y 轴映射目标。/ Y axis target.
    """

    x: Axis2
    y: Axis2

    @staticmethod
    def identity() -> AxisPermutation2:
        """恒等排列。/ Identity permutation."""
        return AxisPermutation2(x=Axis2.X, y=Axis2.Y)

    def apply(self, values: tuple[float, float]) -> tuple[float, float]:
        """应用排列到二维值。

        Apply permutation to a 2D value tuple.

        Args:
            values: 输入值 (x, y)。/ Input values (x, y).

        Returns:
            排列后的值。/ Permuted values.
        """
        mapping = {Axis2.X: values[0], Axis2.Y: values[1]}
        return (mapping[self.x], mapping[self.y])
