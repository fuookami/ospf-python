"""Gantt scheduling framework tests."""

from __future__ import annotations

from ospf_python.framework.gantt_scheduling.domain.resource.model.resource import (
    Resource,
)
from ospf_python.framework.gantt_scheduling.domain.task.model.task import Task


def test_task_creation() -> None:
    t = Task(task_key="t1", name="task1", duration=1.0)
    assert t is not None


def test_resource_creation() -> None:
    r = Resource(
        resource_key="res-1",
        name="Machine A",
        capacity=10.0,
    )
    assert r is not None
