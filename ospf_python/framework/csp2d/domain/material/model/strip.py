"""卷材模型 / Roll material (strip) model.

CSP2D 中的卷材（带材）定义。
Roll material (strip) definition in CSP2D.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Strip:
    """卷材 / Roll material (strip).

    描述可用于二维切割的卷材，宽度固定、长度可变。
    Describes a roll material for 2D cutting,
    with fixed width and variable length.

    Attributes:
        name: 卷材名称 / Strip name.
        width: 卷材宽度 / Strip width.
        length: 卷材长度 / Strip length.
        cost: 卷材单价 / Strip unit cost.
    """

    name: str
    """卷材名称 / Strip name."""

    width: float
    """卷材宽度 / Strip width."""

    length: float
    """卷材长度 / Strip length."""

    cost: float
    """卷材单价 / Strip unit cost."""

    @staticmethod
    def create(
        *,
        name: str,
        width: float,
        length: float,
        cost: float = 0.0,
    ) -> Strip:
        """创建卷材 / Create strip.

        Args:
            name: 卷材名称 / Strip name.
            width: 卷材宽度 / Strip width.
            length: 卷材长度 / Strip length.
            cost: 卷材单价，默认 0.0 / Strip cost, default 0.0.

        Returns:
            卷材实例 / Strip instance.
        """
        return Strip(
            name=name,
            width=width,
            length=length,
            cost=cost,
        )

    @property
    def area(self) -> float:
        """卷材面积 / Strip area.

        Returns:
            宽 x 长 / Width x Length.
        """
        return self.width * self.length

    def can_fit(self, width: float, length: float) -> bool:
        """检查是否能放下指定尺寸 / Check if given size fits.

        Args:
            width: 所需宽度 / Required width.
            length: 所需长度 / Required length.

        Returns:
            是否能放下 / Whether the size fits.
        """
        if width <= 0.0 or length <= 0.0:
            return False
        return width <= self.width and length <= self.length
