"""单次求解时限及审计合同 / Per-solve time limits and audit contracts."""

from __future__ import annotations

import json
import random

import pytest

from ospf_python import _native
from ospf_python._binding.control import SolveHandle, SolveProgress
from ospf_python._binding.model import ConstraintSpec, MetaModelFloat64, VariableSpec
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed


@pytest.fixture(params=["scip", "gurobi10", "gurobi11", "gurobi12"])
def solver(request: pytest.FixtureRequest) -> str:
    name = str(request.param)
    if name not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {name}")
    return name


def test_time_limit_is_in_the_report_and_configuration_fingerprint(solver: str) -> None:
    model = MetaModelFloat64.create("time-limit-audit").unwrap()
    try:
        x = model.add_variables([VariableSpec(name="x", lower=0, upper=2)]).unwrap()[0]
        model.set_objective(terms=[(x, 1)], sense="maximize").unwrap()
        reports = [
            model.solve(solver=solver, time_limit=limit).unwrap()
            for limit in (None, 10.25, 20.5, 10.2500000001, None)
        ]
        raw = [json.loads(report.raw_json) for report in reports]
        assert all(report.objective == pytest.approx(2) for report in reports)
        for report, expected in zip(
            raw,
            ("None", "Some(10.25)", "Some(20.5)", "Some(10.25)", "None"),
            strict=True,
        ):
            provenance = report["provenance"]
            assert provenance["requestedConfiguration"]["time_limit"] == expected
            assert provenance["effectiveConfiguration"]["time_limit"] == expected
        fingerprints = [report["fingerprints"] for report in raw]
        config = [value["configuration"]["value"] for value in fingerprints]
        assert len(set(config[:3])) == 3
        assert config[1] == config[3]
        assert config[0] == config[4]
        assert len({value["model"]["value"] for value in fingerprints}) == 1
        events: list[SolveProgress] = []
        with_progress = model.solve(
            solver=solver, time_limit=10.25, on_progress=events.append
        ).unwrap()
        assert events and events[-1].terminal
        assert (
            json.loads(with_progress.raw_json)["provenance"]["effectiveConfiguration"][
                "time_limit"
            ]
            == "Some(10.25)"
        )
    finally:
        assert model.close().is_ok()


def test_cancelled_report_keeps_the_requested_limit(solver: str) -> None:
    model = MetaModelFloat64.create("cancelled-time-limit").unwrap()
    try:
        x = model.add_variables([VariableSpec(name="x", lower=0, upper=2)]).unwrap()[0]
        model.set_objective(terms=[(x, 1)], sense="maximize").unwrap()
        control = SolveHandle()
        control.cancel().unwrap()
        report = model.solve(
            solver=solver, time_limit=10.25, cancellation=control
        ).unwrap()
        raw = json.loads(report.raw_json)
        assert report.termination_reason == "CANCELLED"
        assert (
            raw["provenance"]["requestedConfiguration"]["time_limit"] == "Some(10.25)"
        )
        assert raw["fingerprints"]["configuration"] is None
    finally:
        assert model.close().is_ok()


def test_real_milp_obeys_the_limit_and_rejected_attempt_is_reusable(
    solver: str,
) -> None:
    model = MetaModelFloat64.create("time-limited-independent-set").unwrap()
    try:
        variables = model.add_variables(
            [VariableSpec(name=f"x{i}", kind="binary") for i in range(80)]
        ).unwrap()
        rng = random.Random(42)
        model.add_constraints(
            [
                ConstraintSpec(
                    name=f"edge-{i}-{j}",
                    terms=[(variables[i], 1), (variables[j], 1)],
                    relation="<=",
                    rhs=1,
                )
                for i in range(80)
                for j in range(i)
                if rng.random() < 0.4
            ]
        ).unwrap()
        model.set_objective(
            terms=[(variable, 1) for variable in variables], sense="maximize"
        ).unwrap()
        control = SolveHandle()
        rejected = model.solve(solver=solver, time_limit=1e-20, cancellation=control)
        assert isinstance(rejected, Failed)
        assert rejected.error.code is ErrorCode.ILLEGAL_ARGUMENT
        assert control.phase == "READY"
        report = model.solve(
            solver=solver, time_limit=1e-9, cancellation=control
        ).unwrap()
        assert report.termination_reason == "TIME_LIMIT"
        assert control.phase == "FINISHED"
        raw = json.loads(report.raw_json)
        assert raw["provenance"]["effectiveConfiguration"]["time_limit"] == "Some(1e-9)"
    finally:
        assert model.close().is_ok()


@pytest.mark.parametrize("seconds", [1e-20, 1e-100, 5e-324])
def test_unrepresentable_time_limit_is_rejected_before_attempt(seconds: float) -> None:
    model = MetaModelFloat64.create("time-limit-precision").unwrap()
    control = SolveHandle()
    try:
        result = model.solve(solver="unknown", time_limit=seconds, cancellation=control)
        assert isinstance(result, Failed)
        assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT
        assert control.phase == "READY"
        assert control.completed_at_epoch_ms is None
    finally:
        assert model.close().is_ok()
