"""Tests for MindOpt solver adapter."""

import pytest

from ospf_python.core.model import (
    MetaModel,
    ObjectiveType,
)
from ospf_python.core.plugin.mindopt import MindOptSolver
from ospf_python.core.symbol import linear_term
from ospf_python.core.variable import continuous
from ospf_python.utils.result import Ok

mindoptpy = pytest.importorskip("mindoptpy", reason="mindoptpy not installed")


class TestMindOptSolver:
    """Tests for MindOptSolver."""

    def test_creation(self) -> None:
        """Test creating MindOpt solver."""
        solver = MindOptSolver()
        assert solver.name() == "MindOpt"

    def test_solve_basic(self) -> None:
        """Test solving basic model."""
        model = MetaModel("test")
        model.add_variable(continuous("x", 0.0, 10.0))
        model.set_objective("obj", linear_term(1.0, "x"), ObjectiveType.MINIMIZE)

        solver = MindOptSolver()
        result = solver.solve(model)
        assert isinstance(result, Ok)
        assert result.value.status.value == "optimal"
