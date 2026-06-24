"""持久化字段解析器 / Persistence field resolver.

解析模型字段到持久化存储的映射。
Resolves model field mappings to persistent storage.
"""

from __future__ import annotations

import abc
from typing import Any


class PersistenceFieldResolver(abc.ABC):
    """持久化字段解析器 / Persistence field resolver.

    提供模型字段到持久化列的解析能力。
    Provides resolution capability from model fields
    to persistence columns.
    """

    @abc.abstractmethod
    def resolve_column(self, field_name: str) -> str:
        """解析字段对应的列名 / Resolve column name for field.

        Args:
            field_name: 模型字段名 / The model field name.

        Returns:
            对应的数据库列名 / The corresponding database column name.
        """
        ...

    @abc.abstractmethod
    def resolve_value(
        self,
        field_name: str,
        value: Any,
    ) -> Any:
        """解析字段值 / Resolve field value.

        Args:
            field_name: 模型字段名 / The model field name.
            value: 原始值 / The raw value.

        Returns:
            转换后的持久化值 / The converted persistence value.
        """
        ...
