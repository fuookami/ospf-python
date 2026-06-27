"""时间使用量最小化 / Time usage minimization.

生成最小化时间使用量的目标函数数据。
Generates objective function data for minimizing
time usage.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TimeUsageObjectiveTerm:
    """时间使用量目标函数项 / Time usage objective term.

    Attributes:
        window_start: 时间窗口起始 / Window start.
        window_end: 时间窗口结束 / Window end.
        weight: 权重系数 / Weight coefficient.
        variable_name: 关联变量名 / Associated variable name.
    """

    window_start: float
    window_end: float
    weight: float
    variable_name: str


@dataclass(frozen=True)
class TimeUsageMinimization:
    """时间使用量最小化 / Time usage minimization.

    构建最小化时间使用量的目标函数项，鼓励调度方案减少
    各时间窗口内的资源占用。适用于希望缩短总工期、压缩
    时间跨度的场景。
    Builds objective function terms for minimizing time usage,
    encouraging scheduling plans that reduce resource occupation
    in each time window. Applicable when the goal is to shorten
    total duration and compress time spans.

    Attributes:
        objective_name: 目标函数名称 / Objective name.
        default_weight: 默认权重 / Default weight.
    """

    objective_name: str = "time_usage_min"
    default_weight: float = 1.0

    def build_objective_terms(
        self,
        time_windows: tuple[tuple[float, float], ...],
        weights: dict[tuple[float, float], float] | None = None,
    ) -> tuple[TimeUsageObjectiveTerm, ...]:
        """构建目标函数项。

        Build objective function terms.

        Args:
            time_windows: 时间窗口列表 / Time window list.
            weights: 自定义权重映射 / Custom weight mapping.

        Returns:
            目标函数项元组。/ Tuple of objective terms.
        """
        effective_weights = weights or {}
        terms: list[TimeUsageObjectiveTerm] = []
        for ws, we in time_windows:
            key = (ws, we)
            weight = effective_weights.get(
                key,
                self.default_weight,
            )
            if weight > 0.0:
                terms.append(
                    TimeUsageObjectiveTerm(
                        window_start=ws,
                        window_end=we,
                        weight=weight,
                        variable_name=self._var_name(
                            window_start=ws,
                            window_end=we,
                        ),
                    )
                )
        return tuple(terms)

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
        return f"time_usage_{window_start}_{window_end}"
