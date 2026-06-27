"""生产使用量最小化 / Produce usage minimization.

生成最小化生产使用量的目标函数数据。
Generates objective function data for minimizing
production usage.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UsageObjectiveTerm:
    """使用量目标函数项 / Usage objective function term.

    表示目标函数中一个生产使用量的加权项。
    Represents a weighted term of production usage in the
    objective function.

    Attributes:
        produce_key: 生产单元标识 / Production unit id.
        window_start: 时间窗口起始 / Window start.
        window_end: 时间窗口结束 / Window end.
        weight: 权重系数 / Weight coefficient.
        variable_name: 关联变量名 / Associated variable name.
    """

    produce_key: str
    window_start: float
    window_end: float
    weight: float
    variable_name: str


@dataclass(frozen=True)
class ProduceUsageMinimization:
    """生产使用量最小化 / Produce usage minimization.

    构建最小化生产使用量的目标函数项，鼓励调度方案使用更少
    的生产单元产能。
    Builds objective function terms for minimizing production
    usage, encouraging scheduling plans that consume less
    production unit capacity.

    Attributes:
        objective_name: 目标函数名称 / Objective name.
        default_weight: 默认权重 / Default weight.
    """

    objective_name: str = "produce_usage_min"
    default_weight: float = 1.0

    def build_objective_terms(
        self,
        produce_keys: tuple[str, ...],
        time_windows: tuple[tuple[float, float], ...],
        weights: dict[tuple[str, float, float], float] | None = None,
    ) -> tuple[UsageObjectiveTerm, ...]:
        """构建目标函数项。

        Build objective function terms.

        Args:
            produce_keys: 生产单元标识列表 /
                Production unit key list.
            time_windows: 时间窗口列表 /
                Time window list.
            weights: 自定义权重映射 / Custom weight mapping.

        Returns:
            目标函数项元组。/ Tuple of objective terms.
        """
        effective_weights = weights or {}
        terms: list[UsageObjectiveTerm] = []
        for pk in produce_keys:
            for ws, we in time_windows:
                key = (pk, ws, we)
                weight = effective_weights.get(
                    key,
                    self.default_weight,
                )
                if weight > 0.0:
                    terms.append(
                        UsageObjectiveTerm(
                            produce_key=pk,
                            window_start=ws,
                            window_end=we,
                            weight=weight,
                            variable_name=self._var_name(
                                produce_key=pk,
                                window_start=ws,
                                window_end=we,
                            ),
                        )
                    )
        return tuple(terms)

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

    def _var_name(
        self,
        *,
        produce_key: str,
        window_start: float,
        window_end: float,
    ) -> str:
        """生成变量名称。

        Generate the variable name.

        Args:
            produce_key: 生产单元标识。/ Production unit id.
            window_start: 窗口起始。/ Window start.
            window_end: 窗口结束。/ Window end.

        Returns:
            变量名称字符串。/ Variable name string.
        """
        return f"usage_{produce_key}_{window_start}_{window_end}"
