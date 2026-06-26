"""任务模型构建器测试 / Task model builder tests.

覆盖 task_model_builder 中的辅助函数。
Covers helper functions in task_model_builder.
"""

from __future__ import annotations

from ospf_python.core.model.mechanism.meta_model import MetaModel
from ospf_python.core.solver.value.solve_value import SolveValue
from ospf_python.framework.gantt_scheduling.application.model.gantt_problem import (
    GanttProblem,
)
from ospf_python.framework.gantt_scheduling.application.service.task.task_column import (
    ConstraintCoeff,
    TaskColumn,
)
from ospf_python.framework.gantt_scheduling.application.service.task.task_model_builder import (
    build_schedule,
    build_triad_model,
    extract_shadow_prices,
)
from ospf_python.framework.gantt_scheduling.domain.task.model.task import Task


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
        """非松弛模式构建成功。/ Non-relaxation build succeeds."""
        mm = _make_meta_model()
        model = build_triad_model(
            meta_model=mm,
            active_columns=_make_columns(),
            constraint_coeffs=_make_coeffs(),
            relaxation=False,
        )
        assert model.name == "test_model"


# ==================== extract_shadow_prices 测试 =================


class TestExtractShadowPrices:
    """extract_shadow_prices 函数测试。/ extract_shadow_prices tests."""

    def test_extract_returns_dict(self) -> None:
        """提取返回字典。/ Extract returns dict."""
        mm = _make_meta_model()
        values = SolveValue(values={"col_c1": 1.0})
        prices = extract_shadow_prices(
            meta_model=mm,
            constraint_coeffs=_make_coeffs(),
            values=values,
        )
        assert isinstance(prices, dict)

    def test_extract_tight_constraint_price_1(self) -> None:
        """紧约束影子价格为 1.0。/ Tight constraint price is 1.0."""
        mm = _make_meta_model()
        values = SolveValue(values={"col_c1": 10.0})
        prices = extract_shadow_prices(
            meta_model=mm,
            constraint_coeffs=(
                ConstraintCoeff(
                    constraint_name="cap_r1_0_10",
                    variable_name="col_c1",
                    coefficient=1.0,
                ),
            ),
            values=values,
        )
        # LHS=10, rhs=10, slack=0 -> price=1.0
        assert prices.get("cap_r1_0_10") == 1.0

    def test_extract_slack_constraint_price_0(self) -> None:
        """松弛约束影子价格为 0.0。/ Slack constraint price is 0.0."""
        mm = _make_meta_model()
        values = SolveValue(values={"col_c1": 0.0})
        prices = extract_shadow_prices(
            meta_model=mm,
            constraint_coeffs=(
                ConstraintCoeff(
                    constraint_name="cap_r1_0_10",
                    variable_name="col_c1",
                    coefficient=1.0,
                ),
            ),
            values=values,
        )
        # LHS=0, rhs=10, slack=10 -> price=0.0
        assert prices.get("cap_r1_0_10") == 0.0

    def test_extract_empty_coeffs(self) -> None:
        """空系数提取成功。/ Empty coeffs extract succeeds."""
        mm = _make_meta_model()
        values = SolveValue(values={})
        prices = extract_shadow_prices(
            meta_model=mm,
            constraint_coeffs=(),
            values=values,
        )
        # All constraints have LHS=0
        assert isinstance(prices, dict)


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
