"""规范化模型 / Normalized models.

定义远程求解的规范化数据模型。
Defines normalized data models for remote solving.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class NormalizedModel:
    """规范化模型 / Normalized model.

    求解器无关的标准化模型表示。
    A solver-agnostic standardized model representation.

    Attributes:
        variables: 变量列表 / The variable list.
        constraints: 约束列表 / The constraint list.
        objective: 目标函数 / The objective function.
    """

    variables: tuple[dict[str, Any], ...]
    constraints: tuple[dict[str, Any], ...]
    objective: dict[str, Any]


@dataclass(frozen=True)
class NormalizedResult:
    """规范化结果 / Normalized result.

    求解器无关的标准化结果表示。
    A solver-agnostic standardized result representation.

    Attributes:
        status: 求解状态 / The solve status.
        objective_value: 目标函数值 / The objective value.
        variable_values: 变量值映射 / The variable value mapping.
    """

    status: str
    objective_value: float
    variable_values: dict[str, float]
