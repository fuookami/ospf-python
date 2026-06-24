"""子对象 / Sub-object.

定义模型对象的子对象结构。
Defines the sub-object structure of model objects.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SubObject:
    """子对象 / Sub-object.

    表示模型对象的组成部分，如约束中的一个项。
    Represents a component of a model object, such as
    a term in a constraint.

    Attributes:
        parent: 父对象名称 / The parent object name.
        name: 子对象名称 / The sub-object name.
        coefficient: 系数 / The coefficient.
    """

    parent: str
    name: str
    coefficient: float = 1.0
