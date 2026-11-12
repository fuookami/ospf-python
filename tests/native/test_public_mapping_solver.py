"""公共精确映射的真实求解消费者 / Real-solver consumer of public exact mapping."""

from __future__ import annotations

from fractions import Fraction
from typing import Any

import numpy as np
import pytest

from ospf_python import _native
from ospf_python._binding.model import ConstraintSpec, MetaModelFloat64, VariableSpec
from ospf_python._binding.numeric import Rational
from ospf_python.multiarray import MultiArray, MutableMultiArray, Shape2, StorageOrder
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.unit.length import METER


@pytest.mark.parametrize("solver", ["scip", "gurobi10", "gurobi11", "gurobi12"])
@pytest.mark.parametrize("storage", [MultiArray, MutableMultiArray])
@pytest.mark.parametrize("order", list(StorageOrder))
@pytest.mark.parametrize("path", ["map_then_flat_map", "flat_map"])
def test_live_map_then_iterable_flat_map_feed_real_configuration_milp(
    *, solver: str, storage: type[Any], order: StorageOrder, path: str
) -> None:
    if solver not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {solver}")
    data = np.empty(2, dtype=object)
    data[0] = Quantity(Fraction(1, 2), METER)
    data[1] = Quantity(Fraction(99), METER)
    source = storage(Shape2(1, 2, order), data)
    seen: list[Fraction] = []

    def double(value: Quantity[Fraction]) -> Quantity[Fraction]:
        seen.append(value.value)
        data[1] = Quantity(Fraction(3, 2), METER)
        output = (value * 2).unwrap()
        assert isinstance(output, Quantity)
        return output

    def expand(value: Quantity[Fraction]) -> tuple[Quantity[Fraction], Quantity[Fraction]]:
        doubled = double(value)
        return doubled, (doubled * 2).unwrap()

    if path == "map_then_flat_map":
        mapped = source.map(double).unwrap()
        expanded = mapped.flat_map(
            lambda value: iter((value, (value * 2).unwrap()))
        ).unwrap()
    else:
        expanded = source.flat_map(expand).unwrap()
    assert seen == [Fraction(1, 2), Fraction(3, 2)]
    candidates = expanded._data.tolist()
    assert [leaf.value for leaf in candidates] == [1, 2, 3, 6]
    assert all(leaf.unit is METER for leaf in candidates)
    assert expanded.shape is source.shape
    # 集中精度/单位转换，不在泛型映射中降为 Float64。 / Centralize precision/unit conversion, never float-coerce generic mapping.
    lengths = [
        Rational.from_value(leaf.value).unwrap().to_float().unwrap()
        for leaf in candidates
    ]
    profits = [
        Rational.from_value(leaf.value * Fraction(3, 2)).unwrap().to_float().unwrap()
        for leaf in candidates
    ]
    bound = Rational.from_value(Fraction(7, 2)).unwrap().to_float().unwrap()
    model = MetaModelFloat64.create("public-live-mapping-configurations-MILP").unwrap()
    try:
        variables = model.add_variables(
            [
                VariableSpec(name=f"configuration-{index}", kind="binary")
                for index in range(4)
            ]
        ).unwrap()
        assert model.add_constraints(
            [
                ConstraintSpec(
                    name="length",
                    terms=list(zip(variables, lengths, strict=True)),
                    relation="<=",
                    rhs=bound,
                ),
                ConstraintSpec(
                    name="choose-one",
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
        assert report.values == pytest.approx((0, 0, 1, 0))
        assert report.objective == pytest.approx(Fraction(9, 2))
    finally:
        assert model.close().is_ok()
