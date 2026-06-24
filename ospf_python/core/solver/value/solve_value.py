"""求解值 / Solve value.

封装求解器返回的变量值映射。
Encapsulates variable value mappings returned by solvers.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SolveValue:
    """求解值 / Solve value.

    冻结数据类，存储变量名到浮点值的映射。
    Frozen dataclass storing variable-name-to-float mappings.

    Attributes:
        values: 变量值映射 / Variable value mapping.
    """

    values: dict[str, float] = field(
        default_factory=dict,
    )
    """变量值映射 / Variable value mapping."""

    def get(
        self,
        name: str,
        default: float = 0.0,
    ) -> float:
        """获取指定变量的值 / Get the value of a variable.

        Args:
            name: 变量名称 / Variable name.
            default: 默认值 / Default value.

        Returns:
            变量值 / The variable value.
        """
        return self.values.get(name, default)

    @property
    def variable_names(self) -> tuple[str, ...]:
        """获取所有变量名 / Get all variable names.

        Returns:
            变量名元组 / Tuple of variable names.
        """
        return tuple(self.values)

    @property
    def is_empty(self) -> bool:
        """是否为空 / Whether empty.

        Returns:
            无变量值时返回 True / True when no values.
        """
        return len(self.values) == 0
