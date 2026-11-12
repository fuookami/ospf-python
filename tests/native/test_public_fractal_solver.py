"""公开分形 Result 驱动真实 Rust MILP。 / Public fractal Results drive real Rust MILPs."""

from __future__ import annotations

import pytest

from ospf_python import _native
from ospf_python._binding.model import ConstraintSpec, MetaModelFloat64, VariableSpec
from ospf_python.math.fractal.julia_set import JuliaSet
from ospf_python.math.fractal.mandelbrot_set import MandelbrotSet


@pytest.mark.parametrize("solver", ("scip", "gurobi10", "gurobi11", "gurobi12"))
def test_fractal_results_feed_real_milp_and_survive_recheck(*, solver: str) -> None:
    if solver not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {solver}")

    julia = JuliaSet(c_real=-0.7, c_imag=0.27015, max_iter=12)
    count_capacity = MandelbrotSet.iterate(complex(0.0, 0.0), 9).unwrap()
    weight_capacity = JuliaSet.iterate(
        complex(0.1, 0.1), complex(-0.7, 0.27015), 12
    ).unwrap()
    eligible = (
        MandelbrotSet(max_iter=12).contains(complex(-0.5, 0.0)).unwrap(),
        julia.contains(0.1, 0.1).unwrap(),
    )
    assert eligible == (True, True)
    costs = (
        MandelbrotSet.iterate(complex(-1.0, 0.0), 3).unwrap(),
        JuliaSet.iterate(complex(0.1, 0.1), complex(-0.7, 0.27015), 2).unwrap(),
    )

    model = MetaModelFloat64.create("public-fractal-resource-MILP").unwrap()
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
                    rhs=count_capacity,
                ),
                ConstraintSpec(
                    name="weight",
                    terms=[(x, 2), (y, 1)],
                    relation="<=",
                    rhs=weight_capacity,
                ),
            ]
        ).unwrap()
        model.set_objective(
            terms=[(x, costs[0]), (y, costs[1])], sense="maximize"
        ).unwrap()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL"
        assert report.values == pytest.approx((3, 6))
        assert report.objective == pytest.approx(21)

        result_x, result_y = (round(value) for value in report.values)
        assert result_x + result_y <= count_capacity
        assert 2 * result_x + result_y <= weight_capacity
        assert costs[0] * result_x + costs[1] * result_y == 21
    finally:
        model.close().unwrap()
