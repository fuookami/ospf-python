"""命名系统枚举 / Naming system enumeration.

对应 Kotlin 端 NamingSystem enum。
Mirrors the Kotlin NamingSystem enum.
"""

from __future__ import annotations

import enum


class NamingSystem(enum.Enum):
    """命名系统枚举 / Naming system enumeration.

    定义代码中常用的命名风格。
    Defines common naming conventions used in code.

    Attributes:
        value: 命名风格名称 / The naming style name.
    """

    CAMEL_CASE = "camelCase"
    """驼峰命名（小驼峰） / Camel case (lower camelCase)."""

    SNAKE_CASE = "snake_case"
    """蛇形命名 / Snake case."""

    PASCAL_CASE = "PascalCase"
    """帕斯卡命名（大驼峰） / Pascal case (upper CamelCase)."""
