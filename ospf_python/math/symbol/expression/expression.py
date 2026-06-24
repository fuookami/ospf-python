"""表达式基类。

Expression base class.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Expression(ABC):
    """所有表达式的抽象基类。

    Abstract base class for all expressions.

    表达式树由节点组成，每个节点可通过绑定求值。
    An expression tree consists of nodes, each evaluable via bindings.
    """

    @abstractmethod
    def evaluate(self, bindings: dict[str, Any]) -> Any:
        """根据绑定求值。

        Evaluate the expression given variable bindings.

        Args:
            bindings: 变量名到值的映射。/ Variable name to value mapping.

        Returns:
            表达式的计算结果。/ Computed result of the expression.
        """

    def __repr__(self) -> str:
        """开发者友好的字符串表示。

        Developer-friendly string representation.
        """
        return f"{type(self).__name__}()"
