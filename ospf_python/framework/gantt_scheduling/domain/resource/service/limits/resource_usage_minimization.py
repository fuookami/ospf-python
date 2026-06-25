"""资源使用量最小化 / Resource usage minimization.

生成最小化资源使用量的目标函数数据，用于减少资源占用。
Generates objective function data for minimizing resource usage,
aiming to reduce resource occupation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UsageObjectiveTerm:
    """目标函数项 / Objective function term.

    表示目标函数中一个资源使用量的加权项。
    Represents a weighted term of resource usage in the
    objective function.

    Attributes:
        resource_key: 资源标识 / Resource identifier.
        window_start: 时间窗口起始 / Time window start.
        window_end: 时间窗口结束 / Time window end.
        weight: 权重系数 / Weight coefficient.
        variable_name: 关联变量名 / Associated variable name.
    """

    resource_key: str
    window_start: float
    window_end: float
    weight: float
    variable_name: str


@dataclass(frozen=True)
class ResourceUsageMinimization:
    """资源使用量最小化 / Resource usage minimization.

    构建最小化资源使用量的目标函数项，鼓励调度方案使用更少
    的资源容量。适用于希望在满足所有需求的前提下尽量减少
    资源占用的场景。
    Builds objective function terms for minimizing resource usage,
    encouraging scheduling plans that use less resource capacity.
    Applicable when the goal is to minimize resource occupation
    while satisfying all demands.

    Attributes:
        objective_name: 目标函数名称 / Objective function name.
        default_weight: 默认权重 / Default weight.
    """

    objective_name: str = "resource_usage_min"
    default_weight: float = 1.0

    def build_objective_terms(
        self,
        resource_keys: tuple[str, ...],
        time_windows: tuple[tuple[float, float], ...],
        weights: dict[tuple[str, float, float], float] | None = None,
    ) -> tuple[UsageObjectiveTerm, ...]:
        """构建目标函数项。

        Build objective function terms for all resource-window
        combinations.

        Args:
            resource_keys: 资源标识列表 / Resource key list.
            time_windows: 时间窗口列表 / Time window list.
            weights: 自定义权重映射，键为
                (resource_key, start, end) /
                Custom weight mapping with keys as
                (resource_key, start, end).

        Returns:
            目标函数项元组。/ Tuple of objective terms.
        """
        effective_weights = weights or {}
        terms: list[UsageObjectiveTerm] = []
        for rk in resource_keys:
            for ws, we in time_windows:
                key = (rk, ws, we)
                weight = effective_weights.get(
                    key,
                    self.default_weight,
                )
                if weight > 0.0:
                    terms.append(
                        UsageObjectiveTerm(
                            resource_key=rk,
                            window_start=ws,
                            window_end=we,
                            weight=weight,
                            variable_name=self._var_name(
                                resource_key=rk,
                                window_start=ws,
                                window_end=we,
                            ),
                        )
                    )
        return tuple(terms)

    def objective_name_for(
        self,
        resource_key: str,
    ) -> str:
        """生成资源特定的目标函数名称。

        Generate resource-specific objective function name.

        Args:
            resource_key: 资源标识。/ Resource identifier.

        Returns:
            目标函数名称。/ Objective function name.
        """
        return f"{self.objective_name}_{resource_key}"

    def _var_name(
        self,
        *,
        resource_key: str,
        window_start: float,
        window_end: float,
    ) -> str:
        """生成变量名称。

        Generate the variable name.

        Args:
            resource_key: 资源标识。/ Resource identifier.
            window_start: 窗口起始。/ Window start.
            window_end: 窗口结束。/ Window end.

        Returns:
            变量名称字符串。/ Variable name string.
        """
        return f"usage_{resource_key}_{window_start}_{window_end}"
