"""批次容量最小化 / Batch volume minimization.

生成最小化批次总容量使用的目标函数数据。
Generates objective function data for minimizing total
batch volume.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BatchVolumeObjectiveTerm:
    """批次容量目标函数项 / Batch volume objective function term.

    Attributes:
        batch_key: 批次标识 / Batch identifier.
        weight: 权重系数 / Weight coefficient.
        variable_name: 关联变量名 / Associated variable name.
        fixed_cost: 固定使用成本 / Fixed usage cost.
    """

    batch_key: str
    weight: float
    variable_name: str
    fixed_cost: float = 0.0


@dataclass(frozen=True)
class BatchVolumeSavingsResult:
    """容量节省结果 / Volume savings result.

    Attributes:
        original_volume: 原始容量 / Original volume.
        optimized_volume: 优化后容量 / Optimized volume.
    """

    original_volume: float
    optimized_volume: float

    @property
    def savings_ratio(self) -> float:
        """节省比例 / Savings ratio."""
        if self.original_volume <= 0.0:
            return 0.0
        return max(
            0.0,
            1.0 - self.optimized_volume / self.original_volume,
        )


@dataclass(frozen=True)
class BatchVolumeMinimization:
    """批次容量最小化 / Batch volume minimization.

    构建最小化批次总容量的目标函数项，鼓励调度方案使用更少
    的批次或更低的容量配置。
    Builds objective function terms for minimizing total batch
    volume, encouraging scheduling plans that use fewer batches
    or lower capacity configurations.

    Attributes:
        objective_name: 目标函数名称 / Objective name.
        default_weight: 默认权重 / Default weight.
    """

    objective_name: str = "batch_volume_min"
    default_weight: float = 1.0

    def build_objective_terms(
        self,
        batch_keys: tuple[str, ...],
        batch_capacities: dict[str, float],
        weights: dict[str, float] | None = None,
        fixed_costs: dict[str, float] | None = None,
    ) -> tuple[BatchVolumeObjectiveTerm, ...]:
        """构建目标函数项。

        Build objective function terms for all batches.

        Args:
            batch_keys: 批次标识列表 / Batch key list.
            batch_capacities: 批次容量映射 /
                Batch capacity mapping.
            weights: 自定义权重映射 / Custom weight mapping.
            fixed_costs: 固定成本映射 / Fixed cost mapping.

        Returns:
            目标函数项元组。/ Tuple of objective terms.
        """
        effective_weights = weights or {}
        effective_costs = fixed_costs or {}
        terms: list[BatchVolumeObjectiveTerm] = []
        for bk in batch_keys:
            weight = effective_weights.get(
                bk,
                self.default_weight,
            )
            if weight > 0.0:
                terms.append(
                    BatchVolumeObjectiveTerm(
                        batch_key=bk,
                        weight=weight,
                        variable_name=self._var_name(bk),
                        fixed_cost=effective_costs.get(bk, 0.0),
                    )
                )
        return tuple(terms)

    def compute_volume_savings(
        self,
        *,
        original_volumes: dict[str, float],
        optimized_volumes: dict[str, float],
    ) -> BatchVolumeSavingsResult:
        """计算容量节省结果。"""
        original_total = sum(original_volumes.values())
        optimized_total = sum(optimized_volumes.values())
        return BatchVolumeSavingsResult(
            original_volume=original_total,
            optimized_volume=optimized_total,
        )

    def objective_name_for(
        self,
        batch_key: str,
    ) -> str:
        """生成批次特定的目标函数名称。"""
        return f"{self.objective_name}_{batch_key}"

    def _var_name(self, batch_key: str) -> str:
        """生成变量名称。"""
        return f"batch_vol_{batch_key}"
