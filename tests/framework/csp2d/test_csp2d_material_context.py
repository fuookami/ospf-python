"""CSP2D 材料上下文行为测试 / CSP2D material context behavioral tests.

测试 MaterialContext 的边缘场景和查询方法。
Test MaterialContext edge cases and lookup methods.
"""

from __future__ import annotations

from ospf_python.framework.csp2d.domain.material.material_context import (
    MaterialContext,
)
from ospf_python.framework.csp2d.domain.material.model.sheet import Sheet
from ospf_python.framework.csp2d.domain.material.model.strip import Strip


class TestMaterialContextBehavioral:
    """材料上下文行为测试 / Material context behavioral tests."""

    def test_register_duplicate_sheet_rejected(self) -> None:
        """重复板材被拒绝 / Duplicate sheet rejected."""
        ctx = MaterialContext()
        sheet = Sheet.create(name="S1", width=100.0, height=200.0, cost=10.0)
        ctx.register_sheet(sheet)
        result = ctx.register_sheet(sheet)
        assert result.is_failed()

    def test_register_duplicate_strip_rejected(self) -> None:
        """重复卷材被拒绝 / Duplicate strip rejected."""
        ctx = MaterialContext()
        strip = Strip.create(name="R1", width=50.0, length=1000.0, cost=5.0)
        ctx.register_strip(strip)
        result = ctx.register_strip(strip)
        assert result.is_failed()

    def test_get_sheet_returns_none_for_missing(self) -> None:
        """获取不存在板材返回 None / Get sheet returns None for missing."""
        ctx = MaterialContext()
        assert ctx.get_sheet("nonexistent") is None

    def test_get_sheet_or_error_not_found(self) -> None:
        """获取不存在板材返回错误 / Get sheet or error not found."""
        ctx = MaterialContext()
        result = ctx.get_sheet_or_error("nonexistent")
        assert result.is_failed()

    def test_get_strip_returns_none_for_missing(self) -> None:
        """获取不存在卷材返回 None / Get strip returns None for missing."""
        ctx = MaterialContext()
        assert ctx.get_strip("nonexistent") is None

    def test_get_strip_or_error_not_found(self) -> None:
        """获取不存在卷材返回错误 / Get strip or error not found."""
        ctx = MaterialContext()
        result = ctx.get_strip_or_error("nonexistent")
        assert result.is_failed()

    def test_sheets_returns_all(self) -> None:
        """获取所有板材 / Get all sheets."""
        ctx = MaterialContext()
        s1 = Sheet.create(name="S1", width=100.0, height=200.0, cost=10.0)
        s2 = Sheet.create(name="S2", width=150.0, height=300.0, cost=20.0)
        ctx.register_sheet(s1)
        ctx.register_sheet(s2)
        all_sheets = ctx.sheets()
        assert len(all_sheets) == 2

    def test_strips_returns_all(self) -> None:
        """获取所有卷材 / Get all strips."""
        ctx = MaterialContext()
        r1 = Strip.create(name="R1", width=50.0, length=1000.0, cost=5.0)
        r2 = Strip.create(name="R2", width=30.0, length=500.0, cost=3.0)
        ctx.register_strip(r1)
        ctx.register_strip(r2)
        all_strips = ctx.strips()
        assert len(all_strips) == 2

    def test_items_combines_sheets_and_strips(self) -> None:
        """items 合并板材和卷材 / Items combines sheets and strips."""
        ctx = MaterialContext()
        s1 = Sheet.create(name="S1", width=100.0, height=200.0, cost=10.0)
        r1 = Strip.create(name="R1", width=50.0, length=1000.0, cost=5.0)
        ctx.register_sheet(s1)
        ctx.register_strip(r1)
        all_items = ctx.items()
        assert len(all_items) == 2

    def test_contains_sheet(self) -> None:
        """检查板材是否存在 / Check sheet exists."""
        ctx = MaterialContext()
        sheet = Sheet.create(name="S1", width=100.0, height=200.0, cost=10.0)
        ctx.register_sheet(sheet)
        assert ctx.contains_sheet("S1") is True
        assert ctx.contains_sheet("nonexistent") is False

    def test_contains_strip(self) -> None:
        """检查卷材是否存在 / Check strip exists."""
        ctx = MaterialContext()
        strip = Strip.create(name="R1", width=50.0, length=1000.0, cost=5.0)
        ctx.register_strip(strip)
        assert ctx.contains_strip("R1") is True
        assert ctx.contains_strip("nonexistent") is False

    def test_sheet_count(self) -> None:
        """板材数量 / Sheet count."""
        ctx = MaterialContext()
        assert ctx.sheet_count == 0
        sheet = Sheet.create(name="S1", width=100.0, height=200.0, cost=10.0)
        ctx.register_sheet(sheet)
        assert ctx.sheet_count == 1

    def test_strip_count(self) -> None:
        """卷材数量 / Strip count."""
        ctx = MaterialContext()
        assert ctx.strip_count == 0
        strip = Strip.create(name="R1", width=50.0, length=1000.0, cost=5.0)
        ctx.register_strip(strip)
        assert ctx.strip_count == 1

    def test_size_combines_sheets_and_strips(self) -> None:
        """size 为板材和卷材总数 / Size combines sheets and strips."""
        ctx = MaterialContext()
        sheet = Sheet.create(name="S1", width=100.0, height=200.0, cost=10.0)
        strip = Strip.create(name="R1", width=50.0, length=1000.0, cost=5.0)
        ctx.register_sheet(sheet)
        ctx.register_strip(strip)
        assert ctx.size == 2

    def test_is_empty_with_only_sheets(self) -> None:
        """仅有板材时不为空 / Not empty with only sheets."""
        ctx = MaterialContext()
        sheet = Sheet.create(name="S1", width=100.0, height=200.0, cost=10.0)
        ctx.register_sheet(sheet)
        assert ctx.is_empty is False

    def test_is_empty_with_only_strips(self) -> None:
        """仅有卷材时不为空 / Not empty with only strips."""
        ctx = MaterialContext()
        strip = Strip.create(name="R1", width=50.0, length=1000.0, cost=5.0)
        ctx.register_strip(strip)
        assert ctx.is_empty is False

    def test_clear(self) -> None:
        """清空材料 / Clear materials."""
        ctx = MaterialContext()
        sheet = Sheet.create(name="S1", width=100.0, height=200.0, cost=10.0)
        strip = Strip.create(name="R1", width=50.0, length=1000.0, cost=5.0)
        ctx.register_sheet(sheet)
        ctx.register_strip(strip)
        ctx.clear()
        assert ctx.is_empty is True
        assert ctx.sheet_count == 0
        assert ctx.strip_count == 0
