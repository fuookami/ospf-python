"""量符号转换 / Quantity symbol conversion."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.core.token.token import Token


@dataclass(frozen=True)
class QuantitySymbolConversion:
    """量符号转换器 / Quantity symbol converter.

    将物理量或数值量转换为符号表示。
    Converts physical or numerical quantities to symbol
    representations.

    Attributes:
        _scale: 缩放因子 / Scale factor.
        _offset: 偏移量 / Offset.
        _mapping: 量到符号的映射 / Quantity-to-symbol mapping.
    """

    _scale: float = 1.0
    """缩放因子 / Scale factor."""

    _offset: float = 0.0
    """偏移量 / Offset."""

    _mapping: dict[str, Token] = field(default_factory=dict)
    """量到符号的映射 / Quantity-to-symbol mapping."""

    def convert_value(
        self,
        value: float,
    ) -> float:
        """转换数值 / Convert value.

        Args:
            value: 输入值 / Input value.

        Returns:
            转换后的值 / Converted value.
        """
        return value * self._scale + self._offset

    def register_quantity(
        self,
        quantity_name: str,
        token: Token,
    ) -> None:
        """注册量符号映射 / Register quantity-symbol mapping.

        Args:
            quantity_name: 量名称 / Quantity name.
            token: 对应符号 / Corresponding token.
        """
        self._mapping[quantity_name] = token

    def resolve_quantity(
        self,
        quantity_name: str,
    ) -> Token | None:
        """解析量名称到符号 / Resolve quantity name to symbol.

        Args:
            quantity_name: 量名称 / Quantity name.

        Returns:
            对应符号或 None / Corresponding token or None.
        """
        return self._mapping.get(quantity_name)

    @property
    def registered_count(self) -> int:
        """获取已注册数量 / Get registered count.

        Returns:
            已注册量数量 / Number of registered quantities.
        """
        return len(self._mapping)

    @staticmethod
    def create(
        *,
        scale: float = 1.0,
        offset: float = 0.0,
    ) -> QuantitySymbolConversion:
        """创建量符号转换器 / Create quantity symbol converter.

        Args:
            scale: 缩放因子 / Scale factor.
            offset: 偏移量 / Offset.

        Returns:
            转换器实例 / Converter instance.
        """
        return QuantitySymbolConversion(
            _scale=scale,
            _offset=offset,
        )
