"""线密度分布 / Linear density distribution.

描述货舱地板沿线性轴方向的质量分布。
Describes the mass distribution along the linear axis
of a cargo deck floor.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LinearDensity:
    """线密度 / Linear density.

    表示飞机货舱地板某一站位置的线性载荷密度，
    用于校验地板结构强度是否满足分布载荷要求。
    Represents the linear load density of a segment on
    the aircraft cargo deck floor, used to verify that
    floor structural strength meets distributed load
    requirements.

    Attributes:
        position: 起始位置(站位，m) / Start position (station, m).
        density: 线密度(kg/m) / Linear density (kg/m).
        length: 段长度(m) / Segment length (m).
    """

    position: float
    density: float
    length: float

    @staticmethod
    def create(
        *,
        position: float,
        density: float,
        length: float,
    ) -> LinearDensity:
        """创建线密度 / Create linear density.

        Args:
            position: 起始位置(站位，m) / Start position (m).
            density: 线密度(kg/m) / Linear density (kg/m).
            length: 段长度(m) / Segment length (m).

        Returns:
            线密度实例 / LinearDensity instance.
        """
        return LinearDensity(
            position=position,
            density=density,
            length=length,
        )

    @property
    def total_mass(self) -> float:
        """段总质量 / Segment total mass.

        Returns:
            密度乘以长度(kg)。
            Density times length (kg).
        """
        return self.density * self.length

    @property
    def end_position(self) -> float:
        """段结束位置 / Segment end position.

        Returns:
            起始位置加长度(m)。
            Start position plus length (m).
        """
        return self.position + self.length

    def contains_position(self, pos: float) -> bool:
        """检查位置是否在段内。

        Check whether a position falls within this segment.

        Args:
            pos: 待检查位置(m)。/ Position to check (m).

        Returns:
            若位置在 [position, end_position) 内则返回 True。
            True if position is within [position, end_position).
        """
        return self.position <= pos < self.end_position

    def exceeds_density(self, limit: float) -> bool:
        """检查密度是否超过限制。

        Check whether density exceeds the given limit.

        Args:
            limit: 密度上限(kg/m)。/ Density upper limit (kg/m).

        Returns:
            若当前密度超过限制则返回 True。
            True if current density exceeds the limit.
        """
        return self.density > limit

    def margin_to_limit(self, limit: float) -> float:
        """计算密度余量 / Calculate density margin.

        Args:
            limit: 密度上限(kg/m)。/ Density upper limit (kg/m).

        Returns:
            距限制的余量(kg/m)，负值表示超限。
            Margin to limit (kg/m); negative means exceeding.
        """
        return limit - self.density

    def split_at(self, split_pos: float) -> tuple[LinearDensity, LinearDensity]:
        """在指定位置分段 / Split segment at position.

        Args:
            split_pos: 分段位置(m)。/ Split position (m).

        Returns:
            分段后的两个线密度实例。
            Two LinearDensity instances after splitting.
        """
        left_len = split_pos - self.position
        right_len = self.length - left_len
        left = LinearDensity(
            position=self.position,
            density=self.density,
            length=left_len,
        )
        right = LinearDensity(
            position=split_pos,
            density=self.density,
            length=right_len,
        )
        return left, right
