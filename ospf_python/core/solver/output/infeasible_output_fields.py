"""不可行输出字段 / Infeasible output fields.

记录不可行求解结果的附加信息。
Records additional information for infeasible solve
results.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class InfeasibleOutputFields:
    """不可行输出字段 / Infeasible output fields.

    冻结数据类，封装不可行结果的诊断信息。
    Frozen dataclass encapsulating diagnostic information
    for infeasible results.

    Attributes:
        message: 诊断消息 / Diagnostic message.
        conflicting_constraints: 冲突约束列表 /
            List of conflicting constraints.
        iis_available: 是否有 IIS 结果 / Whether IIS
            results are available.
    """

    message: str = ""
    """诊断消息 / Diagnostic message."""

    conflicting_constraints: tuple[str, ...] = field(
        default_factory=tuple,
    )
    """冲突约束列表 / List of conflicting constraints."""

    iis_available: bool = False
    """是否有 IIS 结果 / Whether IIS results are available."""

    @property
    def has_conflicts(self) -> bool:
        """是否有冲突约束 / Whether there are conflicting
        constraints.

        Returns:
            有冲突约束时返回 True / True when conflicting
            constraints exist.
        """
        return len(self.conflicting_constraints) > 0

    @staticmethod
    def with_message(msg: str) -> InfeasibleOutputFields:
        """创建带消息的实例 / Create instance with message.

        Args:
            msg: 诊断消息 / Diagnostic message.

        Returns:
            不可行输出字段实例 / Infeasible output fields
            instance.
        """
        return InfeasibleOutputFields(message=msg)
