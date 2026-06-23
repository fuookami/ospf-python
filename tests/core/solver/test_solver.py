"""Tests for ospf_python.core.solver module."""

from ospf_python.core.model import (
    ConstraintType,
    MetaModel,
    ObjectiveType,
)
from ospf_python.core.solver import (
    MockSolver,
    SolverConfig,
    SolverOutput,
    SolverStatus,
    solve_with_mock,
)
from ospf_python.core.symbol import linear_term
from ospf_python.core.variable import continuous
from ospf_python.utils.result import Failed, Ok


class TestSolverConfig:
    """Tests for SolverConfig."""

    def test_creation(self) -> None:
        """Test creating config."""
        config = SolverConfig(time_limit=100.0, gap_tolerance=1e-6)
        assert config.time_limit == 100.0
        assert config.gap_tolerance == 1e-6

    def test_defaults(self) -> None:
        """Test default values."""
        config = SolverConfig()
        assert config.time_limit == 3600.0
        assert config.gap_tolerance == 1e-4

    def test_repr(self) -> None:
        """Test string representation."""
        config = SolverConfig()
        assert "SolverConfig" in repr(config)


class TestSolverOutput:
    """Tests for SolverOutput."""

    def test_creation(self) -> None:
        """Test creating output."""
        output = SolverOutput(
            status=SolverStatus.OPTIMAL,
            objective_value=5.0,
            variable_values={"x": 5.0},
        )
        assert output.status == SolverStatus.OPTIMAL
        assert output.objective_value == 5.0

    def test_repr(self) -> None:
        """Test string representation."""
        output = SolverOutput(
            status=SolverStatus.OPTIMAL,
            objective_value=5.0,
            variable_values={"x": 5.0},
        )
        assert "optimal" in repr(output)


class TestMockSolver:
    """Tests for MockSolver."""

    def test_creation(self) -> None:
        """Test creating mock solver."""
        solver = MockSolver()
        assert solver.name() == "MockSolver"

    def test_solve_basic(self) -> None:
        """Test solving basic model."""
        model = MetaModel("test")
        model.add_variable(continuous("x", 0.0, 10.0))
        model.set_objective("obj", linear_term(1.0, "x"), ObjectiveType.MINIMIZE)

        solver = MockSolver()
        result = solver.solve(model)
        assert isinstance(result, Ok)
        assert result.value.status == SolverStatus.OPTIMAL

    def test_solve_with_solution(self) -> None:
        """Test solving with pre-defined solution."""
        model = MetaModel("test")
        model.add_variable(continuous("x", 0.0, 10.0))
        model.set_objective("obj", linear_term(1.0, "x"), ObjectiveType.MINIMIZE)

        solver = MockSolver({"x": 7.0})
        result = solver.solve(model)
        assert isinstance(result, Ok)
        assert result.value.objective_value == 7.0
        assert result.value.variable_values["x"] == 7.0

    def test_solve_no_objective(self) -> None:
        """Test solving with no objective."""
        model = MetaModel("test")
        model.add_variable(continuous("x"))

        solver = MockSolver()
        result = solver.solve(model)
        assert isinstance(result, Failed)


class TestSolveWithMock:
    """Tests for solve_with_mock function."""

    def test_solve_basic(self) -> None:
        """Test solving basic model."""
        model = MetaModel("test")
        model.add_variable(continuous("x", 0.0, 10.0))
        model.set_objective("obj", linear_term(1.0, "x"), ObjectiveType.MINIMIZE)

        result = solve_with_mock(model)
        assert isinstance(result, Ok)
        assert result.value.status == "optimal"

    def test_solve_with_solution(self) -> None:
        """Test solving with pre-defined solution."""
        model = MetaModel("test")
        model.add_variable(continuous("x", 0.0, 10.0))
        model.set_objective("obj", linear_term(1.0, "x"), ObjectiveType.MINIMIZE)

        result = solve_with_mock(model, {"x": 5.0})
        assert isinstance(result, Ok)
        assert result.value.objective_value == 5.0


class TestMockSolverEndToEnd:
    """End-to-end test: MetaModel → mock solve → solution extraction."""

    def test_minimize_x(self) -> None:
        """Test minimizing x with constraints."""
        # Model: minimize x subject to x >= 2, x <= 10
        model = MetaModel("example")
        model.add_variable(continuous("x", 2.0, 10.0))
        model.add_constraint("c1", linear_term(1.0, "x"), ConstraintType.GE, 2.0)
        model.add_constraint("c2", linear_term(1.0, "x"), ConstraintType.LE, 10.0)
        model.set_objective("obj", linear_term(1.0, "x"), ObjectiveType.MINIMIZE)

        # Solve with mock solver
        result = solve_with_mock(model, {"x": 5.0})
        assert isinstance(result, Ok)
        assert result.value.objective_value == 5.0
        assert result.value.variable_values["x"] == 5.0
        assert result.value.status == "optimal"
