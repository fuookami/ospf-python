"""浮点门面计算接真实 Rust MILP。 / Public floating arithmetic feeds real Rust MILP."""

from __future__ import annotations

import pickle

import pytest

from ospf_python import _native
from ospf_python._binding.model import ConstraintSpec, MetaModelFloat64, VariableSpec
from ospf_python.math.algebra.number.floating import Floating
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.unit.length import METER


@pytest.mark.parametrize("solver", ("scip", "gurobi10", "gurobi11", "gurobi12"))
@pytest.mark.parametrize("integral_payload", (False, True))
def test_floating_quantities_pickle_and_result_recheck_feed_real_milp(
    *, solver: str, integral_payload: bool
) -> None:
    if solver not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {solver}")

    def number(value: int) -> Floating:
        return Floating(value if integral_payload else float(value))

    count = number(7) + number(3)
    weight = (
        Quantity(value=number(20), unit=METER) - Quantity(value=number(6), unit=METER)
    ).unwrap()
    negative_two = -number(2)
    costs = [number(6) / number(2), -negative_two]
    count, weight, costs = pickle.loads(pickle.dumps((count, weight, costs)))
    model = MetaModelFloat64.create("public-floating-computation-MILP").unwrap()
    try:
        x, y = model.add_variables(
            [
                VariableSpec(name="x", kind="integer", lower=0),
                VariableSpec(name="y", kind="integer", lower=0),
            ]
        ).unwrap()
        model.add_constraints(
            [
                ConstraintSpec(
                    name="count",
                    terms=[(x, 1), (y, 1)],
                    relation="<=",
                    rhs=count.value,
                ),
                ConstraintSpec(
                    name="weight",
                    terms=[(x, 2), (y, 1)],
                    relation="<=",
                    rhs=weight.value.value,
                ),
            ]
        ).unwrap()
        model.set_objective(
            terms=[(x, costs[0].value), (y, costs[1].value)], sense="maximize"
        ).unwrap()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL"
        assert report.values == pytest.approx((4, 6))
        assert report.objective == pytest.approx(24)
        result_x, result_y = (Floating(value) for value in report.values)
        assert result_x + result_y <= count
        assert number(2) * result_x + result_y <= weight.value
        assert (costs[0] * result_x + costs[1] * result_y).value == 24.0
    finally:
        model.close().unwrap()
