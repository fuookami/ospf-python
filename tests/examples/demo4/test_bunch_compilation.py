"""Bunch compilation 测试 / Bunch compilation tests.

覆盖 Bunch 创建、BunchStatus、BunchCompiler 和
容量/连续性约束。
Covers Bunch creation, BunchStatus, BunchCompiler,
and capacity/continuity constraints.
"""

from __future__ import annotations

import pytest

from examples.framework_demo.demo4.domain.bunch_compilation.model.bunch import (
    Bunch,
)
from examples.framework_demo.demo4.domain.bunch_compilation.model.bunch_context import (
    BunchContext,
)
from examples.framework_demo.demo4.domain.bunch_compilation.model.bunch_result import (
    BunchResult,
)
from examples.framework_demo.demo4.domain.bunch_compilation.model.bunch_status import (
    BunchStatus,
)
from examples.framework_demo.demo4.domain.bunch_compilation.service.bunch_compiler import (
    BunchCompiler,
    TaskInput,
)
from examples.framework_demo.demo4.domain.bunch_compilation.service.bunch_validator import (
    BunchValidator,
)
from examples.framework_demo.demo4.domain.bunch_compilation.service.limits.bunch_capacity_constraint import (
    BunchCapacityConstraint,
)
from examples.framework_demo.demo4.domain.bunch_compilation.service.limits.bunch_continuity_constraint import (
    BunchContinuityConstraint,
)
from examples.framework_demo.demo4.domain.bunch_compilation.service.limits.bunch_resource_constraint import (
    BunchResourceConstraint,
)


def _make_bunch(
    bunch_id: str = "B1",
    tasks: tuple[str, ...] = ("T1", "T2"),
    resource_type: str = "aircraft",
    start: float = 0.0,
    end: float = 100.0,
) -> Bunch:
    """创建测试任务组 / Create test bunch."""
    return Bunch(
        bunch_id=bunch_id,
        tasks=tasks,
        resource_type=resource_type,
        start_time=start,
        end_time=end,
    )


class TestBunch:
    """Bunch 测试 / Bunch tests."""

    def test_duration(self) -> None:
        """持续时间 / Duration."""
        b = _make_bunch(start=10.0, end=50.0)
        assert b.duration == pytest.approx(40.0)

    def test_task_count(self) -> None:
        """任务数 / Task count."""
        b = _make_bunch(tasks=("T1", "T2", "T3"))
        assert b.task_count == 3

    def test_overlaps_same_resource(self) -> None:
        """同资源重叠 / Same resource overlap."""
        b1 = _make_bunch(start=0.0, end=50.0)
        b2 = _make_bunch(bunch_id="B2", start=30.0, end=80.0)
        assert b1.overlaps(b2) is True

    def test_no_overlap_different_resource(self) -> None:
        """不同资源不重叠 / Different resource no overlap."""
        b1 = _make_bunch(resource_type="A")
        b2 = _make_bunch(bunch_id="B2", resource_type="B")
        assert b1.overlaps(b2) is False

    def test_contains_task(self) -> None:
        """包含任务 / Contains task."""
        b = _make_bunch(tasks=("T1", "T2"))
        assert b.contains_task("T1") is True
        assert b.contains_task("T3") is False

    def test_time_gap_to(self) -> None:
        """时间间隔 / Time gap."""
        b1 = _make_bunch(start=0.0, end=50.0)
        b2 = _make_bunch(bunch_id="B2", start=70.0, end=100.0)
        gap = b1.time_gap_to(b2)
        assert gap == pytest.approx(20.0)

    def test_frozen(self) -> None:
        """不可变 / Frozen."""
        b = _make_bunch()
        with pytest.raises(AttributeError):
            b.bunch_id = "X"  # type: ignore[misc]


class TestBunchStatus:
    """BunchStatus 测试 / BunchStatus tests."""

    def test_is_terminal(self) -> None:
        """终态 / Terminal state."""
        assert BunchStatus.EXECUTED.is_terminal is True
        assert BunchStatus.CANCELLED.is_terminal is True
        assert BunchStatus.PROPOSED.is_terminal is False

    def test_can_transition(self) -> None:
        """状态转换 / State transition."""
        assert BunchStatus.PROPOSED.can_transition_to(BunchStatus.CONFIRMED)
        assert not BunchStatus.EXECUTED.can_transition_to(BunchStatus.PROPOSED)

    def test_description(self) -> None:
        """描述 / Description."""
        assert len(BunchStatus.PROPOSED.description) > 0


class TestBunchResult:
    """BunchResult 测试 / BunchResult tests."""

    def test_is_efficient(self) -> None:
        """是否高效 / Is efficient."""
        r = BunchResult(
            bunch_id="B1",
            status=BunchStatus.CONFIRMED,
            utilization=0.85,
        )
        assert r.is_efficient is True

    def test_utilization_pct(self) -> None:
        """利用率百分比 / Utilization percentage."""
        r = BunchResult(
            bunch_id="B1",
            status=BunchStatus.PROPOSED,
            utilization=0.75,
        )
        assert "75" in r.utilization_pct

    def test_is_better_than(self) -> None:
        """比较优劣 / Comparison."""
        r1 = BunchResult(
            bunch_id="B1",
            status=BunchStatus.CONFIRMED,
            utilization=0.9,
        )
        r2 = BunchResult(
            bunch_id="B2",
            status=BunchStatus.PROPOSED,
            utilization=0.5,
        )
        assert r1.is_better_than(r2) is True


class TestBunchContext:
    """BunchContext 测试 / BunchContext tests."""

    def test_register_and_lookup(self) -> None:
        """注册和查询 / Register and lookup."""
        ctx = BunchContext()
        b = _make_bunch()
        ctx.register(b)
        assert ctx.size == 1
        assert ctx.lookup("B1") is b

    def test_unregister(self) -> None:
        """注销 / Unregister."""
        ctx = BunchContext()
        ctx.register(_make_bunch())
        assert ctx.unregister("B1") is True
        assert ctx.size == 0

    def test_by_resource_type(self) -> None:
        """按资源类型查询 / By resource type."""
        ctx = BunchContext()
        ctx.register(_make_bunch(resource_type="aircraft"))
        ctx.register(
            _make_bunch(
                bunch_id="B2",
                resource_type="vehicle",
            )
        )
        aircraft = ctx.by_resource_type("aircraft")
        assert len(aircraft) == 1

    def test_by_time_range(self) -> None:
        """按时间范围查询 / By time range."""
        ctx = BunchContext()
        ctx.register(_make_bunch(start=10.0, end=50.0))
        ctx.register(_make_bunch(bunch_id="B2", start=200.0, end=300.0))
        found = ctx.by_time_range(start=0.0, end=100.0)
        assert len(found) == 1


class TestBunchCompiler:
    """BunchCompiler 测试 / BunchCompiler tests."""

    def test_compile_adjacent_tasks(self) -> None:
        """编译相邻任务 / Compile adjacent tasks."""
        ctx = BunchContext()
        compiler = BunchCompiler(context=ctx, max_gap=30.0)
        tasks = (
            TaskInput("T1", "aircraft", 0.0, 50.0),
            TaskInput("T2", "aircraft", 60.0, 100.0),
            TaskInput("T3", "aircraft", 110.0, 150.0),
        )
        bunches = compiler.compile_tasks(tasks)
        assert len(bunches) >= 1

    def test_compile_separate_resources(self) -> None:
        """不同资源分开编译 / Separate resources."""
        ctx = BunchContext()
        compiler = BunchCompiler(context=ctx, max_gap=30.0)
        tasks = (
            TaskInput("T1", "aircraft", 0.0, 50.0),
            TaskInput("T2", "vehicle", 0.0, 50.0),
        )
        bunches = compiler.compile_tasks(tasks)
        assert len(bunches) == 2


class TestBunchValidator:
    """BunchValidator 测试 / BunchValidator tests."""

    def test_valid_bunch(self) -> None:
        """有效任务组 / Valid bunch."""
        v = BunchValidator()
        b = _make_bunch()
        assert v.is_valid(b) is True

    def test_validate_returns_empty_for_valid(self) -> None:
        """有效任务组无违规 / No violations for valid."""
        v = BunchValidator()
        b = _make_bunch()
        errors = v.validate(b)
        assert len(errors) == 0


class TestBunchCapacityConstraint:
    """BunchCapacityConstraint 测试 / Capacity tests."""

    def test_within_capacity(self) -> None:
        """在容量内 / Within capacity."""
        c = BunchCapacityConstraint(max_tasks_per_bunch=10)
        b = _make_bunch(tasks=("T1", "T2", "T3"))
        assert c.check(b) is True

    def test_exceeds_capacity(self) -> None:
        """超出容量 / Exceeds capacity."""
        c = BunchCapacityConstraint(max_tasks_per_bunch=2)
        b = _make_bunch(tasks=("T1", "T2", "T3"))
        assert c.check(b) is False
        assert len(c.violations(b)) > 0

    def test_filter_compliant(self) -> None:
        "Filter compliant bunches."
        c = BunchCapacityConstraint(max_tasks_per_bunch=2)
        ok = _make_bunch(tasks=("T1", "T2"))
        bad = _make_bunch(
            bunch_id="B2",
            tasks=("T3", "T4", "T5"),
        )
        result = c.filter_compliant((ok, bad))
        assert len(result) == 1


class TestBunchContinuityConstraint:
    """BunchContinuityConstraint 测试 / Continuity tests."""

    def test_within_gap(self) -> None:
        """间隔在限内 / Gap within limit."""
        c = BunchContinuityConstraint(max_gap_seconds=60.0)
        b = _make_bunch(start=0.0, end=100.0)
        assert c.check(b) is True

    def test_check_sequence(self) -> None:
        """序列检查 / Sequence check."""
        c = BunchContinuityConstraint(max_gap_seconds=100.0)
        b1 = _make_bunch(start=0.0, end=50.0)
        b2 = _make_bunch(
            bunch_id="B2",
            start=120.0,
            end=200.0,
        )
        assert c.check_sequence((b1, b2)) is True


class TestBunchResourceConstraint:
    """BunchResourceConstraint 测试 / Resource tests."""

    def test_allowed_resource(self) -> None:
        """允许的资源 / Allowed resource."""
        c = BunchResourceConstraint(
            allowed_resources=frozenset({"aircraft", "vehicle"})
        )
        b = _make_bunch(resource_type="aircraft")
        assert c.check(b) is True

    def test_disallowed_resource(self) -> None:
        "Disallowed resource."
        c = BunchResourceConstraint(allowed_resources=frozenset({"aircraft"}))
        b = _make_bunch(resource_type="helicopter")
        assert c.check(b) is False

    def test_group_by_resource(self) -> None:
        """按资源分组 / Group by resource."""
        c = BunchResourceConstraint(allowed_resources=frozenset({"A", "B"}))
        b1 = _make_bunch(resource_type="A")
        b2 = _make_bunch(bunch_id="B2", resource_type="B")
        groups = c.group_by_resource((b1, b2))
        assert len(groups) == 2
