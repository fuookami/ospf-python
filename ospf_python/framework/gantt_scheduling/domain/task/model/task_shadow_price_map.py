"""任务影子价格映射 / Task shadow price map.

管理列生成迭代中各约束对应的影子价格（对偶值）。
Manages shadow prices (dual values) for constraints
during column generation iterations.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ShadowPriceKey:
    """影子价格键 / Shadow price key.

    用于唯一标识一个影子价格条目。
    Uniquely identifies a shadow price entry.

    Attributes:
        constraint_name: 约束名称 / Constraint name.
        task_key: 关联的任务键，None 表示全局约束 /
            Associated task key, None for global constraints.
        executor_key: 关联的执行者键，None 表示不限 /
            Associated executor key, None for all executors.
    """

    constraint_name: str
    task_key: str | None = None
    executor_key: str | None = None

    @staticmethod
    def global_constraint(
        constraint_name: str,
    ) -> ShadowPriceKey:
        """创建全局约束键 / Create global constraint key.

        Args:
            constraint_name: 约束名称 / Constraint name.

        Returns:
            全局约束键 / Global constraint key.
        """
        return ShadowPriceKey(constraint_name=constraint_name)

    @staticmethod
    def task_constraint(
        constraint_name: str,
        task_key: str,
    ) -> ShadowPriceKey:
        """创建任务约束键 / Create task constraint key.

        Args:
            constraint_name: 约束名称 / Constraint name.
            task_key: 任务键 / Task key.

        Returns:
            任务约束键 / Task constraint key.
        """
        return ShadowPriceKey(
            constraint_name=constraint_name,
            task_key=task_key,
        )

    @staticmethod
    def executor_constraint(
        constraint_name: str,
        executor_key: str,
    ) -> ShadowPriceKey:
        """创建执行者约束键 / Create executor constraint key.

        Args:
            constraint_name: 约束名称 / Constraint name.
            executor_key: 执行者键 / Executor key.

        Returns:
            执行者约束键 / Executor constraint key.
        """
        return ShadowPriceKey(
            constraint_name=constraint_name,
            executor_key=executor_key,
        )


class TaskShadowPriceMap:
    """任务影子价格映射 / Task shadow price map.

    管理列生成迭代中各约束对应的影子价格。
    用于计算缩减成本（reduced cost）。
    Manages shadow prices for constraints during column
    generation. Used to compute reduced costs.

    Attributes:
        _prices: 内部价格字典 / Internal price dictionary.
    """

    def __init__(self) -> None:
        """初始化空影子价格映射 / Initialize empty map."""
        self._prices: dict[ShadowPriceKey, float] = {}

    def get(
        self,
        key: ShadowPriceKey,
    ) -> float:
        """获取影子价格 / Get shadow price.

        Args:
            key: 影子价格键 / Shadow price key.

        Returns:
            影子价格，未注册时返回 0.0。
            Shadow price, 0.0 if not registered.
        """
        return self._prices.get(key, 0.0)

    def set(
        self,
        key: ShadowPriceKey,
        price: float,
    ) -> None:
        """设置影子价格 / Set shadow price.

        Args:
            key: 影子价格键 / Shadow price key.
            price: 影子价格值 / Shadow price value.
        """
        self._prices[key] = price

    def update(self, prices: dict[ShadowPriceKey, float]) -> None:
        """批量更新影子价格 / Batch update shadow prices.

        Args:
            prices: 键到价格的映射 / Key-to-price mapping.
        """
        self._prices.update(prices)

    def clear(self) -> None:
        """清空所有影子价格 / Clear all shadow prices."""
        self._prices.clear()

    @property
    def keys(self) -> tuple[ShadowPriceKey, ...]:
        """获取所有已注册的键 / Get all registered keys.

        Returns:
            键元组 / Key tuple.
        """
        return tuple(self._prices.keys())

    @property
    def size(self) -> int:
        """获取映射大小 / Get map size.

        Returns:
            条目数量 / Number of entries.
        """
        return len(self._prices)

    def get_task_price(
        self,
        constraint_name: str,
        task_key: str,
    ) -> float:
        """获取任务级影子价格 / Get task-level shadow price.

        Args:
            constraint_name: 约束名称 / Constraint name.
            task_key: 任务键 / Task key.

        Returns:
            影子价格 / Shadow price.
        """
        key = ShadowPriceKey.task_constraint(
            constraint_name=constraint_name,
            task_key=task_key,
        )
        return self.get(key)

    def get_global_price(self, constraint_name: str) -> float:
        """获取全局影子价格 / Get global shadow price.

        Args:
            constraint_name: 约束名称 / Constraint name.

        Returns:
            影子价格 / Shadow price.
        """
        key = ShadowPriceKey.global_constraint(constraint_name)
        return self.get(key)

    def get_executor_price(
        self,
        constraint_name: str,
        executor_key: str,
    ) -> float:
        """获取执行者级影子价格 / Get executor-level shadow price.

        Args:
            constraint_name: 约束名称 / Constraint name.
            executor_key: 执行者键 / Executor key.

        Returns:
            影子价格 / Shadow price.
        """
        key = ShadowPriceKey.executor_constraint(
            constraint_name=constraint_name,
            executor_key=executor_key,
        )
        return self.get(key)

    def reduced_cost(
        self,
        base_cost: float,
        task_keys: tuple[str, ...],
        constraint_name: str,
    ) -> float:
        """计算缩减成本 / Compute reduced cost.

        缩减成本 = 基础成本 - 各任务影子价格之和。
        Reduced cost = base cost - sum of task shadow prices.

        Args:
            base_cost: 基础成本 / Base cost.
            task_keys: 任务键列表 / Task key list.
            constraint_name: 约束名称 / Constraint name.

        Returns:
            缩减成本 / Reduced cost.
        """
        price_sum = sum(self.get_task_price(constraint_name, key) for key in task_keys)
        return base_cost - price_sum

    def __contains__(self, key: ShadowPriceKey) -> bool:
        """检查键是否存在 / Check if key exists."""
        return key in self._prices

    def __len__(self) -> int:
        """获取大小 / Get size."""
        return len(self._prices)
