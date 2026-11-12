"""公共逻辑嵌套导出接真实后端 / Public logical nested export feeds real backends."""

from __future__ import annotations

from fractions import Fraction
from typing import Any

import numpy as np
import pytest

from ospf_python import _native
from ospf_python._binding.model import ConstraintSpec, MetaModelFloat64, VariableSpec
from ospf_python._binding.numeric import Rational
from ospf_python.multiarray.multi_array import MultiArray, MutableMultiArray
from ospf_python.multiarray.shape import Shape2, StorageOrder
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.unit.length import METER


@pytest.mark.parametrize("solver", ["scip", "gurobi10", "gurobi11", "gurobi12"])
@pytest.mark.parametrize("cls", [MultiArray, MutableMultiArray])
@pytest.mark.parametrize("order", list(StorageOrder))
@pytest.mark.parametrize("domain", ["fraction", "quantity"])
def test_public_nested_coefficients_feed_real_lp(
    *, solver: str, cls: type[Any], order: StorageOrder, domain: str
) -> None:
    if solver not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {solver}")
    logical = [
        [Fraction(1), Fraction(2), Fraction(8)],
        [Fraction(1), Fraction(0), Fraction(3)],
    ]
    if domain == "quantity":
        values: Any = [[Quantity(value, METER) for value in row] for row in logical]
    else:
        values = logical
    data = np.array(values, dtype=object).ravel(
        order="F" if order is StorageOrder.COLUMN_MAJOR else "C"
    )
    source = cls(Shape2(2, 3, order), data)
    nested = source.to_list().unwrap()
    assert nested == values

    def checked_float(value: Any) -> float:
        if isinstance(value, Quantity):
            assert value.unit is METER
            value = value.value
        assert isinstance(value, Fraction)
        return (
            Rational.create(numerator=value.numerator, denominator=value.denominator)
            .unwrap()
            .to_float()
            .unwrap()
        )

    model = MetaModelFloat64.create("public-logical-nested-LP").unwrap()
    try:
        x, y = model.add_variables(
            [VariableSpec(name="x", lower=0), VariableSpec(name="y", lower=0)]
        ).unwrap()
        model.add_constraints(
            [
                ConstraintSpec(
                    name=f"row-{index}",
                    terms=[(x, checked_float(row[0])), (y, checked_float(row[1]))],
                    relation="<=",
                    rhs=checked_float(row[2]),
                )
                for index, row in enumerate(nested)
            ]
        ).unwrap()
        model.set_objective(terms=[(x, 0.5), (y, 0.75)], sense="maximize").unwrap()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL"
        assert report.values == pytest.approx((3, 2.5))
        assert report.objective == pytest.approx(27 / 8)
        assert source._data is data
    finally:
        model.close().unwrap()
