"""Tests for ospf_python.core.model module."""

from ospf_python.core.model import (
    Constraint,
    ConstraintType,
    MetaModel,
    Objective,
    ObjectiveType,
    Solution,
)
from ospf_python.core.symbol import linear_term
from ospf_python.core.variable import continuous
from ospf_python.utils.result import Failed, Ok


class TestMetaModel:
    """Tests for MetaModel."""

    def test_creation(self) -> None:
        """Test creating model."""
        model = MetaModel("test")
        assert model.name == "test"

    def test_add_variable(self) -> None:
        """Test adding variable."""
        model = MetaModel("test")
        v = model.add_variable(continuous("x", 0.0, 10.0))
        assert v.name == "x"
        assert len(model.get_variables()) == 1

    def test_add_constraint(self) -> None:
        """Test adding constraint."""
        model = MetaModel("test")
        model.add_variable(continuous("x"))
        expr = linear_term(1.0, "x")
        c = model.add_constraint("c1", expr, ConstraintType.LE, 10.0)
        assert c.name == "c1"
        assert len(model.get_constraints()) == 1

    def test_set_objective(self) -> None:
        """Test setting objective."""
        model = MetaModel("test")
        model.add_variable(continuous("x"))
        expr = linear_term(1.0, "x")
        obj = model.set_objective("obj", expr, ObjectiveType.MINIMIZE)
        assert obj.name == "obj"
        assert model.get_objective() is not None

    def test_get_variable(self) -> None:
        """Test getting variable."""
        model = MetaModel("test")
        model.add_variable(continuous("x"))
        result = model.get_variable("x")
        assert isinstance(result, Ok)
        assert result.value.name == "x"

    def test_get_variable_not_found(self) -> None:
        """Test getting variable not found."""
        model = MetaModel("test")
        result = model.get_variable("x")
        assert isinstance(result, Failed)

    def test_solve_success(self) -> None:
        """Test solving model."""
        model = MetaModel("test")
        model.add_variable(continuous("x"))
        model.set_objective("obj", linear_term(1.0, "x"), ObjectiveType.MINIMIZE)
        result = model.solve({"x": 5.0})
        assert isinstance(result, Ok)
        assert result.value.objective_value == 5.0

    def test_solve_no_objective(self) -> None:
        """Test solving with no objective."""
        model = MetaModel("test")
        result = model.solve({})
        assert isinstance(result, Failed)

    def test_solve_missing_variable(self) -> None:
        """Test solving with missing variable."""
        model = MetaModel("test")
        model.add_variable(continuous("x"))
        model.set_objective("obj", linear_term(1.0, "x"), ObjectiveType.MINIMIZE)
        result = model.solve({})
        assert isinstance(result, Failed)

    def test_solve_constraint_violated(self) -> None:
        """Test solving with violated constraint."""
        model = MetaModel("test")
        model.add_variable(continuous("x"))
        model.add_constraint("c1", linear_term(1.0, "x"), ConstraintType.LE, 10.0)
        model.set_objective("obj", linear_term(1.0, "x"), ObjectiveType.MINIMIZE)
        result = model.solve({"x": 15.0})
        assert isinstance(result, Failed)

    def test_solve_constraint_satisfied(self) -> None:
        """Test solving with satisfied constraint."""
        model = MetaModel("test")
        model.add_variable(continuous("x"))
        model.add_constraint("c1", linear_term(1.0, "x"), ConstraintType.LE, 10.0)
        model.set_objective("obj", linear_term(1.0, "x"), ObjectiveType.MINIMIZE)
        result = model.solve({"x": 5.0})
        assert isinstance(result, Ok)

    def test_repr(self) -> None:
        """Test string representation."""
        model = MetaModel("test")
        assert "test" in repr(model)


class TestConstraint:
    """Tests for Constraint."""

    def test_creation(self) -> None:
        """Test creating constraint."""
        expr = linear_term(1.0, "x")
        c = Constraint("c1", expr, ConstraintType.LE, 10.0)
        assert c.name == "c1"
        assert c.constraint_type == ConstraintType.LE

    def test_repr(self) -> None:
        """Test string representation."""
        expr = linear_term(1.0, "x")
        c = Constraint("c1", expr, ConstraintType.LE, 10.0)
        assert "c1" in repr(c)
        assert "<=" in repr(c)


class TestObjective:
    """Tests for Objective."""

    def test_creation(self) -> None:
        """Test creating objective."""
        expr = linear_term(1.0, "x")
        obj = Objective("obj", expr, ObjectiveType.MINIMIZE)
        assert obj.name == "obj"
        assert obj.objective_type == ObjectiveType.MINIMIZE

    def test_repr(self) -> None:
        """Test string representation."""
        expr = linear_term(1.0, "x")
        obj = Objective("obj", expr, ObjectiveType.MINIMIZE)
        assert "minimize" in repr(obj)


class TestSolution:
    """Tests for Solution."""

    def test_creation(self) -> None:
        """Test creating solution."""
        s = Solution(5.0, {"x": 5.0})
        assert s.objective_value == 5.0
        assert s.variable_values == {"x": 5.0}

    def test_repr(self) -> None:
        """Test string representation."""
        s = Solution(5.0, {"x": 5.0})
        assert "optimal" in repr(s)


class TestModelExample:
    """Test model example: minimize x subject to x <= 10."""

    def test_minimize_x(self) -> None:
        """Test minimizing x."""
        model = MetaModel("example")
        model.add_variable(continuous("x", 0.0, 10.0))
        model.add_constraint("c1", linear_term(1.0, "x"), ConstraintType.LE, 10.0)
        model.set_objective("obj", linear_term(1.0, "x"), ObjectiveType.MINIMIZE)

        result = model.solve({"x": 5.0})
        assert isinstance(result, Ok)
        assert result.value.objective_value == 5.0
        assert result.value.status == "optimal"
