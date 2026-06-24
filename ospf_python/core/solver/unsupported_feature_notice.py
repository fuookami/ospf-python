"""不支持特性通知 / Unsupported feature notice.

通知求解器不支持的特性。
Notifies about features unsupported by the solver.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class UnsupportedFeatureNotice:
    """不支持特性通知 / Unsupported feature notice.

    冻结数据类，描述求解器不支持的特性。
    Frozen dataclass describing a feature unsupported
    by the solver.

    Attributes:
        feature_name: 特性名称 / Feature name.
        solver_name: 求解器名称 / Solver name.
        alternatives: 替代方案 / Alternative suggestions.
    """

    feature_name: str = ""
    """特性名称 / Feature name."""

    solver_name: str = ""
    """求解器名称 / Solver name."""

    alternatives: tuple[str, ...] = field(
        default_factory=tuple,
    )
    """替代方案 / Alternative suggestions."""

    def describe(self) -> str:
        """生成人类可读描述 / Generate human-readable
        description.

        Returns:
            描述字符串 / Description string.
        """
        alt_str = ", ".join(self.alternatives) if self.alternatives else "none"
        return (
            f"Feature '{self.feature_name}' is not "
            f"supported by '{self.solver_name}'. "
            f"Alternatives: {alt_str}"
        )
