"""Tests for ospf_python.framework.csp1d module."""

from ospf_python.framework.csp1d import (
    Csp1dModel,
    Csp1dSolution,
    Csp1dSolver,
    Demand,
    Stock,
)
from ospf_python.quantities import meters
from ospf_python.utils.result import Ok


class TestDemand:
    """Tests for Demand."""

    def test_creation(self) -> None:
        """Test creating demand."""
        demand = Demand("demand1", meters(2.0), 5)
        assert demand.name == "demand1"
        assert demand.length.value == 2.0
        assert demand.quantity == 5


class TestStock:
    """Tests for Stock."""

    def test_creation(self) -> None:
        """Test creating stock."""
        stock = Stock("stock1", meters(10.0), 100.0)
        assert stock.name == "stock1"
        assert stock.length.value == 10.0
        assert stock.cost == 100.0


class TestCsp1dModel:
    """Tests for Csp1dModel."""

    def test_build_meta_model(self) -> None:
        """Test building MetaModel."""
        demands = [
            Demand("demand1", meters(2.0), 5),
            Demand("demand2", meters(3.0), 3),
        ]
        stocks = [
            Stock("stock1", meters(10.0), 100.0),
            Stock("stock2", meters(12.0), 120.0),
        ]

        model = Csp1dModel(demands, stocks)
        meta_model = model.build_meta_model()

        assert meta_model.name == "csp1d"
        assert len(meta_model.get_variables()) > 0
        assert meta_model.get_objective() is not None


class TestCsp1dSolver:
    """Tests for Csp1dSolver."""

    def test_solve_basic(self) -> None:
        """Test solving basic problem."""
        demands = [
            Demand("demand1", meters(2.0), 5),
            Demand("demand2", meters(3.0), 3),
        ]
        stocks = [
            Stock("stock1", meters(10.0), 100.0),
        ]

        solver = Csp1dSolver()
        result = solver.solve(demands, stocks)

        assert isinstance(result, Ok)
        assert isinstance(result.value, Csp1dSolution)

    def test_solve_with_extra_constraints(self) -> None:
        """Test solving with extra constraints."""
        demands = [
            Demand("demand1", meters(2.0), 5),
        ]
        stocks = [
            Stock("stock1", meters(10.0), 100.0),
        ]

        extra_constraints = ["custom_constraint"]

        solver = Csp1dSolver()
        result = solver.solve(demands, stocks, extra_constraints=extra_constraints)

        assert isinstance(result, Ok)
