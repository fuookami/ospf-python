"""大M法函数符号 / BigM function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class BigM(FunctionSymbol):
    """大M法 / BigM.

    大M法函数符号实现。
    BigM function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
        m_value: M值 / M value.
    """

    name: str = "BigM"
    """函数符号名称 / Function symbol name."""

    m_value: float = 1e6
    """M值 / M value."""

    def evaluate(self, args: tuple[float, ...]) -> float:
        """求值 / Evaluate.

        Args:
            args: 实参元组 / Argument tuple.

        Returns:
            求值结果 / Evaluation result.
        """
        if not args:
            return 0.0
        return self.m_value if args[0] != 0.0 else 0.0

    @staticmethod
    def create(
        *,
        m_value: float = 1e6,
    ) -> BigM:
        """创建大M法 / Create BigM.

        Args:
            m_value: M值 / M value.

        Returns:
            大M法实例 / BigM instance.
        """
        return BigM(m_value=m_value)
