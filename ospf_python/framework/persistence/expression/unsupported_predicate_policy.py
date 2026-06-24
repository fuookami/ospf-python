"""不支持谓词策略 / Unsupported predicate policy.

定义遇到不支持的谓词时的处理策略。
Defines handling policies for unsupported predicates.
"""

from __future__ import annotations

import enum


class UnsupportedPredicatePolicy(enum.Enum):
    """不支持谓词策略 / Unsupported predicate policy.

    当持久化层遇到无法处理的谓词时，决定如何响应。
    Determines how to respond when the persistence layer
    encounters a predicate it cannot handle.

    Attributes:
        value: 策略值 / The policy value.
    """

    IGNORE = 0
    """忽略 / Ignore.

    跳过不支持的谓词。
    Skips unsupported predicates.
    """

    WARN = 1
    """警告 / Warn.

    记录警告并跳过。
    Logs a warning and skips.
    """

    ERROR = 2
    """报错 / Error.

    抛出异常终止操作。
    Raises an exception to abort the operation.
    """
