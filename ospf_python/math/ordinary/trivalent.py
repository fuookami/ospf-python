"""三值逻辑类型。

Trivalent (three-valued) logic type.
"""

import enum

from ospf_python._binding.result import BindingResult
from ospf_python._binding.trivalent import logic, optional_bool


class Trivalent(enum.Enum):
    """三值逻辑：真、假、未知。

    Three-valued logic: True, False, Unknown.

    Attributes:
        TRUE: 真。/ True.
        FALSE: 假。/ False.
        UNKNOWN: 未知。/ Unknown.
    """

    TRUE = "true"
    FALSE = "false"
    UNKNOWN = "unknown"

    def __and__(self, other: "Trivalent") -> BindingResult["Trivalent"]:
        """逻辑与。/ Logical AND.

        Args:
            other: 另一个三值。/ Other trivalent.

        Returns:
            原成员或显式失败。/ Original member or explicit failure.
        """
        return logic(members=_MEMBERS, operation="and", left=self, right=other)

    def __or__(self, other: "Trivalent") -> BindingResult["Trivalent"]:
        """逻辑或。/ Logical OR.

        Args:
            other: 另一个三值。/ Other trivalent.

        Returns:
            原成员或显式失败。/ Original member or explicit failure.
        """
        return logic(members=_MEMBERS, operation="or", left=self, right=other)

    def __invert__(self) -> BindingResult["Trivalent"]:
        """逻辑非。/ Logical NOT.

        Returns:
            原成员或显式失败。/ Original member or explicit failure.
        """
        return logic(members=_MEMBERS, operation="not", left=self)

    @property
    def is_true(self) -> bool:
        """是否为真。/ Whether true."""
        return self is Trivalent.TRUE

    @property
    def is_false(self) -> bool:
        """是否为假。/ Whether false."""
        return self is Trivalent.FALSE

    @property
    def is_unknown(self) -> bool:
        """是否未知。/ Whether unknown."""
        return self is Trivalent.UNKNOWN

    def to_bool(self) -> BindingResult[bool | None]:
        """转换为 Python bool 或 None。

        Convert to Python bool or None.

        Returns:
            True/False/None成功值或显式失败。/ Success or explicit failure.
        """
        return optional_bool(members=_MEMBERS, owner=self)


_MEMBERS = (Trivalent.TRUE, Trivalent.FALSE, Trivalent.UNKNOWN)
