"""求解值转换上下文 / Solve value conversion context.

封装求解值转换过程中的上下文信息。
Encapsulates context information during solve value
conversion.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ospf_python.core.solver.value.solve_value import (
    SolveValue,
)


@dataclass(frozen=True)
class SolveValueConversionContext:
    """求解值转换上下文 / Solve value conversion context.

    冻结数据类，记录转换过程中的变量映射和默认值。
    Frozen dataclass recording variable mappings and
    defaults during conversion.

    Attributes:
        variable_names: 变量名称列表 / Variable name list.
        default_value: 默认值 / Default value.
        converted: 已转换的值 / Already converted values.
    """

    variable_names: tuple[str, ...] = ()
    """变量名称列表 / Variable name list."""

    default_value: float = 0.0
    """默认值 / Default value."""

    converted: SolveValue = field(
        default_factory=SolveValue,
    )
    """已转换的值 / Already converted values."""

    def build_solve_value(
        self,
        raw_values: dict[str, float],
    ) -> SolveValue:
        """从原始值构建求解值 / Build solve value from raw
        values.

        Args:
            raw_values: 原始变量值 / Raw variable values.

        Returns:
            求解值实例 / Solve value instance.
        """
        merged: dict[str, float] = {}
        for name in self.variable_names:
            merged[name] = raw_values.get(
                name,
                self.default_value,
            )
        return SolveValue(values=merged)
