"""注册状态枚举 / Registration status enumeration.

定义模型元素注册操作的可能结果。
Defines the possible outcomes of model element
registration operations.
"""

from __future__ import annotations

import enum


class RegistrationStatus(enum.Enum):
    """注册状态 / Registration status.

    表示向模型注册变量、约束或目标函数的结果。
    Represents the result of registering a variable,
    constraint, or objective with a model.

    Attributes:
        value: 状态整数值 / The integer status value.
    """

    REGISTERED = 0
    """注册成功 / Successfully registered."""

    ALREADY_EXISTS = 1
    """已存在 / Already exists."""

    NOT_FOUND = 2
    """未找到 / Not found."""
