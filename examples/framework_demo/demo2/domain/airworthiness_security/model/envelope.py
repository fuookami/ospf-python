"""飞行包线定义 / Flight envelope definition.

定义飞机在不同飞行阶段的重量与重心包线。
Defines the weight and CG envelope of an aircraft
across different flight phases.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Envelope:
    """飞行包线 / Flight envelope.

    描述飞机允许的重量范围与重心（CG）范围，
    用于装箱方案的适航合规校验。
    Describes the allowable weight range and center-of-gravity
    (CG) range of an aircraft, used for airworthiness compliance
    checks of packing solutions.

    Attributes:
        envelope_id: 包线标识 / Envelope identifier.
        max_weight: 最大允许重量(kg) / Max allowable weight (kg).
        min_weight: 最小允许重量(kg) / Min allowable weight (kg).
        max_cg: 最大允许重心位置(%MAC) / Max CG position (%MAC).
        min_cg: 最小允许重心位置(%MAC) / Min CG position (%MAC).
    """

    envelope_id: str
    max_weight: float
    min_weight: float
    max_cg: float
    min_cg: float

    @staticmethod
    def create(
        *,
        envelope_id: str,
        max_weight: float,
        min_weight: float,
        max_cg: float,
        min_cg: float,
    ) -> Envelope:
        """创建飞行包线 / Create flight envelope.

        Args:
            envelope_id: 包线标识 / Envelope identifier.
            max_weight: 最大允许重量(kg) / Max allowable weight.
            min_weight: 最小允许重量(kg) / Min allowable weight.
            max_cg: 最大允许重心(%MAC) / Max CG position.
            min_cg: 最小允许重心(%MAC) / Min CG position.

        Returns:
            飞行包线实例 / Envelope instance.
        """
        return Envelope(
            envelope_id=envelope_id,
            max_weight=max_weight,
            min_weight=min_weight,
            max_cg=max_cg,
            min_cg=min_cg,
        )

    @property
    def weight_range(self) -> float:
        """重量范围宽度 / Weight range width.

        Returns:
            最大重量与最小重量之差(kg)。
            Difference between max and min weight (kg).
        """
        return self.max_weight - self.min_weight

    @property
    def cg_range(self) -> float:
        """重心范围宽度 / CG range width.

        Returns:
            最大重心与最小重心之差(%MAC)。
            Difference between max and min CG (%MAC).
        """
        return self.max_cg - self.min_cg

    def contains_weight(self, weight: float) -> bool:
        """检查重量是否在包线内。

        Check whether the given weight falls within
        the envelope.

        Args:
            weight: 待检查重量(kg)。/ Weight to check (kg).

        Returns:
            若重量在 [min_weight, max_weight] 内则返回 True。
            True if weight is within [min_weight, max_weight].
        """
        return self.min_weight <= weight <= self.max_weight

    def contains_cg(self, cg: float) -> bool:
        """检查重心是否在包线内。

        Check whether the given CG falls within
        the envelope.

        Args:
            cg: 待检查重心(%MAC)。/ CG to check (%MAC).

        Returns:
            若重心在 [min_cg, max_cg] 内则返回 True。
            True if CG is within [min_cg, max_cg].
        """
        return self.min_cg <= cg <= self.max_cg

    def weight_margin(self, weight: float) -> float:
        """计算重量余量 / Calculate weight margin.

        Args:
            weight: 当前重量(kg)。/ Current weight (kg).

        Returns:
            距最大重量的余量(kg)，负值表示超限。
            Margin to max weight (kg); negative means
            exceeding limit.
        """
        return self.max_weight - weight

    def cg_margin(self, cg: float) -> float:
        """计算重心余量 / Calculate CG margin.

        重心余量取两侧边界的较小值。

        Args:
            cg: 当前重心(%MAC)。/ Current CG (%MAC).

        Returns:
            距最近包线边界的余量(%MAC)。
            Margin to the nearest envelope boundary (%MAC).
        """
        return min(self.max_cg - cg, cg - self.min_cg)
