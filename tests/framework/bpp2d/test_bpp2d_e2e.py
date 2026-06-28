"""BPP2D 端到端测试 / BPP2D end-to-end tests.

使用 MockSolver 完成完整二维装箱流程。
Complete 2D bin packing workflow with MockSolver.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ospf_python.framework.bpp2d.domain.bpp2d_context import Bpp2dContext
from ospf_python.framework.bpp2d.domain.constraint.constraint_context import (
    ConstraintContext,
)
from ospf_python.framework.bpp2d.domain.constraint.model.constraint_base import (
    ConstraintType,
)
from ospf_python.framework.bpp2d.domain.constraint.model.geometric_constraint import (
    GeometricConstraint,
)
from ospf_python.framework.bpp2d.domain.constraint.model.weight_constraint import (
    WeightConstraint,
)
from ospf_python.framework.bpp2d.domain.item.item_context import ItemContext
from ospf_python.framework.bpp2d.domain.item.model.circle import Circle
from ospf_python.framework.bpp2d.domain.item.model.rectangle import Rectangle
from ospf_python.framework.bpp2d.domain.service.constraint_checker import (
    ConstraintChecker,
)
from ospf_python.framework.bpp2d.domain.service.geometric_packer import (
    GeometricPacker,
)

if TYPE_CHECKING:
    from ospf_python.framework.bpp2d.domain.item.model.packing_result import (
        PackingResult,
    )


class MockSolver:
    """模拟求解器 / Mock solver for 2D bin packing e2e testing.

    使用简单的贪心策略放置矩形物品。
    Places rectangles using a simple greedy strategy.
    """

    def __init__(self) -> None:
        self._called = False

    def solve(
        self,
        packer: GeometricPacker,
        items: tuple[Rectangle, ...],
    ) -> tuple[PackingResult, ...]:
        """模拟求解 / Mock solve.

        从左到右、从下到上逐行放置。
        Places items left-to-right, bottom-to-top in rows.

        Args:
            packer: 几何装箱器 / Geometric packer.
            items: 待放置矩形 / Rectangles to place.

        Returns:
            放置结果 / Placement results.
        """
        self._called = True
        results: list[PackingResult] = []
        cursor_x = 0.0
        cursor_y = 0.0
        row_height = 0.0

        for item in items:
            if cursor_x + item.width > packer.container_width:
                cursor_x = 0.0
                cursor_y += row_height
                row_height = 0.0

            if cursor_y + item.height > packer.container_height:
                break

            result = packer.place_rectangle(
                item, cursor_x, cursor_y,
            )
            if result.is_ok():
                results.append(result.unwrap())
                cursor_x += item.width
                row_height = max(row_height, item.height)

        return tuple(results)

    @property
    def called(self) -> bool:
        """是否已调用 / Whether called."""
        return self._called


class TestBpp2dE2e:
    """BPP2D 端到端测试 / BPP2D e2e tests."""

    def _make_items(self) -> tuple[Rectangle, ...]:
        """创建测试矩形物品 / Create test rectangles."""
        return (
            Rectangle.create(
                item_key="r1",
                width=30.0,
                height=20.0,
                weight=5.0,
            ),
            Rectangle.create(
                item_key="r2",
                width=20.0,
                height=10.0,
                weight=3.0,
            ),
            Rectangle.create(
                item_key="r3",
                width=15.0,
                height=15.0,
                weight=2.0,
            ),
            Rectangle.create(
                item_key="r4",
                width=25.0,
                height=10.0,
                weight=4.0,
            ),
        )

    def test_mock_solver_places_items(self) -> None:
        """MockSolver 放置物品 / MockSolver places items."""
        packer = GeometricPacker.create(
            container_width=100.0,
            container_height=100.0,
        )
        items = self._make_items()
        solver = MockSolver()
        results = solver.solve(packer, items)

        assert solver.called is True
        assert len(results) == 4

    def test_mock_solver_respects_boundaries(self) -> None:
        """MockSolver 尊重边界 / MockSolver respects boundaries."""
        packer = GeometricPacker.create(
            container_width=60.0,
            container_height=100.0,
        )
        items = self._make_items()
        solver = MockSolver()
        results = solver.solve(packer, items)

        # Some items may not fit in narrow container
        for r in results:
            assert r.right <= packer.container_width + 1e-9
            assert r.top <= packer.container_height + 1e-9

    def test_mock_solver_no_overlap(self) -> None:
        """MockSolver 无重叠 / MockSolver no overlap."""
        packer = GeometricPacker.create(
            container_width=100.0,
            container_height=100.0,
        )
        items = self._make_items()
        solver = MockSolver()
        results = solver.solve(packer, items)

        overlap_result = packer.check_no_overlap(results)
        assert overlap_result.is_ok()

    def test_item_context_register_and_query(self) -> None:
        """物品上下文注册与查询 / Item context register and query."""
        ctx = ItemContext()
        rect = Rectangle.create(
            item_key="r1",
            width=10.0,
            height=5.0,
            weight=2.0,
        )
        circle = Circle.create(item_key="c1", radius=3.0, weight=1.0)

        result_r = ctx.register(rect)
        assert result_r.is_ok()
        result_c = ctx.register(circle)
        assert result_c.is_ok()

        assert ctx.size == 2
        assert len(ctx.rectangles()) == 1
        assert len(ctx.circles()) == 1
        assert ctx.total_weight == 3.0

    def test_item_context_duplicate_rejected(self) -> None:
        """重复物品被拒绝 / Duplicate item rejected."""
        ctx = ItemContext()
        rect = Rectangle.create(item_key="r1", width=10.0, height=5.0)
        ctx.register(rect)
        result = ctx.register(rect)
        assert result.is_failed()

    def test_constraint_context_register_and_query(self) -> None:
        """约束上下文注册与查询 / Constraint context register and query."""
        ctx = ConstraintContext()
        gc = GeometricConstraint.create(
            constraint_key="geo_1",
            max_x=100.0,
            max_y=100.0,
        )
        wc = WeightConstraint.create(
            constraint_key="wt_1",
            max_weight=50.0,
        )
        ctx.register(gc)
        ctx.register(wc)

        assert ctx.size == 2
        assert ctx.get("geo_1").constraint_type == ConstraintType.GEOMETRIC
        assert ctx.get("wt_1").constraint_type == ConstraintType.WEIGHT

    def test_full_domain_wiring(self) -> None:
        """完整领域模型连接 / Full domain model wiring."""
        # Setup contexts
        item_ctx = ItemContext()
        constraint_ctx = ConstraintContext()

        # Register items
        items = self._make_items()
        for item in items:
            item_ctx.register(item)
        assert item_ctx.size == 4

        # Register constraints
        gc = GeometricConstraint.create(
            constraint_key="geo_1",
            max_x=200.0,
            max_y=200.0,
        )
        wc = WeightConstraint.create(
            constraint_key="wt_1",
            max_weight=50.0,
        )
        constraint_ctx.register(gc)
        constraint_ctx.register(wc)
        assert constraint_ctx.size == 2

        # Create aggregate context
        bpp_ctx = Bpp2dContext.create(
            item_context=item_ctx,
            constraint_context=constraint_ctx,
        )
        assert bpp_ctx.is_ready is True
        assert bpp_ctx.item_count == 4
        assert bpp_ctx.constraint_count == 2
        assert bpp_ctx.total_item_weight == 14.0

        # Solve with mock
        packer = GeometricPacker.create(
            container_width=100.0,
            container_height=100.0,
        )
        solver = MockSolver()
        rectangles = item_ctx.rectangles()
        results = solver.solve(packer, rectangles)

        # Validate
        checker = ConstraintChecker.create()
        weight_map = {i.item_key: i.weight for i in items}
        check_result = checker.validate_solution(
            constraints=constraint_ctx.constraints(),
            placed=results,
            item_weights=weight_map,
        )
        assert check_result.is_ok()
