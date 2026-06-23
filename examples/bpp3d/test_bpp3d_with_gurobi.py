"""Example: 3D Bin Packing with Gurobi solver.

示例：使用 Gurobi 求解器的三维装箱问题。
"""

from ospf_python.core.plugin.gurobi import GurobiSolver
from ospf_python.framework.bpp3d import Bin, Bpp3dSolver, Item
from ospf_python.quantities import meters
from ospf_python.utils.result import Ok


def test_bpp3d_with_gurobi() -> None:
    """Test 3D bin packing with Gurobi solver.

    使用 Gurobi 求解器测试三维装箱。
    """
    # Define items to pack
    items = [
        Item("item1", meters(1.0), meters(1.0), meters(1.0), meters(10.0)),
        Item("item2", meters(2.0), meters(2.0), meters(2.0), meters(20.0)),
        Item("item3", meters(1.5), meters(1.5), meters(1.5), meters(15.0)),
    ]

    # Define available bins
    bins = [
        Bin("bin1", meters(10.0), meters(10.0), meters(10.0), meters(100.0)),
        Bin("bin2", meters(10.0), meters(10.0), meters(10.0), meters(100.0)),
    ]

    # Solve with Gurobi
    solver = Bpp3dSolver(GurobiSolver())
    result = solver.solve(items, bins)

    # Verify
    assert isinstance(result, Ok)
    solution = result.value
    print("Gurobi 求解结果:")
    print(f"  使用箱子数: {solution.total_bins}")
    print(f"  总体积: {solution.total_volume}")
    print(f"  目标值: {solution.objective_value}")
    for packing in solution.packings:
        print(
            f"  箱子 {packing.bin_name}: {packing.items}, 利用率: {packing.utilization:.2%}"
        )


def test_bpp3d_with_scip() -> None:
    """Test 3D bin packing with SCIP solver.

    使用 SCIP 求解器测试三维装箱。
    """
    from ospf_python.core.plugin.scip import ScipSolver

    # Define items to pack
    items = [
        Item("item1", meters(1.0), meters(1.0), meters(1.0), meters(10.0)),
        Item("item2", meters(2.0), meters(2.0), meters(2.0), meters(20.0)),
    ]

    # Define available bins
    bins = [
        Bin("bin1", meters(10.0), meters(10.0), meters(10.0), meters(100.0)),
    ]

    # Solve with SCIP
    solver = Bpp3dSolver(ScipSolver())
    result = solver.solve(items, bins)

    # Verify
    assert isinstance(result, Ok)
    solution = result.value
    print("\nSCIP 求解结果:")
    print(f"  使用箱子数: {solution.total_bins}")
    print(f"  总体积: {solution.total_volume}")
    print(f"  目标值: {solution.objective_value}")
