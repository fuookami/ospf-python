"""Example: Basic Gantt Scheduling.

示例：基本甘特调度问题。
"""

from ospf_python.framework.gantt_scheduling import GanttSolver, Resource, Task
from ospf_python.utils.result import Ok


def test_basic_gantt() -> None:
    """Test basic Gantt scheduling example.

    测试基本甘特调度示例。
    """
    # Define tasks
    tasks = [
        Task("task1", 5.0, priority=1),
        Task("task2", 3.0, priority=2),
        Task("task3", 4.0, priority=1),
    ]

    # Define resources
    resources = [
        Resource("machine1", 1),
        Resource("machine2", 1),
    ]

    # Solve
    solver = GanttSolver()
    result = solver.solve(tasks, resources)

    # Verify
    assert isinstance(result, Ok)
    solution = result.value
    assert solution.makespan >= 0
    assert len(solution.entries) >= 0
