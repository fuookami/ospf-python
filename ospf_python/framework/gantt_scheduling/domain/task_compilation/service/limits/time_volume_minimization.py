"""时间容量最小化 / Time volume minimization.

生成最小化时间容量使用的目标函数数据，减少时间窗口的
总容量占用。
Generates objective function data for minimizing time volume,
reducing total capacity occupation across time windows.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TimeVolumeObjectiveTerm:
    """时间容量目标函数项 / Time volume objective term.

    Attributes:
        window_start: 时间窗口起始 / Window start.
        window_end: 时间窗口结束 / Window end.
        weight: 权重系数 / Weight coefficient.
        capacity: 容量值 / Capacity value.
        variable_name: 关联变量名 / Associated variable name.
        fixed_cost: 固定使用成本 / Fixed usage cost.
    """

    window_start: float
    window_end: float
    weight: float
    capacity: float
    variable_name: str
    fixed_cost: float = 0.0


@dataclass(frozen=True)
class TimeVolumeSavingsResult:
    """时间容量节省结果 / Time volume savings result.

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
class TimeVolumeMinimization:
    """时间容量最小化 / Time volume minimization.

    构建最小化时间容量的目标函数项，鼓励调度方案使用更少
    的时间窗口或更低的时间容量配置。适用于希望压缩时间
    维度资源占用的场景。
    Builds objective function terms for minimizing time volume,
    encouraging scheduling plans that use fewer time windows or
    lower time capacity configurations. Applicable when the
    goal is to compress resource occupation in the time
    dimension.

    Attributes:
        objective_name: 目标函数名称 / Objective name.
        default_weight: 默认权重 / Default weight.
    """

    objective_name: str = "time_volume_min"
    default_weight: float = 1.0

    def build_objective_terms(
        self,
        time_windows: tuple[tuple[float, float], ...],
        window_capacities: dict[tuple[float, float], float],
        weights: dict[tuple[float, float], float] | None = None,
        fixed_costs: dict[tuple[float, float], float] | None = None,
    ) -> tuple[TimeVolumeObjectiveTerm, ...]:
        """构建目标函数项。

        Build objective function terms for all time windows.

        Args:
            time_windows: 时间窗口列表 / Time window list.
            window_capacities: 窗口容量映射 /
                Window capacity mapping.
            weights: 自定义权重映射 / Custom weight mapping.
            fixed_costs: 固定成本映射 / Fixed cost mapping.

        Returns:
            目标函数项元组。/ Tuple of objective terms.
        """
        effective_weights = weights or {}
        effective_costs = fixed_costs or {}
        terms: list[TimeVolumeObjectiveTerm] = []
        for ws, we in time_windows:
            key = (ws, we)
            weight = effective_weights.get(
                key,
                self.default_weight,
            )
            cap = window_capacities.get(key, 0.0)
            if weight > 0.0 and cap > 0.0:
                terms.append(
                    TimeVolumeObjectiveTerm(
                        window_start=ws,
                        window_end=we,
                        weight=weight,
                        capacity=cap,
                        variable_name=self._var_name(
                            window_start=ws,
                            window_end=we,
                        ),
                        fixed_cost=effective_costs.get(key, 0.0),
                    )
                )
        return tuple(terms)

    def compute_volume_savings(
        self,
        *,
        original_volumes: dict[tuple[float, float], float],
        optimized_volumes: dict[tuple[float, float], float],
    ) -> TimeVolumeSavingsResult:
        """计算时间容量节省结果。

        Compute time volume savings result.

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
        return TimeVolumeSavingsResult(
            original_volume=original_total,
            optimized_volume=optimized_total,
        )

    def objective_name_for_window(
        self,
        window_start: float,
        window_end: float,
    ) -> str:
        """生成时间窗口特定的目标函数名称。

        Generate time-window-specific objective function name.

        Args:
            window_start: 窗口起始。/ Window start.
            window_end: 窗口结束。/ Window end.

        Returns:
            目标函数名称。/ Objective function name.
        """
        return f"{self.objective_name}_{window_start}_{window_end}"

    def _var_name(
        self,
        *,
        window_start: float,
        window_end: float,
    ) -> str:
        """生成变量名称。

        Generate the variable name.

        Args:
            window_start: 窗口起始。/ Window start.
            window_end: 窗口结束。/ Window end.

        Returns:
            变量名称字符串。/ Variable name string.
        """
        return f"time_vol_{window_start}_{window_end}"
