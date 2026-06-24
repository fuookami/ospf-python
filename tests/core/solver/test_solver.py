"""ospf_python.core.solver 测试 / Tests for ospf_python.core.solver.

覆盖 Phase 14 中所有 29 个求解器文件的基本功能。
Covers basic functionality of all 29 solver files from
Phase 14.
"""

from __future__ import annotations

import pytest

# ---- mock_solver / ----
from ospf_python.core.model.intermediate.linear_triad_model import (
    LinearTriadModel,
)

# ---- config / ----
from ospf_python.core.solver.config.copt_solver_config import (
    CoptSolverConfig,
)
from ospf_python.core.solver.config.gurobi_solver_config import (
    GurobiSolverConfig,
)
from ospf_python.core.solver.config.scip_solver_config import (
    SCIPSolverConfig,
)
from ospf_python.core.solver.config.solver_config import (
    SolverConfig,
)

# ---- heuristic / ----
from ospf_python.core.solver.heuristic.cross import Cross
from ospf_python.core.solver.heuristic.cross_mode import (
    CrossMode,
)
from ospf_python.core.solver.heuristic.iteration import (
    Iteration,
)
from ospf_python.core.solver.heuristic.migration import (
    Migration,
)
from ospf_python.core.solver.heuristic.mutation import (
    Mutation,
)
from ospf_python.core.solver.heuristic.mutation_mode import (
    MutationMode,
)
from ospf_python.core.solver.heuristic.normalization import (
    Normalization,
)
from ospf_python.core.solver.heuristic.particle_swarm_heuristic_solver import (
    ParticleSwarmHeuristicSolver,
)
from ospf_python.core.solver.heuristic.policy import Policy
from ospf_python.core.solver.heuristic.population import (
    Population,
)
from ospf_python.core.solver.heuristic.select_mode import (
    SelectMode,
)
from ospf_python.core.solver.heuristic.selection import (
    Selection,
)

# ---- iis / ----
from ospf_python.core.solver.iis.iis_computing_status import (
    IISComputingStatus,
)
from ospf_python.core.solver.iis.iis_config import IISConfig
from ospf_python.core.solver.iis.linear import LinearIIS
from ospf_python.core.solver.iis.quadratic import (
    QuadraticIIS,
)
from ospf_python.core.solver.mock_solver import MockSolver

# ---- output / ----
from ospf_python.core.solver.output.infeasible_output_fields import (
    InfeasibleOutputFields,
)
from ospf_python.core.solver.output.solver_output import (
    SolverOutput,
)
from ospf_python.core.solver.output.solver_status import (
    SolverStatus,
)
from ospf_python.core.solver.output.solving_status import (
    SolvingStatus,
)

# ---- value / ----
from ospf_python.core.solver.value.into_value import (
    IntoValue,
)
from ospf_python.core.solver.value.solve_value import (
    SolveValue,
)
from ospf_python.core.solver.value.solve_value_conversion_context import (
    SolveValueConversionContext,
)
from ospf_python.core.solver.value.solve_value_validation import (
    SolveValueValidation,
)

# ============================================================
# config/ tests
# ============================================================


class TestSolverConfigABC:
    """SolverConfig 抽象基类测试 / ABC tests."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            SolverConfig()  # type: ignore[abstract]

    def test_subclass(self) -> None:
        """子类可以实例化 / Subclass can be instantiated."""

        class DummyConfig(SolverConfig):
            @property
            def name(self) -> str:
                return "dummy"

            @property
            def time_limit(self) -> float:
                return 60.0

        cfg = DummyConfig()
        assert cfg.name == "dummy"
        assert cfg.time_limit == 60.0


class TestGurobiSolverConfig:
    """GurobiSolverConfig 冻结数据类测试 / Frozen dataclass tests."""

    def test_default_name(self) -> None:
        """默认名称为 gurobi / Default name is gurobi."""
        cfg = GurobiSolverConfig()
        assert cfg.name == "gurobi"

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        cfg = GurobiSolverConfig()
        with pytest.raises(AttributeError):
            cfg.name = "new"  # type: ignore[misc]

    def test_custom_values(self) -> None:
        """可自定义值 / Can customise values."""
        cfg = GurobiSolverConfig(
            time_limit=120.0,
            threads=4,
            mip_gap=1e-6,
        )
        assert cfg.time_limit == 120.0
        assert cfg.threads == 4
        assert cfg.mip_gap == 1e-6

    def test_default_threads(self) -> None:
        """默认线程数为 1 / Default threads is 1."""
        cfg = GurobiSolverConfig()
        assert cfg.threads == 1


class TestSCIPSolverConfig:
    """SCIPSolverConfig 冻结数据类测试 / Frozen dataclass tests."""

    def test_default_name(self) -> None:
        """默认名称为 scip / Default name is scip."""
        cfg = SCIPSolverConfig()
        assert cfg.name == "scip"

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        cfg = SCIPSolverConfig()
        with pytest.raises(AttributeError):
            cfg.verbose = True  # type: ignore[misc]

    def test_custom_time_limit(self) -> None:
        """可自定义时间限制 / Can customise time limit."""
        cfg = SCIPSolverConfig(time_limit=300.0)
        assert cfg.time_limit == 300.0


class TestCoptSolverConfig:
    """CoptSolverConfig 冻结数据类测试 / Frozen dataclass tests."""

    def test_default_name(self) -> None:
        """默认名称为 copt / Default name is copt."""
        cfg = CoptSolverConfig()
        assert cfg.name == "copt"

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        cfg = CoptSolverConfig()
        with pytest.raises(AttributeError):
            cfg.focus = 1  # type: ignore[misc]

    def test_default_focus(self) -> None:
        """默认 focus 为 0 / Default focus is 0."""
        cfg = CoptSolverConfig()
        assert cfg.focus == 0


# ============================================================
# value/ tests
# ============================================================


class TestSolveValue:
    """SolveValue 冻结数据类测试 / Frozen dataclass tests."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        sv = SolveValue(values={"x": 1.0})
        with pytest.raises(AttributeError):
            sv.values = {}  # type: ignore[misc]

    def test_empty(self) -> None:
        """默认为空 / Default is empty."""
        sv = SolveValue()
        assert sv.is_empty is True

    def test_get_existing(self) -> None:
        """获取存在的变量 / Get existing variable."""
        sv = SolveValue(values={"x": 3.14, "y": 2.0})
        assert sv.get("x") == 3.14

    def test_get_missing_uses_default(self) -> None:
        """缺失变量返回默认值 / Missing returns default."""
        sv = SolveValue(values={"x": 1.0})
        assert sv.get("z", default=99.0) == 99.0

    def test_variable_names(self) -> None:
        """变量名元组 / Variable name tuple."""
        sv = SolveValue(values={"a": 1.0, "b": 2.0})
        assert set(sv.variable_names) == {"a", "b"}


class TestIntoValueProtocol:
    """IntoValue 协议测试 / Protocol tests."""

    def test_protocol_check(self) -> None:
        """实现协议的对象符合接口 / Implements protocol."""

        class MyValue:
            def to_solve_value(self) -> SolveValue:
                return SolveValue(values={"x": 1.0})

        obj = MyValue()
        assert isinstance(obj, IntoValue)


class TestSolveValueConversionContext:
    """SolveValueConversionContext 测试 / Tests."""

    def test_build_solve_value(self) -> None:
        """构建求解值 / Build solve value."""
        ctx = SolveValueConversionContext(
            variable_names=("x", "y"),
            default_value=0.0,
        )
        sv = ctx.build_solve_value({"x": 5.0})
        assert sv.get("x") == 5.0
        assert sv.get("y") == 0.0

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        ctx = SolveValueConversionContext()
        with pytest.raises(AttributeError):
            ctx.default_value = 1.0  # type: ignore[misc]


class TestSolveValueValidation:
    """SolveValueValidation 测试 / Tests."""

    def test_valid_values(self) -> None:
        """正常值通过验证 / Normal values pass."""
        sv = SolveValue(values={"x": 1.0, "y": 2.0})
        result = SolveValueValidation.validate(sv)
        assert result.is_valid is True
        assert len(result.issues) == 0

    def test_nan_detected(self) -> None:
        """NaN 值被检测 / NaN detected."""
        sv = SolveValue(values={"x": float("nan")})
        result = SolveValueValidation.validate(sv)
        assert result.is_valid is False
        assert len(result.issues) == 1

    def test_inf_detected(self) -> None:
        """Inf 值被检测 / Inf detected."""
        sv = SolveValue(values={"x": float("inf")})
        result = SolveValueValidation.validate(sv)
        assert result.is_valid is False

    def test_nan_allowed(self) -> None:
        """允许 NaN / NaN allowed."""
        sv = SolveValue(values={"x": float("nan")})
        result = SolveValueValidation.validate(
            sv,
            allow_nan=True,
        )
        assert result.is_valid is True

    def test_inf_allowed(self) -> None:
        """允许 Inf / Inf allowed."""
        sv = SolveValue(values={"x": float("inf")})
        result = SolveValueValidation.validate(
            sv,
            allow_inf=True,
        )
        assert result.is_valid is True


# ============================================================
# output/ tests
# ============================================================


class TestSolverStatus:
    """SolverStatus 枚举测试 / Enum tests."""

    def test_optimal_value(self) -> None:
        """OPTIMAL 值为 0 / OPTIMAL value is 0."""
        assert SolverStatus.OPTIMAL.value == 0

    def test_infeasible_value(self) -> None:
        """INFEASIBLE 值为 1 / INFEASIBLE value is 1."""
        assert SolverStatus.INFEASIBLE.value == 1

    def test_unbounded_value(self) -> None:
        """UNBOUNDED 值为 2 / UNBOUNDED value is 2."""
        assert SolverStatus.UNBOUNDED.value == 2

    def test_timeout_value(self) -> None:
        """TIMEOUT 值为 3 / TIMEOUT value is 3."""
        assert SolverStatus.TIMEOUT.value == 3

    def test_error_value(self) -> None:
        """ERROR 值为 4 / ERROR value is 4."""
        assert SolverStatus.ERROR.value == 4

    def test_unknown_value(self) -> None:
        """UNKNOWN 值为 5 / UNKNOWN value is 5."""
        assert SolverStatus.UNKNOWN.value == 5

    def test_member_count(self) -> None:
        """共 6 个成员 / Has 6 members."""
        assert len(SolverStatus) == 6


class TestSolvingStatus:
    """SolvingStatus 枚举测试 / Enum tests."""

    def test_idle_value(self) -> None:
        """IDLE 值为 0 / IDLE value is 0."""
        assert SolvingStatus.IDLE.value == 0

    def test_completed_value(self) -> None:
        """COMPLETED 值为 4 / COMPLETED value is 4."""
        assert SolvingStatus.COMPLETED.value == 4

    def test_member_count(self) -> None:
        """共 6 个成员 / Has 6 members."""
        assert len(SolvingStatus) == 6


class TestSolverOutput:
    """SolverOutput 冻结数据类测试 / Frozen dataclass tests."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        out = SolverOutput(status=SolverStatus.OPTIMAL)
        with pytest.raises(AttributeError):
            out.objective = 99.0  # type: ignore[misc]

    def test_is_optimal(self) -> None:
        """最优状态检测 / Optimal status detection."""
        out = SolverOutput(status=SolverStatus.OPTIMAL)
        assert out.is_optimal is True

    def test_is_infeasible(self) -> None:
        """不可行状态检测 / Infeasible status detection."""
        out = SolverOutput(
            status=SolverStatus.INFEASIBLE,
        )
        assert out.is_infeasible is True

    def test_optimal_factory(self) -> None:
        """最优工厂方法 / Optimal factory method."""
        sv = SolveValue(values={"x": 1.0})
        out = SolverOutput.optimal(42.0, sv)
        assert out.status is SolverStatus.OPTIMAL
        assert out.objective == 42.0

    def test_infeasible_factory(self) -> None:
        """不可行工厂方法 / Infeasible factory method."""
        out = SolverOutput.infeasible()
        assert out.status is SolverStatus.INFEASIBLE

    def test_timeout_factory(self) -> None:
        """超时工厂方法 / Timeout factory method."""
        out = SolverOutput.timeout(objective=10.0)
        assert out.status is SolverStatus.TIMEOUT
        assert out.objective == 10.0


class TestInfeasibleOutputFields:
    """InfeasibleOutputFields 测试 / Tests."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        f = InfeasibleOutputFields()
        with pytest.raises(AttributeError):
            f.message = "x"  # type: ignore[misc]

    def test_has_conflicts(self) -> None:
        """有冲突约束 / Has conflicting constraints."""
        f = InfeasibleOutputFields(
            conflicting_constraints=("c1", "c2"),
        )
        assert f.has_conflicts is True

    def test_no_conflicts(self) -> None:
        """无冲突约束 / No conflicting constraints."""
        f = InfeasibleOutputFields()
        assert f.has_conflicts is False

    def test_with_message(self) -> None:
        """带消息创建 / Create with message."""
        f = InfeasibleOutputFields.with_message("test")
        assert f.message == "test"


# ============================================================
# iis/ tests
# ============================================================


class TestIISConfig:
    """IISConfig 冻结数据类测试 / Frozen dataclass tests."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        cfg = IISConfig()
        with pytest.raises(AttributeError):
            cfg.time_limit = 1.0  # type: ignore[misc]

    def test_defaults(self) -> None:
        """默认值正确 / Default values correct."""
        cfg = IISConfig()
        assert cfg.time_limit == 300.0
        assert cfg.max_iterations == 1000
        assert cfg.verbose is False


class TestIISComputingStatus:
    """IISComputingStatus 枚举测试 / Enum tests."""

    def test_not_started_value(self) -> None:
        """NOT_STARTED 值为 0 / value is 0."""
        assert IISComputingStatus.NOT_STARTED.value == 0

    def test_found_value(self) -> None:
        """FOUND 值为 2 / FOUND value is 2."""
        assert IISComputingStatus.FOUND.value == 2

    def test_member_count(self) -> None:
        """共 6 个成员 / Has 6 members."""
        assert len(IISComputingStatus) == 6


class TestLinearIIS:
    """LinearIIS 冻结数据类测试 / Frozen dataclass tests."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        iis = LinearIIS()
        with pytest.raises(AttributeError):
            iis.message = "x"  # type: ignore[misc]

    def test_is_found(self) -> None:
        """已找到状态 / Found status."""
        iis = LinearIIS(
            status=IISComputingStatus.FOUND,
            constraints=("c1",),
        )
        assert iis.is_found is True

    def test_not_found(self) -> None:
        """未找到状态 / Not found status."""
        iis = LinearIIS()
        assert iis.is_found is False

    def test_size(self) -> None:
        """IIS 大小 / IIS size."""
        iis = LinearIIS(
            constraints=("c1", "c2"),
            bounds=("x",),
        )
        assert iis.size == 3


class TestQuadraticIIS:
    """QuadraticIIS 冻结数据类测试 / Frozen dataclass tests."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        iis = QuadraticIIS()
        with pytest.raises(AttributeError):
            iis.message = "x"  # type: ignore[misc]

    def test_is_found(self) -> None:
        """已找到状态 / Found status."""
        iis = QuadraticIIS(
            status=IISComputingStatus.FOUND,
            quadratic_constraints=("qc1",),
        )
        assert iis.is_found is True

    def test_size(self) -> None:
        """IIS 大小 / IIS size."""
        lin = LinearIIS(
            constraints=("c1",),
            bounds=("x",),
        )
        iis = QuadraticIIS(
            linear_iis=lin,
            quadratic_constraints=("qc1", "qc2"),
        )
        assert iis.size == 4


# ============================================================
# heuristic/ tests
# ============================================================


class TestSelectMode:
    """SelectMode 枚举测试 / Enum tests."""

    def test_roulette_value(self) -> None:
        """ROULETTE 值为 0 / ROULETTE value is 0."""
        assert SelectMode.ROULETTE.value == 0

    def test_tournament_value(self) -> None:
        """TOURNAMENT 值为 1 / TOURNAMENT value is 1."""
        assert SelectMode.TOURNAMENT.value == 1

    def test_member_count(self) -> None:
        """共 3 个成员 / Has 3 members."""
        assert len(SelectMode) == 3


class TestMutationMode:
    """MutationMode 枚举测试 / Enum tests."""

    def test_uniform_value(self) -> None:
        """UNIFORM 值为 0 / UNIFORM value is 0."""
        assert MutationMode.UNIFORM.value == 0

    def test_gaussian_value(self) -> None:
        """GAUSSIAN 值为 1 / GAUSSIAN value is 1."""
        assert MutationMode.GAUSSIAN.value == 1

    def test_member_count(self) -> None:
        """共 3 个成员 / Has 3 members."""
        assert len(MutationMode) == 3


class TestCrossMode:
    """CrossMode 枚举测试 / Enum tests."""

    def test_single_point_value(self) -> None:
        """SINGLE_POINT 值为 0 / value is 0."""
        assert CrossMode.SINGLE_POINT.value == 0

    def test_arithmetic_value(self) -> None:
        """ARITHMETIC 值为 3 / ARITHMETIC value is 3."""
        assert CrossMode.ARITHMETIC.value == 3

    def test_member_count(self) -> None:
        """共 4 个成员 / Has 4 members."""
        assert len(CrossMode) == 4


class TestPopulation:
    """Population 类测试 / Class tests."""

    def test_empty(self) -> None:
        """默认为空 / Default is empty."""
        pop = Population()
        assert pop.size == 0
        assert pop.best_index == -1

    def test_update_best(self) -> None:
        """更新最优索引 / Update best index."""
        pop = Population(
            individuals=[
                SolveValue(values={"x": 1.0}),
                SolveValue(values={"x": 2.0}),
            ],
            fitness=[10.0, 5.0],
        )
        pop.update_best()
        assert pop.best_index == 1
        assert pop.best_fitness == 5.0

    def test_best_individual(self) -> None:
        """最优个体 / Best individual."""
        sv = SolveValue(values={"x": 1.0})
        pop = Population(
            individuals=[sv],
            fitness=[3.0],
            best_index=0,
        )
        assert pop.best_individual is sv


class TestSelection:
    """Selection 类测试 / Class tests."""

    def test_default_mode(self) -> None:
        """默认轮盘赌模式 / Default is roulette."""
        sel = Selection()
        assert sel.mode is SelectMode.ROULETTE

    def test_select_empty(self) -> None:
        """空种群返回空列表 / Empty population returns []"""
        sel = Selection()
        pop = Population()
        assert sel.select_indices(pop, 3) == []


class TestMutation:
    """Mutation 类测试 / Class tests."""

    def test_default_mode(self) -> None:
        """默认均匀变异 / Default is uniform."""
        m = Mutation()
        assert m.mode is MutationMode.UNIFORM

    def test_mutate_returns_value(self) -> None:
        """变异返回 SolveValue / Returns SolveValue."""
        m = Mutation()
        sv = SolveValue(values={"x": 1.0})
        result = m.mutate(sv)
        assert isinstance(result, SolveValue)


class TestCross:
    """Cross 类测试 / Class tests."""

    def test_default_mode(self) -> None:
        """默认单点交叉 / Default is single point."""
        c = Cross()
        assert c.mode is CrossMode.SINGLE_POINT

    def test_cross_returns_pair(self) -> None:
        """交叉返回两个个体 / Returns two individuals."""
        c = Cross()
        a = SolveValue(values={"x": 1.0})
        b = SolveValue(values={"x": 2.0})
        result = c.cross(a, b)
        assert len(result) == 2


class TestMigration:
    """Migration 类测试 / Class tests."""

    def test_defaults(self) -> None:
        """默认值 / Default values."""
        m = Migration()
        assert m.rate == 0.1
        assert m.size == 1

    def test_migrate_no_error(self) -> None:
        """迁移不抛异常 / Migration does not raise."""
        m = Migration()
        src = Population()
        dst = Population()
        m.migrate(src, dst)


class TestIteration:
    """Iteration 类测试 / Class tests."""

    def test_not_finished_initially(self) -> None:
        """初始未完成 / Initially not finished."""
        it = Iteration(max_iterations=10)
        assert it.is_finished is False

    def test_advance(self) -> None:
        """推进迭代 / Advance iteration."""
        it = Iteration(max_iterations=2)
        it.advance()
        assert it.current == 1
        it.advance()
        assert it.is_finished is True

    def test_reset(self) -> None:
        """重置迭代 / Reset iteration."""
        it = Iteration(max_iterations=5)
        it.advance()
        it.advance()
        it.reset()
        assert it.current == 0


class TestNormalization:
    """Normalization 类测试 / Class tests."""

    def test_normalize(self) -> None:
        """归一化单个值 / Normalize a single value."""
        n = Normalization(min_val=0.0, max_val=1.0)
        result = n.normalize(
            5.0,
            source_min=0.0,
            source_max=10.0,
        )
        assert abs(result - 0.5) < 1e-9

    def test_normalize_batch(self) -> None:
        """批量归一化 / Batch normalization."""
        n = Normalization()
        result = n.normalize_batch([0.0, 5.0, 10.0])
        assert abs(result[0] - 0.0) < 1e-9
        assert abs(result[2] - 1.0) < 1e-9

    def test_normalize_empty_batch(self) -> None:
        """空列表归一化 / Empty batch normalization."""
        n = Normalization()
        assert n.normalize_batch([]) == []

    def test_normalize_constant_range(self) -> None:
        """常数范围归一化 / Constant range normalization."""
        n = Normalization()
        result = n.normalize(
            5.0,
            source_min=5.0,
            source_max=5.0,
        )
        assert result == 0.0


class TestPolicy:
    """Policy 类测试 / Class tests."""

    def test_defaults(self) -> None:
        """默认值 / Default values."""
        p = Policy()
        assert p.population_size == 50
        assert p.selection.mode is SelectMode.ROULETTE
        assert p.mutation.mode is MutationMode.UNIFORM

    def test_custom_policy(self) -> None:
        """自定义策略 / Custom policy."""
        p = Policy(
            population_size=100,
            iteration=Iteration(max_iterations=200),
        )
        assert p.population_size == 100
        assert p.iteration.max_iterations == 200


class TestParticleSwarmHeuristicSolver:
    """ParticleSwarmHeuristicSolver 测试 / Tests."""

    def test_name(self) -> None:
        """求解器名称 / Solver name."""
        s = ParticleSwarmHeuristicSolver()
        assert s.name == "particle_swarm"

    def test_solve_returns_output(self) -> None:
        """求解返回输出 / Solve returns output."""
        s = ParticleSwarmHeuristicSolver()
        result = s.solve(object())
        assert isinstance(result, SolverOutput)


# ============================================================
# MockSolver end-to-end tests
# ============================================================


class TestMockSolver:
    """MockSolver 端到端测试 / End-to-end tests."""

    def test_name(self) -> None:
        """求解器名称 / Solver name."""
        s = MockSolver()
        assert s.name == "mock"

    def test_supports_integer(self) -> None:
        """支持整数 / Supports integer."""
        s = MockSolver()
        assert s.supports_integer() is True

    def test_no_integer_support(self) -> None:
        """不支持整数 / No integer support."""
        s = MockSolver(supports_int=False)
        assert s.supports_integer() is False

    def test_non_model_returns_error(self) -> None:
        """非模型输入返回错误 / Non-model returns error."""
        s = MockSolver()
        result = s.solve("not_a_model")
        assert result.status is SolverStatus.ERROR

    def test_empty_model_infeasible(self) -> None:
        """空模型返回不可行 / Empty model returns infeasible."""
        s = MockSolver()
        model = LinearTriadModel()
        result = s.solve(model)
        assert result.status is SolverStatus.INFEASIBLE

    def test_simple_lp_optimal(self) -> None:
        """简单 LP 返回最优 / Simple LP returns optimal."""
        s = MockSolver()
        model = LinearTriadModel(
            variables=["x", "y"],
            objective={"x": 3.0, "y": 5.0},
            constraints={"c1": {"x": 1.0, "y": 1.0}},
            rhs={"c1": 10.0},
            sense={"c1": "<="},
            lower_bounds={"x": 0.0, "y": 0.0},
        )
        result = s.solve(model)
        assert result.status is SolverStatus.OPTIMAL
        assert result.objective == 0.0
        assert result.values.get("x") == 0.0
        assert result.values.get("y") == 0.0

    def test_infeasible_constraint(self) -> None:
        """不可行约束 / Infeasible constraint.

        x <= -1, 下界 x >= 0 不可行。
        x <= -1 with lower bound x >= 0 is infeasible.
        """
        s = MockSolver()
        model = LinearTriadModel(
            variables=["x"],
            objective={"x": 1.0},
            constraints={"c1": {"x": 1.0}},
            rhs={"c1": -1.0},
            sense={"c1": "<="},
            lower_bounds={"x": 0.0},
        )
        result = s.solve(model)
        assert result.status is SolverStatus.INFEASIBLE

    def test_objective_from_objective_keys(self) -> None:
        """从目标函数键推断变量 / Infer vars from obj keys."""
        s = MockSolver()
        model = LinearTriadModel(
            objective={"x": 1.0, "y": 2.0},
            lower_bounds={"x": 1.0, "y": 2.0},
        )
        result = s.solve(model)
        assert result.status is SolverStatus.OPTIMAL
        assert result.objective == 5.0

    def test_lower_bounds_used(self) -> None:
        """下界被使用 / Lower bounds are used."""
        s = MockSolver()
        model = LinearTriadModel(
            variables=["x"],
            objective={"x": 1.0},
            lower_bounds={"x": 7.0},
        )
        result = s.solve(model)
        assert result.status is SolverStatus.OPTIMAL
        assert result.values.get("x") == 7.0
        assert result.objective == 7.0

    def test_ge_constraint_feasible(self) -> None:
        """GE 约束可行 / GE constraint feasible."""
        s = MockSolver()
        model = LinearTriadModel(
            variables=["x"],
            objective={"x": 1.0},
            constraints={"c1": {"x": 1.0}},
            rhs={"c1": 0.0},
            sense={"c1": ">="},
            lower_bounds={"x": 1.0},
        )
        result = s.solve(model)
        assert result.status is SolverStatus.OPTIMAL

    def test_eq_constraint_infeasible(self) -> None:
        """EQ 约束不可行 / EQ constraint infeasible."""
        s = MockSolver()
        model = LinearTriadModel(
            variables=["x"],
            objective={"x": 1.0},
            constraints={"c1": {"x": 1.0}},
            rhs={"c1": 5.0},
            sense={"c1": "=="},
            lower_bounds={"x": 0.0},
        )
        result = s.solve(model)
        assert result.status is SolverStatus.INFEASIBLE

    def test_multi_variable_model(self) -> None:
        """多变量模型 / Multi-variable model."""
        s = MockSolver()
        model = LinearTriadModel(
            variables=["x", "y", "z"],
            objective={"x": 1.0, "y": 2.0, "z": 3.0},
            lower_bounds={"x": 0.0, "y": 0.0, "z": 0.0},
        )
        result = s.solve(model)
        assert result.status is SolverStatus.OPTIMAL
        assert result.objective == 0.0
