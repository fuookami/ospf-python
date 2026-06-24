"""CSP1D 模型上下文。

持有 CSP1D 优化模型的运行时上下文。
Model context for CSP1D optimization.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Csp1dModelContext:
    """CSP1D 模型上下文 / CSP1D model context.

    持有 CSP1D 列生成或 MILP 模型运行时所需的
    引用和状态。
    Holds references and state required by the CSP1D
    column generation or MILP model at runtime.

    Attributes:
        material_keys: 可用材料标识列表。
            Available material keys.
        product_keys: 产品标识列表。
            Product keys.
        machine_keys: 机器标识列表。
            Machine keys.
        cutting_plan_keys: 已注册切割方案标识列表。
            Registered cutting plan keys.
        shadow_prices: 约束影子价格映射。
            Constraint shadow price mapping.
    """

    material_keys: tuple[str, ...] = ()
    """可用材料标识 / Available material keys."""

    product_keys: tuple[str, ...] = ()
    """产品标识 / Product keys."""

    machine_keys: tuple[str, ...] = ()
    """机器标识 / Machine keys."""

    cutting_plan_keys: tuple[str, ...] = ()
    """切割方案标识 / Cutting plan keys."""

    shadow_prices: tuple[tuple[str, float], ...] = ()
    """影子价格映射 / Shadow price mapping."""

    @staticmethod
    def create(
        *,
        material_keys: tuple[str, ...] = (),
        product_keys: tuple[str, ...] = (),
        machine_keys: tuple[str, ...] = (),
    ) -> Csp1dModelContext:
        """创建模型上下文。

        Create model context.

        Args:
            material_keys: 材料标识。
                Material keys.
            product_keys: 产品标识。
                Product keys.
            machine_keys: 机器标识。
                Machine keys.

        Returns:
            模型上下文实例。
            Model context instance.
        """
        return Csp1dModelContext(
            material_keys=material_keys,
            product_keys=product_keys,
            machine_keys=machine_keys,
        )

    def with_cutting_plans(
        self,
        *,
        plan_keys: tuple[str, ...],
    ) -> Csp1dModelContext:
        """创建包含切割方案的新上下文。

        Create new context with cutting plans.

        Args:
            plan_keys: 切割方案标识。
                Cutting plan keys.

        Returns:
            新上下文实例。
            New context instance.
        """
        return Csp1dModelContext(
            material_keys=self.material_keys,
            product_keys=self.product_keys,
            machine_keys=self.machine_keys,
            cutting_plan_keys=plan_keys,
            shadow_prices=self.shadow_prices,
        )

    def with_shadow_prices(
        self,
        *,
        prices: dict[str, float],
    ) -> Csp1dModelContext:
        """创建包含影子价格的新上下文。

        Create new context with shadow prices.

        Args:
            prices: 约束名到影子价格的映射。
                Constraint name to shadow price mapping.

        Returns:
            新上下文实例。
            New context instance.
        """
        items = tuple(sorted(prices.items(), key=lambda kv: kv[0]))
        return Csp1dModelContext(
            material_keys=self.material_keys,
            product_keys=self.product_keys,
            machine_keys=self.machine_keys,
            cutting_plan_keys=self.cutting_plan_keys,
            shadow_prices=items,
        )

    def get_shadow_price(self, constraint_name: str) -> float:
        """获取约束的影子价格。

        Get shadow price for a constraint.

        Args:
            constraint_name: 约束名称。
                Constraint name.

        Returns:
            影子价格，不存在返回 0.0。
            Shadow price, 0.0 if not found.
        """
        for name, price in self.shadow_prices:
            if name == constraint_name:
                return price
        return 0.0
