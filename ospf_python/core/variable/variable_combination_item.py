"""组合变量项 / Combination variable item."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.variable.abstract_variable_item import (
    AbstractVariableItem,
)
from ospf_python.core.variable.type import VariableType


@dataclass(frozen=True)
class VariableCombinationItem(AbstractVariableItem):
    """组合变量项 / Combination variable item.

    表示由多个变量组合而成的复合变量。
    Represents a composite variable formed by combining
    multiple variables.

    Attributes:
        name: 变量名称 / Variable name.
        type: 变量类型 / Variable type.
        index: 变量索引 / Variable index.
        component_indices: 组成变量的索引列表 / List of
            component variable indices.
    """

    component_indices: tuple[int, ...] = ()
    """组成变量的索引列表 / Component variable indices."""

    @property
    def component_count(self) -> int:
        """获取组成变量数量 / Get component count.

        Returns:
            组成变量数量 / Number of components.
        """
        return len(self.component_indices)

    def has_component(self, index: int) -> bool:
        """判断是否包含指定组件 / Check if contains component.

        Args:
            index: 变量索引 / Variable index.

        Returns:
            是否包含 / Whether the component is present.
        """
        return index in self.component_indices

    @staticmethod
    def from_indices(
        *,
        name: str,
        index: int,
        component_indices: tuple[int, ...],
        type_: VariableType = VariableType.CONTINUOUS,
    ) -> VariableCombinationItem:
        """从索引列表创建组合变量 / Create from indices.

        Args:
            name: 变量名称 / Variable name.
            index: 变量索引 / Variable index.
            component_indices: 组成变量索引 / Component indices.
            type_: 变量类型，默认连续 / Variable type, default
                continuous.

        Returns:
            组合变量实例 / Combination variable instance.
        """
        return VariableCombinationItem(
            name=name,
            type=type_,
            index=index,
            component_indices=tuple(component_indices),
        )
