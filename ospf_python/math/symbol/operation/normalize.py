"""多项式规范化。

Normalize polynomial expressions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from ospf_python.math.symbol.operation.canonical_ops import CanonicalOps
from ospf_python.math.symbol.polynomial.canonical_polynomial import (
    CanonicalPolynomial,
)

T = TypeVar("T")


@dataclass(frozen=True)
class PolynomialNormalizer(Generic[T]):
    """多项式规范器。

    Normalizes polynomial expressions into a canonical
    form.

    Attributes:
        factory: 多项式工厂类型。/ Polynomial factory type.
    """

    factory: type[T]

    def normalize(self, polynomial: T) -> T:
        """规范化多项式。

        Normalize the polynomial to canonical form:
        combine like terms, remove zeros, sort by degree.

        规范化步骤：合并同类项、移除零系数项、按次数降序排列。

        Args:
            polynomial: 输入多项式。/ Input polynomial.

        Returns:
            规范化后的多项式。/ Normalized polynomial.
        """
        if isinstance(polynomial, CanonicalPolynomial):
            ops = CanonicalOps(factory=CanonicalPolynomial)
            return ops.normalize(polynomial)  # type: ignore[return-value]

        raise TypeError(f"Unsupported polynomial type: {type(polynomial)}")

    def is_normalized(self, polynomial: T) -> bool:
        """检查多项式是否已规范化。

        Check if polynomial is already normalized.

        已规范化意味着：
        1. 无重复幂次键的同类项
        2. 无零系数项
        3. 按次数降序排列

        Normalized means:
        1. No like terms with duplicate power keys
        2. No zero-coefficient terms
        3. Sorted by degree descending

        Args:
            polynomial: 输入多项式。/ Input polynomial.

        Returns:
            是否已规范化。/ Whether normalized.
        """
        if isinstance(polynomial, CanonicalPolynomial):
            # 检查零系数项 / Check for zero-coefficient terms
            for term in polynomial.terms:
                if abs(term.coefficient) < 1e-15:
                    return False

            # 检查重复幂次键（同类项未合并）
            # Check for duplicate power keys (uncombined like terms)
            seen_power_keys: set[tuple[tuple[str, int], ...]] = set()
            for term in polynomial.terms:
                # 将幂次映射转为可哈希的排序元组
                # Convert powers dict to hashable sorted tuple
                key = tuple(
                    sorted((sym.name, pow_val) for sym, pow_val in term.powers.items())
                )
                if key in seen_power_keys:
                    return False
                seen_power_keys.add(key)

            # 检查次数降序 / Check degree descending order
            for i in range(len(polynomial.terms) - 1):
                if polynomial.terms[i].degree < polynomial.terms[i + 1].degree:
                    return False

            return True  # justified: polynomial passes all normalization checks

        raise TypeError(f"Unsupported polynomial type: {type(polynomial)}")
