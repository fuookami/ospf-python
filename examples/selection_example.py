"""同步/异步选择保留精确单位并消费 Result。 / Exact-unit synchronous/async selection with Result."""

from __future__ import annotations

import asyncio
from fractions import Fraction
from typing import TYPE_CHECKING

from ospf_python.math.combinatorics import (
    combinations,
    combinations_async,
    permutations,
    permutations_async,
)
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.unit.length import METER

if TYPE_CHECKING:
    from ospf_python._binding.result import BindingResult


def _show(
    name: str,
    result: BindingResult[list[list[Quantity[Fraction]]]],
) -> bool:
    def show_patterns(patterns: list[list[Quantity[Fraction]]]) -> None:
        first = (
            [f"{leaf.value} {leaf.unit.symbol}" for leaf in patterns[0]]
            if patterns
            else []
        )
        print(f"{name}: {len(patterns)} patterns; first={first}")

    result.on_success(show_patterns).on_failure(lambda error: print(error.message))
    return result.is_ok()


async def main_async() -> None:
    """在已有事件循环中消费同一组自然入口。 / Consume natural entry points in an existing event loop."""
    lengths = [Quantity(Fraction(index, 2), METER) for index in (1, 3, 5)]
    if not _show("combinations", combinations(lengths, 2)):
        return
    if not _show("permutations", permutations(lengths, 2)):
        return
    if not _show("combinations_async", await combinations_async(lengths, 2)):
        return
    _show("permutations_async", await permutations_async(lengths, 2))


def main() -> None:
    """从同步程序启动示例。 / Start the example from a synchronous program."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
