"""普通 offset 物化的真实求解消费者 / Real solver consumers of plain offset materialization."""

from __future__ import annotations

from fractions import Fraction
from typing import Any

import numpy as np
import pytest

from ospf_python import _native
from ospf_python._binding.model import ConstraintSpec, MetaModelFloat64, VariableSpec
from ospf_python._binding.numeric import Rational
from ospf_python.multiarray import (
    MultiArray,
    MultiArrayView,
    MutableMultiArray,
    Shape2,
    StorageOrder,
)
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.unit.length import METER


@pytest.mark.parametrize("solver", ["scip", "gurobi10", "gurobi11", "gurobi12"])
@pytest.mark.parametrize("storage", [MultiArray, MutableMultiArray])
@pytest.mark.parametrize("order", list(StorageOrder))
@pytest.mark.parametrize("unit_aware", [False, True])
@pytest.mark.parametrize("kind", ["continuous", "binary"])
def test_plain_offset_materialization_registers_exact_configuration_model(
    *,
    solver: str,
    storage: type[Any],
    order: StorageOrder,
    unit_aware: bool,
    kind: str,
) -> None:
    if solver not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {solver}")
    logical = np.empty((4, 5), dtype=object)
    logical.fill(Fraction(99))
    for row in range(2):
        for column in range(3):
            value = Fraction(row * 3 + column + 1, 2)
            logical[row + 2, column + 2] = (
                Quantity(value, METER) if unit_aware else value
            )
    data = logical.ravel(order="F" if order is StorageOrder.COLUMN_MAJOR else "C")
    source = storage(Shape2(4, 5, order), data)
    view = MultiArrayView(source, offsets=(2, 2))
    materialized = view.materialize().unwrap()
    assert materialized.shape.dims == (2, 3)
    assert materialized.shape.storage_order is order
    assert not np.shares_memory(materialized._data, data)
    leaves = [materialized.get(row, column) for row in range(2) for column in range(3)]
    exact = []
    for index, leaf in enumerate(leaves):
        row, column = divmod(index, 3)
        assert leaf is source.get(row + 2, column + 2)
        if unit_aware:
            assert leaf.unit is METER
            exact.append(leaf.value)
        else:
            exact.append(leaf)
    assert exact == [Fraction(index + 1, 2) for index in range(6)]
    # 仅在注册边界转换精度/单位。 / Convert precision/units only at registration.
    lengths = [
        Rational.from_value(value).unwrap().to_float().unwrap() for value in exact
    ]
    profits = [
        Rational.from_value(value * Fraction(3, 2)).unwrap().to_float().unwrap()
        for value in exact
    ]
    bound = Rational.from_value(Fraction(7, 4)).unwrap().to_float().unwrap()
    model = MetaModelFloat64.create("plain-offset-configurations").unwrap()
    try:
        variables = model.add_variables(
            [
                VariableSpec(name=f"config-{index}", kind=kind, lower=0, upper=1)
                for index in range(6)
            ]
        ).unwrap()
        assert model.add_constraints(
            [
                ConstraintSpec(
                    name="capacity",
                    terms=list(zip(variables, lengths, strict=True)),
                    relation="<=",
                    rhs=bound,
                ),
                ConstraintSpec(
                    name="one",
                    terms=[(variable, 1) for variable in variables],
                    relation="<=",
                    rhs=1,
                ),
            ]
        ).is_ok()
        assert model.set_objective(
            terms=list(zip(variables, profits, strict=True)), sense="maximize"
        ).is_ok()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL"
        expected = Fraction(21, 8) if kind == "continuous" else Fraction(9, 4)
        assert report.objective == pytest.approx(expected)
        assert sum(report.values) <= 1 + 1e-6
        assert (
            sum(
                value * length
                for value, length in zip(report.values, lengths, strict=True)
            )
            <= bound + 1e-6
        )
    finally:
        assert model.close().is_ok()
