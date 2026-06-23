"""Symbolic mathematics module.

Provides symbolic expressions: polynomials, monomials, inequalities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

from ospf_python.math.algebra.number import RealNumber

V = TypeVar("V", bound=RealNumber)


@dataclass(frozen=True, slots=True)
class Monomial:
    """Monomial: coefficient * product of variables raised to powers.

    单项式：系数 * 变量幂次乘积。
    """

    coefficient: float
    variables: tuple[tuple[str, int], ...]  # (name, power) pairs

    def evaluate(self, values: dict[str, float]) -> float:
        """Evaluate monomial.

        Args:
            values: Variable values.

        Returns:
            Evaluated value.
        """
        result = self.coefficient
        for name, power in self.variables:
            result *= values[name] ** power
        return result

    def degree(self) -> int:
        """Get total degree."""
        return sum(power for _, power in self.variables)

    def __add__(self, other: Monomial) -> Polynomial:
        """Add two monomials (returns polynomial)."""
        if self.variables == other.variables:
            return Polynomial(
                [Monomial(self.coefficient + other.coefficient, self.variables)]
            )
        return Polynomial([self, other])

    def __mul__(self, other: Monomial) -> Monomial:
        """Multiply two monomials."""
        # Merge variables
        var_dict = dict(self.variables)
        for name, power in other.variables:
            var_dict[name] = var_dict.get(name, 0) + power
        new_vars = tuple(sorted(var_dict.items()))
        return Monomial(self.coefficient * other.coefficient, new_vars)

    def __repr__(self) -> str:
        """String representation."""
        if not self.variables:
            return str(self.coefficient)
        parts = []
        for name, power in self.variables:
            if power == 1:
                parts.append(name)
            else:
                parts.append(f"{name}^{power}")
        var_str = " * ".join(parts)
        if self.coefficient == 1:
            return var_str
        return f"{self.coefficient} * {var_str}"


@dataclass(frozen=True, slots=True)
class Polynomial:
    """Polynomial: sum of monomials.

    多项式：单项式之和。
    """

    monomials: list[Monomial]

    def evaluate(self, values: dict[str, float]) -> float:
        """Evaluate polynomial.

        Args:
            values: Variable values.

        Returns:
            Evaluated value.
        """
        return sum(m.evaluate(values) for m in self.monomials)

    def degree(self) -> int:
        """Get total degree."""
        if not self.monomials:
            return 0
        return max(m.degree() for m in self.monomials)

    def simplify(self) -> Polynomial:
        """Simplify by combining like terms.

        Returns:
            Simplified polynomial.
        """
        terms: dict[tuple[tuple[str, int], ...], float] = {}
        for m in self.monomials:
            key = m.variables
            terms[key] = terms.get(key, 0) + m.coefficient
        new_monomials = [
            Monomial(coeff, vars) for vars, coeff in sorted(terms.items()) if coeff != 0
        ]
        return Polynomial(new_monomials)

    def __add__(self, other: Polynomial | Monomial) -> Polynomial:
        """Add polynomials."""
        if isinstance(other, Monomial):
            return Polynomial(list(self.monomials) + [other]).simplify()
        return Polynomial(list(self.monomials) + list(other.monomials)).simplify()

    def __sub__(self, other: Polynomial | Monomial) -> Polynomial:
        """Subtract polynomials."""
        if isinstance(other, Monomial):
            negated_m = Monomial(-other.coefficient, other.variables)
            new_monomials: list[Monomial] = list(self.monomials)
            new_monomials.append(negated_m)
            return Polynomial(new_monomials).simplify()
        negated_list = [Monomial(-m.coefficient, m.variables) for m in other.monomials]
        new_monomials = list(self.monomials)
        new_monomials.extend(negated_list)
        return Polynomial(new_monomials).simplify()

    def __mul__(self, other: Polynomial | Monomial) -> Polynomial:
        """Multiply polynomials."""
        if isinstance(other, Monomial):
            return Polynomial([m * other for m in self.monomials]).simplify()
        result_monomials = []
        for m1 in self.monomials:
            for m2 in other.monomials:
                result_monomials.append(m1 * m2)
        return Polynomial(result_monomials).simplify()

    def __repr__(self) -> str:
        """String representation."""
        if not self.monomials:
            return "0"
        return " + ".join(repr(m) for m in self.monomials)

    def to_dict(self) -> dict[str, object]:
        """Serialize to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "type": "Polynomial",
            "monomials": [
                {
                    "coefficient": m.coefficient,
                    "variables": list(m.variables),
                }
                for m in self.monomials
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Polynomial:
        """Deserialize from dictionary.

        Args:
            data: Dictionary representation.

        Returns:
            Polynomial instance.
        """
        monomials: list[Monomial] = []
        monomials_data = data.get("monomials", [])
        if isinstance(monomials_data, list):
            for m_data in monomials_data:
                if isinstance(m_data, dict):
                    coeff = m_data.get("coefficient", 0.0)
                    vars_data = m_data.get("variables", [])
                    monomials.append(
                        Monomial(
                            coefficient=float(coeff)
                            if isinstance(coeff, (int, float))
                            else 0.0,
                            variables=tuple(tuple(v) for v in vars_data)
                            if isinstance(vars_data, list)
                            else (),
                        )
                    )
        return cls(monomials=monomials)


@dataclass(frozen=True, slots=True)
class Inequality:
    """Inequality: left op right, where op is <=, <, >=, >.

    不等式：左边 op 右边。
    """

    left: Polynomial
    operator: str  # "<=", "<", ">=", ">"
    right: Polynomial

    def evaluate(self, values: dict[str, float]) -> bool:
        """Evaluate inequality.

        Args:
            values: Variable values.

        Returns:
            True if inequality holds.
        """
        left_val = self.left.evaluate(values)
        right_val = self.right.evaluate(values)
        if self.operator == "<=":
            return left_val <= right_val
        if self.operator == "<":
            return left_val < right_val
        if self.operator == ">=":
            return left_val >= right_val
        if self.operator == ">":
            return left_val > right_val
        raise ValueError(f"Unknown operator: {self.operator}")

    def simplify(self) -> Inequality:
        """Simplify both sides.

        Returns:
            Simplified inequality.
        """
        return Inequality(self.left.simplify(), self.operator, self.right.simplify())

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.left} {self.operator} {self.right}"

    def to_dict(self) -> dict[str, object]:
        """Serialize to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "type": "Inequality",
            "left": self.left.to_dict(),
            "operator": self.operator,
            "right": self.right.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Inequality:
        """Deserialize from dictionary.

        Args:
            data: Dictionary representation.

        Returns:
            Inequality instance.
        """
        return cls(
            left=Polynomial.from_dict(data["left"]),  # type: ignore[arg-type]
            operator=data["operator"],  # type: ignore[arg-type]
            right=Polynomial.from_dict(data["right"]),  # type: ignore[arg-type]
        )


def variable(name: str) -> Monomial:
    """Create a variable monomial.

    Args:
        name: Variable name.

    Returns:
        Monomial representing the variable.
    """
    return Monomial(1.0, ((name, 1),))


def constant(value: float) -> Monomial:
    """Create a constant monomial.

    Args:
        value: Constant value.

    Returns:
        Monomial representing the constant.
    """
    return Monomial(value, ())
