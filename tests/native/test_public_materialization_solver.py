"""转置/惰性物化的真实单位化配置求解 / Real unit-aware configuration solve after transpose/lazy materialization."""

from __future__ import annotations

from fractions import Fraction
from typing import Any

import numpy as np
import pytest

from ospf_python import _native
from ospf_python._binding.model import ConstraintSpec, MetaModelFloat64, VariableSpec
from ospf_python._binding.numeric import Rational
from ospf_python.multiarray import (
    DynShape,
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
def test_transpose_live_materialization_feeds_real_configuration_milp(
    *, solver: str, storage: type[Any], order: StorageOrder
) -> None:
    if solver not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {solver}")
    data = np.empty(6, dtype=object)
    for index in range(6):
        data[index] = Quantity(Fraction(index + 1, 2), METER)
    source = storage(Shape2(2, 3, order), data)
    flattened = source.flatten().unwrap()
    reshaped = (
        storage(source.shape, flattened._data).reshape(DynShape((2, 3), order)).unwrap()
    )
    transposed = storage(reshaped.shape, reshaped._data).transpose().unwrap()
    calls = 0

    def double(value: Quantity[Fraction]) -> Quantity[Fraction]:
        nonlocal calls
        calls += 1
        transposed._data[1] = Quantity(Fraction(7, 2), METER)
        output = (value * 2).unwrap()
        assert isinstance(output, Quantity)
        return output

    materialized = MultiArrayView(transposed).map(double).materialize().unwrap()
    assert calls == 6 and materialized.shape is transposed.shape
    assert [leaf.value for leaf in materialized._data] == [1, 7, 3, 4, 5, 6]
    for row in range(3):
        for column in range(2):
            assert (
                materialized.get(row, column)
                == (transposed.get(row, column) * 2).unwrap()
            )
    leaves = materialized._data.tolist()
    assert all(leaf.unit is METER for leaf in leaves)
    # 精度和单位转换只在注册边界发生。 / Convert precision and units only at registration.
    lengths = [
        Rational.from_value(leaf.value).unwrap().to_float().unwrap() for leaf in leaves
    ]
    profits = [
        Rational.from_value(leaf.value * Fraction(3, 2)).unwrap().to_float().unwrap()
        for leaf in leaves
    ]
    bound = Rational.from_value(Fraction(7, 2)).unwrap().to_float().unwrap()
    model = MetaModelFloat64.create("public-live-materialized-configurations").unwrap()
    try:
        variables = model.add_variables(
            [VariableSpec(name=f"config-{index}", kind="binary") for index in range(6)]
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
                    terms=[(var, 1) for var in variables],
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
        assert report.values == pytest.approx((0, 0, 1, 0, 0, 0))
        assert report.objective == pytest.approx(Fraction(9, 2))
    finally:
        assert model.close().is_ok()
