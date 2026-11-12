"""开放数值/单位的显式数据快照策略。 / Explicit data-snapshot policy for open values and units."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from ospf_python.utils.functional.result import Result


class SnapshotAdapter[V](Protocol):
    """以纯 JSON 数据连接开放对象，不持久化 callable 或自动导入类。 / Connect open objects with pure JSON data, never persisted callables or automatic class imports."""

    def to_snapshot(self, value: V) -> Result[Any, Any, Any]:
        """导出独立数据，由边界验证并复制。 / Export data for validation and copying at the boundary.

        Args:
            value: 原始数值或单位。 / Original value or unit.

        Returns:
            Ok 中的纯 JSON 数据或保留身份的失败。 / Pure JSON data in Ok or an identity-retaining failure.
        """
        ...

    def from_snapshot(self, snapshot: Any) -> Result[V, Any, Any]:
        """恢复开放对象，不执行来自快照的代码。 / Restore an open object without executing snapshot-supplied code.

        Args:
            snapshot: 独立纯数据副本。 / Independent pure-data copy.

        Returns:
            Ok 中的对象或保留身份的失败。 / Object in Ok or an identity-retaining failure.
        """
        ...
