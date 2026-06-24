"""尾箱分配约束 / Tail bin assignment constraint.

管理尾箱的分配逻辑。
Manages tail bin assignment logic.
"""

from __future__ import annotations

import abc


class TailBinAssignmentConstraint(abc.ABC):
    """尾箱分配约束 / Tail bin assignment constraint.

    确保尾箱分配满足特殊约束。
    Ensures tail bin assignment satisfies special constraints.
    """

    @abc.abstractmethod
    def can_assign_to_tail(
        self,
        layer: object,
        tail_bin: object,
    ) -> bool:
        """检查尾箱分配 / Check tail bin assignment.

        Args:
            layer: 待分配的层 / The layer to assign.
            tail_bin: 尾箱 / The tail bin.

        Returns:
            可分配返回 True / True if assignable.
        """
        ...

    @abc.abstractmethod
    def get_tail_bin_utilization(
        self,
        tail_bin: object,
    ) -> float:
        """计算尾箱利用率 / Calculate tail bin utilization.

        Args:
            tail_bin: 尾箱 / The tail bin.

        Returns:
            利用率（0.0-1.0） / Utilization (0.0-1.0).
        """
        ...
