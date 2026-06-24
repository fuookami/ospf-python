"""CSP1D 排程服务 / CSP1D scheduling service."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.csp1d.application.model.csp1d_assignment import (
        Csp1dAssignment,
    )
    from ospf_python.framework.csp1d.application.model.csp1d_solution import (
        Csp1dSolution,
    )
    from ospf_python.framework.csp1d.domain.material.model.machine import (
        Machine,
    )


class Csp1dSchedule:
    """切割排程服务 / Cutting schedule service.

    将解决方案中的切割分配分配到具体机器上执行。
    Distributes cutting assignments from the solution
    to specific machines for execution.

    Attributes:
        _machines: 可用机器列表 / Available machine list.
    """

    def __init__(
        self,
        machines: tuple[Machine, ...],
    ) -> None:
        """初始化排程服务 / Initialize schedule service.

        Args:
            machines: 可用机器 / Available machines.
        """
        self._machines = list(machines)

    def schedule(
        self,
        solution: Csp1dSolution,
    ) -> tuple[
        tuple[Machine, Csp1dAssignment, int],
        ...,
    ]:
        """将分配排程到机器 / Schedule assignments to machines.

        使用轮询策略将切割分配均匀分配到各台机器。
        Uses round-robin strategy to evenly distribute
        cutting assignments across machines.

        Args:
            solution: 切割解决方案 / Cutting solution.

        Returns:
            (机器, 分配, 批次序号) 元组 / (machine, assignment,
            batch index) tuples.
        """
        if not self._machines:
            return ()

        schedule: list[tuple[Machine, Csp1dAssignment, int]] = []
        machine_idx = 0

        for assignment in solution.assignments:
            for batch in range(assignment.quantity):
                machine = self._machines[machine_idx % len(self._machines)]
                schedule.append((machine, assignment, batch))
                machine_idx += 1

        return tuple(schedule)

    @property
    def machines(self) -> tuple[Machine, ...]:
        """可用机器 / Available machines."""
        return tuple(self._machines)
