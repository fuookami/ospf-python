"""容量容量最小化 / Capacity volume minimization.

生成最小化容量总使用的目标函数数据。
Generates objective function data for minimizing total capacity
volume.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VolumeObjectiveTerm:
    """容量目标函数项 / Volume objective function term.

    Attributes:
        slot_key: 容量槽标识 / Slot identifier.
        weight: 权重系数 / Weight coefficient.
        variable_name: 关联变量名 / Variable name.
        fixed_cost: 固定使用成本 / Fixed usage cost.
    """

    slot_key: str
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
class CapacityVolumeMinimization:
    """容量容量最小化 / Capacity volume minimization.

    构建最小化容量总使用的目标函数项，鼓励调度方案使用更少
    的容量槽或更低的容量配置。

    Attributes:
        objective_name: 目标函数名称 / Objective name.
        default_weight: 默认权重 / Default weight.
    """

    objective_name: str = "cap_volume_min"
    default_weight: float = 1.0

    def build_objective_terms(
        self,
        slot_keys: tuple[str, ...],
        slot_capacities: dict[str, float],
        weights: dict[str, float] | None = None,
        fixed_costs: dict[str, float] | None = None,
    ) -> tuple[VolumeObjectiveTerm, ...]:
        """构建目标函数项。"""
        effective_weights = weights or {}
        effective_costs = fixed_costs or {}
        terms: list[VolumeObjectiveTerm] = []
        for sk in slot_keys:
            weight = effective_weights.get(
                sk,
                self.default_weight,
            )
            if weight > 0.0:
                terms.append(
                    VolumeObjectiveTerm(
                        slot_key=sk,
                        weight=weight,
                        variable_name=self._var_name(sk),
                        fixed_cost=effective_costs.get(sk, 0.0),
                    )
                )
        return tuple(terms)

    def compute_volume_savings(
        self,
        *,
        original_volumes: dict[str, float],
        optimized_volumes: dict[str, float],
    ) -> VolumeSavingsResult:
        """计算容量节省结果。"""
        original_total = sum(original_volumes.values())
        optimized_total = sum(optimized_volumes.values())
        return VolumeSavingsResult(
            original_volume=original_total,
            optimized_volume=optimized_total,
        )

    def objective_name_for(
        self,
        slot_key: str,
    ) -> str:
        """生成容量槽特定的目标函数名称。"""
        return f"{self.objective_name}_{slot_key}"

    def _var_name(self, slot_key: str) -> str:
        """生成变量名称。"""
        return f"volume_{slot_key}"
