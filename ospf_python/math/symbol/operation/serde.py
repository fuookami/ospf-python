"""多项式序列化/反序列化。

Polynomial serialization and deserialization operations.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from ospf_python.math.symbol.monomial.canonical_monomial import (
    CanonicalMonomial,
)
from ospf_python.math.symbol.polynomial.canonical_polynomial import (
    CanonicalPolynomial,
)
from ospf_python.math.symbol.symbol import Symbol

T = TypeVar("T")


def _monomial_to_dict(term: CanonicalMonomial) -> dict[str, Any]:
    """单项式转字典。

    Convert monomial to dictionary for serialization.

    Args:
        term: 单项式。/ Monomial.

    Returns:
        字典表示。/ Dictionary representation.
    """
    symbols = [
        {"name": sym.name, "index": sym.index, "display_name": sym.display_name, "power": pow_val}
        for sym, pow_val in term.powers.items()
    ]
    return {"coefficient": term.coefficient, "symbols": symbols}


def _dict_to_monomial(data: dict[str, Any]) -> CanonicalMonomial:
    """字典转单项式。

    Convert dictionary to monomial for deserialization.

    Args:
        data: 字典表示。/ Dictionary representation.

    Returns:
        单项式。/ Monomial.
    """
    coefficient = data["coefficient"]
    powers: dict[Symbol, int] = {}
    for sym_data in data.get("symbols", []):
        # Symbol 只有 name 和 index，display_name 是计算属性
        # Symbol only has name and index; display_name is a computed property
        symbol = Symbol(
            name=sym_data["name"],
            index=sym_data["index"],
        )
        powers[symbol] = sym_data["power"]
    return CanonicalMonomial(coefficient=coefficient, powers=powers)


@dataclass(frozen=True)
class SerdeOps(Generic[T]):
    """序列化/反序列化操作集。

    Collection of serialization and deserialization
    operations.

    Attributes:
        factory: 多项式工厂类型。/ Polynomial factory type.
    """

    factory: type[T]

    def serialize(self, polynomial: T) -> str:
        """将多项式序列化为 JSON 字符串。

        Serialize polynomial to JSON string.

        Args:
            polynomial: 输入多项式。/ Input polynomial.

        Returns:
            JSON 字符串。/ JSON string.
        """
        if isinstance(polynomial, CanonicalPolynomial):
            terms = [_monomial_to_dict(term) for term in polynomial.terms]
            return json.dumps({"terms": terms}, ensure_ascii=False)

        raise TypeError(f"Unsupported polynomial type: {type(polynomial)}")

    def deserialize(self, data: str) -> T | None:
        """从 JSON 字符串反序列化多项式。

        Deserialize polynomial from JSON string.

        Args:
            data: JSON 字符串。/ JSON string.

        Returns:
            反序列化结果或 None。/
            Deserialized polynomial or None.
        """
        if self.factory is CanonicalPolynomial:
            try:
                obj = json.loads(data)
            except (json.JSONDecodeError, TypeError):
                return None  # justified: invalid JSON

            if not isinstance(obj, dict) or "terms" not in obj:
                return None  # justified: invalid format

            try:
                terms = [_dict_to_monomial(t) for t in obj["terms"]]
            except (KeyError, TypeError):
                return None  # justified: parse error

            if not terms:
                return CanonicalPolynomial.zero()  # type: ignore[return-value]

            return CanonicalPolynomial(terms=terms)  # type: ignore[return-value]

        raise TypeError(f"Unsupported factory type: {self.factory}")

    def to_dict(self, polynomial: T) -> dict[str, Any] | None:
        """将多项式转为字典。

        Convert polynomial to dictionary.

        Args:
            polynomial: 输入多项式。/ Input polynomial.

        Returns:
            字典表示或 None。/ Dictionary or None.
        """
        if isinstance(polynomial, CanonicalPolynomial):
            terms = [_monomial_to_dict(term) for term in polynomial.terms]
            return {"terms": terms}
        return None  # justified: unsupported type

    def from_dict(self, data: dict[str, Any]) -> T | None:
        """从字典反序列化多项式。

        Deserialize polynomial from dictionary.

        Args:
            data: 字典表示。/ Dictionary.

        Returns:
            反序列化结果或 None。/
            Deserialized polynomial or None.
        """
        if self.factory is CanonicalPolynomial:
            if "terms" not in data:
                return None  # justified: missing key
            try:
                terms = [_dict_to_monomial(t) for t in data["terms"]]
            except (KeyError, TypeError):
                return None  # justified: parse error
            if not terms:
                return CanonicalPolynomial.zero()  # type: ignore[return-value]
            return CanonicalPolynomial(terms=terms)  # type: ignore[return-value]
        return None  # justified: unsupported factory
