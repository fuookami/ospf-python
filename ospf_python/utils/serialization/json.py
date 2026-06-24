"""JSON 命名策略 / JSON naming policy.

提供 JSON 序列化/反序列化时的键名转换策略。
Provides key name transformation policies for JSON
serialization/deserialization.
"""

from __future__ import annotations

from typing import Any

from ospf_python.utils.meta_programming.name_transfer import NameTransfer
from ospf_python.utils.meta_programming.naming_system import NamingSystem


class JsonNamingPolicy:
    """JSON 命名策略 / JSON naming policy.

    在 JSON 序列化和反序列化时，按指定命名系统转换键名。
    Transforms JSON key names according to a specified naming
    system during serialization and deserialization.

    Attributes:
        _transfer: 名称转换器 / The name transfer converter.
        _source_system: 源命名系统 / The source naming system.
        _target_system: 目标命名系统 / The target naming system.
    """

    def __init__(
        self,
        *,
        source: NamingSystem = NamingSystem.SNAKE_CASE,
        target: NamingSystem = NamingSystem.CAMEL_CASE,
    ) -> None:
        """初始化 JSON 命名策略 / Initialize the JSON naming policy.

        Args:
            source: 源命名系统 / The source naming system.
            target: 目标命名系统 / The target naming system.
        """
        self._transfer = NameTransfer()
        self._source_system = source
        self._target_system = target

    def apply_to_keys(self, data: dict[str, Any]) -> dict[str, Any]:
        """对字典键名应用命名策略 / Apply the naming policy to
        dictionary keys.

        递归处理嵌套字典和列表。
        Recursively handles nested dictionaries and lists.

        Args:
            data: 待转换的字典 / The dictionary to transform.

        Returns:
            键名已转换的字典 / The dictionary with transformed keys.
        """
        result: dict[str, Any] = {}
        for key, value in data.items():
            new_key = self._convert_key(key)
            result[new_key] = self._transform_value(value)
        return result

    def _convert_key(self, key: str) -> str:
        """转换键名 / Convert a key name.

        Args:
            key: 原始键名 / The original key name.

        Returns:
            转换后的键名 / The converted key name.
        """
        if self._target_system is NamingSystem.SNAKE_CASE:
            return self._transfer.to_snake(key)
        if self._target_system is NamingSystem.CAMEL_CASE:
            return self._transfer.to_camel(key)
        if self._target_system is NamingSystem.PASCAL_CASE:
            return self._transfer.to_pascal(key)
        return key

    def _transform_value(self, value: Any) -> Any:
        """递归转换值 / Recursively transform values.

        Args:
            value: 待转换的值 / The value to transform.

        Returns:
            转换后的值 / The transformed value.
        """
        if isinstance(value, dict):
            return self.apply_to_keys(value)
        if isinstance(value, list):
            return [self._transform_value(item) for item in value]
        return value

    @staticmethod
    def camel_case() -> JsonNamingPolicy:
        """创建 snake_case 到 camelCase 的策略 / Create a
        snake_case to camelCase policy."""
        return JsonNamingPolicy(
            source=NamingSystem.SNAKE_CASE,
            target=NamingSystem.CAMEL_CASE,
        )

    @staticmethod
    def snake_case() -> JsonNamingPolicy:
        """创建 camelCase 到 snake_case 的策略 / Create a
        camelCase to snake_case policy."""
        return JsonNamingPolicy(
            source=NamingSystem.CAMEL_CASE,
            target=NamingSystem.SNAKE_CASE,
        )

    @staticmethod
    def pascal_case() -> JsonNamingPolicy:
        """创建 snake_case 到 PascalCase 的策略 / Create a
        snake_case to PascalCase policy."""
        return JsonNamingPolicy(
            source=NamingSystem.SNAKE_CASE,
            target=NamingSystem.PASCAL_CASE,
        )
