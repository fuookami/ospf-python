"""可转换为求解值的协议 / Protocol convertible to solve value.

定义将对象转换为 SolveValue 的协议。
Defines the protocol for converting objects to SolveValue.
"""

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from ospf_python.core.solver.value.solve_value import (
        SolveValue,
    )


@typing.runtime_checkable
class IntoValue(typing.Protocol):
    """可转换为求解值的协议 / Protocol convertible to solve value.

    实现此协议的对象可以转换为 SolveValue。
    Objects implementing this protocol can be converted
    to SolveValue.
    """

    def to_solve_value(self) -> SolveValue:
        """转换为求解值 / Convert to solve value.

        Returns:
            求解值实例 / Solve value instance.
        """
        ...
