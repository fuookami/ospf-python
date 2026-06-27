"""任务容量最小化 / Task volume minimization.

生成最小化任务总容量使用的目标函数数据，减少任务对
资源的总体占用。
Generates objective function data for minimizing total task
volume, reducing overall resource occupation by tasks.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskVolumeObjectiveTerm:
    """任务容量目标函数项 / Task volume objective term.

    表示目标函数中一个任务容量的加权项。
    Represents a weighted term of task volume in the
    objective function.

    Attributes:
        task_key: 任务标识 / Task identifier.
        resource_key: 资源标识 / Resource identifier.
        weight: 权重系数 / Weight coefficient.
        volume: 容量值 / Volume value.
        variable_name: 关联变量名 / Associated variable name.
    """

    task_key: str
    resource_key: str
    weight: float
    volume: float
    variable_name: str


@dataclass(frozen=True)
class TaskVolumeSavingsResult:
    """任务容量节省结果 / Task volume savings result.

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
class TaskVolumeMinimization:
    """任务容量最小化 / Task volume minimization.

    构建最小化任务总容量的目标函数项，鼓励调度方案减少
    任务对资源的总体占用量。适用于希望压缩任务资源消耗、
    降低整体负载的场景。
    Builds objective function terms for minimizing total task
    volume, encouraging scheduling plans that reduce overall
    resource occupation by tasks. Applicable when the goal is
    to compress task resource consumption and lower overall
    load.

    Attributes:
        objective_name: 目标函数名称 / Objective name.
        default_weight: 默认权重 / Default weight.
    """

    objective_name: str = "task_volume_min"
    default_weight: float = 1.0

    def build_objective_terms(
        self,
        task_keys: tuple[str, ...],
        task_volumes: dict[str, float],
        weights: dict[str, float] | None = None,
    ) -> tuple[TaskVolumeObjectiveTerm, ...]:
        """构建目标函数项。

        Build objective function terms for all tasks.

        Args:
            task_keys: 任务标识列表 / Task key list.
            task_volumes: 任务容量映射 / Task volume mapping.
            weights: 自定义权重映射 / Custom weight mapping.

        Returns:
            目标函数项元组。/ Tuple of objective terms.
        """
        effective_weights = weights or {}
        terms: list[TaskVolumeObjectiveTerm] = []
        for tk in task_keys:
            weight = effective_weights.get(
                tk,
                self.default_weight,
            )
            volume = task_volumes.get(tk, 0.0)
            if weight > 0.0 and volume > 0.0:
                terms.append(
                    TaskVolumeObjectiveTerm(
                        task_key=tk,
                        resource_key="",
                        weight=weight,
                        volume=volume,
                        variable_name=self._var_name(tk),
                    )
                )
        return tuple(terms)

    def compute_volume_savings(
        self,
        *,
        original_volumes: dict[str, float],
        optimized_volumes: dict[str, float],
    ) -> TaskVolumeSavingsResult:
        """计算任务容量节省结果。

        Compute task volume savings result.

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
        return TaskVolumeSavingsResult(
            original_volume=original_total,
            optimized_volume=optimized_total,
        )

    def objective_name_for(
        self,
        task_key: str,
    ) -> str:
        """生成任务特定的目标函数名称。

        Generate task-specific objective function name.

        Args:
            task_key: 任务标识。/ Task identifier.

        Returns:
            目标函数名称。/ Objective function name.
        """
        return f"{self.objective_name}_{task_key}"

    def _var_name(self, task_key: str) -> str:
        """生成变量名称。

        Generate the variable name.

        Args:
            task_key: 任务标识。/ Task identifier.

        Returns:
            变量名称字符串。/ Variable name string.
        """
        return f"task_vol_{task_key}"
