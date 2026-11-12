"""三值逻辑。

Three-valued logic.
"""

from enum import Enum, unique

from ospf_python._binding.result import BindingResult
from ospf_python._binding.trivalent import logic


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


_TRIVALENT_MEMBERS = (Trivalent.TRUE, Trivalent.FALSE, Trivalent.UNKNOWN)
_BALANCED_MEMBERS = (
    BalancedTrivalent.TRUE,
    BalancedTrivalent.FALSE,
    BalancedTrivalent.BALANCED,
)


def and_(
    a: Trivalent,
    b: Trivalent,
) -> BindingResult[Trivalent]:
    """三值逻辑与运算。

    Trivalent AND operation.

    Args:
        a: 左操作数。/ Left operand.
        b: 右操作数。/ Right operand.

    Returns:
        原成员或显式失败。/ Original member or explicit failure.
    """
    return logic(members=_TRIVALENT_MEMBERS, operation="and", left=a, right=b)


def or_(
    a: Trivalent,
    b: Trivalent,
) -> BindingResult[Trivalent]:
    """三值逻辑或运算。

    Trivalent OR operation.

    Args:
        a: 左操作数。/ Left operand.
        b: 右操作数。/ Right operand.

    Returns:
        原成员或显式失败。/ Original member or explicit failure.
    """
    return logic(members=_TRIVALENT_MEMBERS, operation="or", left=a, right=b)


def not_(a: Trivalent) -> BindingResult[Trivalent]:
    """三值逻辑非运算。

    Trivalent NOT operation.

    Args:
        a: 操作数。/ Operand.

    Returns:
        原成员或显式失败。/ Original member or explicit failure.
    """
    return logic(members=_TRIVALENT_MEMBERS, operation="not", left=a)


def balanced_and(
    a: BalancedTrivalent,
    b: BalancedTrivalent,
) -> BindingResult[BalancedTrivalent]:
    """平衡三值逻辑与运算。

    Balanced trivalent AND operation.

    Args:
        a: 左操作数。/ Left operand.
        b: 右操作数。/ Right operand.

    Returns:
        原成员或显式失败。/ Original member or explicit failure.
    """
    return logic(members=_BALANCED_MEMBERS, operation="and", left=a, right=b)


def balanced_or(
    a: BalancedTrivalent,
    b: BalancedTrivalent,
) -> BindingResult[BalancedTrivalent]:
    """平衡三值逻辑或运算。

    Balanced trivalent OR operation.

    Args:
        a: 左操作数。/ Left operand.
        b: 右操作数。/ Right operand.

    Returns:
        原成员或显式失败。/ Original member or explicit failure.
    """
    return logic(members=_BALANCED_MEMBERS, operation="or", left=a, right=b)


def balanced_not(
    a: BalancedTrivalent,
) -> BindingResult[BalancedTrivalent]:
    """平衡三值逻辑非运算。

    Balanced trivalent NOT operation.

    Args:
        a: 操作数。/ Operand.

    Returns:
        原成员或显式失败。/ Original member or explicit failure.
    """
    return logic(members=_BALANCED_MEMBERS, operation="not", left=a)
