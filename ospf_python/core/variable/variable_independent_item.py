"""独立变量项 / Independent variable item."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.variable.abstract_variable_item import (
    AbstractVariableItem,
)
from ospf_python.core.variable.type import VariableType
from ospf_python.core.variable.variable_range import VariableRange


@dataclass(frozen=True)
class VariableIndependentItem(AbstractVariableItem):
    """独立变量项 / Independent variable item.

    表示优化模型中的独立决策变量。
    Represents an independent decision variable in an
    optimization model.

    Attributes:
        name: 变量名称 / Variable name.
        type: 变量类型 / Variable type.
        index: 变量索引 / Variable index.
        bounds: 变量取值范围 / Variable value range.
    """

    bounds: VariableRange = VariableRange()
    """变量取值范围 / Variable value range."""

    def is_binary(self) -> bool:
        """判断是否为二元变量 / Check if binary.

        Returns:
            是否为二元变量 / Whether the variable is binary.
        """
        return self.type is VariableType.BINARY

    def is_integer(self) -> bool:
        """判断是否为整数变量 / Check if integer.

        Returns:
            是否为整数变量 / Whether the variable is integer.
        """
        return self.type in (
            VariableType.INTEGER,
            VariableType.BINARY,
            VariableType.SEMI_INTEGER,
        )

    def is_continuous(self) -> bool:
        """判断是否为连续变量 / Check if continuous.

        Returns:
            是否为连续变量 / Whether the variable is continuous.
        """
        return self.type is VariableType.CONTINUOUS
