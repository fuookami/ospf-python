"""值提供器。

Value provider for polynomial evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class ValueProvider(Protocol):
    """值提供器协议。

    Protocol for providing variable values during
    polynomial evaluation.
    """

    def get(self, name: str) -> float:
        """获取变量值。

        Get variable value.

        Args:
            name: 变量名。/ Variable name.

        Returns:
            变量值。/ Variable value.
        """
        ...


@dataclass(frozen=True)
class DictValueProvider:
    """字典值提供器。

    Value provider backed by a dictionary.

    Attributes:
        bindings: 变量绑定字典。/ Variable bindings.
    """

    bindings: dict[str, float]

    def get(self, name: str) -> float:
        """获取变量值。

        Get variable value.

        Args:
            name: 变量名。/ Variable name.

        Returns:
            变量值。/ Variable value.
        """
        return self.bindings[name]


@dataclass(frozen=True)
class LambdaValueProvider(Generic[T]):
    """Lambda 值提供器。

    Value provider backed by a callable.

    Attributes:
        getter: 获取值的函数。/ Value getter function.
    """

    getter: object

    def get(self, name: str) -> float:
        """获取变量值。

        Get variable value.

        Args:
            name: 变量名。/ Variable name.

        Returns:
            变量值。/ Variable value.
        """
        return self.getter(name)  # type: ignore[operator, no-any-return]
