"""束编组原生模型合同 / Native bunch-model contracts.

验证束服务以 Rust `MetaModelFloat64` 为唯一可变模型权威，并通过只读线性
快照求解。
Verify that the bunch service uses Rust `MetaModelFloat64` as its sole mutable
model authority and solves through a read-only linear snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from ospf_python.core.solver.output.solver_output import SolverOutput
from ospf_python.core.solver.output.solver_status import SolverStatus
from ospf_python.core.solver.value.solve_value import SolveValue
from ospf_python.framework.gantt_scheduling.application.model.gantt_problem import (
    GanttProblem,
    PrecedenceRelation,
)
from ospf_python.framework.gantt_scheduling.application.service.bunch.bunch_application_service import (
    BunchApplicationService,
)
from ospf_python.framework.gantt_scheduling.application.service.bunch.bunch_column import (
    BunchColumn,
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
        name="native-bunch",
        tasks=(
            Task(
                task_key="t1",
                name="T1",
                duration=3.0,
                earliest_start=0.0,
                deadline=10.0,
                resource_requirements=(("r1", 1.0),),
            ),
            Task(
                task_key="t2",
                name="T2",
                duration=2.0,
                earliest_start=1.0,
                deadline=12.0,
                resource_requirements=(("r1", 1.0),),
            ),
        ),
        resources=(Resource(resource_key="r1", name="R1", capacity=2.0),),
        time_horizon=20.0,
    )


def _service(*, solver: object | None = None) -> BunchApplicationService:
    return BunchApplicationService(
        solver=solver or _SuccessfulSolver(),  # type: ignore[arg-type]
        task_context=TaskContext(),
        resource_context=ResourceContext(),
        bunch_context=BunchGenerationContext(),
    )


@dataclass(frozen=True)
class _SuccessfulSolver:
    @property
    def name(self) -> str:
        return "successful-fixture"

    def solve(self, model: object, *, options: object = None) -> SolverOutput:
        del model, options
        return SolverOutput(
            status=SolverStatus.OPTIMAL,
            objective=0.0,
            values=SolveValue(values={}),
        )


@dataclass(frozen=True)
class _DualSolver:
    @property
    def name(self) -> str:
        return "dual-fixture"

    def solve(self, model: object, *, options: object = None) -> SolverOutput:
        del model, options
        return SolverOutput(
            status=SolverStatus.OPTIMAL,
            values=SolveValue(values={}),
            dual_values={"demand_t1": -2.0, "demand_t2": -3.0},
        )


def _column(
    *,
    key: str,
    assignments: tuple[tuple[str, float], ...],
    cost: float,
) -> BunchColumn:
    return BunchColumn(
        bunch_key=key,
        task_assignments=assignments,
        resource_key="r1",
        cost=cost,
    )


def test_register_exports_task_variables_and_demand_rows() -> None:
    service = _service()
    assert service.register(_problem()).is_ok()

    native_model = service._native_model
    assert native_model is not None
    exported = native_model.to_linear_triad().unwrap()
    variables = {variable.name: variable for variable in exported.variables}
    rows = {row.name: row for row in exported.rows}

    assert variables["start_t1"].kind == "continuous"
    assert variables["start_t1"].lower == 0.0
    assert variables["start_t1"].upper == 7.0
    assert variables["start_t2"].lower == 1.0
    assert variables["start_t2"].upper == 10.0
    assert variables["covered_t1"].kind == "binary"
    assert variables["covered_t2"].kind == "binary"
    assert rows["demand_t1"].relation == ">="
    assert rows["demand_t1"].rhs == 1.0
    assert rows["demand_t2"].coefficients == {}
    assert rows["cover_presence_0"].coefficients == {"covered_t1": 1.0}
    assert rows["cover_presence_0"].relation == "=="
    assert rows["start_bridge_0"].coefficients == {"start_t1": 1.0}
    assert rows["start_bridge_0"].relation == "=="
    assert exported.sense == "minimize"
    assert exported.objective == {}


def test_add_column_exports_binary_variable_and_accumulates_capacity_coefficients() -> (
    None
):
    service = _service()
    assert service.register(_problem()).is_ok()
    column = _column(
        key="both",
        assignments=(("t1", 0.0), ("t2", 1.0)),
        cost=7.0,
    )
    assert service.add_columns((column,)).is_ok()

    native_model = service._native_model
    assert native_model is not None
    exported = native_model.to_linear_triad().unwrap()
    variables = {variable.name: variable for variable in exported.variables}
    rows = {row.name: row for row in exported.rows}

    assert variables["bunch_both"].kind == "binary"
    assert variables["cover_mode_0_0"].kind == "binary"
    assert variables["cover_mode_1_0"].kind == "binary"
    assert rows["demand_t1"].coefficients == {"bunch_both": 1.0}
    assert rows["demand_t2"].coefficients == {"bunch_both": 1.0}
    assert rows["cover_presence_0"].coefficients == {
        "covered_t1": 1.0,
        "cover_mode_0_0": -1.0,
    }
    assert rows["cover_presence_0"].relation == "=="
    assert rows["cover_link_0_0"].coefficients == {
        "bunch_both": 1.0,
        "cover_mode_0_0": -1.0,
    }
    assert rows["cover_mode_members_0_0"].coefficients == {
        "cover_mode_0_0": 1.0,
        "bunch_both": -1.0,
    }
    assert rows["start_bridge_0"].coefficients == {"start_t1": 1.0}
    assert rows["start_bridge_1"].coefficients == {
        "start_t2": 1.0,
        "cover_mode_1_0": -1.0,
    }
    assert exported.objective == {"bunch_both": 7.0}

    overlapping = [
        row
        for row in exported.rows
        if row.name.startswith("cap_r1_") and row.coefficients.get("bunch_both") == 2.0
    ]
    assert len(overlapping) == 1
    assert overlapping[0].relation == "<="
    assert overlapping[0].rhs == 2.0


def test_capacity_coefficients_use_actual_resource_demand() -> None:
    problem = GanttProblem(
        name="demand-weighted-bunch",
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
                resource_requirements=(("r1", 3.0),),
            ),
        ),
        resources=(Resource(resource_key="r1", name="R1", capacity=5.0),),
        time_horizon=10.0,
    )
    service = _service()
    assert service.register(problem).is_ok()
    column = _column(
        key="both",
        assignments=(("t1", 0.0), ("t2", 0.0)),
        cost=1.0,
    )
    assert service.add_columns((column,)).is_ok()

    native_model = service._native_model
    assert native_model is not None
    exported = native_model.to_linear_triad().unwrap()
    rows = {row.name: row for row in exported.rows}

    assert rows["cap_r1_0_2"].coefficients == {"bunch_both": 5.0}
    assert rows["cap_r1_2_3"].coefficients == {"bunch_both": 2.0}


def test_capacity_windows_include_candidate_column_boundaries() -> None:
    problem = GanttProblem(
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
    service = _service()
    assert service.register(problem).is_ok()
    assert service.add_columns(
        (
            BunchColumn("t1_only", (("t1", 0.3),), "r1", 1.0),
            BunchColumn("t2_only", (("t2", 0.7),), "r1", 1.0),
        )
    ).is_ok()

    native_model = service._native_model
    assert native_model is not None
    exported = native_model.to_linear_triad().unwrap()
    rows = {row.name: row for row in exported.rows}

    assert rows["cap_r1_0.3_0.5"].coefficients == {"bunch_t1_only": 1.0}
    assert rows["cap_r1_0.7_0.8"].coefficients == {"bunch_t2_only": 1.0}
    assert rows["cap_r1_0.8_0.9"].coefficients == {"bunch_t2_only": 1.0}
    assert all(
        not (
            "bunch_t1_only" in row.coefficients and "bunch_t2_only" in row.coefficients
        )
        for name, row in rows.items()
        if name.startswith("cap_r1_")
    )


def test_register_rejects_negative_resource_demand_before_native_publication() -> None:
    problem = GanttProblem(
        name="negative-demand",
        tasks=(
            Task(
                task_key="t1",
                name="T1",
                duration=1.0,
                resource_requirements=(("r1", -1.0),),
            ),
        ),
        resources=(Resource(resource_key="r1", name="R1", capacity=1.0),),
    )
    service = _service()

    result = service.register(problem)

    assert result.is_failed()
    assert "t1.r1" in result.error.message
    assert service._native_model is None


def test_failed_batch_preserves_native_model_identity_and_active_columns() -> None:
    service = _service()
    assert service.register(_problem()).is_ok()
    first = _column(key="first", assignments=(("t1", 0.0),), cost=1.0)
    assert service.add_columns((first,)).is_ok()
    native_model = service._native_model
    assert native_model is not None
    identity = native_model.model_identity

    duplicate = _column(key="duplicate", assignments=(("t2", 1.0),), cost=2.0)
    result = service.add_columns((duplicate, duplicate))

    assert result.is_failed()
    assert service._native_model is native_model
    assert native_model.model_identity == identity
    assert service.active_columns == (first,)


@pytest.mark.parametrize(
    "column",
    [
        _column(key="", assignments=(("t1", 0.0),), cost=1.0),
        _column(key="unknown-task", assignments=(("missing", 0.0),), cost=1.0),
        _column(key="bad-start", assignments=(("t1", float("nan")),), cost=1.0),
        BunchColumn("unknown-resource", (("t1", 0.0),), "missing", 1.0),
        _column(key="nan-cost", assignments=(("t1", 0.0),), cost=float("nan")),
        _column(key="early", assignments=(("t2", 0.0),), cost=1.0),
        _column(
            key="inconsistent-start",
            assignments=(("t1", 0.0), ("t1", 1.0)),
            cost=1.0,
        ),
    ],
)
def test_invalid_column_batch_does_not_publish(column: BunchColumn) -> None:
    service = _service()
    assert service.register(_problem()).is_ok()

    assert service.add_columns((column,)).is_failed()
    assert service.active_columns == ()


def test_remove_columns_rebuilds_and_replaces_native_model() -> None:
    service = _service()
    assert service.register(_problem()).is_ok()
    keep = _column(key="keep", assignments=(("t1", 0.0),), cost=1.0)
    remove = _column(key="remove", assignments=(("t2", 1.0),), cost=2.0)
    assert service.add_columns((keep, remove)).is_ok()
    previous = service._native_model
    assert previous is not None
    previous_identity = previous.model_identity

    assert service.remove_columns(("remove",)).is_ok()

    assert service._native_model is not previous
    assert service._native_model is not None
    assert service._native_model.model_identity != previous_identity
    assert service.active_columns == (keep,)
    exported = service._native_model.to_linear_triad().unwrap()
    names = {variable.name for variable in exported.variables}
    assert "bunch_keep" in names
    assert "bunch_remove" not in names
    assert previous.to_linear_triad().is_failed()


def test_refresh_shadow_price_publishes_real_dual_values() -> None:
    service = _service(solver=_DualSolver())
    assert service.register(_problem()).is_ok()
    column = _column(
        key="both",
        assignments=(("t1", 0.0), ("t2", 1.0)),
        cost=7.0,
    )
    assert service.add_columns((column,)).is_ok()

    result = service.refresh_shadow_price()

    assert result.is_ok()
    assert result.unwrap() == {"demand_t1": -2.0, "demand_t2": -3.0}
    assert service.iteration == 1


def test_precedence_uses_linked_start_variables() -> None:
    problem = GanttProblem(
        name="bunch-precedence",
        tasks=(
            Task(
                task_key="t1",
                name="T1",
                duration=3.0,
                resource_requirements=(("r1", 1.0),),
            ),
            Task(
                task_key="t2",
                name="T2",
                duration=2.0,
                resource_requirements=(("r1", 1.0),),
            ),
        ),
        resources=(Resource(resource_key="r1", name="R1", capacity=2.0),),
        precedence_relations=(PrecedenceRelation("t1", "t2"),),
        time_horizon=20.0,
    )
    service = _service()
    assert service.register(problem).is_ok()
    column = _column(
        key="serial",
        assignments=(("t1", 0.0), ("t2", 3.0)),
        cost=1.0,
    )
    assert service.add_columns((column,)).is_ok()

    native_model = service._native_model
    assert native_model is not None
    exported = native_model.to_linear_triad().unwrap()
    rows = {row.name: row for row in exported.rows}

    assert rows["prec_t1_t2"].coefficients == {
        "start_t1": -1.0,
        "start_t2": 1.0,
    }
    assert rows["prec_t1_t2"].rhs == 3.0
    assert rows["prec_t1_t2"].relation == ">="
    assert rows["start_bridge_0"].coefficients == {"start_t1": 1.0}
    assert rows["start_bridge_1"].coefficients == {
        "start_t2": 1.0,
        "cover_mode_1_0": -3.0,
    }


def test_incompatible_covering_columns_are_mutually_exclusive() -> None:
    service = _service()
    assert service.register(_problem()).is_ok()
    early = _column(key="early", assignments=(("t1", 0.0),), cost=1.0)
    late = _column(key="late", assignments=(("t1", 2.0),), cost=1.0)
    assert service.add_columns((early, late)).is_ok()

    native_model = service._native_model
    assert native_model is not None
    exported = native_model.to_linear_triad().unwrap()
    rows = {row.name: row for row in exported.rows}

    assert rows["cover_mode_exclusive_0"].coefficients == {
        "cover_mode_0_0": 1.0,
        "cover_mode_0_1": 1.0,
    }
    assert rows["cover_mode_exclusive_0"].rhs == 1.0
    assert rows["cover_mode_exclusive_0"].relation == "<="
    assert rows["start_bridge_0"].coefficients == {
        "start_t1": 1.0,
        "cover_mode_0_1": -2.0,
    }


def test_compatible_covering_columns_share_one_mode() -> None:
    service = _service()
    assert service.register(_problem()).is_ok()
    first = _column(key="first", assignments=(("t1", 0.0),), cost=1.0)
    second = _column(key="second", assignments=(("t1", 0.0),), cost=1.0)
    assert service.add_columns((first, second)).is_ok()

    native_model = service._native_model
    assert native_model is not None
    exported = native_model.to_linear_triad().unwrap()
    rows = {row.name: row for row in exported.rows}

    assert rows["cover_link_0_0"].coefficients == {
        "bunch_first": 1.0,
        "cover_mode_0_0": -1.0,
    }
    assert rows["cover_link_0_1"].coefficients == {
        "bunch_second": 1.0,
        "cover_mode_0_0": -1.0,
    }
    assert rows["cover_mode_members_0_0"].coefficients == {
        "cover_mode_0_0": 1.0,
        "bunch_first": -1.0,
        "bunch_second": -1.0,
    }
    assert "cover_mode_0_1" not in rows
    assert "cover_mode_exclusive_0" not in rows


def test_relaxation_keeps_binary_bounds_but_changes_types() -> None:
    service = _service()
    assert service.register(_problem()).is_ok()
    column = _column(
        key="both",
        assignments=(("t1", 0.0), ("t2", 1.0)),
        cost=7.0,
    )
    assert service.add_columns((column,)).is_ok()

    triad = service._native_triad(relaxation=True)

    assert triad.is_ok()
    relaxed = triad.unwrap()
    assert set(relaxed.variable_types.values()) == {"continuous"}
    assert relaxed.lower_bounds["bunch_both"] == 0.0
    assert relaxed.upper_bounds["bunch_both"] == 1.0
