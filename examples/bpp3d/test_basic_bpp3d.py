"""Example: Basic 3D Bin Packing.

示例：基本三维装箱问题。
"""

from ospf_python.framework.bpp3d import Bin, Bpp3dSolver, Item
from ospf_python.quantities import meters
from ospf_python.utils.result import Ok


def test_basic_bpp3d() -> None:
    """Test basic 3D bin packing example.

    测试基本三维装箱示例。
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

    # Solve
    solver = Bpp3dSolver()
    result = solver.solve(items, bins)

    # Verify
    assert isinstance(result, Ok)
    solution = result.value
    assert solution.total_bins >= 0
    assert solution.total_volume >= 0
