"""集装器定义 / ULD definition.

航空集装器 (Unit Load Device) 定义。
Aviation Unit Load Device definition.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ULD:
    """航空集装器 / Unit Load Device.

    描述航空货运中使用的标准化集装容器。
    Describes a standardized container used in air cargo.

    Attributes:
        uld_type: 集装器类型代码 / ULD type code.
        width: 集装器宽度 (m) / ULD width (m).
        height: 集装器高度 (m) / ULD height (m).
        depth: 集装器纵深 (m) / ULD depth (m).
        max_weight: 最大载重 (kg) / Maximum weight (kg).
        tare_weight: 自重 (kg) / Tare weight (kg).
    """

    uld_type: str
    """集装器类型代码 / ULD type code."""

    width: float
    """集装器宽度 (m) / ULD width (m)."""

    height: float
    """集装器高度 (m) / ULD height (m)."""

    depth: float
    """集装器纵深 (m) / ULD depth (m)."""

    max_weight: float
    """最大载重 (kg) / Maximum weight (kg)."""

    tare_weight: float
    """自重 (kg) / Tare weight (kg)."""

    @staticmethod
    def create(
        *,
        uld_type: str,
        width: float,
        height: float,
        depth: float,
        max_weight: float,
        tare_weight: float = 0.0,
    ) -> ULD:
        """创建集装器实例 / Create ULD instance.

        Args:
            uld_type: 集装器类型代码 / ULD type code.
            width: 集装器宽度 / ULD width.
            height: 集装器高度 / ULD height.
            depth: 集装器纵深 / ULD depth.
            max_weight: 最大载重 / Max weight.
            tare_weight: 自重，默认 0 / Tare weight, default 0.

        Returns:
            集装器实例 / ULD instance.
        """
        return ULD(
            uld_type=uld_type,
            width=width,
            height=height,
            depth=depth,
            max_weight=max_weight,
            tare_weight=tare_weight,
        )

    @property
    def volume(self) -> float:
        """集装器外部体积 / ULD external volume.

        Returns:
            宽 x 高 x 深 (m^3) / Width x Height x Depth (m^3).
        """
        return self.width * self.height * self.depth

    @property
    def max_payload(self) -> float:
        """最大有效载荷 / Maximum payload.

        最大载重减去自重。
        Max weight minus tare weight.

        Returns:
            最大有效载荷 (kg) / Max payload (kg).
        """
        return self.max_weight - self.tare_weight

    def remaining_capacity(self, current_load: float) -> float:
        """计算剩余载荷能力 / Calculate remaining load capacity.

        Args:
            current_load: 当前载荷 (kg) / Current load (kg).

        Returns:
            剩余可装载重量 (kg) / Remaining loadable weight (kg).
        """
        return max(0.0, self.max_payload - current_load)

    def is_within_weight_limit(self, cargo_weight: float) -> bool:
        """检查货物重量是否在限制内 / Check if cargo weight is within limit.

        Args:
            cargo_weight: 货物重量 (kg) / Cargo weight (kg).

        Returns:
            重量不超过最大有效载荷时为 True /
            True if weight does not exceed max payload.
        """
        return cargo_weight <= self.max_payload
