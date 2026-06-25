"""Gantt scheduling demo — 甘特调度示例 / Gantt scheduling example."""

from __future__ import annotations

from ospf_python.framework.gantt_scheduling.domain.resource.model.resource import (
    Resource,
)
from ospf_python.framework.gantt_scheduling.domain.task.model.task import Task


def run_demo() -> None:
    """运行 Gantt demo / Run Gantt demo."""
    task = Task(task_key="t1", name="Task 1", duration=3.0)
    resource = Resource(resource_key="r1", name="Resource 1", capacity=8.0)
    print(f"Task: {task}")
    print(f"Resource: {resource}")
    print("Gantt demo completed successfully.")


if __name__ == "__main__":
    run_demo()
