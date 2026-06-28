"""BPP1D 端到端测试 / BPP1D end-to-end tests.

使用 MockSolver 完成完整装箱流程。
Complete packing workflow with MockSolver.
"""

from __future__ import annotations

from ospf_python.framework.bpp1d.application.bpp1d_application_service import (
    Bpp1dApplicationService,
    PackingRequest,
    PackingResponse,
)
from ospf_python.framework.bpp1d.domain.constraint.constraint_context import (
    ConstraintContext,
)
from ospf_python.framework.bpp1d.domain.constraint.model.constraint import (
    Constraint,
)
from ospf_python.framework.bpp1d.domain.item.item_context import ItemContext
from ospf_python.framework.bpp1d.domain.item.model.item import Item
from ospf_python.framework.bpp1d.domain.solution.model.solution import Solution
from ospf_python.framework.bpp1d.domain.solution.solution_context import (
    SolutionContext,
)
from ospf_python.framework.bpp1d.infrastructure.bpp1d_dto import (
    Bpp1dInputDto,
    Bpp1dOutputDto,
    ItemDto,
)
from ospf_python.framework.bpp1d.infrastructure.bpp1d_solver_adapter import (
    Bpp1dSolverAdapter,
)


class MockSolver:
    """模拟求解器 / Mock solver for e2e testing.

    不调用真实求解器，直接返回预设方案。
    Returns preset solutions without calling a real solver.
    """

    def __init__(self) -> None:
        self._called = False

    def solve(
        self,
        input_dto: Bpp1dInputDto,
    ) -> Bpp1dOutputDto:
        """模拟求解 / Mock solve.

        Args:
            input_dto: 输入 DTO / Input DTO.

        Returns:
            模拟输出 DTO / Mock output DTO.
        """
        self._called = True
        bin_dtos = tuple(
            Bpp1dOutputDto.BinDto(
                bin_key=f"mock_bin_{i}",
                item_keys=tuple(d.item_key for d in input_dto.items[i : i + 2]),
                used_capacity=sum(
                    d.width for d in input_dto.items[i : i + 2]
                ),
            )
            for i in range(0, len(input_dto.items), 2)
        )
        return Bpp1dOutputDto.create(
            solution_key="mock_solution",
            bins=bin_dtos,
            bin_count=len(bin_dtos),
            objective_value=float(len(bin_dtos)),
        )

    @property
    def called(self) -> bool:
        """是否已调用 / Whether called."""
        return self._called


class TestBpp1dE2e:
    """BPP1D 端到端测试 / BPP1D e2e tests."""

    def _make_items(self) -> tuple[Item, ...]:
        """创建测试物品 / Create test items."""
        return (
            Item.create(item_key="item_a", width=3.0, height=1.0, weight=1.0),
            Item.create(item_key="item_b", width=4.0, height=1.0, weight=2.0),
            Item.create(item_key="item_c", width=2.0, height=1.0, weight=0.5),
            Item.create(item_key="item_d", width=5.0, height=1.0, weight=1.5),
        )

    def test_application_service_flow(self) -> None:
        """应用服务完整流程 / Application service full flow."""
        service = Bpp1dApplicationService.create(bin_capacity=10.0)
        items = self._make_items()
        request = PackingRequest.create(bin_capacity=10.0, items=items)
        response = service.execute(request)

        assert isinstance(response, PackingResponse)
        assert response.solution.bin_count >= 1
        assert response.solution.total_items == 4
        assert response.is_valid is True

    def test_application_service_with_constraints(self) -> None:
        """带约束的应用服务 / Application service with constraints."""
        service = Bpp1dApplicationService.create(bin_capacity=10.0)
        items = self._make_items()
        constraints = (
            Constraint.weight_limit(
                constraint_key="w1",
                item_keys=("item_a", "item_b"),
                max_weight=5.0,
            ),
        )
        request = PackingRequest.create(
            bin_capacity=10.0,
            items=items,
            constraints=constraints,
        )
        response = service.execute(request)
        assert response.solution.bin_count >= 1

    def test_solver_adapter(self) -> None:
        """求解器适配器 / Solver adapter."""
        adapter = Bpp1dSolverAdapter.create(bin_capacity=10.0)
        items = self._make_items()
        input_dto = Bpp1dInputDto.create(
            bin_capacity=10.0,
            items=tuple(
                ItemDto.create(
                    item_key=i.item_key,
                    width=i.width,
                    height=i.height,
                    weight=i.weight,
                )
                for i in items
            ),
        )
        output = adapter.solve(input_dto)
        assert isinstance(output, Bpp1dOutputDto)
        assert output.bin_count >= 1
        assert len(output.bins) >= 1

    def test_mock_solver_workflow(self) -> None:
        """MockSolver 工作流 / MockSolver workflow."""
        mock = MockSolver()
        items = self._make_items()
        input_dto = Bpp1dInputDto.create(
            bin_capacity=10.0,
            items=tuple(
                ItemDto.create(
                    item_key=i.item_key,
                    width=i.width,
                    height=i.height,
                    weight=i.weight,
                )
                for i in items
            ),
        )
        output = mock.solve(input_dto)
        assert mock.called is True
        assert output.solution_key == "mock_solution"
        assert output.bin_count == 2

    def test_item_context_register_and_lookup(self) -> None:
        """物品上下文注册与查询 / Item context register and lookup."""
        ctx = ItemContext.create()
        items = self._make_items()
        ctx = ctx.register_many(items)
        assert ctx.count == 4
        assert ctx.get("item_a").width == 3.0
        assert len(ctx.get_all()) == 4

    def test_constraint_context_register(self) -> None:
        """约束上下文注册 / Constraint context register."""
        ctx = ConstraintContext.create()
        c = Constraint.weight_limit(
            constraint_key="w1",
            item_keys=("a", "b"),
            max_weight=10.0,
        )
        ctx = ctx.register(c)
        assert ctx.count == 1
        assert ctx.get("w1").is_weight_limit
        assert len(ctx.get_by_item("a")) == 1

    def test_solution_context_register_and_best(self) -> None:
        """解上下文注册与最优解 / Solution context register and best."""
        ctx = SolutionContext.create()
        sol_a = Solution.create(
            solution_key="s1",
            objective_value=3.0,
        )
        sol_b = Solution.create(
            solution_key="s2",
            objective_value=1.0,
        )
        ctx = ctx.register(sol_a)
        ctx = ctx.register(sol_b)
        assert ctx.count == 2
        best = ctx.get_best()
        assert best.solution_key == "s2"

    def test_full_domain_wiring(self) -> None:
        """完整领域模型连接 / Full domain model wiring."""
        items = self._make_items()
        constraint = Constraint.weight_limit(
            constraint_key="w1",
            item_keys=("item_a", "item_b", "item_c", "item_d"),
            max_weight=20.0,
        )

        # Register items
        item_ctx = ItemContext.create().register_many(items)
        assert item_ctx.count == 4

        # Register constraint
        constraint_ctx = ConstraintContext.create().register(constraint)
        assert constraint_ctx.count == 1

        # Execute packing
        service = Bpp1dApplicationService.create(bin_capacity=10.0)
        request = PackingRequest.create(
            bin_capacity=10.0,
            items=item_ctx.get_all(),
            constraints=constraint_ctx.get_all(),
        )
        response = service.execute(request)

        # Register solution
        sol_ctx = SolutionContext.create().register(response.solution)
        assert sol_ctx.count == 1
        assert sol_ctx.get_best().bin_count >= 1
