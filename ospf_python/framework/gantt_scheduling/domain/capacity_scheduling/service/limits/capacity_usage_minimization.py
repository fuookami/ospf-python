"""容量使用量最小化 / Capacity usage minimization.

生成最小化容量使用量的目标函数数据。
Generates objective function data for minimizing capacity usage.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UsageObjectiveTerm:
    """目标函数项 / Objective function term.

    Attributes:
        slot_key: 容量槽标识 / Slot identifier.
        window_start: 时间窗口起始 / Window start.
        window_end: 时间窗口结束 / Window end.
        weight: 权重系数 / Weight coefficient.
        variable_name: 关联变量名 / Variable name.
    """

    slot_key: str
    window_start: float
    window_end: float
    weight: float
    variable_name: str


@dataclass(frozen=True)
class CapacityUsageMinimization:
    """容量使用量最小化 / Capacity usage minimization.

    构建最小化容量使用量的目标函数项，鼓励调度方案使用更少
    的容量槽容量。

    Attributes:
        objective_name: 目标函数名称 / Objective name.
        default_weight: 默认权重 / Default weight.
    """

    objective_name: str = "cap_usage_min"
    default_weight: float = 1.0

    def build_objective_terms(
        self,
        slot_keys: tuple[str, ...],
        time_windows: tuple[tuple[float, float], ...],
        weights: dict[tuple[str, float, float], float] | None = None,
    ) -> tuple[UsageObjectiveTerm, ...]:
        """构建目标函数项。"""
        effective_weights = weights or {}
        terms: list[UsageObjectiveTerm] = []
        for sk in slot_keys:
            for ws, we in time_windows:
                key = (sk, ws, we)
                weight = effective_weights.get(
                    key,
                    self.default_weight,
                )
                if weight > 0.0:
                    terms.append(
                        UsageObjectiveTerm(
                            slot_key=sk,
                            window_start=ws,
                            window_end=we,
                            weight=weight,
                            variable_name=self._var_name(
                                slot_key=sk,
                                window_start=ws,
                                window_end=we,
                            ),
                        )
                    )
        return tuple(terms)

    def objective_name_for(
        self,
        slot_key: str,
    ) -> str:
        """生成容量槽特定的目标函数名称。"""
        return f"{self.objective_name}_{slot_key}"

    def _var_name(
        self,
        *,
        slot_key: str,
        window_start: float,
        window_end: float,
    ) -> str:
        """生成变量名称。"""
        return f"usage_{slot_key}_{window_start}_{window_end}"
