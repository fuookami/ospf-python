"""列绑定器 / Column binder.

提供数据库列与模型字段的绑定机制。
Provides binding mechanism between database columns and model fields.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ColumnBinder:
    """列绑定器 / Column binder.

    定义数据库列名与模型属性名之间的映射关系。
    Defines the mapping between database column names
    and model property names.

    Attributes:
        column_name: 数据库列名 / The database column name.
        field_name: 模型字段名 / The model field name.
        is_primary: 是否为主键 / Whether this is a primary key.
    """

    column_name: str
    field_name: str
    is_primary: bool = False
