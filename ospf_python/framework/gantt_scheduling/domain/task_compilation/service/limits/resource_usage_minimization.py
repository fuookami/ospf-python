"""资源使用量最小化 / Resource usage minimization.

生成最小化资源使用量的目标函数数据。
Generates objective function data for minimizing
resource usage.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceUsageObjectiveTerm:
    """资源使用量目标函数项 / Resource usage objective term.

    Attributes:
        resource_key: 资源标识 / Resource identifier.
        window_start: 时间窗口起始 / Window start.
        window_end: 时间窗口结束 / Window end.
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
    的资源产能。
    Builds objective function terms for minimizing resource
    usage, encouraging scheduling plans that consume less
    resource capacity.

    Attributes:
        objective_name: 目标函数名称 / Objective name.
        default_weight: 默认权重 / Default weight.
    """

    objective_name: str = "resource_usage_min"
    default_weight: float = 1.0

    def build_objective_terms(
        self,
        resource_keys: tuple[str, ...],
        time_windows: tuple[tuple[float, float], ...],
        weights: dict[tuple[str, float, float], float] | None = None,
    ) -> tuple[ResourceUsageObjectiveTerm, ...]:
        """构建目标函数项。

        Build objective function terms.

        Args:
            resource_keys: 资源标识列表 / Resource key list.
            time_windows: 时间窗口列表 / Time window list.
            weights: 自定义权重映射 / Custom weight mapping.

        Returns:
            目标函数项元组。/ Tuple of objective terms.
        """
        effective_weights = weights or {}
        terms: list[ResourceUsageObjectiveTerm] = []
        for rk in resource_keys:
            for ws, we in time_windows:
                key = (rk, ws, we)
                weight = effective_weights.get(
                    key,
                    self.default_weight,
                )
                if weight > 0.0:
                    terms.append(
                        ResourceUsageObjectiveTerm(
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
        """生成资源特定的目标函数名称。"""
        return f"{self.objective_name}_{resource_key}"

    def _var_name(
        self,
        *,
        resource_key: str,
        window_start: float,
        window_end: float,
    ) -> str:
        """生成变量名称。"""
        return f"usage_{resource_key}_{window_start}_{window_end}"
