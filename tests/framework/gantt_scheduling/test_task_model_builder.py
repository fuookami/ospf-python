"""任务模型构建器测试 / Task model builder tests.

覆盖 task_model_builder 中的辅助函数。
Covers helper functions in task_model_builder.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ospf_python.core.model.mechanism.meta_model import MetaModel
from ospf_python.core.solver.mock_solver import MockSolver
from ospf_python.core.solver.value.solve_value import SolveValue
from ospf_python.framework.gantt_scheduling.application.model.gantt_problem import (
    GanttProblem,
    PrecedenceRelation,
)
from ospf_python.framework.gantt_scheduling.application.service.task.task_application_service import (
    TaskApplicationService,
)
from ospf_python.framework.gantt_scheduling.application.service.task.task_column import (
    ConstraintCoeff,
    TaskColumn,
)
from ospf_python.framework.gantt_scheduling.application.service.task.task_model_builder import (
    _build_triad_from_export,
    _discretize_windows,
    build_schedule,
    build_triad_model,
    extract_shadow_prices,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource import (
    Resource,
)
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource_context import (
    ResourceContext,
)
from ospf_python.framework.gantt_scheduling.domain.task.model.task import Task
from ospf_python.framework.gantt_scheduling.domain.task.model.task_context import (
    TaskContext,
)

if TYPE_CHECKING:
    from ospf_python.core.model.intermediate.linear_triad_model import (
        LinearTriadModel,
    )


def _make_meta_model() -> MetaModel:
    """构建测试用元模型。/ Build test meta model."""
    mm = MetaModel(name="test_model")
    mm.register_variable(
        "start_t1",
        {"type": "continuous", "lb": 0.0, "ub": 10.0},
    )
    mm.register_variable(
        "start_t2",
        {"type": "continuous", "lb": 0.0, "ub": 10.0},
    )
    mm.register_variable(
        "assign_t1_r1",
        {"type": "binary", "task_key": "t1", "resource_key": "r1"},
    )
    mm.register_variable(
        "col_c1",
        TaskColumn(
            column_key="c1",
            task_assignments=(("t1", "r1", 0.0),),
            cost=5.0,
        ),
    )
    mm.register_constraint(
        "cap_r1_0_10",
        {
            "type": "capacity",
            "resource_key": "r1",
            "window_start": 0.0,
            "window_end": 10.0,
            "rhs": 10.0,
            "sense": "<=",
        },
    )
    mm.register_constraint(
        "prec_t1_t2",
        {
            "type": "precedence",
            "predecessor_key": "t1",
            "successor_key": "t2",
            "min_gap": 3.0,
            "sense": ">=",
        },
    )
    return mm


def _make_columns() -> tuple[TaskColumn, ...]:
    """构建测试用列。/ Build test columns."""
    return (
        TaskColumn(
            column_key="c1",
            task_assignments=(("t1", "r1", 0.0),),
            cost=5.0,
        ),
    )


def _make_coeffs() -> tuple[ConstraintCoeff, ...]:
    """构建测试用约束系数。/ Build test constraint coefficients."""
    return (
        ConstraintCoeff(
            constraint_name="cap_r1_0_10",
            variable_name="col_c1",
            coefficient=1.0,
        ),
    )


def _make_closed_native_triad(
    *,
    relaxation: bool = False,
) -> LinearTriadModel:
    """Build the task service's closed native triad without solving it."""
    problem = GanttProblem(
        name="p3_ae",
        tasks=(
            Task(
                task_key="t1",
                name="T1",
                duration=3.0,
                resource_requirements=(("r1", 2.0),),
            ),
            Task(
                task_key="t2",
                name="T2",
                duration=2.0,
                resource_requirements=(("r1", 2.0),),
            ),
        ),
        resources=(Resource(resource_key="r1", name="R1", capacity=3.0),),
        precedence_relations=(PrecedenceRelation("t1", "t2"),),
        time_horizon=10.0,
    )
    columns = (
        TaskColumn("capacity_bad", (("t1", "r1", 0.0), ("t2", "r1", 0.0)), 0.0),
        TaskColumn(
            "precedence_bad",
            (("t1", "r1", 3.0), ("t2", "r1", 0.0)),
            0.0,
        ),
        TaskColumn("serial_ok", (("t1", "r1", 0.0), ("t2", "r1", 3.0)), 1.0),
    )
    service = TaskApplicationService(
        solver=MockSolver(),
        task_context=TaskContext(),
        resource_context=ResourceContext(),
    )
    assert service.register(problem).is_ok()
    assert service.add_columns(columns).is_ok()
    native_model = service._native_model
    assert native_model is not None
    exported = native_model.to_linear_triad().unwrap()
    return _build_triad_from_export(
        exported=exported,
        relaxation=relaxation,
    ).unwrap()


def _make_staggered_window_problem() -> GanttProblem:
    """Build two short tasks whose selected starts need column boundaries."""
    return GanttProblem(
        name="staggered-window",
        tasks=(
            Task(
                task_key="t1",
                name="T1",
                duration=0.2,
                deadline=1.0,
                resource_requirements=(("r1", 1.0),),
            ),
            Task(
                task_key="t2",
                name="T2",
                duration=0.2,
                deadline=1.0,
                resource_requirements=(("r1", 1.0),),
            ),
        ),
        resources=(Resource(resource_key="r1", name="R1", capacity=1.0),),
        time_horizon=1.0,
    )


def _make_staggered_task_columns() -> tuple[TaskColumn, ...]:
    """Build disjoint task columns that straddle the old event window."""
    return (
        TaskColumn("t1_only", (("t1", "r1", 0.3),), 1.0),
        TaskColumn("t2_only", (("t2", "r1", 0.7),), 1.0),
    )


# ==================== build_triad_model 测试 =====================


class TestBuildTriadModel:
    """build_triad_model 函数测试。/ build_triad_model tests."""

    def test_build_returns_triad_model(self) -> None:
        """构建返回 LinearTriadModel。/ Build returns LinearTriadModel."""
        from ospf_python.core.model.intermediate.linear_triad_model import (
            LinearTriadModel,
        )

        mm = _make_meta_model()
        model = build_triad_model(
            meta_model=mm,
            active_columns=_make_columns(),
            constraint_coeffs=_make_coeffs(),
            relaxation=True,
        )
        assert isinstance(model, LinearTriadModel)

    def test_build_model_has_name(self) -> None:
        """构建模型有名称。/ Built model has name."""
        mm = _make_meta_model()
        model = build_triad_model(
            meta_model=mm,
            active_columns=_make_columns(),
            constraint_coeffs=_make_coeffs(),
            relaxation=True,
        )
        assert model.name == "test_model"

    def test_build_model_has_variables(self) -> None:
        """构建模型有变量。/ Built model has variables."""
        mm = _make_meta_model()
        model = build_triad_model(
            meta_model=mm,
            active_columns=_make_columns(),
            constraint_coeffs=_make_coeffs(),
            relaxation=True,
        )
        assert len(model.variables) > 0

    def test_build_model_has_constraints(self) -> None:
        """构建模型有约束。/ Built model has constraints."""
        mm = _make_meta_model()
        model = build_triad_model(
            meta_model=mm,
            active_columns=_make_columns(),
            constraint_coeffs=_make_coeffs(),
            relaxation=True,
        )
        assert len(model.constraints) > 0

    def test_build_model_objective_from_columns(self) -> None:
        """目标函数来自列成本。/ Objective from column costs."""
        mm = _make_meta_model()
        model = build_triad_model(
            meta_model=mm,
            active_columns=_make_columns(),
            constraint_coeffs=_make_coeffs(),
            relaxation=True,
        )
        assert "col_c1" in model.objective
        assert model.objective["col_c1"] == 5.0

    def test_build_model_populates_coefficients(self) -> None:
        """约束系数正确填充。/ Constraint coefficients populated."""
        mm = _make_meta_model()
        model = build_triad_model(
            meta_model=mm,
            active_columns=_make_columns(),
            constraint_coeffs=_make_coeffs(),
            relaxation=True,
        )
        cap_coefs = model.constraints.get("cap_r1_0_10", {})
        assert cap_coefs.get("col_c1") == 1.0

    def test_build_model_has_bounds(self) -> None:
        """模型有上下界。/ Model has bounds."""
        mm = _make_meta_model()
        model = build_triad_model(
            meta_model=mm,
            active_columns=_make_columns(),
            constraint_coeffs=_make_coeffs(),
            relaxation=True,
        )
        assert "start_t1" in model.lower_bounds
        assert "start_t1" in model.upper_bounds

    def test_build_model_rhs_and_sense(self) -> None:
        """模型有右端项和方向。/ Model has rhs and sense."""
        mm = _make_meta_model()
        model = build_triad_model(
            meta_model=mm,
            active_columns=_make_columns(),
            constraint_coeffs=_make_coeffs(),
            relaxation=True,
        )
        assert "cap_r1_0_10" in model.rhs
        assert "cap_r1_0_10" in model.sense

    def test_build_model_empty_columns(self) -> None:
        """空列构建成功。/ Empty columns build succeeds."""
        mm = _make_meta_model()
        model = build_triad_model(
            meta_model=mm,
            active_columns=(),
            constraint_coeffs=(),
            relaxation=True,
        )
        assert model.objective == {}

    def test_build_model_non_relaxation(self) -> None:
        """非松弛模式保留变量类型。/ Non-relaxation preserves variable types."""
        mm = _make_meta_model()
        model = build_triad_model(
            meta_model=mm,
            active_columns=_make_columns(),
            constraint_coeffs=_make_coeffs(),
            relaxation=False,
        )
        assert model.name == "test_model"
        assert model.variable_types == {
            "start_t1": "continuous",
            "start_t2": "continuous",
            "assign_t1_r1": "binary",
            "col_c1": "binary",
        }
        assert model.upper_bounds["assign_t1_r1"] == 1.0
        assert model.upper_bounds["col_c1"] == 1.0

    def test_build_model_relaxation_makes_all_variables_continuous(self) -> None:
        """LP 松弛把全部变量改为连续。/ LP relaxation makes all variables continuous."""
        mm = _make_meta_model()
        model = build_triad_model(
            meta_model=mm,
            active_columns=_make_columns(),
            constraint_coeffs=_make_coeffs(),
            relaxation=True,
        )
        assert set(model.variable_types) == set(mm.variables)
        assert set(model.variable_types.values()) == {"continuous"}
        assert model.upper_bounds["assign_t1_r1"] == 1.0
        assert model.upper_bounds["col_c1"] == 1.0

    def test_closed_task_model_has_exact_compilation_rows(self) -> None:
        """每个任务恰好由一列覆盖，并形成 Rust 同名影子价格行。"""
        model = _make_closed_native_triad()

        assert model.constraints["task_compilation_0"] == {
            "col_capacity_bad": 1.0,
            "col_precedence_bad": 1.0,
            "col_serial_ok": 1.0,
        }
        assert model.rhs["task_compilation_0"] == 1.0
        assert model.sense["task_compilation_0"] == "=="

    def test_closed_task_model_links_schedule_variables_to_columns(self) -> None:
        """开始时间和分配变量由所选列等式派生。"""
        model = _make_closed_native_triad()

        assert model.constraints["start_link_t1"] == {
            "start_t1": 1.0,
            "col_precedence_bad": -3.0,
        }
        assert model.constraints["assign_link_t2_r1"] == {
            "assign_t2_r1": 1.0,
            "col_capacity_bad": -1.0,
            "col_precedence_bad": -1.0,
            "col_serial_ok": -1.0,
        }

    def test_closed_task_model_uses_demand_for_capacity(self) -> None:
        """容量行使用资源需求量，而不是固定系数 1。"""
        model = _make_closed_native_triad()

        assert model.constraints["cap_r1_0_2"]["col_capacity_bad"] == 4.0
        assert model.constraints["cap_r1_0_2"]["col_serial_ok"] == 2.0
        assert model.rhs["cap_r1_0_2"] == 3.0

    def test_discretize_windows_includes_candidate_column_boundaries(self) -> None:
        """容量窗口包含候选列开始和结束事件。"""
        problem = _make_staggered_window_problem()
        windows = _discretize_windows(
            problem=problem,
            resource_key="r1",
            active_columns=_make_staggered_task_columns(),
        )

        assert (0.3, 0.5) in windows
        assert (0.7, 0.8) in windows
        assert (0.8, 0.9) in windows
        assert (0.2, 0.8) not in windows

    def test_disjoint_task_columns_do_not_share_capacity_window(self) -> None:
        """旧窗口内的不重叠列被拆到独立容量行。"""
        problem = _make_staggered_window_problem()
        service = TaskApplicationService(
            solver=MockSolver(),
            task_context=TaskContext(),
            resource_context=ResourceContext(),
        )
        assert service.register(problem).is_ok()
        assert service.add_columns(_make_staggered_task_columns()).is_ok()

        native_model = service._native_model
        assert native_model is not None
        exported = native_model.to_linear_triad().unwrap()
        capacity_rows = [row for row in exported.rows if row.name.startswith("cap_r1_")]

        assert all(
            not (
                "col_t1_only" in row.coefficients and "col_t2_only" in row.coefficients
            )
            for row in capacity_rows
        )
        assert any(row.coefficients == {"col_t1_only": 1.0} for row in capacity_rows)
        assert any(row.coefficients == {"col_t2_only": 1.0} for row in capacity_rows)

    def test_closed_task_model_encodes_precedence_and_makespan(self) -> None:
        """优先关系和完工时间都由真实开始变量表达。"""
        model = _make_closed_native_triad()

        assert model.constraints["prec_t1_t2"] == {
            "start_t1": -1.0,
            "start_t2": 1.0,
        }
        assert model.rhs["prec_t1_t2"] == 3.0
        assert model.constraints["makespan_task_1"] == {
            "makespan": 1.0,
            "start_t2": -1.0,
        }
        assert model.rhs["makespan_task_1"] == 2.0
        assert model.objective["makespan"] == 1.0

    def test_native_export_preserves_the_complete_task_contract(self) -> None:
        """原生导出完整保留变量、行、边界、方向和目标。"""
        model = _make_closed_native_triad()

        assert model.name == "cg_p3_ae"
        assert model.variables == [
            "start_t1",
            "assign_t1_r1",
            "start_t2",
            "assign_t2_r1",
            "makespan",
            "col_capacity_bad",
            "col_precedence_bad",
            "col_serial_ok",
        ]
        assert model.lower_bounds == {
            "start_t1": 0.0,
            "assign_t1_r1": 0.0,
            "start_t2": 0.0,
            "assign_t2_r1": 0.0,
            "makespan": 0.0,
            "col_capacity_bad": 0.0,
            "col_precedence_bad": 0.0,
            "col_serial_ok": 0.0,
        }
        assert model.upper_bounds == {
            "start_t1": float("inf"),
            "assign_t1_r1": 1.0,
            "start_t2": float("inf"),
            "assign_t2_r1": 1.0,
            "makespan": float("inf"),
            "col_capacity_bad": 1.0,
            "col_precedence_bad": 1.0,
            "col_serial_ok": 1.0,
        }
        assert model.variable_types == {
            "start_t1": "continuous",
            "assign_t1_r1": "binary",
            "start_t2": "continuous",
            "assign_t2_r1": "binary",
            "makespan": "continuous",
            "col_capacity_bad": "binary",
            "col_precedence_bad": "binary",
            "col_serial_ok": "binary",
        }
        assert model.constraints == {
            "task_compilation_0": {
                "col_capacity_bad": 1.0,
                "col_precedence_bad": 1.0,
                "col_serial_ok": 1.0,
            },
            "task_compilation_1": {
                "col_capacity_bad": 1.0,
                "col_precedence_bad": 1.0,
                "col_serial_ok": 1.0,
            },
            "cap_r1_0_2": {
                "col_capacity_bad": 4.0,
                "col_precedence_bad": 2.0,
                "col_serial_ok": 2.0,
            },
            "cap_r1_2_3": {
                "col_capacity_bad": 2.0,
                "col_serial_ok": 2.0,
            },
            "cap_r1_3_5": {
                "col_precedence_bad": 2.0,
                "col_serial_ok": 2.0,
            },
            "cap_r1_5_6": {
                "col_precedence_bad": 2.0,
            },
            "cap_r1_6_10": {},
            "prec_t1_t2": {
                "start_t1": -1.0,
                "start_t2": 1.0,
            },
            "makespan_task_0": {
                "makespan": 1.0,
                "start_t1": -1.0,
            },
            "makespan_task_1": {
                "makespan": 1.0,
                "start_t2": -1.0,
            },
            "start_link_t1": {
                "start_t1": 1.0,
                "col_precedence_bad": -3.0,
            },
            "assign_link_t1_r1": {
                "assign_t1_r1": 1.0,
                "col_capacity_bad": -1.0,
                "col_precedence_bad": -1.0,
                "col_serial_ok": -1.0,
            },
            "start_link_t2": {
                "start_t2": 1.0,
                "col_serial_ok": -3.0,
            },
            "assign_link_t2_r1": {
                "assign_t2_r1": 1.0,
                "col_capacity_bad": -1.0,
                "col_precedence_bad": -1.0,
                "col_serial_ok": -1.0,
            },
        }
        assert model.rhs == {
            "task_compilation_0": 1.0,
            "task_compilation_1": 1.0,
            "cap_r1_0_2": 3.0,
            "cap_r1_2_3": 3.0,
            "cap_r1_3_5": 3.0,
            "cap_r1_5_6": 3.0,
            "cap_r1_6_10": 3.0,
            "prec_t1_t2": 3.0,
            "makespan_task_0": 3.0,
            "makespan_task_1": 2.0,
            "start_link_t1": 0.0,
            "assign_link_t1_r1": 0.0,
            "start_link_t2": 0.0,
            "assign_link_t2_r1": 0.0,
        }
        assert model.sense == {
            "task_compilation_0": "==",
            "task_compilation_1": "==",
            "cap_r1_0_2": "<=",
            "cap_r1_2_3": "<=",
            "cap_r1_3_5": "<=",
            "cap_r1_5_6": "<=",
            "cap_r1_6_10": "<=",
            "prec_t1_t2": ">=",
            "makespan_task_0": ">=",
            "makespan_task_1": ">=",
            "start_link_t1": "==",
            "assign_link_t1_r1": "==",
            "start_link_t2": "==",
            "assign_link_t2_r1": "==",
        }
        assert model.objective == {
            "col_serial_ok": 1.0,
            "makespan": 1.0,
        }

    def test_native_relaxation_preserves_binary_bounds(self) -> None:
        """原生 LP 松弛只取消整数性，不移除二元边界。"""
        model = _make_closed_native_triad(relaxation=True)

        assert set(model.variable_types.values()) == {"continuous"}
        assert model.lower_bounds["col_serial_ok"] == 0.0
        assert model.upper_bounds["col_serial_ok"] == 1.0
        assert model.upper_bounds["start_t1"] == float("inf")


# ==================== extract_shadow_prices 测试 =================


class TestExtractShadowPrices:
    """extract_shadow_prices 函数测试。/ extract_shadow_prices tests."""

    @pytest.mark.parametrize(
        ("values", "coeffs"),
        [
            ({"col_c1": 1.0}, "default"),
            ({"col_c1": 10.0}, "cap_only"),
            ({"col_c1": 0.0}, "cap_only"),
            ({}, "empty"),
        ],
    )
    def test_no_dual_values_is_not_a_shadow_price(
        self,
        values: dict[str, float],
        coeffs: str,
    ) -> None:
        """没有真实对偶时一律报错，不返回 0/1 松弛标记。/ Without real duals, fail instead of returning 0/1 flags."""
        mm = _make_meta_model()
        selected: tuple[ConstraintCoeff, ...]
        if coeffs == "default":
            selected = _make_coeffs()
        elif coeffs == "cap_only":
            selected = (
                ConstraintCoeff(
                    constraint_name="cap_r1_0_10",
                    variable_name="col_c1",
                    coefficient=1.0,
                ),
            )
        else:
            selected = ()
        # 决定 3（2026-11-11 用户裁决 A）：紧约束记 1.0 / 松弛记 0.0 与边际价格不是同一个量，
        # 静默返回会让调用方拿到错数字且没有任何错误信号。
        # Decision 3: tightness flags are not marginal prices; return an error instead.
        with pytest.raises(ValueError, match="影子价格"):
            extract_shadow_prices(
                meta_model=mm,
                constraint_coeffs=selected,
                values=SolveValue(values=values),
            )

    def test_extract_uses_real_dual_values_not_tightness(self) -> None:
        """真实对偶不按紧约束映射为 0/1。 / Real duals are not mapped to 0/1 by tightness."""
        mm = MetaModel(name="dual-prices")
        mm.register_constraint("task_compilation_0", {"rhs": 0.0, "sense": "<="})
        mm.register_constraint("task_compilation_1", {"rhs": 0.0, "sense": "<="})
        mm.register_constraint("capacity", {"rhs": 1.0, "sense": "<="})

        prices = extract_shadow_prices(
            meta_model=mm,
            constraint_coeffs=(),
            values=SolveValue(values={}),
            dual_values={
                "task_compilation_0": -3.5,
                "task_compilation_1": 0.0,
                "capacity": 9.0,
            },
        )

        assert prices == {"task_compilation_0": -3.5}

    def test_extract_dual_path_honors_explicit_task_count(self) -> None:
        """显式任务数限制原生提取范围。 / Explicit task count bounds native extraction."""
        mm = MetaModel(name="bounded-task-duals")
        mm.register_constraint("task_compilation_0", {"rhs": 0.0, "sense": "<="})
        mm.register_constraint("task_compilation_1", {"rhs": 0.0, "sense": "<="})

        prices = extract_shadow_prices(
            meta_model=mm,
            constraint_coeffs=(),
            values=SolveValue(values={}),
            dual_values={
                "task_compilation_0": 1.0,
                "task_compilation_1": 2.0,
            },
            task_count=1,
        )

        assert prices == {"task_compilation_0": 1.0}

    def test_extract_rejects_unknown_dual_row(self) -> None:
        """未知对偶行不能静默偏移索引。 / Unknown dual rows cannot silently shift indices."""
        mm = MetaModel(name="unknown-dual-row")
        mm.register_constraint("task_compilation_0", {"rhs": 0.0, "sense": "<="})

        with pytest.raises(ValueError, match="unknown constraints"):
            extract_shadow_prices(
                meta_model=mm,
                constraint_coeffs=(),
                values=SolveValue(values={}),
                dual_values={"stale_row": 2.0},
            )


# ==================== build_schedule 测试 =========================


class TestBuildSchedule:
    """build_schedule 函数测试。/ build_schedule tests."""

    def test_build_schedule_returns_tuple(self) -> None:
        """构建调度返回元组。/ Build schedule returns tuple."""
        tasks = (
            Task(task_key="t1", name="T1", duration=3.0),
            Task(task_key="t2", name="T2", duration=2.0),
        )
        problem = GanttProblem(name="test", tasks=tasks)
        values = SolveValue(values={"start_t1": 0.0, "start_t2": 3.0})
        schedule = build_schedule(problem=problem, values=values)
        assert isinstance(schedule, tuple)

    def test_build_schedule_entry_count_matches_tasks(self) -> None:
        """调度条目数等于任务数。/ Entry count matches task count."""
        tasks = (
            Task(task_key="t1", name="T1", duration=3.0),
            Task(task_key="t2", name="T2", duration=2.0),
        )
        problem = GanttProblem(name="test", tasks=tasks)
        values = SolveValue(values={"start_t1": 0.0, "start_t2": 3.0})
        schedule = build_schedule(problem=problem, values=values)
        assert len(schedule) == 2

    def test_build_schedule_default_start_zero(self) -> None:
        """默认开始时间为 0。/ Default start time is 0."""
        tasks = (Task(task_key="t1", name="T1", duration=3.0),)
        problem = GanttProblem(name="test", tasks=tasks)
        values = SolveValue(values={})
        schedule = build_schedule(problem=problem, values=values)
        assert schedule[0].start_time == 0.0

    def test_build_schedule_end_time_equals_start_plus_duration(self) -> None:
        """结束时间等于开始时间加持续时间。/ End = start + duration."""
        tasks = (Task(task_key="t1", name="T1", duration=3.0),)
        problem = GanttProblem(name="test", tasks=tasks)
        values = SolveValue(values={"start_t1": 5.0})
        schedule = build_schedule(problem=problem, values=values)
        assert schedule[0].end_time == 8.0

    def test_build_schedule_assigns_resource(self) -> None:
        """调度分配资源。/ Schedule assigns resource."""
        tasks = (
            Task(
                task_key="t1",
                name="T1",
                duration=3.0,
                resource_requirements=(("r1", 1.0),),
            ),
        )
        problem = GanttProblem(name="test", tasks=tasks)
        values = SolveValue(
            values={"start_t1": 0.0, "assign_t1_r1": 1.0},
        )
        schedule = build_schedule(problem=problem, values=values)
        assert schedule[0].assigned_resource == "r1"
