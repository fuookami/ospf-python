"""三维坐标轴排列。

Three-dimensional axis permutation.
"""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.math.geometry.axis3 import Axis3


@dataclass(frozen=True)
class AxisPermutation3:
    """三维坐标轴排列，映射源轴到目标轴。

    Three-dimensional axis permutation mapping
    source axes to target axes.

    Attributes:
        x: X 轴映射目标。/ X axis target.
        y: Y 轴映射目标。/ Y axis target.
        z: Z 轴映射目标。/ Z axis target.
    """

    x: Axis3
    y: Axis3
    z: Axis3

    @staticmethod
    def identity() -> AxisPermutation3:
        """恒等排列。/ Identity permutation."""
        return AxisPermutation3(
            x=Axis3.X,
            y=Axis3.Y,
            z=Axis3.Z,
        )

    def apply(
        self,
        values: tuple[float, float, float],
    ) -> tuple[float, float, float]:
        """应用排列到三维值。

        Apply permutation to a 3D value tuple.

        Args:
            values: 输入值 (x, y, z)。/ Input values.

        Returns:
            排列后的值。/ Permuted values.
        """
        mapping = {
            Axis3.X: values[0],
            Axis3.Y: values[1],
            Axis3.Z: values[2],
        }
        return (mapping[self.x], mapping[self.y], mapping[self.z])
