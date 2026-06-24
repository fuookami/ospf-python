"""线性 IIS / Linear IIS.

表示线性规划问题中的不可约不可行子系统。
Represents an Irreducible Infeasible Subsystem in
linear programming problems.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ospf_python.core.solver.iis.iis_computing_status import (
    IISComputingStatus,
)


@dataclass(frozen=True)
class LinearIIS:
    """线性 IIS / Linear IIS.

    冻结数据类，记录线性约束的不可约不可行子系统。
    Frozen dataclass recording the IIS of linear
    constraints.

    Attributes:
        status: 计算状态 / Computing status.
        constraints: IIS 中的约束名 / Constraint names
            in the IIS.
        bounds: IIS 中的变量界 / Variable bounds in the
            IIS.
        message: 附加消息 / Additional message.
    """

    status: IISComputingStatus = IISComputingStatus.NOT_STARTED
    """计算状态 / Computing status."""

    constraints: tuple[str, ...] = field(
        default_factory=tuple,
    )
    """IIS 中的约束名 / Constraint names in the IIS."""

    bounds: tuple[str, ...] = field(
        default_factory=tuple,
    )
    """IIS 中的变量界 / Variable bounds in the IIS."""

    message: str = ""
    """附加消息 / Additional message."""

    @property
    def is_found(self) -> bool:
        """是否已找到 IIS / Whether IIS was found.

        Returns:
            已找到返回 True / True when found.
        """
        return self.status is IISComputingStatus.FOUND

    @property
    def size(self) -> int:
        """IIS 大小 / IIS size.

        Returns:
            约束与变量界之和 / Sum of constraints and
            bounds.
        """
        return len(self.constraints) + len(self.bounds)
