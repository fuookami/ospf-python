"""二次四元组中间模型 / Quadratic tetrad intermediate model.

表示二次规划问题的中间表示形式。
Represents an intermediate representation of a
quadratic programming problem.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class QuadraticTetradModel:
    """二次四元组中间模型 / Quadratic tetrad intermediate model.

    以字典形式存储二次规划的线性和二次约束矩阵及边界信息。
    Stores the linear and quadratic constraint matrices and
    bound information of a quadratic program in dictionary form.

    Attributes:
        name: 模型名称 / The model name.
        variables: 变量名列表 / List of variable names.
        linear_constraints: 线性约束映射 / Linear constraint
            mapping.
        quadratic_constraints: 二次约束映射 / Quadratic
            constraint mapping.
        objective: 目标函数系数字典 / Objective function
            coefficient dictionary.
        lower_bounds: 变量下界 / Variable lower bounds.
        upper_bounds: 变量上界 / Variable upper bounds.
        rhs: 约束右端项 / Constraint right-hand side values.
        sense: 约束方向 / Constraint senses.
    """

    name: str = ""
    variables: list[str] = field(default_factory=list)
    linear_constraints: dict[str, dict[str, float]] = field(
        default_factory=dict,
    )
    quadratic_constraints: dict[str, dict[tuple[str, str], float]] = field(
        default_factory=dict
    )
    objective: dict[str, float] = field(default_factory=dict)
    lower_bounds: dict[str, float] = field(default_factory=dict)
    upper_bounds: dict[str, float] = field(default_factory=dict)
    rhs: dict[str, float] = field(default_factory=dict)
    sense: dict[str, str] = field(default_factory=dict)
