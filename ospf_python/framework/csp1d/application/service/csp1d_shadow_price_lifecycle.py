"""CSP1D 影子价格生命周期 / CSP1D shadow price lifecycle."""

from __future__ import annotations

from ospf_python.framework.csp1d.domain.material.model.shadow_price_map import (
    ShadowPriceMap,
)


class Csp1dShadowPriceLifecycle:
    """影子价格生命周期管理 / Shadow price lifecycle manager.

    管理列生成过程中影子价格的初始化、更新、收敛判定
    和最终提取。
    Manages initialization, update, convergence check,
    and final extraction of shadow prices during
    column generation.

    Attributes:
        _prices: 当前影子价格 / Current shadow prices.
        _history: 历史价格快照 / Historical price snapshots.
        _converged: 是否收敛 / Whether converged.
        _tolerance: 收敛容差 / Convergence tolerance.
    """

    def __init__(
        self,
        tolerance: float = 1e-6,
    ) -> None:
        """初始化生命周期管理器 / Initialize lifecycle manager.

        Args:
            tolerance: 收敛容差 / Convergence tolerance.
        """
        self._prices = ShadowPriceMap()
        self._history: list[dict[str, float]] = []
        self._converged: bool = False
        self._tolerance: float = tolerance

    def initialize(
        self,
        products: tuple[str, ...],
    ) -> None:
        """初始化影子价格 / Initialize shadow prices.

        为所有产品设置初始零影子价格。
        Sets initial zero shadow prices for all products.

        Args:
            products: 产品名称列表 / Product name list.
        """
        self._prices.clear()
        for product in products:
            self._prices.set(product, 0.0)
        self._history.clear()
        self._converged = False

    def update(
        self,
        new_prices: dict[str, float],
    ) -> None:
        """更新影子价格 / Update shadow prices.

        Args:
            new_prices: 新的价格值 / New price values.
        """
        snapshot = {p: self._prices.get(p) for p in self._prices.products}
        self._history.append(snapshot)
        self._prices.update(new_prices)
        self._check_convergence()

    def _check_convergence(self) -> None:
        """检查收敛性 / Check convergence."""
        if len(self._history) < 2:
            return
        prev = self._history[-1]
        max_diff = 0.0
        for product in self._prices.products:
            old_val = prev.get(product, 0.0)
            new_val = self._prices.get(product)
            max_diff = max(max_diff, abs(new_val - old_val))
        self._converged = max_diff < self._tolerance

    @property
    def prices(self) -> ShadowPriceMap:
        """当前影子价格 / Current shadow prices."""
        return self._prices

    @property
    def converged(self) -> bool:
        """是否收敛 / Whether converged."""
        return self._converged

    @property
    def iteration(self) -> int:
        """已完成迭代次数 / Completed iteration count."""
        return len(self._history)
