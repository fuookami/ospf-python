"""BPP1D 迁移基线 / BPP1D migration baseline."""

from __future__ import annotations

from ospf_python.framework.bpp1d.application.bpp1d_application_service import (
    Bpp1dApplicationService,
    PackingRequest,
)
from ospf_python.framework.bpp1d.domain.constraint.model.constraint import Constraint
from ospf_python.framework.bpp1d.domain.item.item_context import ItemContext
from ospf_python.framework.bpp1d.domain.item.model.bin import Bin
from ospf_python.framework.bpp1d.domain.item.model.item import Item
from ospf_python.framework.bpp1d.domain.solution.model.solution import Solution
from ospf_python.framework.bpp1d.domain.solution.service.bin_packer import BinPacker
from ospf_python.framework.bpp1d.domain.solution.service.solution_validator import (
    SolutionValidator,
)
from ospf_python.framework.bpp1d.infrastructure.bpp1d_dto import (
    Bpp1dInputDto,
    ConstraintDto,
    ItemDto,
)
from ospf_python.framework.bpp1d.infrastructure.bpp1d_solver_adapter import (
    Bpp1dSolverAdapter,
)


def test_legacy_ffd_observation_is_not_an_optimality_claim() -> None:
    """记录旧 FFD 输出而非最优性 / Record legacy FFD, not optimality."""
    sizes = (6.0, 5.0, 3.0, 2.0, 2.0, 2.0)
    items = tuple(
        Item.create(item_key=f"i{i}", width=size, height=1.0)
        for i, size in enumerate(sizes)
    )
    packer = BinPacker.create(bin_capacity=10.0)
    solution = packer.pack(items)
    detailed, _ = packer.pack_with_results(items)
    groups = tuple(
        tuple(item.item_key for item in bin_.items) for bin_ in solution.bins
    )
    assert groups == (("i0", "i2"), ("i1", "i3", "i4"), ("i5",))
    assert detailed == solution
    assert solution.objective_value == 3.0

    witness = ((0, 3, 4), (1, 2, 5))
    assert sorted(i for group in witness for i in group) == list(range(len(items)))
    assert all(sum(sizes[i] for i in group) <= 10.0 for group in witness)


def test_legacy_merge_observation_does_not_require_identity_loss() -> None:
    """记录合并现状，不将其作为目标 / Observe merging without requiring identity loss."""
    items = (
        Item.create(item_key="a", width=3.0, height=1.0, weight=2.0),
        Item.create(item_key="b", width=3.0, height=1.0, weight=5.0),
    )
    request = PackingRequest.create(
        bin_capacity=10.0,
        items=items,
        constraints=(
            Constraint.item_exclusion(constraint_key="x", item_keys=("a", "b")),
        ),
    )
    response = Bpp1dApplicationService.create(bin_capacity=10.0).execute(request)
    assert response.item_context.get_all() == items
    assert response.solution.total_items == 1
    assert response.solution.bins[0].items == (
        Item.create(item_key="a", width=3.0, height=1.0, weight=7.0),
    )
    assert response.is_valid


def test_legacy_application_observes_request_capacity_and_overwrites_id() -> None:
    """请求容量和身份覆盖现状 / Observe request capacity and identity replacement."""
    old = Item.create(item_key="a", width=1.0, height=1.0)
    current = Item.create(item_key="a", width=6.0, height=1.0)
    other = Item.create(item_key="b", width=5.0, height=1.0)
    context = ItemContext.create().register(old)
    service = Bpp1dApplicationService(
        packer=BinPacker.create(bin_capacity=100.0), item_context=context
    )
    response = service.execute(
        PackingRequest.create(bin_capacity=10.0, items=(current, other))
    )
    assert context.get("a") == old
    assert response.item_context.get("a") == current
    assert response.solution.bin_count == 2
    assert all(bin_.capacity == 10.0 for bin_ in response.solution.bins)


def test_legacy_application_checks_exclusion_after_packing() -> None:
    """约束仅事后检查 / Constraints are checked after packing."""
    items = (
        Item.create(item_key="a", width=3.0, height=1.0),
        Item.create(item_key="b", width=2.0, height=1.0),
    )
    request = PackingRequest.create(
        bin_capacity=10.0,
        items=items,
        constraints=(
            Constraint.item_exclusion(constraint_key="x", item_keys=("a", "b")),
        ),
    )
    response = Bpp1dApplicationService.create(bin_capacity=10.0).execute(request)
    assert response.solution.bin_count == 1
    assert not response.is_valid
    assert "Exclusion violated" in response.report.errors[0]


def test_legacy_dto_adapter_observes_configured_capacity_not_dto_fields() -> None:
    """DTO 约束和容量当前未参与求解 / DTO constraints and capacity are not used."""
    request = Bpp1dInputDto.create(
        bin_capacity=3.0,
        items=(
            ItemDto.create(item_key="a", width=3.0, height=1.0),
            ItemDto.create(item_key="b", width=2.0, height=1.0),
        ),
        constraints=(
            ConstraintDto.create(
                constraint_key="x",
                constraint_type="item_exclusion",
                item_keys=("a", "b"),
            ),
        ),
    )
    result = Bpp1dSolverAdapter.create(bin_capacity=10.0).solve(request)
    assert result.bin_count == 1
    assert result.bins[0].item_keys == ("a", "b")
    assert result.bins[0].used_capacity == 5.0


def test_legacy_validator_observation_is_not_a_completeness_guarantee() -> None:
    """现有验证器不验证全局件数 / Existing validation does not check global counts."""
    item = Item.create(item_key="a", width=2.0, height=1.0)
    validator = SolutionValidator.create()
    missing = Solution.create(solution_key="missing")
    repeated = Solution.create(
        solution_key="repeated",
        bins=(
            Bin.create(bin_key="first", capacity=10.0, items=(item,)),
            Bin.create(bin_key="second", capacity=10.0, items=(item,)),
        ),
    )
    assert validator.validate(solution=missing, items=(item,), constraints=()).valid
    assert validator.validate(solution=repeated, items=(item,), constraints=()).valid
