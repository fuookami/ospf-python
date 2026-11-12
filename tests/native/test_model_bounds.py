"""私有模型的变量范围合同 / Variable-range contracts for the private model."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ospf_python import _native
from ospf_python._binding.model import ConstraintSpec, MetaModelFloat64, VariableSpec
from ospf_python._binding.result import BindingResult, invoke
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed

if TYPE_CHECKING:
    from ospf_python._binding.control import SolveProgress


@pytest.fixture(params=["scip", "gurobi10", "gurobi11", "gurobi12"])
def solver(request: pytest.FixtureRequest) -> str:
    name = str(request.param)
    if name not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {name}")
    return name


@pytest.mark.parametrize(
    ("kind", "lower", "upper"),
    [
        ("continuous", 2, 1),
        ("continuous", float("nan"), 1),
        ("continuous", 0, float("inf")),
        ("continuous", True, 1),
        ("continuous", 0, 2**53),
        ("integer", 0.5, 2),
        ("integer", 0, float(2**53)),
        ("binary", -1, 1),
        ("binary", 0, 2),
        ("binary", 0, 0.5),
    ],
)
def test_invalid_bounds_are_rejected(
    kind: str, lower: int | float, upper: int | float
) -> None:
    model = MetaModelFloat64.create("invalid-bounds").unwrap()
    try:
        variable = model.add_variables([VariableSpec(name="x", kind=kind)]).unwrap()[0]
        result = model.set_bounds(handle=variable, lower=lower, upper=upper)
        assert isinstance(result, Failed)
        assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT
        assert model.snapshot().unwrap()[2:] == (1, 0)
    finally:
        model.close().unwrap()


def test_foreign_and_closed_model_reject_bounds_update() -> None:
    first = MetaModelFloat64.create("first").unwrap()
    second = MetaModelFloat64.create("second").unwrap()
    try:
        variable = first.add_variables([VariableSpec(name="x")]).unwrap()[0]
        result = second.set_bounds(handle=variable, lower=0, upper=1)
        assert isinstance(result, Failed)
        assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT
        first.close().unwrap()
        result = first.set_bounds(handle=variable, lower=0, upper=1)
        assert isinstance(result, Failed)
        assert result.error.code is ErrorCode.NOT_INITIALIZED
    finally:
        first.close().unwrap()
        second.close().unwrap()


@pytest.mark.parametrize("bound", [float("nan"), float("inf"), 0.5])
def test_native_boundary_also_rejects_invalid_integer_bounds(bound: float) -> None:
    model = MetaModelFloat64.create("native-bounds").unwrap()
    try:
        variable = model.add_variables(
            [VariableSpec(name="x", kind="integer")]
        ).unwrap()[0]
        result: BindingResult[None] = invoke(
            lambda: model._handle.set_bounds(handle=variable, lower=bound, upper=2)
        )
        assert isinstance(result, Failed)
        assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT
    finally:
        model.close().unwrap()


@pytest.mark.parametrize("kind", ["continuous", "integer"])
def test_bounds_update_changes_repeated_real_solves(solver: str, kind: str) -> None:
    model = MetaModelFloat64.create("bounds-update").unwrap()
    try:
        x, y = model.add_variables(
            [
                VariableSpec(name="x", kind=kind, lower=0, upper=4),
                VariableSpec(name="y", lower=0, upper=2),
            ]
        ).unwrap()
        model.add_constraints(
            [
                ConstraintSpec(
                    name="capacity", terms=[(x, 1), (y, 1)], relation="<=", rhs=5
                )
            ]
        ).unwrap()
        model.set_objective(terms=[(x, 3), (y, 1)], sense="maximize").unwrap()
        before = model.solve(solver=solver).unwrap()
        assert before.values == pytest.approx((4, 1))
        assert before.objective == pytest.approx(13)

        model.set_bounds(handle=x, lower=0, upper=0).unwrap()
        retired = model.solve(solver=solver).unwrap()
        assert retired.values == pytest.approx((0, 2))
        assert retired.objective == pytest.approx(2)

        assert model.set_bounds(handle=x, lower=3, upper=1).is_failed()
        unchanged = model.solve(solver=solver).unwrap()
        assert unchanged.values == pytest.approx((0, 2))
        assert unchanged.objective == pytest.approx(2)

        model.set_bounds(handle=x, lower=0, upper=2).unwrap()
        restored = model.solve(solver=solver).unwrap()
        assert restored.values == pytest.approx((2, 2))
        assert restored.objective == pytest.approx(8)
        assert before.values == pytest.approx((4, 1))
        assert retired.values == pytest.approx((0, 2))
    finally:
        model.close().unwrap()


def test_binary_bounds_can_be_fixed_and_reset(solver: str) -> None:
    model = MetaModelFloat64.create("binary-bounds").unwrap()
    try:
        variable = model.add_variables(
            [VariableSpec(name="x", kind="binary")]
        ).unwrap()[0]
        model.set_objective(terms=[(variable, 1)], sense="maximize").unwrap()
        assert model.solve(solver=solver).unwrap().values == pytest.approx((1,))
        model.set_bounds(handle=variable, lower=0, upper=0).unwrap()
        assert model.set_bounds(handle=variable, lower=0, upper=2).is_failed()
        assert model.solve(solver=solver).unwrap().values == pytest.approx((0,))
        model.set_bounds(handle=variable, lower=None, upper=None).unwrap()
        assert model.solve(solver=solver).unwrap().values == pytest.approx((1,))
    finally:
        model.close().unwrap()


@pytest.mark.parametrize("kind", ["continuous", "integer"])
def test_none_removes_nonbinary_bounds(solver: str, kind: str) -> None:
    model = MetaModelFloat64.create("unbounded-bounds").unwrap()
    try:
        variable = model.add_variables(
            [VariableSpec(name="x", kind=kind, lower=-2, upper=1)]
        ).unwrap()[0]
        model.add_constraints(
            [
                ConstraintSpec(
                    name="upper", terms=[(variable, 1)], relation="<=", rhs=5
                ),
                ConstraintSpec(
                    name="lower", terms=[(variable, 1)], relation=">=", rhs=-4
                ),
            ]
        ).unwrap()
        model.set_objective(terms=[(variable, 1)], sense="maximize").unwrap()
        assert model.solve(solver=solver).unwrap().values == pytest.approx((1,))
        model.set_bounds(handle=variable, lower=None, upper=None).unwrap()
        assert model.solve(solver=solver).unwrap().values == pytest.approx((5,))
        model.set_objective(terms=[(variable, 1)], sense="minimize").unwrap()
        assert model.solve(solver=solver).unwrap().values == pytest.approx((-4,))
    finally:
        model.close().unwrap()


def test_bounds_update_is_rejected_during_progress_callback(solver: str) -> None:
    model = MetaModelFloat64.create("busy-bounds").unwrap()
    try:
        variable = model.add_variables(
            [VariableSpec(name="x", lower=0, upper=2)]
        ).unwrap()[0]
        model.set_objective(terms=[(variable, 1)], sense="maximize").unwrap()
        errors: list[ErrorCode] = []

        def callback(event: SolveProgress) -> None:
            if not errors:
                result = model.set_bounds(handle=variable, lower=0, upper=0)
                assert isinstance(result, Failed)
                errors.append(result.error.code)

        report = model.solve(solver=solver, on_progress=callback).unwrap()
        assert report.values == pytest.approx((2,))
        assert errors == [ErrorCode.FAILED_PRECONDITION]
        model.set_bounds(handle=variable, lower=0, upper=0).unwrap()
        assert model.solve(solver=solver).unwrap().values == pytest.approx((0,))
    finally:
        model.close().unwrap()
