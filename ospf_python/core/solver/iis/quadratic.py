"""二次 IIS / Quadratic IIS.

表示二次规划问题中的不可约不可行子系统。
Represents an Irreducible Infeasible Subsystem in
quadratic programming problems.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ospf_python.core.solver.iis.iis_computing_status import (
    IISComputingStatus,
)
from ospf_python.core.solver.iis.linear import LinearIIS


@dataclass(frozen=True)
class QuadraticIIS:
    """二次 IIS / Quadratic IIS.

    冻结数据类，记录二次约束的不可约不可行子系统。
    Frozen dataclass recording the IIS of quadratic
    constraints.

    Attributes:
        status: 计算状态 / Computing status.
        linear_iis: 线性部分 IIS / Linear part of the IIS.
        quadratic_constraints: 二次约束名 / Quadratic
            constraint names.
        message: 附加消息 / Additional message.
    """

    status: IISComputingStatus = IISComputingStatus.NOT_STARTED
    """计算状态 / Computing status."""

    linear_iis: LinearIIS = field(
        default_factory=LinearIIS,
    )
    """线性部分 IIS / Linear part of the IIS."""

    quadratic_constraints: tuple[str, ...] = field(
        default_factory=tuple,
    )
    """二次约束名 / Quadratic constraint names."""

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
            线性部分加二次约束数量 / Linear part plus
            quadratic constraint count.
        """
        return self.linear_iis.size + len(self.quadratic_constraints)
