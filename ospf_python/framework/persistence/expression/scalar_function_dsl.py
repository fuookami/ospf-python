"""标量函数 DSL / Scalar function DSL.

定义持久化层标量函数的 DSL 接口。
Defines the DSL interface for persistence layer scalar functions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ScalarFunctionDsl:
    """标量函数 DSL / Scalar function DSL.

    描述持久化查询中使用的标量函数调用。
    Describes scalar function calls used in persistence queries.

    Attributes:
        function_name: 函数名称 / The function name.
        arguments: 函数参数 / The function arguments.
        alias: 结果别名 / The result alias.
    """

    function_name: str
    arguments: tuple[Any, ...] = ()
    alias: str = ""
