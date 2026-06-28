"""BPP1D 求解器集成测试 / BPP1D solver integration tests.

测试 BinPacker 装箱算法和 SolutionValidator 验证逻辑。
Test BinPacker algorithm and SolutionValidator in BPP1D.
"""

from __future__ import annotations

from ospf_python.framework.bpp1d.domain.constraint.model.constraint import (
    Constraint,
)
from ospf_python.framework.bpp1d.domain.item.model.item import Item
from ospf_python.framework.bpp1d.domain.item.service.item_merger import (
    ItemMerger,
)
from ospf_python.framework.bpp1d.domain.solution.service.bin_packer import (
    BinPacker,
)
from ospf_python.framework.bpp1d.domain.solution.service.solution_validator import (
    SolutionValidator,
    ValidationReport,
)


class TestBinPacker:
    """装箱器测试 / Bin packer tests."""

    def test_pack_empty_items(self) -> None:
        """空物品装箱 / Pack empty items."""
        packer = BinPacker.create(bin_capacity=10.0)
        solution = packer.pack(())
        assert solution.bin_count == 0
        assert solution.solution_key == "empty"

    def test_pack_single_item(self) -> None:
        """单物品装箱 / Pack single item."""
        packer = BinPacker.create(bin_capacity=10.0)
        item = Item.create(item_key="a", width=5.0, height=1.0)
        solution = packer.pack((item,))
        assert solution.bin_count == 1
        assert solution.total_items == 1

    def test_pack_multiple_items_one_bin(self) -> None:
        """多物品装入一个箱子 / Multiple items in one bin."""
        packer = BinPacker.create(bin_capacity=10.0)
        items = (
            Item.create(item_key="a", width=3.0, height=1.0),
            Item.create(item_key="b", width=4.0, height=1.0),
            Item.create(item_key="c", width=2.0, height=1.0),
        )
        solution = packer.pack(items)
        assert solution.bin_count == 1
        assert solution.total_items == 3

    def test_pack_multiple_bins(self) -> None:
        """需要多个箱子 / Multiple bins needed."""
        packer = BinPacker.create(bin_capacity=5.0)
        items = (
            Item.create(item_key="a", width=4.0, height=1.0),
            Item.create(item_key="b", width=4.0, height=1.0),
            Item.create(item_key="c", width=4.0, height=1.0),
        )
        solution = packer.pack(items)
        assert solution.bin_count >= 2
        assert solution.total_items == 3

    def test_pack_ffd_order(self) -> None:
        """FFD 降序排列 / FFD descending order."""
        packer = BinPacker.create(bin_capacity=10.0)
        items = (
            Item.create(item_key="small", width=1.0, height=1.0),
            Item.create(item_key="large", width=8.0, height=1.0),
            Item.create(item_key="medium", width=5.0, height=1.0),
        )
        solution = packer.pack(items)
        # large(8) + small(1) = 9 in bin_0, medium(5) in bin_1
        assert solution.bin_count == 2

    def test_pack_with_results(self) -> None:
        """带详细结果的装箱 / Pack with detailed results."""
        packer = BinPacker.create(bin_capacity=10.0)
        items = (
            Item.create(item_key="a", width=5.0, height=1.0),
            Item.create(item_key="b", width=3.0, height=1.0),
        )
        solution, results = packer.pack_with_results(items)
        assert solution.bin_count == 1
        assert len(results) == 2


class TestSolutionValidator:
    """解验证器测试 / Solution validator tests."""

    def test_valid_solution(self) -> None:
        """有效解验证 / Validate valid solution."""
        packer = BinPacker.create(bin_capacity=10.0)
        items = (
            Item.create(item_key="a", width=5.0, height=1.0),
            Item.create(item_key="b", width=3.0, height=1.0),
        )
        solution = packer.pack(items)
        validator = SolutionValidator.create()
        report = validator.validate(
            solution=solution,
            items=items,
            constraints=(),
        )
        assert report.valid is True
        assert len(report.errors) == 0

    def test_solution_with_weight_constraint(self) -> None:
        """带重量约束的解验证 / Validate with weight constraint."""
        packer = BinPacker.create(bin_capacity=10.0)
        items = (
            Item.create(item_key="a", width=5.0, height=1.0, weight=3.0),
            Item.create(item_key="b", width=3.0, height=1.0, weight=4.0),
        )
        solution = packer.pack(items)
        validator = SolutionValidator.create()

        # Constraint that is satisfied
        constraint_ok = Constraint.weight_limit(
            constraint_key="w1",
            item_keys=("a", "b"),
            max_weight=10.0,
        )
        report = validator.validate(
            solution=solution,
            items=items,
            constraints=(constraint_ok,),
        )
        assert report.valid is True

    def test_validation_report_fail(self) -> None:
        """验证报告失败 / Validation report fail."""
        report = ValidationReport.fail(errors=("error_1", "error_2"))
        assert report.valid is False
        assert len(report.errors) == 2


class TestItemMerger:
    """物品合并器测试 / Item merger tests."""

    def test_merge_empty(self) -> None:
        """合并空物品 / Merge empty items."""
        merger = ItemMerger.create()
        result = merger.merge_duplicates(())
        assert len(result) == 0

    def test_merge_no_duplicates(self) -> None:
        """合并不重复物品 / Merge non-duplicate items."""
        merger = ItemMerger.create()
        items = (
            Item.create(item_key="a", width=3.0, height=2.0),
            Item.create(item_key="b", width=5.0, height=1.0),
        )
        result = merger.merge_duplicates(items)
        assert len(result) == 2

    def test_merge_duplicates(self) -> None:
        """合并重复物品 / Merge duplicate items."""
        merger = ItemMerger.create()
        items = (
            Item.create(item_key="a", width=3.0, height=2.0, weight=1.0),
            Item.create(item_key="b", width=3.0, height=2.0, weight=2.0),
            Item.create(item_key="c", width=5.0, height=1.0, weight=0.5),
        )
        result = merger.merge_duplicates(items)
        assert len(result) == 2
        # Merged item should have summed weight
        weights = sorted(i.weight for i in result)
        assert weights == [0.5, 3.0]

    def test_sort_by_width_desc(self) -> None:
        """按宽度降序排序 / Sort by width descending."""
        merger = ItemMerger.create()
        items = (
            Item.create(item_key="s", width=1.0, height=1.0),
            Item.create(item_key="l", width=5.0, height=1.0),
            Item.create(item_key="m", width=3.0, height=1.0),
        )
        result = merger.sort_by_width_desc(items)
        assert result[0].width == 5.0
        assert result[1].width == 3.0
        assert result[2].width == 1.0

    def test_filter_fit(self) -> None:
        """过滤可装入物品 / Filter items that fit."""
        merger = ItemMerger.create()
        items = (
            Item.create(item_key="a", width=3.0, height=1.0),
            Item.create(item_key="b", width=8.0, height=1.0),
            Item.create(item_key="c", width=5.0, height=1.0),
        )
        result = merger.filter_fit(items, capacity=5.0)
        assert len(result) == 2
        keys = {i.item_key for i in result}
        assert keys == {"a", "c"}


# ============================================================
# Deep behavioral: feasible/infeasible, boundary, objective
# ============================================================


class TestBinPackerFeasibility:
    """装箱可行性测试。/ Bin packer feasibility tests."""

    def test_item_exactly_fits_capacity(self) -> None:
        """物品恰好等于容量。/ Item exactly equals capacity."""
        packer = BinPacker.create(bin_capacity=10.0)
        item = Item.create(item_key="a", width=10.0, height=1.0)
        solution = packer.pack((item,))
        assert solution.bin_count == 1
        assert solution.total_items == 1

    def test_item_exceeds_capacity_still_packed(self) -> None:
        """物品超出容量仍被装入（FFD 允许）。/ Item exceeding capacity still packed (FFD allows)."""
        packer = BinPacker.create(bin_capacity=5.0)
        item = Item.create(item_key="a", width=10.0, height=1.0)
        solution = packer.pack((item,))
        # FFD will place it in a new bin even if it overflows
        assert solution.bin_count == 1
        assert solution.total_items == 1

    def test_many_items_fill_bins_efficiently(self) -> None:
        """多个物品高效装箱。/ Many items packed efficiently."""
        packer = BinPacker.create(bin_capacity=10.0)
        items = tuple(
            Item.create(item_key=f"i{i}", width=3.0, height=1.0)
            for i in range(10)
        )
        solution = packer.pack(items)
        # 10 items of width 3 → 3 per bin → ceil(10/3) = 4 bins
        assert solution.bin_count == 4
        assert solution.total_items == 10

    def test_objective_value_equals_bin_count(self) -> None:
        """目标值等于箱数。/ Objective value equals bin count."""
        packer = BinPacker.create(bin_capacity=10.0)
        items = (
            Item.create(item_key="a", width=6.0, height=1.0),
            Item.create(item_key="b", width=6.0, height=1.0),
            Item.create(item_key="c", width=6.0, height=1.0),
        )
        solution = packer.pack(items)
        assert solution.objective_value == float(solution.bin_count)

    def test_ffd_sorting_by_width_desc(self) -> None:
        """FFD 按宽度降序排列。/ FFD sorts by width descending."""
        packer = BinPacker.create(bin_capacity=10.0)
        items = (
            Item.create(item_key="s", width=1.0, height=1.0),
            Item.create(item_key="l", width=9.0, height=1.0),
            Item.create(item_key="m", width=5.0, height=1.0),
        )
        solution = packer.pack(items)
        # l(9) + s(1) = 10 in bin_0, m(5) in bin_1
        assert solution.bin_count == 2

    def test_pack_with_results_consistency(self) -> None:
        """带结果装箱与普通装箱一致。/ Pack with results consistent with pack."""
        packer = BinPacker.create(bin_capacity=10.0)
        items = (
            Item.create(item_key="a", width=5.0, height=1.0),
            Item.create(item_key="b", width=3.0, height=1.0),
            Item.create(item_key="c", width=4.0, height=1.0),
        )
        sol1 = packer.pack(items)
        sol2, results = packer.pack_with_results(items)
        assert sol1.bin_count == sol2.bin_count
        assert sol1.total_items == sol2.total_items
        assert len(results) == 3


class TestSolutionValidatorDeep:
    """解验证器深度测试。/ Solution validator deep tests."""

    def test_validate_all_items_packed(self) -> None:
        """验证所有物品已装入。/ Validate all items are packed."""
        packer = BinPacker.create(bin_capacity=10.0)
        items = (
            Item.create(item_key="a", width=5.0, height=1.0),
            Item.create(item_key="b", width=3.0, height=1.0),
        )
        solution = packer.pack(items)
        validator = SolutionValidator.create()
        report = validator.validate(solution=solution, items=items, constraints=())
        assert report.valid is True

    def test_validate_with_violated_weight_constraint(self) -> None:
        """验证违反重量约束的解。/ Validate solution violating weight constraint."""
        packer = BinPacker.create(bin_capacity=100.0)
        items = (
            Item.create(item_key="a", width=5.0, height=1.0, weight=8.0),
            Item.create(item_key="b", width=3.0, height=1.0, weight=7.0),
        )
        solution = packer.pack(items)
        validator = SolutionValidator.create()
        # Constraint that is violated (max 10, total 15)
        constraint = Constraint.weight_limit(
            constraint_key="w1",
            item_keys=("a", "b"),
            max_weight=10.0,
        )
        report = validator.validate(
            solution=solution,
            items=items,
            constraints=(constraint,),
        )
        assert report.valid is False
