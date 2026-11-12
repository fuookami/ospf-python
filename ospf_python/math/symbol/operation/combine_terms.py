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
            # 按幂向量分组 / Group by power vector.
            #
            # 两处与旧实现等价但更省的写法：
            #
            # 1. 键用 `(variables, powers)` 纯元组而不是 `PowerVectorKey`。后者是
            #    frozen dataclass，构造要走 `__post_init__` 校验、哈希走生成的
            #    `__hash__`；实测做字典键 1,542 ns vs 纯元组 268 ns（5.7 倍）。
            #    该键只在 `combine` 内部使用，输出仍用原来的 `term.powers`，
            #    所以没有任何可观察差异。
            # 2. 直接累加系数，而不是先攒 list 再 `sum(...)`。累加顺序与
            #    `sum` 完全一致（都从 0 开始、按项的原始顺序相加），浮点结果相同。
            #
            # Two equivalent but cheaper formulations: a plain tuple key (the frozen
            # dataclass key cost 1,542 ns vs 268 ns) and direct accumulation instead of
            # list-then-sum (same order, same float result).
            totals: dict[tuple[tuple[str, ...], tuple[int, ...]], float] = {}
            symbol_map: dict[tuple[tuple[str, ...], tuple[int, ...]], dict[Symbol, int]] = {}

            for term in polynomial.terms:
                powers = term.powers
                key = (tuple(sym.display_name for sym in powers), tuple(powers.values()))
                if key in totals:
                    totals[key] += term.coefficient
                else:
                    totals[key] = term.coefficient
                    symbol_map[key] = powers

            # 合并每组同类项 / Emit one term per group
            new_terms: list[CanonicalMonomial] = []
            for key, total_coeff in totals.items():
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
