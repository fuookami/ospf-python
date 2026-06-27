"""资源容量最小化 / Resource volume minimization.

生成最小化资源容量使用的目标函数数据，用于减少资源种类数。
Generates objective function data for minimizing resource
volume, aiming to reduce the number of resource types used.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceVolumeObjectiveTerm:
    """资源容量目标函数项 / Resource volume objective term.

    Attributes:
        resource_key: 资源标识 / Resource identifier.
        weight: 权重系数 / Weight coefficient.
        variable_name: 关联变量名 / Associated variable name.
        fixed_cost: 固定使用成本 / Fixed usage cost.
    """

    resource_key: str
    weight: float
    variable_name: str
    fixed_cost: float = 0.0


@dataclass(frozen=True)
class ResourceVolumeSavingsResult:
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
class ResourceVolumeMinimization:
    """资源容量最小化 / Resource volume minimization.

    构建最小化资源总容量的目标函数项，鼓励调度方案使用更少
    的资源种类或更低的资源容量配置。
    Builds objective function terms for minimizing total resource
    volume, encouraging scheduling plans that use fewer resource
    types or lower resource capacity configurations.

    Attributes:
        objective_name: 目标函数名称 / Objective name.
        default_weight: 默认权重 / Default weight.
        fixed_cost_weight: 固定成本权重 / Fixed cost weight.
    """

    objective_name: str = "resource_volume_min"
    default_weight: float = 1.0
    fixed_cost_weight: float = 0.0

    def build_objective_terms(
        self,
        resource_keys: tuple[str, ...],
        resource_capacities: dict[str, float],
        weights: dict[str, float] | None = None,
        fixed_costs: dict[str, float] | None = None,
    ) -> tuple[ResourceVolumeObjectiveTerm, ...]:
        """构建目标函数项。

        Build objective function terms for all resources.

        Args:
            resource_keys: 资源标识列表 / Resource key list.
            resource_capacities: 资源容量映射 /
                Resource capacity mapping.
            weights: 自定义权重映射 / Custom weight mapping.
            fixed_costs: 固定成本映射 / Fixed cost mapping.

        Returns:
            目标函数项元组。/ Tuple of objective terms.
        """
        effective_weights = weights or {}
        effective_costs = fixed_costs or {}
        terms: list[ResourceVolumeObjectiveTerm] = []
        for rk in resource_keys:
            weight = effective_weights.get(
                rk,
                self.default_weight,
            )
            if weight > 0.0:
                terms.append(
                    ResourceVolumeObjectiveTerm(
                        resource_key=rk,
                        weight=weight,
                        variable_name=self._var_name(rk),
                        fixed_cost=effective_costs.get(rk, 0.0),
                    )
                )
        return tuple(terms)

    def compute_volume_savings(
        self,
        *,
        original_volumes: dict[str, float],
        optimized_volumes: dict[str, float],
    ) -> ResourceVolumeSavingsResult:
        """计算容量节省结果。"""
        original_total = sum(original_volumes.values())
        optimized_total = sum(optimized_volumes.values())
        return ResourceVolumeSavingsResult(
            original_volume=original_total,
            optimized_volume=optimized_total,
        )

    def objective_name_for(
        self,
        resource_key: str,
    ) -> str:
        """生成资源特定的目标函数名称。"""
        return f"{self.objective_name}_{resource_key}"

    def _var_name(self, resource_key: str) -> str:
        """生成变量名称。"""
        return f"volume_{resource_key}"
