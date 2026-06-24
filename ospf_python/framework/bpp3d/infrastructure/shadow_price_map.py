"""影子价格映射 / Shadow price map.

BPP3D 基础设施层的影子价格映射。
Shadow price map for BPP3D infrastructure layer.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ShadowPriceMap:
    """影子价格映射 / Shadow price map.

    存储约束的影子价格，用于灵敏度分析。
    Stores shadow prices of constraints for
    sensitivity analysis.

    Attributes:
        prices: 约束名到影子价格的映射 /
            Constraint name to shadow price mapping.
    """

    prices: tuple[tuple[str, float], ...]
    """约束名到影子价格的映射 /
    Constraint name to shadow price mapping."""

    @staticmethod
    def create(
        *,
        prices: tuple[tuple[str, float], ...],
    ) -> ShadowPriceMap:
        """创建影子价格映射 / Create shadow price map.

        Args:
            prices: 价格元组 / Price tuples.

        Returns:
            影子价格映射实例 / ShadowPriceMap instance.
        """
        return ShadowPriceMap(prices=prices)

    def get_price(self, name: str) -> float:
        """获取影子价格 / Get shadow price.

        Args:
            name: 约束名称 / Constraint name.

        Returns:
            影子价格，未找到返回 0 / Shadow price, 0 if not found.
        """
        for key, price in self.prices:
            if key == name:
                return price
        return 0.0

    @property
    def size(self) -> int:
        """映射大小 / Map size.

        Returns:
            约束数量 / Number of constraints.
        """
        return len(self.prices)
