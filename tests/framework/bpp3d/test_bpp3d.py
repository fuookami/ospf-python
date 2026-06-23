"""Tests for ospf_python.framework.bpp3d module."""

from ospf_python.framework.bpp3d import (
    Bin,
    Bpp3dModel,
    Bpp3dSolution,
    Bpp3dSolver,
    Item,
)
from ospf_python.quantities import meters
from ospf_python.utils.result import Ok


class TestItem:
    """Tests for Item."""

    def test_creation(self) -> None:
        """Test creating item."""
        item = Item("item1", meters(1.0), meters(1.0), meters(1.0), meters(10.0))
        assert item.name == "item1"
        assert item.width.value == 1.0

    def test_volume(self) -> None:
        """Test item volume."""
        item = Item("item1", meters(2.0), meters(3.0), meters(4.0), meters(10.0))
        assert item.volume.value == 24.0


class TestBin:
    """Tests for Bin."""

    def test_creation(self) -> None:
        """Test creating bin."""
        bin = Bin("bin1", meters(10.0), meters(10.0), meters(10.0), meters(100.0))
        assert bin.name == "bin1"
        assert bin.width.value == 10.0

    def test_volume(self) -> None:
        """Test bin volume."""
        bin = Bin("bin1", meters(2.0), meters(3.0), meters(4.0), meters(100.0))
        assert bin.volume.value == 24.0


class TestBpp3dModel:
    """Tests for Bpp3dModel."""

    def test_build_meta_model(self) -> None:
        """Test building MetaModel."""
        items = [
            Item("item1", meters(1.0), meters(1.0), meters(1.0), meters(10.0)),
            Item("item2", meters(2.0), meters(2.0), meters(2.0), meters(20.0)),
        ]
        bins = [
            Bin("bin1", meters(10.0), meters(10.0), meters(10.0), meters(100.0)),
        ]

        model = Bpp3dModel(items, bins)
        meta_model = model.build_meta_model()

        assert meta_model.name == "bpp3d"
        assert len(meta_model.get_variables()) > 0
        assert meta_model.get_objective() is not None


class TestBpp3dSolver:
    """Tests for Bpp3dSolver."""

    def test_solve_basic(self) -> None:
        """Test solving basic problem."""
        items = [
            Item("item1", meters(1.0), meters(1.0), meters(1.0), meters(10.0)),
            Item("item2", meters(2.0), meters(2.0), meters(2.0), meters(20.0)),
        ]
        bins = [
            Bin("bin1", meters(10.0), meters(10.0), meters(10.0), meters(100.0)),
            Bin("bin2", meters(10.0), meters(10.0), meters(10.0), meters(100.0)),
        ]

        solver = Bpp3dSolver()
        result = solver.solve(items, bins)

        assert isinstance(result, Ok)
        assert isinstance(result.value, Bpp3dSolution)

    def test_solve_with_extra_constraints(self) -> None:
        """Test solving with extra constraints (extension point)."""
        items = [
            Item("item1", meters(1.0), meters(1.0), meters(1.0), meters(10.0)),
        ]
        bins = [
            Bin("bin1", meters(10.0), meters(10.0), meters(10.0), meters(100.0)),
        ]

        # Extension point: extra constraints
        extra_constraints = ["custom_constraint_1"]

        solver = Bpp3dSolver()
        result = solver.solve(items, bins, extra_constraints=extra_constraints)

        assert isinstance(result, Ok)
