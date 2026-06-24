"""模型对象 / Model object.

定义模型中的通用对象结构。
Defines the generic object structure in a model.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.core.model.basic.object_category import (
        ObjectCategory,
    )


@dataclass(frozen=True)
class Object:
    """模型对象 / Model object.

    表示模型中的一个通用对象，可以是变量、约束或目标函数。
    Represents a generic object in a model, which can be a
    variable, constraint, or objective.

    Attributes:
        name: 对象名称 / The object name.
        category: 对象类别 / The object category.
        index: 对象索引 / The object index.
    """

    name: str
    category: ObjectCategory
    index: int = -1
