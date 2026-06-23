"""Example: Basic 1D Cutting Stock.

示例：基本一维下料问题。
"""

from ospf_python.framework.csp1d import Csp1dSolver, Demand, Stock
from ospf_python.quantities import meters
from ospf_python.utils.result import Ok


def test_basic_csp1d() -> None:
    """Test basic 1D cutting stock example.

    测试基本一维下料示例。
    """
    # Define demands
    demands = [
        Demand("demand1", meters(2.0), 5),
        Demand("demand2", meters(3.0), 3),
        Demand("demand3", meters(1.5), 4),
    ]

    # Define stocks
    stocks = [
        Stock("stock1", meters(10.0), 100.0),
        Stock("stock2", meters(12.0), 120.0),
    ]

    # Solve
    solver = Csp1dSolver()
    result = solver.solve(demands, stocks)

    # Verify
    assert isinstance(result, Ok)
    solution = result.value
    assert solution.total_stock >= 0
    assert solution.total_waste >= 0
