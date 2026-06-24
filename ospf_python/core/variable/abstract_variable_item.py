"""抽象变量项 / Abstract variable item."""

from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.core.variable.type import VariableType


@dataclass(frozen=True)
class AbstractVariableItem(abc.ABC):
    """变量项抽象基类 / Abstract base class for variable items.

    所有变量类型的公共接口。每个变量项包含名称、类型和索引。
    Common interface for all variable types. Each variable item
    carries a name, type, and index.

    Attributes:
        name: 变量名称 / Variable name.
        type: 变量类型 / Variable type.
        index: 变量索引 / Variable index.
    """

    name: str
    """变量名称 / Variable name."""

    type: VariableType
    """变量类型 / Variable type."""

    index: int
    """变量索引 / Variable index."""

    def __str__(self) -> str:
        return f"{self.name}[{self.index}]({self.type.value})"
