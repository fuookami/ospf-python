"""模型视图 / Model view.

提供模型约束和目标函数的只读视图。
Provides read-only views of model constraints
and objectives.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ModelView:
    """模型视图 / Model view.

    冻结数据类，保存模型中约束和目标函数的只读视图。
    A frozen dataclass holding read-only views of constraints
    and objectives within a model.

    Attributes:
        constraint_views: 约束视图列表 / List of constraint views.
        objective_views: 目标函数视图列表 / List of objective views.
    """

    constraint_views: tuple[object, ...] = field(
        default_factory=tuple,
    )
    objective_views: tuple[object, ...] = field(
        default_factory=tuple,
    )
