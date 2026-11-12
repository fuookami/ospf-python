"""值域限制结果用于真实整数模型。 / Clamp Results feed a real integer model."""

from __future__ import annotations

import pytest

from ospf_python import _native
from ospf_python._binding.model import ConstraintSpec, MetaModelFloat64, VariableSpec
from ospf_python.math.ordinary.clamp import clamp


@pytest.mark.parametrize("solver", ("scip", "gurobi10", "gurobi11", "gurobi12"))
def test_clamped_coefficients_solve_and_recheck(solver: str) -> None:
    if solver not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {solver}")
    coefficients = [clamp(value, min_val=1, max_val=4).unwrap() for value in (0, 2, 8)]
    assert coefficients == [1, 2, 4]
    model = MetaModelFloat64.create("public-clamp-resource-MILP").unwrap()
    try:
        variables = model.add_variables(
            [VariableSpec(name=f"item-{index}", kind="binary") for index in range(3)]
        ).unwrap()
        terms = list(zip(variables, coefficients, strict=True))
        model.add_constraints(
            [ConstraintSpec(name="capacity", terms=terms, relation="<=", rhs=3)]
        ).unwrap()
        model.set_objective(terms=terms, sense="maximize").unwrap()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL"
        assert report.values == pytest.approx((1, 1, 0))
        assert report.objective == pytest.approx(3)
    finally:
        model.close().unwrap()
