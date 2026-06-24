"""整数范围。

Integer range.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Generic, TypeVar

IntT = TypeVar("IntT", bound=int)


@dataclass(frozen=True)
class IntegerRange(Generic[IntT]):
    """泛型整数范围。

    Generic integer range with start, end, and step.

    Attributes:
        start: 起始值（含）。/ Start value (inclusive).
        end: 结束值（不含）。/ End value (exclusive).
        step: 步长。/ Step size.
    """

    start: IntT
    end: IntT
    step: IntT = 1  # type: ignore[assignment]

    def __post_init__(self) -> None:
        """校验范围合法性。/ Validate range."""
        if self.step == 0:
            object.__setattr__(self, "step", 1)

    def __contains__(self, value: int) -> bool:
        """检查值是否在范围内。

        Check whether value is in range.

        Args:
            value: 待检查的值。/ Value to check.

        Returns:
            是否在范围内。/ Whether in range.
        """
        if self.step > 0:
            return (
                value >= self.start
                and value < self.end
                and (value - self.start) % self.step == 0
            )
        return (
            value <= self.start
            and value > self.end
            and (self.start - value) % (-self.step) == 0
        )

    def __iter__(self) -> Iterator[int]:
        """迭代范围内的值。/ Iterate over range values."""
        current: int = self.start
        if self.step > 0:
            while current < self.end:
                yield current
                current += self.step
        else:
            while current > self.end:
                yield current
                current += self.step

    def __len__(self) -> int:
        """获取范围长度。/ Get range length."""
        if self.step > 0 and self.start < self.end:
            return (self.end - self.start + self.step - 1) // self.step
        if self.step < 0 and self.start > self.end:
            return (self.start - self.end - self.step - 1) // (-self.step)
        return 0


@dataclass(frozen=True)
class NumericUIntegerRange(IntegerRange[int]):
    """无符号整数范围。

    Unsigned integer range. Start must be non-negative.

    Attributes:
        start: 起始值（含），须 >= 0。/ Start (inclusive), must >= 0.
        end: 结束值（不含）。/ End (exclusive).
        step: 步长。/ Step size.
    """

    def __post_init__(self) -> None:
        """校验无符号约束。/ Validate unsigned constraint."""
        super().__post_init__()
        if self.start < 0:
            object.__setattr__(self, "start", 0)
