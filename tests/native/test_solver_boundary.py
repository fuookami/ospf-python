"""仅真实 Rust 后端验收，无 SDK 或 fake 替代 / Verify real Rust backends, never SDK/fake substitutes."""

from __future__ import annotations

import json
import pickle
from fractions import Fraction

import numpy as np
import pytest

from ospf_python import _native
from ospf_python._binding.model import ConstraintSpec, MetaModelFloat64, VariableSpec
from ospf_python._binding.multiarray import (
    MappedMultiArrayView,
    MultiArrayView,
    MutableMultiArray,
    RationalMultiArray,
)
from ospf_python._binding.numeric import Rational, RationalArray
from ospf_python.math.combinatorics import cross
from ospf_python.multiarray.multi_array import MultiArray as PublicArray
from ospf_python.multiarray.multi_array import MutableMultiArray as PublicMutableArray
from ospf_python.multiarray.multi_array_view import MultiArrayView as PublicView
from ospf_python.multiarray.shape import DynShape, Shape2, StorageOrder
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.unit.length import METER

_SOLVERS = ["scip", "gurobi10", "gurobi11", "gurobi12"]


@pytest.fixture(params=_SOLVERS)
def solver(request: pytest.FixtureRequest) -> str:
    name = str(request.param)
    if name not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {name}")
    return name


@pytest.mark.parametrize("storage", [PublicArray, PublicMutableArray])
@pytest.mark.parametrize("order", list(StorageOrder))
def test_public_live_reduction_feeds_exact_unit_aware_real_milp(
    *,
    solver: str,
    storage: type[
        PublicArray[Quantity[Fraction], Shape2]
        | PublicMutableArray[Quantity[Fraction], Shape2]
    ],
    order: StorageOrder,
) -> None:
    data = np.empty(3, dtype=object)
    for index, value in enumerate((1, 2, 3)):
        data[index] = Quantity(Fraction(value, 2), METER)
    source = storage(Shape2(1, 3, order), data)
    calls = 0

    def combine(
        left: Quantity[Fraction], right: Quantity[Fraction]
    ) -> Quantity[Fraction]:
        nonlocal calls
        assert left.unit is METER and right.unit is METER
        calls += 1
        if calls == 1:
            data[2] = Quantity(Fraction(5, 2), METER)
        # Quantity arithmetic is checked and returns Result; reduce preserves
        # Result as data, so the callback must explicitly unwrap its sum.
        return (left + right).unwrap()

    capacity = source.reduce(combine).unwrap()
    assert capacity == Quantity(Fraction(4), METER) and calls == 2
    # 单位与精度转换集中在注册边界，不把泛型归约变成 float 求和。 / Centralize unit/precision conversion at registration, never float-coerce the generic fold.
    bound = Rational.from_value(capacity.value).unwrap().to_float().unwrap()
    profit = Rational.from_value(Fraction(3, 2)).unwrap().to_float().unwrap()
    model = MetaModelFloat64.create("public-live-reduction-MILP").unwrap()
    try:
        variable = model.add_variables(
            [VariableSpec(name="units", kind="integer", lower=0)]
        ).unwrap()[0]
        assert model.add_constraints(
            [
                ConstraintSpec(
                    name="length", terms=[(variable, 1)], relation="<=", rhs=bound
                )
            ]
        ).is_ok()
        assert model.set_objective(terms=[(variable, profit)], sense="maximize").is_ok()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL"
        assert report.values == pytest.approx((4,))
        assert report.objective == pytest.approx(6)
    finally:
        assert model.close().is_ok()


def test_public_cartesian_configs_feed_exact_unit_aware_real_milp(solver: str) -> None:
    left = [Quantity(Fraction(value, 2), METER) for value in (1, 2, 3)]
    right = [Quantity(Fraction(value, 2), METER) for value in (1, 2, 4)]
    patterns = cross(iter(left), iter(right)).unwrap()
    assert len(patterns) == 9
    assert all(a.unit is METER and b.unit is METER for a, b in patterns)
    lengths = [
        Rational.from_value(a.value + b.value).unwrap().to_float().unwrap()
        for a, b in patterns
    ]
    profits = [
        Rational.from_value(3 * a.value + 5 * b.value).unwrap().to_float().unwrap()
        for a, b in patterns
    ]
    model = MetaModelFloat64.create("cartesian-unit-aware-configuration-MILP").unwrap()
    try:
        variables = model.add_variables(
            [
                VariableSpec(name=f"configuration-{index}", kind="binary")
                for index in range(len(patterns))
            ]
        ).unwrap()
        model.add_constraints(
            [
                ConstraintSpec(
                    name="choose-one",
                    terms=[(variable, 1) for variable in variables],
                    relation="==",
                    rhs=1,
                ),
                ConstraintSpec(
                    name="length-m",
                    terms=list(zip(variables, lengths, strict=True)),
                    relation="<=",
                    rhs=2.5,
                ),
            ]
        ).unwrap()
        model.set_objective(
            terms=list(zip(variables, profits, strict=True)), sense="maximize"
        ).unwrap()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL"
        assert report.objective == pytest.approx(23 / 2)
        selected = [
            patterns[index] for index, value in enumerate(report.values) if value > 0.5
        ]
        assert len(selected) == 1
        assert selected[0][0] is left[0] and selected[0][1] is right[2]
    finally:
        model.close().unwrap()


@pytest.mark.parametrize("order", [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR])
def test_public_checked_shared_access_registers_real_solver_coefficients(
    solver: str, order: StorageOrder
) -> None:
    logical = np.array(
        [[Fraction(v) for v in row] for row in [[1, 2, 8], [1, 0, 3]]], dtype=object
    )
    data = logical.ravel(order="F" if order is StorageOrder.COLUMN_MAJOR else "C")
    shape = Shape2(2, 3, order)
    source = PublicMutableArray(shape, data)
    alias = PublicArray(shape, data)
    source.set_at(indices=(1, 2), value=Fraction(4)).unwrap()
    assert source.set_at(indices=(0, 3), value=Fraction(99)).is_failed()
    assert source.at(indices=(1, 2)).unwrap() == Fraction(4)
    assert alias.at(indices=(1, 2)).unwrap() == Fraction(4)
    model = MetaModelFloat64.create("public-checked-shared-access-LP").unwrap()
    try:
        variables = model.add_variables(
            [VariableSpec(name="x", lower=0), VariableSpec(name="y", lower=0)]
        ).unwrap()
        model.add_constraints(
            [
                ConstraintSpec(
                    name=f"row-{row}",
                    terms=[
                        (
                            variable,
                            Rational.from_value(alias.at(indices=(row, col)).unwrap())
                            .unwrap()
                            .to_float()
                            .unwrap(),
                        )
                        for col, variable in enumerate(variables)
                    ],
                    relation="<=",
                    rhs=Rational.from_value(alias.at(indices=(row, 2)).unwrap())
                    .unwrap()
                    .to_float()
                    .unwrap(),
                )
                for row in range(2)
            ]
        ).unwrap()
        model.set_objective(
            terms=[(variables[0], 0.5), (variables[1], 0.75)], sense="maximize"
        ).unwrap()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL"
        assert report.values == pytest.approx((4, 2))
        assert report.objective == pytest.approx(7 / 2)
    finally:
        model.close().unwrap()


@pytest.mark.parametrize("order", [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR])
def test_public_batch_checked_reads_feed_real_solver_without_scalar_ffi(
    solver: str, order: StorageOrder
) -> None:
    logical = np.array(
        [[Fraction(value) for value in row] for row in [[1, 2, 8], [1, 0, 3]]],
        dtype=object,
    )
    data = logical.ravel(order="F" if order is StorageOrder.COLUMN_MAJOR else "C")
    source = PublicMutableArray(Shape2(2, 3, order), data)
    source.set_at(indices=(1, 2), value=Fraction(4)).unwrap()
    coordinates = [(row, col) for row in range(2) for col in range(3)]
    values = source.at_many(indices=coordinates).unwrap()
    assert source.at_many(indices=coordinates + [(0, 3)]).is_failed()
    exact = RationalArray.create(
        [value.as_integer_ratio() for value in values]
    ).unwrap()
    coefficients = [exact.at(index).unwrap().to_float().unwrap() for index in range(6)]
    model = MetaModelFloat64.create("public-batch-checked-LP").unwrap()
    try:
        variables = model.add_variables(
            [VariableSpec(name="x", lower=0), VariableSpec(name="y", lower=0)]
        ).unwrap()
        model.add_constraints(
            [
                ConstraintSpec(
                    name=f"row-{row}",
                    terms=[
                        (variable, coefficients[row * 3 + col])
                        for col, variable in enumerate(variables)
                    ],
                    relation="<=",
                    rhs=coefficients[row * 3 + 2],
                )
                for row in range(2)
            ]
        ).unwrap()
        model.set_objective(
            terms=[(variables[0], 0.5), (variables[1], 0.75)], sense="maximize"
        ).unwrap()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL"
        assert report.values == pytest.approx((4, 2))
        assert report.objective == pytest.approx(7 / 2)
    finally:
        model.close().unwrap()


@pytest.mark.parametrize("storage", [PublicArray, PublicMutableArray])
@pytest.mark.parametrize("order", [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR])
def test_public_shared_iteration_live_snapshot_feeds_real_solver(
    solver: str,
    storage: type[PublicArray[Fraction, Shape2] | PublicMutableArray[Fraction, Shape2]],
    order: StorageOrder,
) -> None:
    logical = np.array(
        [[Fraction(v) for v in row] for row in [[1, 2, 8], [1, 0, 3]]], dtype=object
    )
    data = logical.ravel(order="F" if order is StorageOrder.COLUMN_MAJOR else "C")
    shape = Shape2(2, 3, order)
    source = storage(shape, data)
    cursor = iter(source)
    first = [next(cursor) for _ in range(3)]
    assert isinstance(cursor.gi_yieldfrom, _native.SharedArrayIterator)
    data[-1] = Fraction(4)
    from ospf_python._binding.multiarray import MultiArray

    imported = MultiArray.create(
        values=first + list(cursor), shape=shape, access_order=order
    ).unwrap()
    exact = imported.map(Rational.from_value).unwrap()
    model = MetaModelFloat64.create("public-shared-live-iteration-LP").unwrap()
    try:
        variables = model.add_variables(
            [VariableSpec(name="x", lower=0), VariableSpec(name="y", lower=0)]
        ).unwrap()
        model.add_constraints(
            [
                ConstraintSpec(
                    name=f"row-{row}",
                    terms=[
                        (variable, exact.at((row, col)).unwrap().to_float().unwrap())
                        for col, variable in enumerate(variables)
                    ],
                    relation="<=",
                    rhs=exact.at((row, 2)).unwrap().to_float().unwrap(),
                )
                for row in range(2)
            ]
        ).unwrap()
        model.set_objective(
            terms=[(variables[0], 0.5), (variables[1], 0.75)], sense="maximize"
        ).unwrap()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL"
        assert report.values == pytest.approx((4, 2))
        assert report.objective == pytest.approx(7 / 2)
    finally:
        cursor.close()
        model.close().unwrap()


@pytest.mark.parametrize("order", [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR])
def test_legacy_offset_view_import_registers_only_effective_fraction_region(
    solver: str, order: StorageOrder
) -> None:
    logical = np.array(
        [
            [Fraction(v) for v in row]
            for row in [[99, 99, 99, 99], [99, 1, 2, 8], [99, 1, 0, 3]]
        ],
        dtype=object,
    )
    data = logical.ravel(order="F" if order is StorageOrder.COLUMN_MAJOR else "C")
    old = PublicView(PublicArray(Shape2(3, 4, order), data), offsets=(1, 1))
    imported = MultiArrayView.from_legacy_state(payload=vars(old), copy=True).unwrap()
    assert imported.shape.dims == (2, 3)
    data[:] = Fraction(99)
    exact = imported.map(Rational.from_value).unwrap()
    assert exact.shape.dims == (2, 3)
    model = MetaModelFloat64.create("legacy-view-extent-LP").unwrap()
    try:
        variables = model.add_variables(
            [VariableSpec(name="x", lower=0), VariableSpec(name="y", lower=0)]
        ).unwrap()
        model.add_constraints(
            [
                ConstraintSpec(
                    name=f"row-{row}",
                    terms=[
                        (variable, exact.at((row, col)).unwrap().to_float().unwrap())
                        for col, variable in enumerate(variables)
                    ],
                    relation="<=",
                    rhs=exact.at((row, 2)).unwrap().to_float().unwrap(),
                )
                for row in range(2)
            ]
        ).unwrap()
        model.set_objective(
            terms=[(variables[0], 0.5), (variables[1], 0.75)], sense="maximize"
        ).unwrap()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL"
        assert report.values == pytest.approx((3, 2.5))
        assert report.objective == pytest.approx(27 / 8)
    finally:
        model.close().unwrap()


@pytest.mark.parametrize("order", [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR])
def test_live_fraction_rows_observe_later_writes_before_real_solver_registration(
    solver: str, order: StorageOrder
) -> None:
    source = MutableMultiArray.from_list(
        data=[[Fraction(value) for value in row] for row in [[1, 2, 8], [1, 0, 3]]],
        shape=Shape2(2, 3, order),
    ).unwrap()
    cursor = source.iter_live(access_order=StorageOrder.ROW_MAJOR).unwrap()
    first = [next(cursor) for _ in range(3)]
    source.set(indices=(1, 2), value=Fraction(4)).unwrap()
    second = []
    for _ in range(3):
        present, value = cursor.advance().unwrap()
        assert present
        second.append(value)
    assert cursor.advance().unwrap() == (False, None)
    assert first == [Fraction(1), Fraction(2), Fraction(8)]
    assert second == [Fraction(1), Fraction(0), Fraction(4)]
    model = MetaModelFloat64.create("live-rows-LP").unwrap()
    try:
        variables = model.add_variables(
            [VariableSpec(name="x", lower=0), VariableSpec(name="y", lower=0)]
        ).unwrap()
        for index, row in enumerate((first, second)):
            exact = [Rational.from_value(value).unwrap() for value in row]
            model.add_constraints(
                [
                    ConstraintSpec(
                        name=f"row-{index}",
                        terms=[
                            (variable, exact[col].to_float().unwrap())
                            for col, variable in enumerate(variables)
                        ],
                        relation="<=",
                        rhs=exact[2].to_float().unwrap(),
                    )
                ]
            ).unwrap()
        model.set_objective(
            terms=[(variables[0], 0.5), (variables[1], 0.75)], sense="maximize"
        ).unwrap()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL"
        assert report.values == pytest.approx((4, 2))
        assert report.objective == pytest.approx(7 / 2)
    finally:
        cursor.close()
        model.close().unwrap()


@pytest.mark.parametrize("order", [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR])
def test_checked_comparison_snapshots_feed_exact_rows_to_real_solver(
    solver: str, order: StorageOrder
) -> None:
    source = MutableMultiArray.from_list(
        data=[[Fraction(value) for value in row] for row in [[1, 2, 8], [1, 0, 3]]],
        shape=Shape2(2, 3, order),
    ).unwrap()
    other_order = (
        StorageOrder.COLUMN_MAJOR
        if order is StorageOrder.ROW_MAJOR
        else StorageOrder.ROW_MAJOR
    )
    frozen = source.to_immutable().unwrap().to_storage_order(other_order).unwrap()
    calls = []

    def comparator(left: Fraction, right: Fraction) -> object:
        calls.append((left, right))
        source.set(indices=(0, 0), value=Fraction(99)).unwrap()
        return Rational.from_value(left).flat_map(
            lambda a: Rational.from_value(right).flat_map(
                lambda b: a.compare(b).map(lambda comparison: comparison == 0)
            )
        )

    assert source.equals(frozen, comparator=comparator).unwrap() is True
    assert len(calls) == 6 and source.at((0, 0)).unwrap() == Fraction(99)
    exact = frozen.map(Rational.from_value).unwrap()
    model = MetaModelFloat64.create("checked-comparison-LP").unwrap()
    try:
        variables = model.add_variables(
            [VariableSpec(name="x", lower=0), VariableSpec(name="y", lower=0)]
        ).unwrap()
        model.add_constraints(
            [
                ConstraintSpec(
                    name=f"row-{row}",
                    terms=[
                        (variable, exact.at((row, col)).unwrap().to_float().unwrap())
                        for col, variable in enumerate(variables)
                    ],
                    relation="<=",
                    rhs=exact.at((row, 2)).unwrap().to_float().unwrap(),
                )
                for row in range(2)
            ]
        ).unwrap()
        model.set_objective(
            terms=[(variables[0], 0.5), (variables[1], 0.75)], sense="maximize"
        ).unwrap()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL"
        assert report.values == pytest.approx((3, 2.5))
        assert report.objective == pytest.approx(27 / 8)
    finally:
        assert model.close().is_ok()


@pytest.mark.parametrize("order", [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR])
def test_nested_fraction_rows_and_costs_use_checked_native_conversion_with_real_solver(
    solver: str, order: StorageOrder
) -> None:
    rows = [[Fraction(value) for value in row] for row in [[1, 2, 8], [1, 0, 3]]]
    imported = MutableMultiArray.from_list(
        data=rows, shape=Shape2(2, 3, order)
    ).unwrap()
    rows[0][0] = Fraction(99)
    source, matrix = pickle.loads(
        pickle.dumps((imported, imported.to_immutable().unwrap()))
    )
    source.set(indices=(0, 0), value=Fraction(101)).unwrap()
    exact = matrix.map(Rational.from_value).unwrap()
    costs = (
        MutableMultiArray.from_list(
            data=[Fraction(1, 2), Fraction(3, 4)], shape=DynShape((2,), order)
        )
        .unwrap()
        .map(Rational.from_value)
        .unwrap()
    )
    model = MetaModelFloat64.create("nested-reference-LP").unwrap()
    try:
        variables = model.add_variables(
            [VariableSpec(name="x", lower=0), VariableSpec(name="y", lower=0)]
        ).unwrap()
        model.add_constraints(
            [
                ConstraintSpec(
                    name=f"row-{row}",
                    terms=[
                        (variable, exact.at((row, col)).unwrap().to_float().unwrap())
                        for col, variable in enumerate(variables)
                    ],
                    relation="<=",
                    rhs=exact.at((row, 2)).unwrap().to_float().unwrap(),
                )
                for row in range(2)
            ]
        ).unwrap()
        model.set_objective(
            terms=[
                (variable, costs.at((index,)).unwrap().to_float().unwrap())
                for index, variable in enumerate(variables)
            ],
            sense="maximize",
        ).unwrap()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL"
        assert report.values == pytest.approx((3, 2.5))
        assert report.objective == pytest.approx(27 / 8)
        assert imported.at((0, 0)).unwrap() == Fraction(1)
    finally:
        assert model.close().is_ok()


@pytest.mark.parametrize("order", [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR])
def test_legacy_physical_state_import_registers_exact_rows_with_real_solver(
    solver: str, order: StorageOrder
) -> None:
    logical = np.array([[Fraction(v) for v in row] for row in [[1, 2, 8], [1, 0, 3]]])
    data = logical.ravel(order="F" if order is StorageOrder.COLUMN_MAJOR else "C")
    imported = MutableMultiArray.from_legacy_state(
        payload={"_shape": Shape2(2, 3, order), "_data": data}, copy=True
    ).unwrap()
    data[:] = Fraction(99)
    exact = imported.map(Rational.from_value).unwrap()
    model = MetaModelFloat64.create("legacy-state-import-LP").unwrap()
    try:
        variables = model.add_variables(
            [VariableSpec(name="x", lower=0), VariableSpec(name="y", lower=0)]
        ).unwrap()
        model.add_constraints(
            [
                ConstraintSpec(
                    name=f"row-{row}",
                    terms=[
                        (variable, exact.at((row, col)).unwrap().to_float().unwrap())
                        for col, variable in enumerate(variables)
                    ],
                    relation="<=",
                    rhs=exact.at((row, 2)).unwrap().to_float().unwrap(),
                )
                for row in range(2)
            ]
        ).unwrap()
        model.set_objective(
            terms=[(variables[0], 0.5), (variables[1], 0.75)], sense="maximize"
        ).unwrap()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL"
        assert report.values == pytest.approx((3, 2.5))
        assert report.objective == pytest.approx(27 / 8)
    finally:
        assert model.close().is_ok()


@pytest.mark.parametrize("order", [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR])
def test_restored_reference_graph_registers_checked_exact_coefficients_with_real_solver(
    solver: str, order: StorageOrder
) -> None:
    source = MutableMultiArray.full(
        shape=Shape2(3, 4, order), value=Fraction(99)
    ).unwrap()
    source.set_many(
        [
            ((row + 1, col), Fraction(value))
            for row, values in enumerate([[1, 2, 8], [1, 0, 3]])
            for col, value in enumerate(values)
        ]
    ).unwrap()
    restored_dto = MutableMultiArray.from_snapshot(
        source.to_snapshot().unwrap()
    ).unwrap()
    region = restored_dto.view(offsets=(1, 0), shape=Shape2(2, 3, order)).unwrap()
    restored, view = pickle.loads(pickle.dumps((restored_dto, region)))
    assert view._source is restored
    restored_dto.set(indices=(1, 0), value=Fraction(999)).unwrap()
    exact = view.map(Rational.from_value).unwrap().to_list().unwrap()
    model = MetaModelFloat64.create("restored-reference-graph-LP").unwrap()
    try:
        variables = model.add_variables(
            [VariableSpec(name="x", lower=0), VariableSpec(name="y", lower=0)]
        ).unwrap()
        model.add_constraints(
            [
                ConstraintSpec(
                    name=f"row-{row}",
                    terms=[
                        (variable, exact[row][col].to_float().unwrap())
                        for col, variable in enumerate(variables)
                    ],
                    relation="<=",
                    rhs=exact[row][2].to_float().unwrap(),
                )
                for row in range(2)
            ]
        ).unwrap()
        model.set_objective(
            terms=[(variables[0], 0.5), (variables[1], 0.75)], sense="maximize"
        ).unwrap()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL"
        assert report.values == pytest.approx((3, 2.5))
        assert report.objective == pytest.approx(27 / 8)
        assert view.at((0, 0)).unwrap() == Fraction(1)
    finally:
        assert model.close().is_ok()


def test_real_linear_program_and_full_report(solver: str) -> None:
    instance = MetaModelFloat64.create("LP").unwrap()
    x, y = instance.add_variables(
        [VariableSpec(name="x", lower=0, upper=2), VariableSpec(name="y", lower=0)]
    ).unwrap()
    assert instance.add_constraints(
        [ConstraintSpec(name="capacity", terms=[(x, 1), (y, 1)], relation="<=", rhs=4)]
    ).is_ok()
    assert instance.set_objective(terms=[(x, 3), (y, 2)], sense="maximize").is_ok()
    report = instance.solve(solver=solver).unwrap()
    assert report.model_identity == instance.model_identity
    assert report.problem_status == "FEASIBLE"
    assert report.termination_reason == "COMPLETED"
    assert report.solution_presence == "OPTIMAL"
    assert report.objective == pytest.approx(10)
    assert report.values == pytest.approx((2, 2))
    raw = json.loads(report.raw_json)
    assert raw["schemaVersion"] == "1.0"
    assert raw["proof"] is not None
    assert raw["modelMapping"] is not None
    assert {
        "statistics",
        "diagnostics",
        "provenance",
        "fingerprints",
        "trace",
    } <= raw.keys()
    assert instance.close().is_ok()
    assert report.values == pytest.approx((2, 2))


@pytest.mark.parametrize("order", [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR])
def test_mutable_offset_view_snapshot_to_real_solver(
    solver: str, order: StorageOrder
) -> None:
    external = np.array(
        [
            [Fraction(value) for value in row]
            for row in [[99, 99, 99, 99], [99, 1, 2, 9], [99, 1, 0, 4]]
        ],
        dtype=object,
    )
    source = MutableMultiArray.from_numpy(
        values=external, copy=True, storage_order=order
    ).unwrap()
    view = source.view(offsets=(1, 1), shape=Shape2(2, 3, order)).unwrap()
    assert view.set_many([((0, 2), Fraction(8)), ((1, 2), Fraction(3))]).is_ok()
    snapshot = view.materialize().unwrap()
    assert source.set(indices=(1, 1), value=Fraction(100)).is_ok()
    assert snapshot.at((0, 0)).unwrap() is external[1, 1]
    assert external[1, 3] == Fraction(9)
    model = MetaModelFloat64.create("offset-view-LP").unwrap()
    try:
        variables = model.add_variables(
            [VariableSpec(name="x", lower=0), VariableSpec(name="y", lower=0)]
        ).unwrap()
        assert model.add_constraints(
            [
                ConstraintSpec(
                    name=f"row-{row}",
                    terms=[
                        (
                            variable,
                            Rational.from_value(snapshot.at((row, col)).unwrap())
                            .unwrap()
                            .to_float()
                            .unwrap(),
                        )
                        for col, variable in enumerate(variables)
                    ],
                    relation="<=",
                    rhs=Rational.from_value(snapshot.at((row, 2)).unwrap())
                    .unwrap()
                    .to_float()
                    .unwrap(),
                )
                for row in range(2)
            ]
        ).is_ok()
        assert model.set_objective(
            terms=[
                (variable, Rational.from_value(cost).unwrap().to_float().unwrap())
                for variable, cost in zip(
                    variables, [Fraction(1, 2), Fraction(3, 4)], strict=True
                )
            ],
            sense="maximize",
        ).is_ok()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL"
        assert report.values == pytest.approx((3, 2.5))
        assert report.objective == pytest.approx(27 / 8)
        assert snapshot.at((0, 0)).unwrap() == Fraction(1)
        assert source.at((1, 1)).unwrap() == Fraction(100)
    finally:
        assert model.close().is_ok()


@pytest.mark.parametrize("order", [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR])
def test_rust_filled_storage_folded_costs_and_nested_matrix_with_real_solver(
    solver: str, order: StorageOrder
) -> None:
    source = MutableMultiArray.full(
        shape=Shape2(3, 4, order), value=Rational.from_value(99).unwrap()
    ).unwrap()
    assert source.set_many(
        [
            ((row + 1, col), Rational.from_value(value).unwrap())
            for row, values in enumerate([[1, 2, 8], [1, 0, 3]])
            for col, value in enumerate(values)
        ]
    ).is_ok()
    region = source.view(offsets=(1, 0), shape=Shape2(2, 3, order)).unwrap()
    nested = region.to_list().unwrap()
    cost_source = MutableMultiArray.full(
        value=Rational.from_value(Fraction(1, 2)).unwrap(),
        shape=DynShape((2,), order),
    ).unwrap()
    cost_source.set(
        indices=(1,), value=Rational.from_value(Fraction(3, 4)).unwrap()
    ).unwrap()
    costs = cost_source.to_immutable().unwrap()
    cost_source.set(indices=(0,), value=Rational.from_value(9).unwrap()).unwrap()
    scale = costs.reduce(lambda left, right: left.add(right)).unwrap()
    assert scale.as_integer_ratio() == (5, 4)
    scaled = [
        cost.multiply(scale).unwrap().to_float().unwrap()
        for cost in costs.iter_snapshot().unwrap()
    ]
    source.set(indices=(1, 0), value=Rational.from_value(100).unwrap()).unwrap()
    model = MetaModelFloat64.create("folded-costs-nested-LP").unwrap()
    try:
        variables = model.add_variables(
            [VariableSpec(name="x", lower=0), VariableSpec(name="y", lower=0)]
        ).unwrap()
        assert model.add_constraints(
            [
                ConstraintSpec(
                    name=f"row-{row}",
                    terms=[
                        (variable, nested[row][col].to_float().unwrap())
                        for col, variable in enumerate(variables)
                    ],
                    relation="<=",
                    rhs=nested[row][2].to_float().unwrap(),
                )
                for row in range(2)
            ]
        ).is_ok()
        assert model.set_objective(
            terms=list(zip(variables, scaled, strict=True)), sense="maximize"
        ).is_ok()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL"
        assert report.values == pytest.approx((3, 2.5))
        assert report.objective == pytest.approx(135 / 32)
        assert nested[0][0].as_integer_ratio() == (1, 1)
    finally:
        assert model.close().is_ok()


@pytest.mark.parametrize("order", [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR])
def test_lazy_region_snapshot_registers_checked_values_with_real_solver(
    solver: str, order: StorageOrder
) -> None:
    source = MutableMultiArray.create(
        values=[
            Fraction(value) for value in [99, 99, 99, 99, 1, 2, 8, 99, 1, 0, 3, 99]
        ],
        shape=Shape2(3, 4, order),
    ).unwrap()
    region = source.view(offsets=(1, 0), shape=Shape2(2, 3, order)).unwrap()
    mapped = MappedMultiArrayView.create(
        source=region,
        callback=lambda value: Rational.from_value(value).flat_map(
            lambda exact: exact.to_float()
        ),
    ).unwrap()
    source.set(indices=(1, 2), value=Fraction(10)).unwrap()
    assert mapped.at((0, 2)).unwrap() == 10
    source.set(indices=(1, 2), value=Fraction(8)).unwrap()
    snapshot = mapped.materialize().unwrap()
    source.set(indices=(1, 0), value=Fraction(100)).unwrap()
    assert mapped.at((0, 0)).unwrap() == 100
    model = MetaModelFloat64.create("lazy-region-LP").unwrap()
    try:
        variables = model.add_variables(
            [VariableSpec(name="x", lower=0), VariableSpec(name="y", lower=0)]
        ).unwrap()
        assert model.add_constraints(
            [
                ConstraintSpec(
                    name=f"row-{row}",
                    terms=[
                        (variable, snapshot.at((row, col)).unwrap())
                        for col, variable in enumerate(variables)
                    ],
                    relation="<=",
                    rhs=snapshot.at((row, 2)).unwrap(),
                )
                for row in range(2)
            ]
        ).is_ok()
        assert model.set_objective(
            terms=[(variables[0], 0.5), (variables[1], 0.75)], sense="maximize"
        ).is_ok()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL"
        assert report.values == pytest.approx((3, 2.5))
        assert report.objective == pytest.approx(27 / 8)
        assert snapshot.at((0, 0)).unwrap() == 1
    finally:
        assert model.close().is_ok()


@pytest.mark.parametrize("order", [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR])
def test_transposed_mapped_snapshot_registers_with_real_solver(
    solver: str, order: StorageOrder
) -> None:
    source = MutableMultiArray.create(
        values=[Fraction(value) for value in [1, 1, 2, 0, 8, 3]],
        shape=Shape2(3, 2, order),
    ).unwrap()
    rows = source.transpose().unwrap()

    def convert(value: Fraction) -> object:
        return Rational.from_value(value).flat_map(lambda exact: exact.to_float())

    converted = rows.map(convert).unwrap()
    assert source.set(indices=(0, 0), value=Fraction(99)).is_ok()
    flattened = converted.flat_map(
        lambda value: (value,), shape=DynShape((6,))
    ).unwrap()
    assert flattened.flatten().unwrap() == [1, 2, 8, 1, 0, 3]
    model = MetaModelFloat64.create("mapped-transpose-LP").unwrap()
    try:
        variables = model.add_variables(
            [VariableSpec(name="x", lower=0), VariableSpec(name="y", lower=0)]
        ).unwrap()
        assert model.add_constraints(
            [
                ConstraintSpec(
                    name=f"row-{row}",
                    terms=[
                        (variable, converted.at((row, col)).unwrap())
                        for col, variable in enumerate(variables)
                    ],
                    relation="<=",
                    rhs=flattened.at((row * 3 + 2,)).unwrap(),
                )
                for row in range(2)
            ]
        ).is_ok()
        assert model.set_objective(
            terms=[(variables[0], 0.5), (variables[1], 0.75)], sense="maximize"
        ).is_ok()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL"
        assert report.values == pytest.approx((3, 2.5))
        assert report.objective == pytest.approx(27 / 8)
    finally:
        assert model.close().is_ok()


@pytest.mark.parametrize("order", [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR])
def test_exact_matrix_to_real_solver_uses_explicit_checked_conversion(
    solver: str, order: StorageOrder
) -> None:
    coefficients = RationalArray.create([(1, 1), (2, 1), (1, 1), (0, 1)]).unwrap()
    shape = Shape2(d0=2, d1=2, storage_order=order)
    matrix = RationalMultiArray.create(values=coefficients, shape=shape).unwrap()
    costs = RationalArray.create([(1, 2), (3, 4)]).unwrap()
    model = MetaModelFloat64.create("exact-matrix-LP").unwrap()
    try:
        variables = model.add_variables(
            [VariableSpec(name="x", lower=0), VariableSpec(name="y", lower=0)]
        ).unwrap()
        assert model.add_constraints(
            [
                ConstraintSpec(
                    name=f"row-{row}",
                    terms=[
                        (variable, matrix.at((row, col)).unwrap().to_float().unwrap())
                        for col, variable in enumerate(variables)
                    ],
                    relation="<=",
                    rhs=rhs,
                )
                for row, rhs in enumerate([8, 3])
            ]
        ).is_ok()
        assert model.set_objective(
            terms=[
                (variable, costs.at(col).unwrap().to_float().unwrap())
                for col, variable in enumerate(variables)
            ],
            sense="maximize",
        ).is_ok()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL"
        assert report.objective == pytest.approx(27 / 8)
        assert report.values == pytest.approx((3, 2.5))
        assert (
            matrix.flatten().unwrap().as_integer_ratios()
            == coefficients.as_integer_ratios()
        )
        assert costs.as_integer_ratios() == [(1, 2), (3, 4)]
    finally:
        assert model.close().is_ok()


def test_real_mixed_integer_program(solver: str) -> None:
    instance = MetaModelFloat64.create("MILP").unwrap()
    x, b = instance.add_variables(
        [
            VariableSpec(name="x", kind="integer", lower=0, upper=3),
            VariableSpec(name="b", kind="binary"),
        ]
    ).unwrap()
    assert instance.add_constraints(
        [
            ConstraintSpec(
                name="integer_limit", terms=[(x, 1)], relation="<=", rhs=2.5
            ),
            ConstraintSpec(name="binary_limit", terms=[(b, 1)], relation="<=", rhs=0.5),
        ]
    ).is_ok()
    assert instance.set_objective(terms=[(x, 1), (b, 0.1)], sense="maximize").is_ok()
    report = instance.solve(solver=solver).unwrap()
    assert report.problem_status == "FEASIBLE"
    assert report.solution_presence == "OPTIMAL"
    assert report.objective == pytest.approx(2)
    assert report.values == pytest.approx((2, 0))


def test_infeasible_is_a_normal_report_not_a_failure(solver: str) -> None:
    instance = MetaModelFloat64.create("infeasible").unwrap()
    x = instance.add_variables([VariableSpec(name="x", lower=0, upper=1)]).unwrap()[0]
    assert instance.add_constraints(
        [ConstraintSpec(name="impossible", terms=[(x, 1)], relation=">=", rhs=2)]
    ).is_ok()
    assert instance.set_objective(terms=[(x, 1)], sense="minimize").is_ok()
    report = instance.solve(solver=solver).unwrap()
    assert report.problem_status == "INFEASIBLE"
    assert report.solution_presence == "NONE"
    assert report.objective is None
    assert report.values == ()


def test_unbounded_is_a_normal_report_not_a_failure(solver: str) -> None:
    instance = MetaModelFloat64.create("unbounded").unwrap()
    x = instance.add_variables([VariableSpec(name="x", lower=0)]).unwrap()[0]
    assert instance.set_objective(terms=[(x, 1)], sense="maximize").is_ok()
    report = instance.solve(solver=solver).unwrap()
    assert report.problem_status == "UNBOUNDED"
    assert report.solution_presence == "NONE"
    assert report.objective is None


def test_failed_mutation_preserves_objective_and_repeated_solve_refreshes(
    solver: str,
) -> None:
    instance = MetaModelFloat64.create("repeated").unwrap()
    x = instance.add_variables([VariableSpec(name="x", lower=0, upper=5)]).unwrap()[0]
    assert instance.set_objective(terms=[(x, 1)], sense="maximize").is_ok()
    assert instance.solve(solver=solver).unwrap().objective == pytest.approx(5)
    assert instance.set_objective(terms=[(x, 10)], sense="unknown").is_failed()
    assert instance.set_objective(
        terms=[(x, 10)], sense="maximize", constant=5
    ).is_failed()
    assert instance.solve(solver=solver).unwrap().objective == pytest.approx(5)
    assert instance.add_constraints(
        [ConstraintSpec(name="tightened", terms=[(x, 1)], relation="<=", rhs=3)]
    ).is_ok()
    assert instance.solve(solver=solver).unwrap().objective == pytest.approx(3)
