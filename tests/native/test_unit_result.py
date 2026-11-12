"""unit 值与失败的传输合同 / Unit-value and failure transport contracts."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ospf_python import _native
from ospf_python._binding.model import ConstraintSpec, MetaModelFloat64, VariableSpec
from ospf_python._binding.multiarray import MutableMultiArray
from ospf_python.multiarray.shape import DynShape
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed

if TYPE_CHECKING:
    from ospf_python._binding.control import SolveProgress
    from ospf_python._binding.result import BindingResult


def test_model_unit_results_match_the_declared_python_contract() -> None:
    model = MetaModelFloat64.create("unit-results").unwrap()
    try:
        x = model.add_variables([VariableSpec(name="x")]).unwrap()[0]
        assert (
            model.add_constraints(
                [ConstraintSpec(name="limit", terms=[(x, 1)], relation="<=", rhs=2)]
            ).unwrap()
            is None
        )
        assert model.set_bounds(handle=x, lower=0, upper=2).unwrap() is None
        assert model.set_objective(terms=[(x, 1)], sense="maximize").unwrap() is None
        result = model.set_bounds(handle=x, lower=2, upper=1)
        assert isinstance(result, Failed)
        assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT
    finally:
        assert model.close().unwrap() is None
        assert model.close().unwrap() is None


def test_native_model_unit_transport_uses_none_without_losing_failure() -> None:
    model = MetaModelFloat64.create("native-unit-results").unwrap()
    x = model.add_variables([VariableSpec(name="x")]).unwrap()[0]
    assert model._handle.add_constraints([("limit", [(x, 1.0)], "<=", 2.0)]) == (
        None,
        None,
    )
    assert model._handle.set_bounds(handle=x, lower=0.0, upper=2.0) == (None, None)
    assert model._handle.set_objective(terms=[(x, 1.0)], sense="maximize") == (
        None,
        None,
    )
    value, failure = model._handle.set_bounds(handle=x, lower=2.0, upper=1.0)
    assert value is None and failure is not None
    assert failure.category == "ILLEGAL_ARGUMENT"
    assert model._handle.close() == (None, None)


def test_array_and_view_unit_results_preserve_none_elements_and_rollback() -> None:
    values: list[int | None] = [1, 2]
    array = MutableMultiArray.create(values=values, shape=DynShape((2,))).unwrap()
    view = array.view(offsets=(0,), shape=DynShape((2,))).unwrap()
    assert array.set_many([((0,), None)]).unwrap() is None
    assert array.at((0,)).unwrap() is None
    assert view.set_many([((1,), None)]).unwrap() is None
    assert view.at((1,)).unwrap() is None
    assert array._handle.set_many([([0], 1)]) == (None, None)
    assert array._handle.region_set_many(view._handle, [([1], 2)]) == (None, None)
    assert array.set_many([((0,), 4), ((0,), 5)]).is_failed()
    assert array.flatten().unwrap() == [1, 2]


@pytest.mark.parametrize("solver", ["scip", "gurobi10", "gurobi11", "gurobi12"])
def test_unit_result_can_be_returned_by_progress_callback(solver: str) -> None:
    if solver not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {solver}")
    array = MutableMultiArray.create(values=[0], shape=DynShape((1,))).unwrap()
    model = MetaModelFloat64.create("unit-callback").unwrap()
    try:
        x = model.add_variables([VariableSpec(name="x", lower=0, upper=2)]).unwrap()[0]
        model.set_objective(terms=[(x, 1)], sense="maximize").unwrap()
        calls = 0

        def callback(event: SolveProgress) -> BindingResult[None]:
            nonlocal calls
            calls += 1
            return array.set(indices=(0,), value=calls)

        report = model.solve(solver=solver, on_progress=callback).unwrap()
        assert report.objective == 2
        assert calls > 0
        assert array.at((0,)).unwrap() == calls
    finally:
        model.close().unwrap()
