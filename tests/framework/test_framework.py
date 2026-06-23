"""Tests for ospf_python.framework module."""

from ospf_python.core.model import MetaModel, ObjectiveType, Solution
from ospf_python.core.solver import MockSolver
from ospf_python.core.symbol import linear_term
from ospf_python.core.variable import continuous
from ospf_python.framework import (
    ConsoleLogger,
    FrameworkConfig,
    FrameworkModel,
    SimpleFrameworkSolver,
)
from ospf_python.utils.result import Ok


class TestLogger:
    """Tests for Logger."""

    def test_console_logger(self) -> None:
        """Test console logger."""
        logger = ConsoleLogger()
        logger.info("Test message")


class TestFrameworkConfig:
    """Tests for FrameworkConfig."""

    def test_creation(self) -> None:
        """Test creating config."""
        config = FrameworkConfig(solver_name="gurobi", time_limit=100.0)
        assert config.solver_name == "gurobi"
        assert config.time_limit == 100.0

    def test_defaults(self) -> None:
        """Test default values."""
        config = FrameworkConfig()
        assert config.solver_name == "mock"
        assert config.time_limit == 3600.0


class TestSimpleFrameworkSolver:
    """Tests for SimpleFrameworkSolver."""

    def test_solve(self) -> None:
        """Test solving with framework solver."""

        class TestModel(FrameworkModel):
            def build_meta_model(self) -> MetaModel:
                model = MetaModel("test")
                model.add_variable(continuous("x", 0.0, 10.0))
                model.set_objective(
                    "obj", linear_term(1.0, "x"), ObjectiveType.MINIMIZE
                )
                return model

            def extract_solution(self, solution: Solution) -> dict:
                return {"x": solution.variable_values.get("x", 0.0)}

        solver = SimpleFrameworkSolver(MockSolver({"x": 5.0}))
        model = TestModel()
        result = solver.solve(model)
        assert isinstance(result, Ok)
