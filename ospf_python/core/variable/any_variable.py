"""通用变量 / Generic variable with bounds."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.variable.abstract_variable_item import (
    AbstractVariableItem,
)
from ospf_python.core.variable.type import VariableType
from ospf_python.core.variable.variable_range import VariableRange


@dataclass(frozen=True)
class AnyVariable(AbstractVariableItem):
    """通用变量 / Generic variable with bounds.

    支持任意变量类型，附带取值范围。
    Supports any variable type with an associated value range.

    Attributes:
        name: 变量名称 / Variable name.
        type: 变量类型 / Variable type.
        index: 变量索引 / Variable index.
        bounds: 变量取值范围 / Variable value range.
    """

    bounds: VariableRange = VariableRange()
    """变量取值范围 / Variable value range."""

    @staticmethod
    def continuous(
        *,
        name: str,
        index: int,
        lower: float = float("-inf"),
        upper: float = float("inf"),
    ) -> AnyVariable:
        """创建连续变量 / Create continuous variable.

        Args:
            name: 变量名称 / Variable name.
            index: 变量索引 / Variable index.
            lower: 下界 / Lower bound.
            upper: 上界 / Upper bound.

        Returns:
            连续变量实例 / Continuous variable instance.
        """
        return AnyVariable(
            name=name,
            type=VariableType.CONTINUOUS,
            index=index,
            bounds=VariableRange(lower=lower, upper=upper),
        )

    @staticmethod
    def integer(
        *,
        name: str,
        index: int,
        lower: float = float("-inf"),
        upper: float = float("inf"),
    ) -> AnyVariable:
        """创建整数变量 / Create integer variable.

        Args:
            name: 变量名称 / Variable name.
            index: 变量索引 / Variable index.
            lower: 下界 / Lower bound.
            upper: 上界 / Upper bound.

        Returns:
            整数变量实例 / Integer variable instance.
        """
        return AnyVariable(
            name=name,
            type=VariableType.INTEGER,
            index=index,
            bounds=VariableRange(lower=lower, upper=upper),
        )

    @staticmethod
    def binary(
        *,
        name: str,
        index: int,
    ) -> AnyVariable:
        """创建二元变量 / Create binary variable.

        Args:
            name: 变量名称 / Variable name.
            index: 变量索引 / Variable index.

        Returns:
            二元变量实例 / Binary variable instance.
        """
        return AnyVariable(
            name=name,
            type=VariableType.BINARY,
            index=index,
            bounds=VariableRange(lower=0.0, upper=1.0),
        )
