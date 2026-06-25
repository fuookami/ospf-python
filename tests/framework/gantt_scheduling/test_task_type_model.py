"""TaskType model tests / 任务类型模型测试.

Exercises TaskType enum properties and compatibility checks.
覆盖 TaskType 枚举属性和兼容性检查。
"""

from __future__ import annotations

from ospf_python.framework.gantt_scheduling.domain.task.model.task_type import TaskType


class TestTaskTypeProperties:
    """TaskType property tests / 属性测试."""

    def test_allows_preemption_only_preemptive(self) -> None:
        """Only PREEMPTIVE allows preemption. / 仅 PREEMPTIVE 允许抢占."""
        assert TaskType.PREEMPTIVE.allows_preemption is True
        assert TaskType.FIXED.allows_preemption is False
        assert TaskType.VARIABLE.allows_preemption is False

    def test_allows_duration_change(self) -> None:
        """VARIABLE and PREEMPTIVE allow duration change. / 可变和可抢占允许时长变更."""
        assert TaskType.VARIABLE.allows_duration_change is True
        assert TaskType.PREEMPTIVE.allows_duration_change is True
        assert TaskType.FIXED.allows_duration_change is False

    def test_enum_values(self) -> None:
        """Enum string values. / 枚举字符串值."""
        assert TaskType.FIXED.value == "fixed"
        assert TaskType.VARIABLE.value == "variable"
        assert TaskType.PREEMPTIVE.value == "preemptive"


class TestTaskTypeCompatibility:
    """TaskType compatibility tests / 兼容性测试."""

    def test_fixed_incompatible_with_preemptive(self) -> None:
        """FIXED incompatible with PREEMPTIVE. / FIXED 与 PREEMPTIVE 不兼容."""
        assert TaskType.FIXED.is_compatible_with(TaskType.PREEMPTIVE) is False

    def test_preemptive_incompatible_with_fixed(self) -> None:
        """PREEMPTIVE incompatible with FIXED. / PREEMPTIVE 与 FIXED 不兼容."""
        assert TaskType.PREEMPTIVE.is_compatible_with(TaskType.FIXED) is False

    def test_fixed_compatible_with_variable(self) -> None:
        """FIXED compatible with VARIABLE. / FIXED 与 VARIABLE 兼容."""
        assert TaskType.FIXED.is_compatible_with(TaskType.VARIABLE) is True

    def test_variable_compatible_with_preemptive(self) -> None:
        """VARIABLE compatible with PREEMPTIVE. / VARIABLE 与 PREEMPTIVE 兼容."""
        assert TaskType.VARIABLE.is_compatible_with(TaskType.PREEMPTIVE) is True

    def test_self_compatible(self) -> None:
        """All types self-compatible. / 所有类型自兼容."""
        for tt in TaskType:
            assert tt.is_compatible_with(tt) is True
