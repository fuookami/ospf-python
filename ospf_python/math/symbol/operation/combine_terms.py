"""合并同类项。

Combine like terms in polynomial expressions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

from ospf_python.math.symbol.monomial.canonical_monomial import (
    CanonicalMonomial,
)
from ospf_python.math.symbol.operation.power_vector_key import PowerVectorKey
from ospf_python.math.symbol.polynomial.canonical_polynomial import (
    CanonicalPolynomial,
)

if TYPE_CHECKING:
    from ospf_python.math.symbol.symbol import Symbol

T = TypeVar("T")


def _make_power_key(term: CanonicalMonomial) -> PowerVectorKey:
    """从单项式创建幂向量键。

    Create a power vector key from a monomial.

    Args:
        term: 单项式。/ Monomial.

    Returns:
        幂向量键。/ Power vector key.
    """
    symbols = tuple(sym.display_name for sym in term.powers)
    powers = tuple(term.powers.values())
    return PowerVectorKey(variables=symbols, powers=powers)


@dataclass(frozen=True)
class TermCombiner(Generic[T]):
    """同类项合并器。

    Combines like terms in a polynomial expression.

    Attributes:
        factory: 多项式工厂类型。/ Polynomial factory type.
    """

    factory: type[T]

    def combine(self, polynomial: T) -> T:
        """合并多项式中的同类项。

        Combine like terms in the polynomial.

        将相同幂次结构的项合并（系数相加），
        并移除系数为零的项。

        Combines terms with identical power structures
        (adding coefficients) and removes zero-coefficient terms.

        Args:
            polynomial: 输入多项式。/ Input polynomial.

        Returns:
            合并同类项后的多项式。/
            Polynomial with combined terms.
        """
        if isinstance(polynomial, CanonicalPolynomial):
            # 按幂向量键分组 / Group by power vector key
            groups: dict[PowerVectorKey, list[CanonicalMonomial]] = {}
            symbol_map: dict[PowerVectorKey, dict[Symbol, int]] = {}

            for term in polynomial.terms:
                key = _make_power_key(term)
                if key not in groups:
                    groups[key] = []
                    symbol_map[key] = term.powers
                groups[key].append(term)

            # 合并每组同类项 / Combine each group
            new_terms: list[CanonicalMonomial] = []
            for key, terms in groups.items():
                total_coeff = sum(t.coefficient for t in terms)
                # 跳过系数为零的项 / Skip zero-coefficient terms
                if abs(total_coeff) < 1e-15:
                    continue
                new_terms.append(
                    CanonicalMonomial(
                        coefficient=total_coeff,
                        powers=symbol_map[key],
                    )
                )

            if not new_terms:
                return CanonicalPolynomial.zero()  # type: ignore[return-value]

            return CanonicalPolynomial(terms=new_terms)  # type: ignore[return-value]

        raise TypeError(f"Unsupported polynomial type: {type(polynomial)}")
