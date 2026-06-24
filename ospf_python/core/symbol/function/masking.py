"""掩码函数符号 / Masking function symbol."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.symbol.function.function_symbol import (
    FunctionSymbol,
)


@dataclass(frozen=True)
class Masking(FunctionSymbol):
    """掩码 / Masking.

    掩码函数符号实现。
    Masking function symbol implementation.

    Attributes:
        name: 函数符号名称 / Function symbol name.
        mask_value: 掩码值 / Mask value.
    """

    name: str = "Masking"
    """函数符号名称 / Function symbol name."""

    mask_value: float = 0.0
    """掩码值 / Mask value."""

    def evaluate(self, args: tuple[float, ...]) -> float:
        """求值 / Evaluate.

        Args:
            args: 实参元组 / Argument tuple.

        Returns:
            求值结果 / Evaluation result.
        """
        if not args:
            return self.mask_value
        if args[0] != 0.0:
            return args[0]
        return self.mask_value

    @staticmethod
    def create(
        *,
        mask_value: float = 0.0,
    ) -> Masking:
        """创建掩码 / Create Masking.

        Args:
            mask_value: 掩码值 / Mask value.

        Returns:
            掩码实例 / Masking instance.
        """
        return Masking(mask_value=mask_value)
