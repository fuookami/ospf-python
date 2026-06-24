"""线性三元组中间模型 / Linear triad intermediate model.

表示线性规划问题的中间表示形式。
Represents an intermediate representation of a
linear programming problem.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LinearTriadModel:
    """线性三元组中间模型 / Linear triad intermediate model.

    以字典形式存储线性规划的约束矩阵和边界信息。
    Stores the constraint matrix and bound information of
    a linear program in dictionary form.

    Attributes:
        name: 模型名称 / The model name.
        variables: 变量名列表 / List of variable names.
        constraints: 约束名到系数字典的映射 / Mapping from
            constraint names to coefficient dictionaries.
        objective: 目标函数系数字典 / Objective function
            coefficient dictionary.
        lower_bounds: 变量下界 / Variable lower bounds.
        upper_bounds: 变量上界 / Variable upper bounds.
        rhs: 约束右端项 / Constraint right-hand side values.
        sense: 约束方向 / Constraint senses.
    """

    name: str = ""
    variables: list[str] = field(default_factory=list)
    constraints: dict[str, dict[str, float]] = field(
        default_factory=dict,
    )
    objective: dict[str, float] = field(default_factory=dict)
    lower_bounds: dict[str, float] = field(default_factory=dict)
    upper_bounds: dict[str, float] = field(default_factory=dict)
    rhs: dict[str, float] = field(default_factory=dict)
    sense: dict[str, str] = field(default_factory=dict)
