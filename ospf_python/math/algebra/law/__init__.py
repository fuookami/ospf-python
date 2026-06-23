"""Algebraic laws module.

Provides verification of algebraic properties: commutativity, associativity, etc.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from ospf_python.math.algebra.number import RealNumber

V = TypeVar("V", bound=RealNumber)


def is_commutative(
    op: Callable[[V, V], V],
    a: V,
    b: V,
) -> bool:
    """Check if operation is commutative for given values.

    Args:
        op: Binary operation.
        a: First operand.
        b: Second operand.

    Returns:
        True if op(a, b) == op(b, a).
    """
    return op(a, b) == op(b, a)


def is_associative(
    op: Callable[[V, V], V],
    a: V,
    b: V,
    c: V,
) -> bool:
    """Check if operation is associative for given values.

    Args:
        op: Binary operation.
        a: First operand.
        b: Second operand.
        c: Third operand.

    Returns:
        True if op(op(a, b), c) == op(a, op(b, c)).
    """
    return op(op(a, b), c) == op(a, op(b, c))


def has_identity(
    op: Callable[[V, V], V],
    identity: V,
    a: V,
) -> bool:
    """Check if identity element exists for given value.

    Args:
        op: Binary operation.
        identity: Identity element.
        a: Operand.

    Returns:
        True if op(a, identity) == a and op(identity, a) == a.
    """
    return op(a, identity) == a and op(identity, a) == a


def has_inverse(
    op: Callable[[V, V], V],
    identity: V,
    a: V,
    inverse: V,
) -> bool:
    """Check if inverse exists for given value.

    Args:
        op: Binary operation.
        identity: Identity element.
        a: Operand.
        inverse: Inverse of a.

    Returns:
        True if op(a, inverse) == identity and op(inverse, a) == identity.
    """
    return op(a, inverse) == identity and op(inverse, a) == identity


def is_distributive(
    add: Callable[[V, V], V],
    multiply: Callable[[V, V], V],
    a: V,
    b: V,
    c: V,
) -> bool:
    """Check if multiplication distributes over addition.

    Args:
        add: Addition operation.
        multiply: Multiplication operation.
        a: First operand.
        b: Second operand.
        c: Third operand.

    Returns:
        True if a * (b + c) == a * b + a * c.
    """
    return multiply(a, add(b, c)) == add(multiply(a, b), multiply(a, c))
