"""生产容量最小化 / Produce volume minimization.

生成最小化生产容量使用的目标函数数据，用于减少生产单元种类数。
Generates objective function data for minimizing production
volume, aiming to reduce the number of production unit types
used.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VolumeObjectiveTerm:
    """容量目标函数项 / Volume objective function term.

    表示目标函数中一个生产容量的加权项。
    Represents a weighted term of production volume in the
    objective function.

    Attributes:
        produce_key: 生产单元标识 / Production unit id.
        weight: 权重系数 / Weight coefficient.
        variable_name: 关联变量名 / Associated variable name.
        fixed_cost: 固定使用成本 / Fixed usage cost.
    """

    produce_key: str
    weight: float
    variable_name: str
    fixed_cost: float = 0.0


@dataclass(frozen=True)
class VolumeSavingsResult:
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
class ProduceVolumeMinimization:
    """生产容量最小化 / Produce volume minimization.

    构建最小化生产总容量的目标函数项，鼓励调度方案使用更少
    的生产单元种类或更低的容量配置。
    Builds objective function terms for minimizing total
    production volume, encouraging scheduling plans that use
    fewer production unit types or lower capacity configurations.

    Attributes:
        objective_name: 目标函数名称 / Objective name.
        default_weight: 默认权重 / Default weight.
        fixed_cost_weight: 固定成本权重 / Fixed cost weight.
    """

    objective_name: str = "produce_volume_min"
    default_weight: float = 1.0
    fixed_cost_weight: float = 0.0

    def build_objective_terms(
        self,
        produce_keys: tuple[str, ...],
        produce_capacities: dict[str, float],
        weights: dict[str, float] | None = None,
        fixed_costs: dict[str, float] | None = None,
    ) -> tuple[VolumeObjectiveTerm, ...]:
        """构建目标函数项。

        Build objective function terms for all production units.

        Args:
            produce_keys: 生产单元标识列表 /
                Production unit key list.
            produce_capacities: 生产容量映射 /
                Production capacity mapping.
            weights: 自定义权重映射 / Custom weight mapping.
            fixed_costs: 固定成本映射 / Fixed cost mapping.

        Returns:
            目标函数项元组。/ Tuple of objective terms.
        """
        effective_weights = weights or {}
        effective_costs = fixed_costs or {}
        terms: list[VolumeObjectiveTerm] = []
        for pk in produce_keys:
            weight = effective_weights.get(
                pk,
                self.default_weight,
            )
            if weight > 0.0:
                terms.append(
                    VolumeObjectiveTerm(
                        produce_key=pk,
                        weight=weight,
                        variable_name=self._var_name(pk),
                        fixed_cost=effective_costs.get(pk, 0.0),
                    )
                )
        return tuple(terms)

    def compute_volume_savings(
        self,
        *,
        original_volumes: dict[str, float],
        optimized_volumes: dict[str, float],
    ) -> VolumeSavingsResult:
        """计算容量节省结果。

        Compute volume savings result.

        Args:
            original_volumes: 原始容量映射 /
                Original volume mapping.
            optimized_volumes: 优化后容量映射 /
                Optimized volume mapping.

        Returns:
            容量节省结果。/ Volume savings result.
        """
        original_total = sum(original_volumes.values())
        optimized_total = sum(optimized_volumes.values())
        return VolumeSavingsResult(
            original_volume=original_total,
            optimized_volume=optimized_total,
        )

    def objective_name_for(
        self,
        produce_key: str,
    ) -> str:
        """生成生产单元特定的目标函数名称。

        Generate produce-specific objective function name.

        Args:
            produce_key: 生产单元标识。/ Production unit id.

        Returns:
            目标函数名称。/ Objective function name.
        """
        return f"{self.objective_name}_{produce_key}"

    def _var_name(self, produce_key: str) -> str:
        """生成变量名称。

        Generate the variable name.

        Args:
            produce_key: 生产单元标识。/ Production unit id.

        Returns:
            变量名称字符串。/ Variable name string.
        """
        return f"volume_{produce_key}"
