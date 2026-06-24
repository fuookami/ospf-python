"""比较运算枚举。

Comparison operator enumeration for inequalities.
"""

from __future__ import annotations

from enum import Enum, unique


@unique
class Comparison(Enum):
    """不等式比较运算符。

    Inequality comparison operator.

    Attributes:
        LE: 小于等于 <=。/ Less-than-or-equal <=.
        GE: 大于等于 >=。/ Greater-than-or-equal >=.
        LT: 小于 <。/ Less-than <.
        GT: 大于 >。/ Greater-than >.
        EQ: 等于 ==。/ Equal ==.
        NE: 不等于 !=。/ Not-equal !=.
    """

    LE = "<="
    GE = ">="
    LT = "<"
    GT = ">"
    EQ = "=="
    NE = "!="

    @property
    def symbol(self) -> str:
        """获取比较符号。/ Get comparison symbol."""
        return self.value

    @property
    def is_strict(self) -> bool:
        """是否为严格比较。/ Whether strict comparison."""
        return self in (Comparison.LT, Comparison.GT, Comparison.NE)

    @property
    def negated(self) -> Comparison:
        """获取取反后的比较运算。/ Get negated comparison."""
        _negation_map: dict[Comparison, Comparison] = {
            Comparison.LE: Comparison.GT,
            Comparison.GE: Comparison.LT,
            Comparison.LT: Comparison.GE,
            Comparison.GT: Comparison.LE,
            Comparison.EQ: Comparison.NE,
            Comparison.NE: Comparison.EQ,
        }
        return _negation_map[self]

    @property
    def reversed(self) -> Comparison:
        """获取反转后的比较运算（左右互换）。/
        Get reversed comparison (swap operands).
        """
        _reverse_map: dict[Comparison, Comparison] = {
            Comparison.LE: Comparison.GE,
            Comparison.GE: Comparison.LE,
            Comparison.LT: Comparison.GT,
            Comparison.GT: Comparison.LT,
            Comparison.EQ: Comparison.EQ,
            Comparison.NE: Comparison.NE,
        }
        return _reverse_map[self]
