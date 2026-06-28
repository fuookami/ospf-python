"""BPP1D 领域模型测试 / BPP1D domain model tests.

测试物品、箱子、装箱结果和解的创建与属性。
Test creation and properties of Item, Bin, PackingResult,
and Solution in BPP1D.
"""

from __future__ import annotations

from ospf_python.framework.bpp1d.domain.item.model.bin import Bin
from ospf_python.framework.bpp1d.domain.item.model.item import Item
from ospf_python.framework.bpp1d.domain.item.model.packing_result import (
    PackingResult,
)
from ospf_python.framework.bpp1d.domain.solution.model.solution import Solution


class TestItem:
    """物品模型测试 / Item model tests."""

    def test_create_item_with_factory(self) -> None:
        """使用工厂方法创建物品 / Create item with factory."""
        item = Item.create(
            item_key="item_1",
            width=10.0,
            height=5.0,
            weight=2.0,
        )
        assert item.item_key == "item_1"
        assert item.width == 10.0
        assert item.height == 5.0
        assert item.weight == 2.0

    def test_create_item_with_defaults(self) -> None:
        """使用默认值创建物品 / Create item with defaults."""
        item = Item(item_key="i1", width=3.0, height=2.0)
        assert item.weight == 0.0

    def test_item_area(self) -> None:
        """物品面积计算 / Item area calculation."""
        item = Item.create(
            item_key="i1",
            width=4.0,
            height=3.0,
        )
        assert item.area == 12.0

    def test_item_is_frozen(self) -> None:
        """物品不可变 / Item is frozen."""
        item = Item(item_key="i1", width=1.0, height=1.0)
        try:
            item.width = 2.0  # type: ignore[misc]
            raise AssertionError("Should raise FrozenInstanceError")
        except AttributeError:
            pass


class TestBin:
    """箱子模型测试 / Bin model tests."""

    def _make_items(self) -> tuple[Item, ...]:
        """创建测试物品 / Create test items."""
        return (
            Item.create(item_key="a", width=3.0, height=1.0, weight=1.5),
            Item.create(item_key="b", width=2.0, height=1.0, weight=0.5),
        )

    def test_create_empty_bin(self) -> None:
        """创建空箱子 / Create empty bin."""
        bin_ = Bin.create(bin_key="bin_0", capacity=10.0)
        assert bin_.bin_key == "bin_0"
        assert bin_.capacity == 10.0
        assert bin_.item_count == 0
        assert bin_.used_capacity == 0.0

    def test_bin_with_items(self) -> None:
        """装有物品的箱子 / Bin with items."""
        items = self._make_items()
        bin_ = Bin.create(bin_key="b1", capacity=10.0, items=items)
        assert bin_.item_count == 2
        assert bin_.used_capacity == 5.0

    def test_remaining_capacity(self) -> None:
        """剩余容量计算 / Remaining capacity."""
        items = self._make_items()
        bin_ = Bin.create(bin_key="b1", capacity=10.0, items=items)
        assert bin_.remaining_capacity == 5.0

    def test_is_full(self) -> None:
        """满箱检测 / Full bin detection."""
        items = (
            Item.create(item_key="a", width=10.0, height=1.0),
        )
        bin_ = Bin.create(bin_key="b1", capacity=10.0, items=items)
        assert bin_.is_full is True

    def test_total_weight(self) -> None:
        """总重量计算 / Total weight."""
        items = self._make_items()
        bin_ = Bin.create(bin_key="b1", capacity=10.0, items=items)
        assert bin_.total_weight == 2.0


class TestPackingResult:
    """装箱结果模型测试 / Packing result model tests."""

    def test_create_packing_result(self) -> None:
        """创建装箱结果 / Create packing result."""
        item = Item.create(item_key="i1", width=5.0, height=2.0)
        result = PackingResult.create(
            item=item,
            bin_key="bin_0",
            position=3.0,
        )
        assert result.item.item_key == "i1"
        assert result.bin_key == "bin_0"
        assert result.position == 3.0

    def test_end_position(self) -> None:
        """结束位置计算 / End position calculation."""
        item = Item.create(item_key="i1", width=5.0, height=2.0)
        result = PackingResult.create(
            item=item,
            bin_key="bin_0",
            position=3.0,
        )
        assert result.end_position == 8.0


class TestSolution:
    """解模型测试 / Solution model tests."""

    def _make_solution(self) -> Solution:
        """创建测试解 / Create test solution."""
        items_a = (
            Item.create(item_key="a", width=3.0, height=1.0, weight=1.0),
            Item.create(item_key="b", width=2.0, height=1.0, weight=2.0),
        )
        items_b = (
            Item.create(item_key="c", width=4.0, height=1.0, weight=0.5),
        )
        bins = (
            Bin.create(bin_key="bin_0", capacity=10.0, items=items_a),
            Bin.create(bin_key="bin_1", capacity=10.0, items=items_b),
        )
        return Solution.create(
            solution_key="sol_1",
            bins=bins,
            objective_value=2.0,
        )

    def test_solution_properties(self) -> None:
        """解的基本属性 / Solution basic properties."""
        sol = self._make_solution()
        assert sol.solution_key == "sol_1"
        assert sol.bin_count == 2
        assert sol.objective_value == 2.0

    def test_total_items(self) -> None:
        """解中总物品数 / Total items in solution."""
        sol = self._make_solution()
        assert sol.total_items == 3

    def test_total_weight(self) -> None:
        """解中总重量 / Total weight in solution."""
        sol = self._make_solution()
        assert sol.total_weight == 3.5

    def test_average_fill_rate(self) -> None:
        """平均填充率 / Average fill rate."""
        sol = self._make_solution()
        # bin_0: 5/10 = 0.5, bin_1: 4/10 = 0.4
        # avg = (0.5 + 0.4) / 2 = 0.45
        assert abs(sol.average_fill_rate - 0.45) < 1e-9

    def test_empty_solution_fill_rate(self) -> None:
        """空解的填充率 / Empty solution fill rate."""
        sol = Solution.create(solution_key="empty")
        assert sol.average_fill_rate == 0.0
        assert sol.bin_count == 0
        assert sol.total_items == 0
