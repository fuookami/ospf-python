"""转换为多项式。

Convert various representations to polynomial form.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")
U = TypeVar("U")


@dataclass(frozen=True)
class ToPolynomial(Generic[T, U]):
    """多项式转换器。

    Converts various representations (matrix, dict, list)
    to polynomial form.

    Attributes:
        factory: 目标多项式工厂。/ Target factory.
    """

    factory: type[T]

    def from_dict(
        self,
        data: dict[str, float],
    ) -> T:
        """从字典（变量名 -> 系数）创建多项式。

        Create polynomial from dict (variable -> coeff).

        Args:
            data: 系数字典。/ Coefficient dict.

        Returns:
            多项式。/ Polynomial.
        """
        # TODO: 实现转换逻辑
        # TODO: implement conversion logic
        raise NotImplementedError

    def from_list(
        self,
        coefficients: list[float],
        variable: str,
    ) -> T:
        """从系数列表创建单变量多项式。

        Create single-variable polynomial from coeff list.

        Args:
            coefficients: 系数列表（低次到高次）。/
                Coefficient list (low to high degree).
            variable: 变量名。/ Variable name.

        Returns:
            多项式。/ Polynomial.
        """
        # TODO: 实现转换逻辑
        # TODO: implement conversion logic
        raise NotImplementedError
