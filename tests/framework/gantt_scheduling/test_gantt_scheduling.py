"""Tests for ospf_python.framework.gantt_scheduling module."""

from ospf_python.framework.gantt_scheduling import (
    GanttModel,
    GanttSolution,
    GanttSolver,
    Resource,
    Task,
)
from ospf_python.utils.result import Ok


class TestTask:
    """Tests for Task."""

    def test_creation(self) -> None:
        """Test creating task."""
        task = Task("task1", 5.0, priority=1)
        assert task.name == "task1"
        assert task.duration == 5.0
        assert task.priority == 1


class TestResource:
    """Tests for Resource."""

    def test_creation(self) -> None:
        """Test creating resource."""
        resource = Resource("machine1", 2)
        assert resource.name == "machine1"
        assert resource.capacity == 2


class TestGanttModel:
    """Tests for GanttModel."""

    def test_build_meta_model(self) -> None:
        """Test building MetaModel."""
        tasks = [
            Task("task1", 5.0),
            Task("task2", 3.0),
        ]
        resources = [
            Resource("machine1", 1),
            Resource("machine2", 1),
        ]

        model = GanttModel(tasks, resources)
        meta_model = model.build_meta_model()

        assert meta_model.name == "gantt"
        assert len(meta_model.get_variables()) > 0
        assert meta_model.get_objective() is not None


class TestGanttSolver:
    """Tests for GanttSolver."""

    def test_solve_basic(self) -> None:
        """Test solving basic problem."""
        tasks = [
            Task("task1", 5.0),
            Task("task2", 3.0),
        ]
        resources = [
            Resource("machine1", 1),
        ]

        solver = GanttSolver()
        result = solver.solve(tasks, resources)

        assert isinstance(result, Ok)
        assert isinstance(result.value, GanttSolution)

    def test_solve_with_extra_constraints(self) -> None:
        """Test solving with extra constraints."""
        tasks = [
            Task("task1", 5.0),
        ]
        resources = [
            Resource("machine1", 1),
        ]

        extra_constraints = ["custom_constraint"]

        solver = GanttSolver()
        result = solver.solve(tasks, resources, extra_constraints=extra_constraints)

        assert isinstance(result, Ok)
