"""Gantt 迁移观察：这些旧行为不是目标合同 / Legacy observations, not target contracts."""

from __future__ import annotations

import pytest

from ospf_python.core.model.mechanism.meta_model import MetaModel
from ospf_python.core.solver.mock_solver import MockSolver
from ospf_python.core.solver.value.solve_value import SolveValue
from ospf_python.framework.gantt_scheduling.application.model.gantt_problem import (
    GanttProblem,
    PrecedenceRelation,
)
from ospf_python.framework.gantt_scheduling.application.service.bunch.bunch_application_service import (
    BunchApplicationService,
    _build_triad_model,
)
from ospf_python.framework.gantt_scheduling.application.service.bunch.bunch_column import (
    BunchColumn,
)
from ospf_python.framework.gantt_scheduling.application.service.task.task_application_service import (
    TaskApplicationService,
)
from ospf_python.framework.gantt_scheduling.application.service.task.task_column import (
    ConstraintCoeff,
    TaskColumn,
)
from ospf_python.framework.gantt_scheduling.application.service.task.task_model_builder import (
    build_triad_model,
    extract_shadow_prices,
)
from ospf_python.framework.gantt_scheduling.domain.bunch_generation.model.bunch_generation_context import (
    BunchGenerationContext,
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


def _problem() -> GanttProblem:
    return GanttProblem(
        name="legacy-precedence",
        tasks=(Task("a", "A", 3.0), Task("b", "B", 2.0)),
        resources=(Resource("r", "R", 10.0),),
        precedence_relations=(PrecedenceRelation("a", "b"),),
    )


def test_task_service_registers_real_precedence_and_requires_columns() -> None:
    """旧的无列伪最优已移除，优先关系进入真实开始时间变量。"""
    service = TaskApplicationService(
        solver=MockSolver(),
        task_context=TaskContext(),
        resource_context=ResourceContext(),
    )
    assert service.register(_problem()).is_ok()
    assert service.extract_solution().is_failed()

    native_model = service._native_model
    assert native_model is not None
    exported = native_model.to_linear_triad().unwrap()
    rows = {row.name: row for row in exported.rows}
    assert rows["prec_a_b"].rhs == 3.0
    assert rows["prec_a_b"].coefficients == {
        "start_a": -1.0,
        "start_b": 1.0,
    }


def test_legacy_bunch_builder_does_not_encode_relaxation_or_precedence() -> None:
    """旧束构建不区分松弛 / The legacy bunch builder does not distinguish relaxation."""
    model = MetaModel(name="legacy")
    model.register_variable("start_a", {"type": "binary", "lb": 0.0, "ub": 1.0})
    model.register_constraint("prec_a_b", {"min_gap": 3.0, "sense": ">="})
    model.register_objective("minimize_makespan", {"type": "minimize"})
    lp = _build_triad_model(
        meta_model=model,
        active_columns=(),
        constraint_coeffs=(),
        relaxation=True,
    )
    mip = _build_triad_model(
        meta_model=model,
        active_columns=(),
        constraint_coeffs=(),
        relaxation=False,
    )
    assert lp == mip
    assert lp.constraints["prec_a_b"] == {}
    assert lp.rhs["prec_a_b"] == 0.0
    assert lp.objective == {}


def test_task_builder_encodes_relaxation_but_not_precedence_coefficients() -> None:
    """任务构建保留变量类型，但优先关系和目标仍未闭环。"""
    model = MetaModel(name="legacy-task")
    model.register_variable("start_a", {"type": "binary", "lb": 0.0, "ub": 1.0})
    model.register_constraint("prec_a_b", {"min_gap": 3.0, "sense": ">="})
    model.register_objective("minimize_makespan", {"type": "minimize"})
    lp = build_triad_model(
        meta_model=model,
        active_columns=(),
        constraint_coeffs=(),
        relaxation=True,
    )
    mip = build_triad_model(
        meta_model=model,
        active_columns=(),
        constraint_coeffs=(),
        relaxation=False,
    )
    assert lp != mip
    assert lp.variable_types == {"start_a": "continuous"}
    assert mip.variable_types == {"start_a": "binary"}
    assert mip.constraints["prec_a_b"] == {}
    assert mip.rhs["prec_a_b"] == 0.0
    assert mip.objective == {}


def test_legacy_slack_flags_are_not_offered_as_shadow_prices() -> None:
    """紧约束标记不再被当作影子价格返回，而是明确报错。 / Tightness flags are refused, not returned as prices."""
    model = MetaModel(name="legacy-price")
    model.register_constraint("required", {"rhs": 1.0, "sense": ">="})
    values = SolveValue(values={"x": 1.0})

    # 决定 3（2026-11-11 用户裁决 A）：没有真实对偶时必须报错。
    # 1.0/0.0 是"是否紧"的指示量，与边际价格不同；静默返回等于给调用方错数字。
    # Decision 3: without real duals the extraction must fail, not fabricate prices.
    with pytest.raises(ValueError, match="影子价格"):
        extract_shadow_prices(
            meta_model=model,
            constraint_coeffs=(ConstraintCoeff("required", "x", 1.0),),
            values=values,
        )

    # bunch 侧那条"松弛标记冒充影子价格"的私有函数已删除，不再有可调用的入口。
    # The bunch-side private function that fabricated prices from slack flags is gone.
    bunch_service_module = __import__(
        "ospf_python.framework.gantt_scheduling.application.service.bunch."
        "bunch_application_service",
        fromlist=["_extract_shadow_prices"],
    )
    assert not hasattr(bunch_service_module, "_extract_shadow_prices")

    exact_rhs_change = 3.0 * 2.0 - 3.0 * 1.0
    assert exact_rhs_change == 3.0


def test_duplicate_batch_is_atomic_for_task_and_bunch_services() -> None:
    """任务列和束列都在整批预检失败后保持原状态。"""
    task_service = TaskApplicationService(
        solver=MockSolver(),
        task_context=TaskContext(),
        resource_context=ResourceContext(),
    )
    bunch_service = BunchApplicationService(
        solver=MockSolver(),
        task_context=TaskContext(),
        resource_context=ResourceContext(),
        bunch_context=BunchGenerationContext(),
    )
    assert task_service.register(_problem()).is_ok()
    assert bunch_service.register(_problem()).is_ok()
    task_column = TaskColumn("task", (("a", "r", 0.0),), 1.0)
    bunch_column = BunchColumn("bunch", (("a", 0.0),), "r", 1.0)
    assert task_service.add_columns((task_column, task_column)).is_failed()
    assert bunch_service.add_columns((bunch_column, bunch_column)).is_failed()
    assert task_service.active_columns == ()
    assert bunch_service.active_columns == ()
