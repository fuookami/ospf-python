"""Rule engine 测试 / Rule engine tests.

覆盖 Rule 创建、RuleType、RuleEngine 评估和
规则管线。
Covers Rule creation, RuleType, RuleEngine evaluation,
and rule pipeline.
"""

from __future__ import annotations

from typing import Any

import pytest

from examples.framework_demo.demo4.domain.rule.model.rule import Rule
from examples.framework_demo.demo4.domain.rule.model.rule_aggregation import (
    RuleAggregation,
)
from examples.framework_demo.demo4.domain.rule.model.rule_context import (
    RuleContext,
)
from examples.framework_demo.demo4.domain.rule.model.rule_result import (
    RuleResult,
)
from examples.framework_demo.demo4.domain.rule.model.rule_type import (
    RuleType,
)
from examples.framework_demo.demo4.domain.rule.service.limits.resource_rule_constraint import (
    ResourceRuleConstraint,
    ResourceView,
)
from examples.framework_demo.demo4.domain.rule.service.limits.scheduling_rule_constraint import (
    SchedulingRuleConstraint,
    TaskView,
)
from examples.framework_demo.demo4.domain.rule.service.limits.time_rule_constraint import (
    TimeRuleConstraint,
    TimeSlotView,
)
from examples.framework_demo.demo4.domain.rule.service.rule_engine import (
    RuleEngine,
    ScheduleView,
)


def _make_rule(
    rule_id: str = "R1",
    rule_type: RuleType = RuleType.SCHEDULING,
    priority: int = 5,
    params: dict[str, Any] | None = None,
) -> Rule:
    """创建测试规则 / Create test rule."""
    return Rule(
        rule_id=rule_id,
        rule_type=rule_type,
        parameters=params or {},
        priority=priority,
    )


class TestRuleType:
    """RuleType 测试 / RuleType tests."""

    def test_all_values(self) -> None:
        """所有值 / All values."""
        values = set(RuleType)
        assert RuleType.SCHEDULING in values
        assert RuleType.RESOURCE in values
        assert RuleType.TIME in values

    def test_description(self) -> None:
        """描述 / Description."""
        assert len(RuleType.SCHEDULING.description) > 0


class TestRule:
    """Rule 测试 / Rule tests."""

    def test_is_high_priority(self) -> None:
        """高优先级 / High priority."""
        high = _make_rule(priority=9)
        low = _make_rule(priority=3)
        assert high.is_high_priority is True
        assert low.is_high_priority is False

    def test_display_name(self) -> None:
        """显示名称 / Display name."""
        r = _make_rule(rule_id="R1", rule_type=RuleType.TIME)
        assert "R1" in r.display_name
        assert "TIME" in r.display_name

    def test_has_parameter(self) -> None:
        """参数检查 / Has parameter."""
        r = _make_rule(params={"max_overlap": 3})
        assert r.has_parameter("max_overlap") is True
        assert r.has_parameter("missing") is False

    def test_get_parameter(self) -> None:
        """获取参数 / Get parameter."""
        r = _make_rule(params={"max_overlap": 3})
        assert r.get_parameter("max_overlap") == 3
        assert r.get_parameter("missing", 42) == 42

    def test_applies_to_resource(self) -> None:
        """适用资源 / Applies to resource."""
        r = _make_rule(params={"resource_type": "aircraft"})
        assert r.applies_to_resource("aircraft") is True
        assert r.applies_to_resource("vehicle") is False

    def test_frozen(self) -> None:
        """不可变 / Frozen."""
        r = _make_rule()
        with pytest.raises(AttributeError):
            r.priority = 99  # type: ignore[misc]


class TestRuleResult:
    """RuleResult 测试 / RuleResult tests."""

    def test_is_clean(self) -> None:
        """无违规 / Is clean."""
        clean = RuleResult(
            rule_id="R1",
            satisfied=True,
            violations=(),
        )
        dirty = RuleResult(
            rule_id="R2",
            satisfied=False,
            violations=("v1",),
        )
        assert clean.is_clean is True
        assert dirty.is_clean is False

    def test_violation_count(self) -> None:
        """违规数 / Violation count."""
        r = RuleResult(
            rule_id="R1",
            satisfied=False,
            violations=("v1", "v2"),
        )
        assert r.violation_count == 2

    def test_summary(self) -> None:
        """摘要 / Summary."""
        r = RuleResult(
            rule_id="R1",
            satisfied=True,
            violations=(),
        )
        assert "R1" in r.summary()

    def test_merge(self) -> None:
        """合并 / Merge."""
        r1 = RuleResult(
            rule_id="R1",
            satisfied=True,
            violations=(),
        )
        r2 = RuleResult(
            rule_id="R2",
            satisfied=False,
            violations=("v1",),
        )
        merged = r1.merge(r2)
        assert merged.satisfied is False
        assert merged.violation_count == 1


class TestRuleContext:
    """RuleContext 测试 / Context tests."""

    def test_register_and_lookup(self) -> None:
        """注册和查询 / Register and lookup."""
        ctx = RuleContext()
        r = _make_rule()
        ctx.register(r)
        assert ctx.size == 1
        assert ctx.lookup("R1") is r

    def test_by_type(self) -> None:
        """按类型查询 / By type."""
        ctx = RuleContext()
        ctx.register(_make_rule("R1", RuleType.SCHEDULING))
        ctx.register(_make_rule("R2", RuleType.TIME))
        scheduling = ctx.by_type(RuleType.SCHEDULING)
        assert len(scheduling) == 1

    def test_unregister(self) -> None:
        """注销 / Unregister."""
        ctx = RuleContext()
        ctx.register(_make_rule())
        assert ctx.unregister("R1") is True
        assert ctx.size == 0

    def test_clear(self) -> None:
        """清空 / Clear."""
        ctx = RuleContext()
        ctx.register(_make_rule("R1"))
        ctx.register(_make_rule("R2"))
        ctx.clear()
        assert ctx.size == 0

    def test_has_rule(self) -> None:
        """是否包含 / Has rule."""
        ctx = RuleContext()
        ctx.register(_make_rule())
        assert ctx.has_rule("R1") is True
        assert ctx.has_rule("NOPE") is False


class TestRuleAggregation:
    """RuleAggregation 测试 / Aggregation tests."""

    def test_from_rules(self) -> None:
        """从规则构建 / Build from rules."""
        rules = (
            _make_rule("R1", RuleType.SCHEDULING, 9),
            _make_rule("R2", RuleType.TIME, 3),
        )
        agg = RuleAggregation.from_rules(rules)
        assert agg.count == 2

    def test_high_priority_rules(self) -> None:
        """高优先级规则 / High priority rules."""
        rules = (
            _make_rule("R1", RuleType.SCHEDULING, 9),
            _make_rule("R2", RuleType.TIME, 3),
        )
        agg = RuleAggregation.from_rules(rules)
        assert len(agg.high_priority_rules) == 1

    def test_type_counts(self) -> None:
        """类型计数 / Type counts."""
        rules = (
            _make_rule("R1", RuleType.SCHEDULING),
            _make_rule("R2", RuleType.SCHEDULING),
            _make_rule("R3", RuleType.TIME),
        )
        agg = RuleAggregation.from_rules(rules)
        assert agg.type_counts[RuleType.SCHEDULING] == 2

    def test_for_type(self) -> None:
        """按类型筛选 / For type."""
        rules = (
            _make_rule("R1", RuleType.RESOURCE),
            _make_rule("R2", RuleType.TIME),
        )
        agg = RuleAggregation.from_rules(rules)
        resource = agg.for_type(RuleType.RESOURCE)
        assert len(resource) == 1


class TestSchedulingRuleConstraint:
    """SchedulingRuleConstraint 测试 / Scheduling constraint tests."""

    def test_no_overlap_pass(self) -> None:
        """无重叠通过 / No overlap pass."""
        c = SchedulingRuleConstraint(max_overlap=0)
        tasks = (
            TaskView("T1", "aircraft", 0.0, 50.0),
            TaskView("T2", "aircraft", 60.0, 100.0),
        )
        errors = c.check(tasks)
        assert len(errors) == 0

    def test_overlap_detected(self) -> None:
        """检测重叠 / Overlap detected."""
        c = SchedulingRuleConstraint(max_overlap=0)
        tasks = (
            TaskView("T1", "aircraft", 0.0, 70.0),
            TaskView("T2", "aircraft", 50.0, 100.0),
        )
        errors = c.check(tasks)
        assert len(errors) > 0


class TestResourceRuleConstraint:
    """ResourceRuleConstraint 测试 / Resource constraint tests."""

    def test_within_capacity(self) -> None:
        """在容量内 / Within capacity."""
        c = ResourceRuleConstraint()
        resources = (ResourceView("R1", "aircraft", 100.0, 80.0),)
        errors = c.check(resources)
        assert len(errors) == 0

    def test_overcapacity(self) -> None:
        """超容量 / Overcapacity."""
        c = ResourceRuleConstraint(allow_overcapacity=False)
        resources = (ResourceView("R1", "aircraft", 100.0, 120.0),)
        errors = c.check(resources)
        assert len(errors) > 0


class TestTimeRuleConstraint:
    """TimeRuleConstraint 测试 / Time constraint tests."""

    def test_min_gap_pass(self) -> None:
        """最小间隔通过 / Min gap pass."""
        c = TimeRuleConstraint(min_gap=10.0)
        slots = (
            TimeSlotView("S1", 0.0, 50.0, 1),
            TimeSlotView("S2", 70.0, 100.0, 1),
        )
        errors = c.check(slots)
        assert len(errors) == 0


class TestRuleEngine:
    """RuleEngine 测试 / RuleEngine tests."""

    def test_evaluate(self) -> None:
        """评估 / Evaluate."""
        ctx = RuleContext()
        ctx.register(_make_rule("R1", RuleType.SCHEDULING, 5))
        engine = RuleEngine(ctx)
        schedule = ScheduleView(
            tasks=({"task_id": "T1", "start": 0.0, "end": 50.0},),
            resources=(),
            time_slots=(),
        )
        results = engine.evaluate(schedule)
        assert len(results) >= 1
