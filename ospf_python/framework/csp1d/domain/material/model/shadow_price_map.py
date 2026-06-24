"""CSP1D 影子价格映射 / CSP1D shadow price map."""

from __future__ import annotations


class ShadowPriceMap:
    """影子价格映射表 / Shadow price mapping table.

    管理列生成迭代中各产品需求约束对应的影子价格（对偶值）。
    Manages shadow prices (dual values) associated with
    product demand constraints during column generation.

    Attributes:
        _prices: 内部价格字典 / Internal price dictionary.
    """

    def __init__(self) -> None:
        """初始化空影子价格映射 / Initialize empty shadow price map."""
        self._prices: dict[str, float] = {}

    def get(self, product: str) -> float:
        """获取产品影子价格 / Get shadow price for a product.

        Args:
            product: 产品名称 / Product name.

        Returns:
            影子价格，未注册时返回 0.0 / Shadow price, 0.0 if
            not registered.
        """
        return self._prices.get(product, 0.0)

    def set(
        self,
        product: str,
        price: float,
    ) -> None:
        """设置产品影子价格 / Set shadow price for a product.

        Args:
            product: 产品名称 / Product name.
            price: 影子价格 / Shadow price.
        """
        self._prices[product] = price

    def update(self, prices: dict[str, float]) -> None:
        """批量更新影子价格 / Batch update shadow prices.

        Args:
            prices: 产品到价格的映射 / Product-to-price mapping.
        """
        self._prices.update(prices)

    def clear(self) -> None:
        """清空所有影子价格 / Clear all shadow prices."""
        self._prices.clear()

    @property
    def products(self) -> tuple[str, ...]:
        """获取已注册产品列表 / Get list of registered products."""
        return tuple(self._prices.keys())

    def __contains__(self, product: str) -> bool:
        return product in self._prices

    def __len__(self) -> int:
        return len(self._prices)
