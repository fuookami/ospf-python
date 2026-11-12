"""无符号数值整数 / Unsigned numeric integer.

对应 Kotlin NumericUInteger。
Mirrors Kotlin NumericUInteger.
"""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python import _native


@dataclass(frozen=True)
class NumericUInteger:
    """无符号数值整数 / Unsigned numeric integer.

    Args:
        value: 非负整数值 / Non-negative integer value.
    """

    _value: int

    def __post_init__(self) -> None:
        _integer.initialize(self)

    @property
    def value(self) -> int:
        """获取值 / Get value."""
        return self._value

    def safe_add(self, other: NumericUInteger) -> NumericUInteger:
        """安全加法 / Safe addition."""
        return _integer.add(owner=self, other=other)

    def safe_mul(self, other: NumericUInteger) -> NumericUInteger:
        """安全乘法 / Safe multiplication."""
        return _integer.multiply(owner=self, other=other)

    def __add__(self, other: NumericUInteger) -> NumericUInteger:
        return _integer.add(owner=self, other=other)

    def __mul__(self, other: NumericUInteger) -> NumericUInteger:
        return _integer.multiply(owner=self, other=other)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NumericUInteger):
            return NotImplemented
        return _integer.equal(left=self._value, right=other._value)

    def __lt__(self, other: NumericUInteger) -> bool:
        return _integer.less(left=self._value, right=other._value)

    def __le__(self, other: NumericUInteger) -> bool:
        return _integer.less_equal(left=self._value, right=other._value)

    def __hash__(self) -> int:
        return hash(self._value)

    def __str__(self) -> str:
        return str(self._value)


_integer = _native._public_integer.facade(
    reference=NumericUInteger.__add__, domain="numeric_u_integer"
)
