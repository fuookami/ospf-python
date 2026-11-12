"""公共精确有理数计算接真实 Rust 后端 / Public exact rational arithmetic feeds real Rust backends."""

from __future__ import annotations

import pickle

import pytest

from ospf_python import _native
from ospf_python._binding.model import ConstraintSpec, MetaModelFloat64, VariableSpec
from ospf_python._binding.numeric import Rational as StrictRational
from ospf_python.math.algebra.number.rational import Rational


@pytest.mark.parametrize("solver", ["scip", "gurobi10", "gurobi11", "gurobi12"])
def test_public_rational_arithmetic_and_pickle_feed_real_lp(solver: str) -> None:
    if solver not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {solver}")
    rhs = [Rational(2, 3) / Rational(1, 12), Rational(5, 2) + Rational(1, 2)]
    negative_cost = -Rational(3, 4)
    costs = [Rational(1, 2), -negative_cost]
    rhs, costs = pickle.loads(pickle.dumps((rhs, costs)))
    assert rhs == [Rational(8), Rational(3)]

    def checked_float(value: Rational) -> float:
        return (
            StrictRational.create(
                numerator=value.numerator, denominator=value.denominator
            )
            .unwrap()
            .to_float()
            .unwrap()
        )

    model = MetaModelFloat64.create("public-rational-computation-LP").unwrap()
    try:
        x, y = model.add_variables(
            [VariableSpec(name="x", lower=0), VariableSpec(name="y", lower=0)]
        ).unwrap()
        model.add_constraints(
            [
                ConstraintSpec(
                    name="capacity",
                    terms=[(x, 1), (y, 2)],
                    relation="<=",
                    rhs=checked_float(rhs[0]),
                ),
                ConstraintSpec(
                    name="bound",
                    terms=[(x, 1)],
                    relation="<=",
                    rhs=checked_float(rhs[1]),
                ),
            ]
        ).unwrap()
        model.set_objective(
            terms=[(x, checked_float(costs[0])), (y, checked_float(costs[1]))],
            sense="maximize",
        ).unwrap()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL"
        assert report.values == pytest.approx((3, 2.5))
        assert report.objective == pytest.approx(27 / 8)
        exact_x, exact_y = Rational(3), Rational(5, 2)
        assert exact_x + Rational(2) * exact_y <= rhs[0]
        assert costs[0] * exact_x + costs[1] * exact_y == Rational(27, 8)
    finally:
        model.close().unwrap()
