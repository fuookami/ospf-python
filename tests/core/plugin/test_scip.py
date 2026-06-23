"""Tests for SCIP solver adapter."""

import pytest

from ospf_python.core.model import (
    ConstraintType,
    MetaModel,
    ObjectiveType,
)
from ospf_python.core.plugin.scip import ScipSolver
from ospf_python.core.symbol import linear_term
from ospf_python.core.variable import continuous
from ospf_python.utils.result import Ok

pyscipopt = pytest.importorskip("pyscipopt", reason="pyscipopt not installed")


class TestScipSolver:
    """Tests for ScipSolver."""

    def test_creation(self) -> None:
        """Test creating SCIP solver."""
        solver = ScipSolver()
        assert solver.name() == "SCIP"

    def test_solve_basic(self) -> None:
        """Test solving basic model."""
        model = MetaModel("test")
        model.add_variable(continuous("x", 0.0, 10.0))
        model.set_objective("obj", linear_term(1.0, "x"), ObjectiveType.MINIMIZE)

        solver = ScipSolver()
        result = solver.solve(model)
        assert isinstance(result, Ok)
        assert result.value.status.value == "optimal"

    def test_solve_with_constraints(self) -> None:
        """Test solving with constraints."""
        model = MetaModel("test")
        model.add_variable(continuous("x", 0.0, 10.0))
        model.add_constraint("c1", linear_term(1.0, "x"), ConstraintType.GE, 2.0)
        model.set_objective("obj", linear_term(1.0, "x"), ObjectiveType.MINIMIZE)

        solver = ScipSolver()
        result = solver.solve(model)
        assert isinstance(result, Ok)
        assert abs(result.value.objective_value - 2.0) < 1e-6
