"""公开整数计算接真实 Rust MILP。 / Public integer arithmetic feeds real Rust MILP backends."""

from __future__ import annotations

import pickle
from typing import Any

import pytest

from ospf_python import _native
from ospf_python._binding.model import ConstraintSpec, MetaModelFloat64, VariableSpec
from ospf_python.math.algebra.number.integer import Integer
from ospf_python.math.algebra.number.numeric_integer import NumericInteger
from ospf_python.math.algebra.number.numeric_u_integer import NumericUInteger
from ospf_python.math.algebra.number.uinteger import UInteger


@pytest.mark.parametrize("solver", ("scip", "gurobi10", "gurobi11", "gurobi12"))
@pytest.mark.parametrize("cls", (Integer, UInteger, NumericInteger, NumericUInteger))
def test_public_integer_arithmetic_pickle_and_exact_recheck_feed_real_milp(
    *, solver: str, cls: Any
) -> None:
    if solver not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {solver}")

    def add(left: Any, right: Any) -> Any:
        return left.safe_add(right) if cls is NumericInteger else left + right

    def multiply(left: Any, right: Any) -> Any:
        return left.safe_mul(right) if cls is NumericInteger else left * right

    capacities = [add(cls(7), cls(3)), multiply(cls(2), cls(7))]
    costs = [add(cls(2), cls(1)), multiply(cls(2), cls(1))]
    capacities, costs = pickle.loads(pickle.dumps((capacities, costs)))
    model = MetaModelFloat64.create("public-integer-computation-MILP").unwrap()
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
                    rhs=capacities[0].value,
                ),
                ConstraintSpec(
                    name="weight",
                    terms=[(x, 2), (y, 1)],
                    relation="<=",
                    rhs=capacities[1].value,
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
        exact_x, exact_y = (cls(round(value)) for value in report.values)
        assert add(exact_x, exact_y).value <= capacities[0].value
        assert add(multiply(cls(2), exact_x), exact_y).value <= capacities[1].value
        objective = add(multiply(costs[0], exact_x), multiply(costs[1], exact_y))
        assert objective.value == 24
    finally:
        model.close().unwrap()
