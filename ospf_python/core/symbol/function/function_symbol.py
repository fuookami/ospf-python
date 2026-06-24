"""函数符号基类 / Function symbol base class."""

from __future__ import annotations

import abc
from dataclasses import dataclass


@dataclass(frozen=True)
class FunctionSymbol(abc.ABC):
    """函数符号抽象基类 / Abstract base class for function symbols.

    所有函数符号的公共接口，每个符号携带名称并可求值。
    Common interface for all function symbols. Each symbol
    carries a name and can be evaluated.

    Attributes:
        name: 函数符号名称 / Function symbol name.
    """

    name: str
    """函数符号名称 / Function symbol name."""

    @abc.abstractmethod
    def evaluate(self, args: tuple[float, ...]) -> float:
        """求值 / Evaluate.

        Args:
            args: 实参元组 / Argument tuple.

        Returns:
            求值结果 / Evaluation result.
        """

    def __str__(self) -> str:
        return self.name
