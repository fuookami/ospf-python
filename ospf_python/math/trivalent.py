"""三值逻辑。

Three-valued logic.
"""

from __future__ import annotations

from enum import Enum, unique


@unique
class Trivalent(Enum):
    """三值逻辑枚举。

    Three-valued logic enum: TRUE, FALSE, UNKNOWN.

    Attributes:
        TRUE: 真。/ True.
        FALSE: 假。/ False.
        UNKNOWN: 未知。/ Unknown.
    """

    TRUE = "true"
    FALSE = "false"
    UNKNOWN = "unknown"


@unique
class BalancedTrivalent(Enum):
    """平衡三值逻辑枚举。

    Balanced three-valued logic: TRUE, FALSE, BALANCED.

    Attributes:
        TRUE: 真。/ True.
        FALSE: 假。/ False.
        BALANCED: 平衡。/ Balanced.
    """

    TRUE = "true"
    FALSE = "false"
    BALANCED = "balanced"


# Trivalent 操作 / Trivalent operations


_TRIVALENT_AND: dict[tuple[Trivalent, Trivalent], Trivalent] = {
    (Trivalent.TRUE, Trivalent.TRUE): Trivalent.TRUE,
    (Trivalent.TRUE, Trivalent.FALSE): Trivalent.FALSE,
    (Trivalent.TRUE, Trivalent.UNKNOWN): Trivalent.UNKNOWN,
    (Trivalent.FALSE, Trivalent.TRUE): Trivalent.FALSE,
    (Trivalent.FALSE, Trivalent.FALSE): Trivalent.FALSE,
    (Trivalent.FALSE, Trivalent.UNKNOWN): Trivalent.FALSE,
    (Trivalent.UNKNOWN, Trivalent.TRUE): Trivalent.UNKNOWN,
    (Trivalent.UNKNOWN, Trivalent.FALSE): Trivalent.FALSE,
    (Trivalent.UNKNOWN, Trivalent.UNKNOWN): Trivalent.UNKNOWN,
}

_TRIVALENT_OR: dict[tuple[Trivalent, Trivalent], Trivalent] = {
    (Trivalent.TRUE, Trivalent.TRUE): Trivalent.TRUE,
    (Trivalent.TRUE, Trivalent.FALSE): Trivalent.TRUE,
    (Trivalent.TRUE, Trivalent.UNKNOWN): Trivalent.TRUE,
    (Trivalent.FALSE, Trivalent.TRUE): Trivalent.TRUE,
    (Trivalent.FALSE, Trivalent.FALSE): Trivalent.FALSE,
    (Trivalent.FALSE, Trivalent.UNKNOWN): Trivalent.UNKNOWN,
    (Trivalent.UNKNOWN, Trivalent.TRUE): Trivalent.TRUE,
    (Trivalent.UNKNOWN, Trivalent.FALSE): Trivalent.UNKNOWN,
    (Trivalent.UNKNOWN, Trivalent.UNKNOWN): Trivalent.UNKNOWN,
}

_TRIVALENT_NOT: dict[Trivalent, Trivalent] = {
    Trivalent.TRUE: Trivalent.FALSE,
    Trivalent.FALSE: Trivalent.TRUE,
    Trivalent.UNKNOWN: Trivalent.UNKNOWN,
}

# BalancedTrivalent 操作 / BalancedTrivalent operations


_BALANCED_AND: dict[
    tuple[BalancedTrivalent, BalancedTrivalent],
    BalancedTrivalent,
] = {
    (BalancedTrivalent.TRUE, BalancedTrivalent.TRUE): (BalancedTrivalent.TRUE),
    (BalancedTrivalent.TRUE, BalancedTrivalent.FALSE): (BalancedTrivalent.FALSE),
    (BalancedTrivalent.TRUE, BalancedTrivalent.BALANCED): (BalancedTrivalent.BALANCED),
    (BalancedTrivalent.FALSE, BalancedTrivalent.TRUE): (BalancedTrivalent.FALSE),
    (BalancedTrivalent.FALSE, BalancedTrivalent.FALSE): (BalancedTrivalent.FALSE),
    (BalancedTrivalent.FALSE, BalancedTrivalent.BALANCED): (BalancedTrivalent.FALSE),
    (BalancedTrivalent.BALANCED, BalancedTrivalent.TRUE): (BalancedTrivalent.BALANCED),
    (BalancedTrivalent.BALANCED, BalancedTrivalent.FALSE): (BalancedTrivalent.FALSE),
    (BalancedTrivalent.BALANCED, BalancedTrivalent.BALANCED): (
        BalancedTrivalent.BALANCED
    ),
}

_BALANCED_OR: dict[
    tuple[BalancedTrivalent, BalancedTrivalent],
    BalancedTrivalent,
] = {
    (BalancedTrivalent.TRUE, BalancedTrivalent.TRUE): (BalancedTrivalent.TRUE),
    (BalancedTrivalent.TRUE, BalancedTrivalent.FALSE): (BalancedTrivalent.TRUE),
    (BalancedTrivalent.TRUE, BalancedTrivalent.BALANCED): (BalancedTrivalent.TRUE),
    (BalancedTrivalent.FALSE, BalancedTrivalent.TRUE): (BalancedTrivalent.TRUE),
    (BalancedTrivalent.FALSE, BalancedTrivalent.FALSE): (BalancedTrivalent.FALSE),
    (BalancedTrivalent.FALSE, BalancedTrivalent.BALANCED): (BalancedTrivalent.BALANCED),
    (BalancedTrivalent.BALANCED, BalancedTrivalent.TRUE): (BalancedTrivalent.TRUE),
    (BalancedTrivalent.BALANCED, BalancedTrivalent.FALSE): (BalancedTrivalent.BALANCED),
    (BalancedTrivalent.BALANCED, BalancedTrivalent.BALANCED): (
        BalancedTrivalent.BALANCED
    ),
}

_BALANCED_NOT: dict[BalancedTrivalent, BalancedTrivalent] = {
    BalancedTrivalent.TRUE: BalancedTrivalent.FALSE,
    BalancedTrivalent.FALSE: BalancedTrivalent.TRUE,
    BalancedTrivalent.BALANCED: BalancedTrivalent.BALANCED,
}


def and_(
    a: Trivalent,
    b: Trivalent,
) -> Trivalent:
    """三值逻辑与运算。

    Trivalent AND operation.

    Args:
        a: 左操作数。/ Left operand.
        b: 右操作数。/ Right operand.

    Returns:
        运算结果。/ Operation result.
    """
    return _TRIVALENT_AND[(a, b)]


def or_(
    a: Trivalent,
    b: Trivalent,
) -> Trivalent:
    """三值逻辑或运算。

    Trivalent OR operation.

    Args:
        a: 左操作数。/ Left operand.
        b: 右操作数。/ Right operand.

    Returns:
        运算结果。/ Operation result.
    """
    return _TRIVALENT_OR[(a, b)]


def not_(a: Trivalent) -> Trivalent:
    """三值逻辑非运算。

    Trivalent NOT operation.

    Args:
        a: 操作数。/ Operand.

    Returns:
        运算结果。/ Operation result.
    """
    return _TRIVALENT_NOT[a]


def balanced_and(
    a: BalancedTrivalent,
    b: BalancedTrivalent,
) -> BalancedTrivalent:
    """平衡三值逻辑与运算。

    Balanced trivalent AND operation.

    Args:
        a: 左操作数。/ Left operand.
        b: 右操作数。/ Right operand.

    Returns:
        运算结果。/ Operation result.
    """
    return _BALANCED_AND[(a, b)]


def balanced_or(
    a: BalancedTrivalent,
    b: BalancedTrivalent,
) -> BalancedTrivalent:
    """平衡三值逻辑或运算。

    Balanced trivalent OR operation.

    Args:
        a: 左操作数。/ Left operand.
        b: 右操作数。/ Right operand.

    Returns:
        运算结果。/ Operation result.
    """
    return _BALANCED_OR[(a, b)]


def balanced_not(
    a: BalancedTrivalent,
) -> BalancedTrivalent:
    """平衡三值逻辑非运算。

    Balanced trivalent NOT operation.

    Args:
        a: 操作数。/ Operand.

    Returns:
        运算结果。/ Operation result.
    """
    return _BALANCED_NOT[a]
