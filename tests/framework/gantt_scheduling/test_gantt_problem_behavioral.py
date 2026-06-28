"""GanttProblem behavioral tests.

Covers GanttProblem validation, queries, and internal validation methods.
"""

from __future__ import annotations

import pytest

from ospf_python.framework.gantt_scheduling.application.model.gantt_problem import (
    GanttProblem,
    PrecedenceRelation,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource import (
    Resource,
)
from ospf_python.framework.gantt_scheduling.domain.task.model.task import Task


def _make_task(
    key: str = "t1",
    name: str = "Task",
    duration: float = 1.0,
    priority: int = 0,
    resource_requirements: tuple[tuple[str, float], ...] = (),
) -> Task:
    return Task(
        task_key=key,
        name=name,
        duration=duration,
        priority=priority,
        resource_requirements=resource_requirements,
    )


def _make_resource(key: str = "r1", capacity: float = 10.0) -> Resource:
    return Resource(resource_key=key, name=key, capacity=capacity)


# ==================== PrecedenceRelation tests ====================


class TestPrecedenceRelation:
    """PrecedenceRelation behavioral tests."""

    def test_default_min_gap(self) -> None:
        rel = PrecedenceRelation(predecessor_key="t1", successor_key="t2")
        assert rel.min_gap == pytest.approx(0.0)

    def test_custom_min_gap(self) -> None:
        rel = PrecedenceRelation(
            predecessor_key="t1", successor_key="t2", min_gap=5.0
        )
        assert rel.min_gap == pytest.approx(5.0)

    def test_frozen(self) -> None:
        rel = PrecedenceRelation(predecessor_key="t1", successor_key="t2")
        with pytest.raises(AttributeError):
            rel.min_gap = 1.0  # type: ignore[misc]


# ==================== GanttProblem validation tests ====================


class TestGanttProblemValidation:
    """GanttProblem.validate() behavioral tests."""

    def test_validate_no_tasks_fails(self) -> None:
        problem = GanttProblem(name="empty", tasks=(), resources=())
        result = problem.validate()
        assert result.is_failed()

    def test_validate_valid_problem(self) -> None:
        tasks = (_make_task("t1"),)
        resources = (_make_resource("r1"),)
        problem = GanttProblem(name="valid", tasks=tasks, resources=resources)
        result = problem.validate()
        assert result.is_ok()

    def test_validate_duplicate_task_keys_fails(self) -> None:
        tasks = (_make_task("t1"), _make_task("t1"))
        resources = (_make_resource("r1"),)
        problem = GanttProblem(name="dup", tasks=tasks, resources=resources)
        result = problem.validate()
        assert result.is_failed()

    def test_validate_invalid_resource_reference_fails(self) -> None:
        tasks = (_make_task("t1", resource_requirements=(("r_missing", 1.0),)),)
        resources = (_make_resource("r1"),)
        problem = GanttProblem(name="bad_res", tasks=tasks, resources=resources)
        result = problem.validate()
        assert result.is_failed()

    def test_validate_invalid_precedence_task_fails(self) -> None:
        tasks = (_make_task("t1"),)
        resources = (_make_resource("r1"),)
        rels = (PrecedenceRelation(predecessor_key="t1", successor_key="t_missing"),)
        problem = GanttProblem(
            name="bad_prec", tasks=tasks, resources=resources, precedence_relations=rels
        )
        result = problem.validate()
        assert result.is_failed()

    def test_validate_invalid_predecessor_fails(self) -> None:
        tasks = (_make_task("t1"),)
        resources = (_make_resource("r1"),)
        rels = (PrecedenceRelation(predecessor_key="t_missing", successor_key="t1"),)
        problem = GanttProblem(
            name="bad_pred", tasks=tasks, resources=resources, precedence_relations=rels
        )
        result = problem.validate()
        assert result.is_failed()

    def test_validate_valid_precedence_ok(self) -> None:
        tasks = (_make_task("t1"), _make_task("t2"))
        resources = (_make_resource("r1"),)
        rels = (PrecedenceRelation(predecessor_key="t1", successor_key="t2"),)
        problem = GanttProblem(
            name="good_prec", tasks=tasks, resources=resources, precedence_relations=rels
        )
        result = problem.validate()
        assert result.is_ok()


# ==================== GanttProblem query tests ====================


class TestGanttProblemQueries:
    """GanttProblem query method behavioral tests."""

    def _make_problem(self) -> GanttProblem:
        tasks = (
            _make_task("t1", priority=3, resource_requirements=(("r1", 1.0),)),
            _make_task("t2", priority=5, resource_requirements=(("r1", 2.0), ("r2", 1.0))),
            _make_task("t3", priority=1, resource_requirements=(("r2", 1.0),)),
        )
        resources = (_make_resource("r1"), _make_resource("r2"))
        rels = (
            PrecedenceRelation(predecessor_key="t1", successor_key="t2"),
            PrecedenceRelation(predecessor_key="t1", successor_key="t3"),
        )
        return GanttProblem(
            name="query_test",
            tasks=tasks,
            resources=resources,
            precedence_relations=rels,
        )

    def test_task_keys(self) -> None:
        problem = self._make_problem()
        assert problem.task_keys == ("t1", "t2", "t3")

    def test_resource_keys(self) -> None:
        problem = self._make_problem()
        assert problem.resource_keys == ("r1", "r2")

    def test_task_count(self) -> None:
        problem = self._make_problem()
        assert problem.task_count == 3

    def test_resource_count(self) -> None:
        problem = self._make_problem()
        assert problem.resource_count == 2

    def test_precedence_count(self) -> None:
        problem = self._make_problem()
        assert problem.precedence_count == 2

    def test_task_by_key_found(self) -> None:
        problem = self._make_problem()
        task = problem.task_by_key("t2")
        assert task is not None
        assert task.task_key == "t2"
        assert task.priority == 5

    def test_task_by_key_not_found(self) -> None:
        problem = self._make_problem()
        assert problem.task_by_key("t99") is None

    def test_resource_by_key_found(self) -> None:
        problem = self._make_problem()
        res = problem.resource_by_key("r1")
        assert res is not None
        assert res.resource_key == "r1"

    def test_resource_by_key_not_found(self) -> None:
        problem = self._make_problem()
        assert problem.resource_by_key("r99") is None

    def test_successors_of(self) -> None:
        problem = self._make_problem()
        assert problem.successors_of("t1") == ("t2", "t3")

    def test_successors_of_no_successors(self) -> None:
        problem = self._make_problem()
        assert problem.successors_of("t2") == ()

    def test_predecessors_of(self) -> None:
        problem = self._make_problem()
        assert problem.predecessors_of("t2") == ("t1",)

    def test_predecessors_of_no_predecessors(self) -> None:
        problem = self._make_problem()
        assert problem.predecessors_of("t1") == ()

    def test_filter_by_priority(self) -> None:
        problem = self._make_problem()
        high = problem.filter_by_priority(3)
        assert len(high) == 2
        assert all(t.priority >= 3 for t in high)

    def test_filter_by_priority_none_match(self) -> None:
        problem = self._make_problem()
        result = problem.filter_by_priority(100)
        assert result == ()

    def test_tasks_for_resource(self) -> None:
        problem = self._make_problem()
        r1_tasks = problem.tasks_for_resource("r1")
        assert len(r1_tasks) == 2
        r2_tasks = problem.tasks_for_resource("r2")
        assert len(r2_tasks) == 2

    def test_tasks_for_resource_none(self) -> None:
        problem = self._make_problem()
        assert problem.tasks_for_resource("r99") == ()

    def test_has_task_true(self) -> None:
        problem = self._make_problem()
        assert problem.has_task("t1") is True

    def test_has_task_false(self) -> None:
        problem = self._make_problem()
        assert problem.has_task("t99") is False

    def test_has_resource_true(self) -> None:
        problem = self._make_problem()
        assert problem.has_resource("r1") is True

    def test_has_resource_false(self) -> None:
        problem = self._make_problem()
        assert problem.has_resource("r99") is False


# ==================== GanttProblem internal validation tests ====================


class TestGanttProblemInternalValidation:
    """GanttProblem _find_* internal validation method tests."""

    def test_find_duplicate_task_keys_none(self) -> None:
        tasks = (_make_task("t1"), _make_task("t2"))
        problem = GanttProblem(name="test", tasks=tasks)
        assert problem._find_duplicate_task_keys() is None

    def test_find_duplicate_task_keys_found(self) -> None:
        tasks = (_make_task("t1"), _make_task("t2"), _make_task("t1"))
        problem = GanttProblem(name="test", tasks=tasks)
        assert problem._find_duplicate_task_keys() == "t1"

    def test_find_invalid_resource_reference_none(self) -> None:
        tasks = (_make_task("t1", resource_requirements=(("r1", 1.0),)),)
        resources = (_make_resource("r1"),)
        problem = GanttProblem(name="test", tasks=tasks, resources=resources)
        assert problem._find_invalid_resource_reference() is None

    def test_find_invalid_resource_reference_found(self) -> None:
        tasks = (_make_task("t1", resource_requirements=(("r_missing", 1.0),)),)
        resources = (_make_resource("r1"),)
        problem = GanttProblem(name="test", tasks=tasks, resources=resources)
        assert problem._find_invalid_resource_reference() == "r_missing"

    def test_find_invalid_precedence_none(self) -> None:
        tasks = (_make_task("t1"), _make_task("t2"))
        rels = (PrecedenceRelation(predecessor_key="t1", successor_key="t2"),)
        problem = GanttProblem(name="test", tasks=tasks, precedence_relations=rels)
        assert problem._find_invalid_precedence() is None

    def test_find_invalid_precedence_bad_successor(self) -> None:
        tasks = (_make_task("t1"),)
        rels = (PrecedenceRelation(predecessor_key="t1", successor_key="t_missing"),)
        problem = GanttProblem(name="test", tasks=tasks, precedence_relations=rels)
        assert problem._find_invalid_precedence() == "t_missing"

    def test_find_invalid_precedence_bad_predecessor(self) -> None:
        tasks = (_make_task("t1"),)
        rels = (PrecedenceRelation(predecessor_key="t_missing", successor_key="t1"),)
        problem = GanttProblem(name="test", tasks=tasks, precedence_relations=rels)
        assert problem._find_invalid_precedence() == "t_missing"
