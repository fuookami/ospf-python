"""资源影子价格映射 / Resource shadow price map.

存储资源约束的影子价格，用于列生成定价和灵敏度分析。
Stores shadow prices of resource constraints, used for column
generation pricing and sensitivity analysis.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceShadowPriceMap:
    """资源影子价格映射 / Resource shadow price map.

    维护资源约束名称到影子价格的映射，支持按资源和时间窗口
    查询，以及总定价成本计算。
    Maintains a mapping from resource constraint names to shadow
    prices, supporting queries by resource and time window,
    and total pricing cost computation.

    Attributes:
        prices: 约束名到影子价格的映射 /
            Mapping from constraint name to shadow price.
        resource_prices: (资源标识, 窗口起始, 窗口结束) 到
            影子价格的映射 /
            Mapping from (resource_key, window_start, window_end)
            to shadow price.
    """

    prices: tuple[tuple[str, float], ...] = ()
    resource_prices: tuple[tuple[tuple[str, float, float], float], ...] = ()

    def get_price(self, constraint_name: str) -> float:
        """按约束名获取影子价格。

        Get shadow price by constraint name.

        Args:
            constraint_name: 约束名称。/ Constraint name.

        Returns:
            影子价格，不存在时返回 0.0。
            Shadow price, or 0.0 if not found.
        """
        for name, price in self.prices:
            if name == constraint_name:
                return price
        return 0.0

    def get_resource_price(
        self,
        *,
        resource_key: str,
        window_start: float,
        window_end: float,
    ) -> float:
        """按资源和时间窗口获取影子价格。

        Get shadow price by resource key and time window.

        Args:
            resource_key: 资源标识。/ Resource identifier.
            window_start: 窗口起始。/ Window start.
            window_end: 窗口结束。/ Window end.

        Returns:
            影子价格，不存在时返回 0.0。
            Shadow price, or 0.0 if not found.
        """
        key = (resource_key, window_start, window_end)
        for k, price in self.resource_prices:
            if k == key:
                return price
        return 0.0

    def with_price(
        self,
        *,
        constraint_name: str,
        price: float,
    ) -> ResourceShadowPriceMap:
        """创建添加影子价格后的副本。

        Create a copy with an additional shadow price entry.

        Args:
            constraint_name: 约束名称。/ Constraint name.
            price: 影子价格。/ Shadow price.

        Returns:
            包含新影子价格的 ResourceShadowPriceMap 副本。
            A new instance with the shadow price added.
        """
        return ResourceShadowPriceMap(
            prices=self.prices + ((constraint_name, price),),
            resource_prices=self.resource_prices,
        )

    def with_resource_price(
        self,
        *,
        resource_key: str,
        window_start: float,
        window_end: float,
        price: float,
    ) -> ResourceShadowPriceMap:
        """创建添加资源影子价格后的副本。

        Create a copy with an additional resource shadow price.

        Args:
            resource_key: 资源标识。/ Resource identifier.
            window_start: 窗口起始。/ Window start.
            window_end: 窗口结束。/ Window end.
            price: 影子价格。/ Shadow price.

        Returns:
            包含新资源影子价格的副本。
            A new instance with the resource shadow price added.
        """
        key = (resource_key, window_start, window_end)
        return ResourceShadowPriceMap(
            prices=self.prices,
            resource_prices=self.resource_prices + ((key, price),),
        )

    def total_pricing_cost(
        self,
        demands: tuple[tuple[str, float, float, float], ...],
    ) -> float:
        """计算总定价成本。

        Compute total pricing cost for a set of demands.

        Args:
            demands: 需求元组列表，每项为
                (resource_key, window_start, window_end, amount)。
                List of demand tuples, each as
                (resource_key, window_start, window_end, amount).

        Returns:
            总定价成本 / Total pricing cost.
        """
        return sum(
            self.get_resource_price(
                resource_key=rk,
                window_start=ws,
                window_end=we,
            )
            * amount
            for rk, ws, we, amount in demands
        )
