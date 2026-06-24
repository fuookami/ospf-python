"""bpp3d 框架 Phase 18 测试 / Tests for bpp3d framework Phase 18.

覆盖 Phase 18 中所有 54 个文件的基本功能。
Covers basic functionality of all 54 files from Phase 18.
"""

from __future__ import annotations

import pytest

# ---- application/service/ ----
from ospf_python.framework.bpp3d.application.service.column_generation_algorithm import (
    ColumnGenerationAlgorithm,
)
from ospf_python.framework.bpp3d.application.service.column_generation_application_service import (
    ColumnGenerationApplicationService,
)
from ospf_python.framework.bpp3d.application.service.column_generation_packing_analyzer import (
    ColumnGenerationPackingAnalyzer,
)
from ospf_python.framework.bpp3d.application.service.column_generation_standard_executors import (
    ColumnGenerationStandardExecutor,
)
from ospf_python.framework.bpp3d.application.service.depth_boundary_layer_orientation_policy import (
    DepthBoundaryLayerOrientationPolicy,
)
from ospf_python.framework.bpp3d.application.service.layer_placement_adapter import (
    LayerPlacementAdapter,
)

# ---- domain/bla/ ----
from ospf_python.framework.bpp3d.domain.bla.bla_context import (
    BLAContext,
)
from ospf_python.framework.bpp3d.domain.bla.service.bottom_up_left_justified_algorithm import (
    BottomUpLeftJustifiedAlgorithm,
)
from ospf_python.framework.bpp3d.domain.bla.service.bottom_up_left_justified_algorithm_3d import (
    BottomUpLeftJustifiedAlgorithm3D,
)
from ospf_python.framework.bpp3d.domain.bla.service.bpp3d_bla_async import (
    Bpp3dBlaAsync,
)

# ---- domain/block_loading/ ----
from ospf_python.framework.bpp3d.domain.block_loading.block_loading_context import (
    BlockLoadingContext,
)
from ospf_python.framework.bpp3d.domain.block_loading.model.space import (
    Space,
)
from ospf_python.framework.bpp3d.domain.block_loading.service.bpp3d_block_loading_async import (
    Bpp3dBlockLoadingAsync,
)
from ospf_python.framework.bpp3d.domain.block_loading.service.complex_block_generator import (
    ComplexBlockGenerator,
)
from ospf_python.framework.bpp3d.domain.block_loading.service.cylinder_unsupported_guard import (
    CylinderUnsupportedGuard,
)
from ospf_python.framework.bpp3d.domain.block_loading.service.depth_first_search_algorithm import (
    DepthFirstSearchAlgorithm,
)
from ospf_python.framework.bpp3d.domain.block_loading.service.multi_layer_heuristic_search_algorithm import (
    MultiLayerHeuristicSearchAlgorithm,
)
from ospf_python.framework.bpp3d.domain.block_loading.service.simple_block_generator import (
    SimpleBlockGenerator,
)

# ---- domain/layer_assignment/ ----
from ospf_python.framework.bpp3d.domain.layer_assignment.imprecise_aggregation import (
    ImpreciseAggregation,
)
from ospf_python.framework.bpp3d.domain.layer_assignment.layer_assignment_context import (
    LayerAssignmentContext,
)
from ospf_python.framework.bpp3d.domain.layer_assignment.model.assignment import (
    Assignment,
)
from ospf_python.framework.bpp3d.domain.layer_assignment.model.bpp3d_solver_value_adapter import (
    Bpp3dSolverValueAdapter,
)
from ospf_python.framework.bpp3d.domain.layer_assignment.model.capacity import (
    Capacity,
)
from ospf_python.framework.bpp3d.domain.layer_assignment.model.layer_aggregation import (
    LayerAggregation,
)
from ospf_python.framework.bpp3d.domain.layer_assignment.model.load import (
    Load,
)
from ospf_python.framework.bpp3d.domain.layer_assignment.model.scaled_bpp3d_solver_value_adapter import (
    ScaledBpp3dSolverValueAdapter,
)
from ospf_python.framework.bpp3d.domain.layer_assignment.precise_aggregation import (
    PreciseAggregation,
)
from ospf_python.framework.bpp3d.domain.layer_assignment.service.limits.better_layer_maximization import (
    BetterLayerMaximization,
)
from ospf_python.framework.bpp3d.domain.layer_assignment.service.limits.bin_amount_minimization import (
    BinAmountMinimization,
)
from ospf_python.framework.bpp3d.domain.layer_assignment.service.limits.bin_capacity_constraint import (
    BinCapacityConstraint,
)
from ospf_python.framework.bpp3d.domain.layer_assignment.service.limits.bin_depth_constraint import (
    BinDepthConstraint,
)
from ospf_python.framework.bpp3d.domain.layer_assignment.service.limits.bin_loading_order_constraint import (
    BinLoadingOrderConstraint,
)
from ospf_python.framework.bpp3d.domain.layer_assignment.service.limits.demand_constraint import (
    DemandConstraint,
)
from ospf_python.framework.bpp3d.domain.layer_assignment.service.limits.rest_amount_minimization import (
    RestAmountMinimization,
)
from ospf_python.framework.bpp3d.domain.layer_assignment.service.limits.tail_bin_assignment_constraint import (
    TailBinAssignmentConstraint,
)
from ospf_python.framework.bpp3d.domain.layer_assignment.service.limits.tail_bin_loading_rate_minimization import (
    TailBinLoadingRateMinimization,
)
from ospf_python.framework.bpp3d.domain.layer_assignment.service.limits.volume_minimization import (
    VolumeMinimization,
)
from ospf_python.framework.bpp3d.domain.layer_assignment.service.solution_analyzer import (
    SolutionAnalyzer,
)

# ---- domain/layer_generation/ ----
from ospf_python.framework.bpp3d.domain.layer_generation.layer_generation_context import (
    LayerGenerationContext,
)
from ospf_python.framework.bpp3d.domain.layer_generation.layer_generation_program_candidate_adapters import (
    LayerGenerationProgramCandidateAdapter,
)

# ---- domain/packing/ ----
from ospf_python.framework.bpp3d.domain.packing.aggregation import (
    PackingAggregation,
)
from ospf_python.framework.bpp3d.domain.packing.model.material_attribute import (
    MaterialAttribute,
)
from ospf_python.framework.bpp3d.domain.packing.model.material_packing_numbers import (
    MaterialPackingNumbers,
)
from ospf_python.framework.bpp3d.domain.packing.model.material_packing_plan import (
    MaterialPackingPlan,
)
from ospf_python.framework.bpp3d.domain.packing.model.package_solution_like_adapter import (
    PackageSolutionLikeAdapter,
)
from ospf_python.framework.bpp3d.domain.packing.packing_context import (
    PackingContext,
)
from ospf_python.framework.bpp3d.domain.packing.service.exhaustive_material_packing_solver_executor import (
    ExhaustiveMaterialPackingSolverExecutor,
)
from ospf_python.framework.bpp3d.domain.packing.service.material_packer import (
    MaterialPacker,
)
from ospf_python.framework.bpp3d.domain.packing.service.material_packing_solver_executor import (
    MaterialPackingSolverExecutor,
)
from ospf_python.framework.bpp3d.domain.packing.service.packer import (
    Packer,
)
from ospf_python.framework.bpp3d.domain.packing.service.packing_geometry_contract import (
    PackingGeometryContract,
)
from ospf_python.framework.bpp3d.domain.packing.service.packing_geometry_guard import (
    PackingGeometryGuard,
)
from ospf_python.framework.bpp3d.domain.packing.service.packing_renderer_adapter import (
    PackingRendererAdapter,
)

# ============================================================
# application/service/ tests
# ============================================================


class TestColumnGenerationAlgorithm:
    """ColumnGenerationAlgorithm ABC 测试 / ABC tests."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            ColumnGenerationAlgorithm()  # type: ignore[abstract]

    def test_has_initialize(self) -> None:
        """有 initialize 方法 / Has initialize method."""
        assert hasattr(ColumnGenerationAlgorithm, "initialize")

    def test_has_is_optimal(self) -> None:
        """有 is_optimal 方法 / Has is_optimal method."""
        assert hasattr(ColumnGenerationAlgorithm, "is_optimal")


class TestColumnGenerationApplicationService:
    """ColumnGenerationApplicationService ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            ColumnGenerationApplicationService()  # type: ignore[abstract]

    def test_has_execute(self) -> None:
        """有 execute 方法 / Has execute method."""
        assert hasattr(ColumnGenerationApplicationService, "execute")


class TestColumnGenerationPackingAnalyzer:
    """ColumnGenerationPackingAnalyzer ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            ColumnGenerationPackingAnalyzer()  # type: ignore[abstract]

    def test_has_analyze(self) -> None:
        """有 analyze 方法 / Has analyze method."""
        assert hasattr(ColumnGenerationPackingAnalyzer, "analyze")


class TestColumnGenerationStandardExecutor:
    """ColumnGenerationStandardExecutor ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            ColumnGenerationStandardExecutor()  # type: ignore[abstract]


class TestDepthBoundaryLayerOrientationPolicy:
    """DepthBoundaryLayerOrientationPolicy ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            DepthBoundaryLayerOrientationPolicy()  # type: ignore[abstract]


class TestLayerPlacementAdapter:
    """LayerPlacementAdapter ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            LayerPlacementAdapter()  # type: ignore[abstract]


# ============================================================
# domain/bla/ tests
# ============================================================


class TestBLAContext:
    """BLAContext 冻结数据类测试 / Frozen dataclass tests."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        ctx = BLAContext(container_width=10.0)
        with pytest.raises(AttributeError):
            ctx.container_width = 20.0  # type: ignore[misc]

    def test_default_values(self) -> None:
        """默认值正确 / Default values are correct."""
        ctx = BLAContext()
        assert ctx.container_width == 0.0
        assert ctx.container_height == 0.0
        assert ctx.container_depth == 0.0
        assert ctx.items == ()
        assert ctx.max_iterations == 1000

    def test_custom_values(self) -> None:
        """自定义值正确 / Custom values are correct."""
        ctx = BLAContext(
            container_width=5.0,
            container_height=10.0,
            container_depth=3.0,
            max_iterations=500,
        )
        assert ctx.container_width == 5.0
        assert ctx.container_height == 10.0
        assert ctx.max_iterations == 500


class TestBottomUpLeftJustifiedAlgorithm:
    """BottomUpLeftJustifiedAlgorithm ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            BottomUpLeftJustifiedAlgorithm()  # type: ignore[abstract]


class TestBottomUpLeftJustifiedAlgorithm3D:
    """BottomUpLeftJustifiedAlgorithm3D ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            BottomUpLeftJustifiedAlgorithm3D()  # type: ignore[abstract]


class TestBpp3dBlaAsync:
    """Bpp3dBlaAsync ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            Bpp3dBlaAsync()  # type: ignore[abstract]


# ============================================================
# domain/block_loading/ tests
# ============================================================


class TestBlockLoadingContext:
    """BlockLoadingContext 冻结数据类测试 / Frozen dataclass tests."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        ctx = BlockLoadingContext(container_width=10.0)
        with pytest.raises(AttributeError):
            ctx.container_width = 20.0  # type: ignore[misc]

    def test_default_values(self) -> None:
        """默认值正确 / Default values are correct."""
        ctx = BlockLoadingContext()
        assert ctx.container_width == 0.0
        assert ctx.blocks == ()
        assert ctx.max_depth == 100


class TestSpace:
    """Space 冻结数据类测试 / Frozen dataclass tests."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        s = Space(x=1.0, y=2.0, z=3.0)
        with pytest.raises(AttributeError):
            s.x = 5.0  # type: ignore[misc]

    def test_default_values(self) -> None:
        """默认值为零 / Default values are zero."""
        s = Space()
        assert s.x == 0.0
        assert s.y == 0.0
        assert s.z == 0.0
        assert s.width == 0.0
        assert s.height == 0.0
        assert s.depth == 0.0

    def test_custom_values(self) -> None:
        """自定义值正确 / Custom values are correct."""
        s = Space(
            x=1.0,
            y=2.0,
            z=3.0,
            width=4.0,
            height=5.0,
            depth=6.0,
        )
        assert s.x == 1.0
        assert s.width == 4.0
        assert s.depth == 6.0


class TestBpp3dBlockLoadingAsync:
    """Bpp3dBlockLoadingAsync ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            Bpp3dBlockLoadingAsync()  # type: ignore[abstract]


class TestComplexBlockGenerator:
    """ComplexBlockGenerator ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            ComplexBlockGenerator()  # type: ignore[abstract]


class TestCylinderUnsupportedGuard:
    """CylinderUnsupportedGuard ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            CylinderUnsupportedGuard()  # type: ignore[abstract]


class TestDepthFirstSearchAlgorithm:
    """DepthFirstSearchAlgorithm ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            DepthFirstSearchAlgorithm()  # type: ignore[abstract]


class TestMultiLayerHeuristicSearchAlgorithm:
    """MultiLayerHeuristicSearchAlgorithm ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            MultiLayerHeuristicSearchAlgorithm()  # type: ignore[abstract]


class TestSimpleBlockGenerator:
    """SimpleBlockGenerator ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            SimpleBlockGenerator()  # type: ignore[abstract]


# ============================================================
# domain/layer_assignment/ tests
# ============================================================


class TestImpreciseAggregation:
    """ImpreciseAggregation 冻结数据类测试."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        agg = ImpreciseAggregation(tolerance=0.01)
        with pytest.raises(AttributeError):
            agg.tolerance = 0.05  # type: ignore[misc]

    def test_default_values(self) -> None:
        """默认值正确 / Default values are correct."""
        agg = ImpreciseAggregation()
        assert agg.tolerance == 0.01
        assert agg.max_deviation == 0.05


class TestLayerAssignmentContext:
    """LayerAssignmentContext 冻结数据类测试."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        ctx = LayerAssignmentContext(demand=10)
        with pytest.raises(AttributeError):
            ctx.demand = 20  # type: ignore[misc]

    def test_default_values(self) -> None:
        """默认值正确 / Default values are correct."""
        ctx = LayerAssignmentContext()
        assert ctx.layers == ()
        assert ctx.containers == ()
        assert ctx.demand == 0
        assert ctx.max_layers_per_bin == 100


class TestPreciseAggregation:
    """PreciseAggregation 冻结数据类测试."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        agg = PreciseAggregation(precision=1e-10)
        with pytest.raises(AttributeError):
            agg.precision = 1e-5  # type: ignore[misc]

    def test_default_precision(self) -> None:
        """默认精度正确 / Default precision is correct."""
        agg = PreciseAggregation()
        assert agg.precision == 1e-10


class TestAssignment:
    """Assignment 冻结数据类测试."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        a = Assignment(layer_id="l1", container_id="c1")
        with pytest.raises(AttributeError):
            a.layer_id = "l2"  # type: ignore[misc]

    def test_default_values(self) -> None:
        """默认值正确 / Default values are correct."""
        a = Assignment()
        assert a.layer_id == ""
        assert a.container_id == ""
        assert a.quantity == 0

    def test_custom_values(self) -> None:
        """自定义值正确 / Custom values are correct."""
        a = Assignment(
            layer_id="l1",
            container_id="c1",
            quantity=5,
        )
        assert a.layer_id == "l1"
        assert a.quantity == 5


class TestBpp3dSolverValueAdapter:
    """Bpp3dSolverValueAdapter ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            Bpp3dSolverValueAdapter()  # type: ignore[abstract]


class TestCapacity:
    """Capacity 冻结数据类测试."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        c = Capacity(width=10.0)
        with pytest.raises(AttributeError):
            c.width = 20.0  # type: ignore[misc]

    def test_default_values(self) -> None:
        """默认值正确 / Default values are correct."""
        c = Capacity()
        assert c.width == 0.0
        assert c.height == 0.0
        assert c.depth == 0.0
        assert c.weight == float("inf")

    def test_custom_values(self) -> None:
        """自定义值正确 / Custom values are correct."""
        c = Capacity(
            width=10.0,
            height=20.0,
            depth=30.0,
            weight=100.0,
        )
        assert c.width == 10.0
        assert c.weight == 100.0


class TestLayerAggregation:
    """LayerAggregation ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            LayerAggregation()  # type: ignore[abstract]


class TestLoad:
    """Load 冻结数据类测试."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        l = Load(width=5.0)
        with pytest.raises(AttributeError):
            l.width = 10.0  # type: ignore[misc]

    def test_default_values(self) -> None:
        """默认值为零 / Default values are zero."""
        l = Load()
        assert l.width == 0.0
        assert l.height == 0.0
        assert l.depth == 0.0
        assert l.weight == 0.0


class TestScaledBpp3dSolverValueAdapter:
    """ScaledBpp3dSolverValueAdapter ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            ScaledBpp3dSolverValueAdapter()  # type: ignore[abstract]


class TestSolutionAnalyzer:
    """SolutionAnalyzer ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            SolutionAnalyzer()  # type: ignore[abstract]


class TestBetterLayerMaximization:
    """BetterLayerMaximization ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            BetterLayerMaximization()  # type: ignore[abstract]


class TestBinAmountMinimization:
    """BinAmountMinimization ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            BinAmountMinimization()  # type: ignore[abstract]


class TestBinCapacityConstraint:
    """BinCapacityConstraint ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            BinCapacityConstraint()  # type: ignore[abstract]


class TestBinDepthConstraint:
    """BinDepthConstraint ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            BinDepthConstraint()  # type: ignore[abstract]


class TestBinLoadingOrderConstraint:
    """BinLoadingOrderConstraint ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            BinLoadingOrderConstraint()  # type: ignore[abstract]


class TestDemandConstraint:
    """DemandConstraint ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            DemandConstraint()  # type: ignore[abstract]


class TestRestAmountMinimization:
    """RestAmountMinimization ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            RestAmountMinimization()  # type: ignore[abstract]


class TestTailBinAssignmentConstraint:
    """TailBinAssignmentConstraint ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            TailBinAssignmentConstraint()  # type: ignore[abstract]


class TestTailBinLoadingRateMinimization:
    """TailBinLoadingRateMinimization ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            TailBinLoadingRateMinimization()  # type: ignore[abstract]


class TestVolumeMinimization:
    """VolumeMinimization ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            VolumeMinimization()  # type: ignore[abstract]


# ============================================================
# domain/layer_generation/ tests
# ============================================================


class TestLayerGenerationContext:
    """LayerGenerationContext 冻结数据类测试."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        ctx = LayerGenerationContext(container_width=10.0)
        with pytest.raises(AttributeError):
            ctx.container_width = 20.0  # type: ignore[misc]

    def test_default_values(self) -> None:
        """默认值正确 / Default values are correct."""
        ctx = LayerGenerationContext()
        assert ctx.items == ()
        assert ctx.container_width == 0.0
        assert ctx.container_depth == 0.0
        assert ctx.max_layers == 100
        assert ctx.candidates == ()


class TestLayerGenerationProgramCandidateAdapter:
    """LayerGenerationProgramCandidateAdapter ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            LayerGenerationProgramCandidateAdapter()  # type: ignore[abstract]


# ============================================================
# domain/packing/ tests
# ============================================================


class TestPackingAggregation:
    """PackingAggregation ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            PackingAggregation()  # type: ignore[abstract]


class TestPackingContext:
    """PackingContext 冻结数据类测试."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        ctx = PackingContext(container_width=10.0)
        with pytest.raises(AttributeError):
            ctx.container_width = 20.0  # type: ignore[misc]

    def test_default_values(self) -> None:
        """默认值正确 / Default values are correct."""
        ctx = PackingContext()
        assert ctx.container_width == 0.0
        assert ctx.container_height == 0.0
        assert ctx.container_depth == 0.0
        assert ctx.items == ()
        assert ctx.max_solutions == 1


class TestMaterialAttribute:
    """MaterialAttribute 冻结数据类测试."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        attr = MaterialAttribute(width=5.0)
        with pytest.raises(AttributeError):
            attr.width = 10.0  # type: ignore[misc]

    def test_default_values(self) -> None:
        """默认值正确 / Default values are correct."""
        attr = MaterialAttribute()
        assert attr.width == 0.0
        assert attr.height == 0.0
        assert attr.depth == 0.0
        assert attr.weight == 0.0
        assert attr.is_fragile is False
        assert attr.is_cylindrical is False

    def test_custom_values(self) -> None:
        """自定义值正确 / Custom values are correct."""
        attr = MaterialAttribute(
            width=5.0,
            height=10.0,
            depth=3.0,
            weight=2.5,
            is_fragile=True,
            is_cylindrical=False,
        )
        assert attr.width == 5.0
        assert attr.is_fragile is True


class TestMaterialPackingNumbers:
    """MaterialPackingNumbers 冻结数据类测试."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        nums = MaterialPackingNumbers(material_id="m1")
        with pytest.raises(AttributeError):
            nums.material_id = "m2"  # type: ignore[misc]

    def test_default_values(self) -> None:
        """默认值正确 / Default values are correct."""
        nums = MaterialPackingNumbers()
        assert nums.material_id == ""
        assert nums.packed_quantity == 0
        assert nums.remaining_quantity == 0


class TestMaterialPackingPlan:
    """MaterialPackingPlan 冻结数据类测试."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        plan = MaterialPackingPlan(material_id="m1")
        with pytest.raises(AttributeError):
            plan.material_id = "m2"  # type: ignore[misc]

    def test_default_values(self) -> None:
        """默认值正确 / Default values are correct."""
        plan = MaterialPackingPlan()
        assert plan.material_id == ""
        assert plan.container_id == ""
        assert plan.quantity == 0
        assert plan.position == (0.0, 0.0, 0.0)

    def test_custom_position(self) -> None:
        """自定义位置正确 / Custom position is correct."""
        plan = MaterialPackingPlan(
            position=(1.0, 2.0, 3.0),
        )
        assert plan.position == (1.0, 2.0, 3.0)


class TestPackageSolutionLikeAdapter:
    """PackageSolutionLikeAdapter ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            PackageSolutionLikeAdapter()  # type: ignore[abstract]


class TestExhaustiveMaterialPackingSolverExecutor:
    """ExhaustiveMaterialPackingSolverExecutor ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            ExhaustiveMaterialPackingSolverExecutor()  # type: ignore[abstract]


class TestMaterialPacker:
    """MaterialPacker ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            MaterialPacker()  # type: ignore[abstract]


class TestMaterialPackingSolverExecutor:
    """MaterialPackingSolverExecutor ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            MaterialPackingSolverExecutor()  # type: ignore[abstract]


class TestPacker:
    """Packer ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            Packer()  # type: ignore[abstract]


class TestPackingGeometryContract:
    """PackingGeometryContract ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            PackingGeometryContract()  # type: ignore[abstract]


class TestPackingGeometryGuard:
    """PackingGeometryGuard ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            PackingGeometryGuard()  # type: ignore[abstract]


class TestPackingRendererAdapter:
    """PackingRendererAdapter ABC 测试."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            PackingRendererAdapter()  # type: ignore[abstract]
