"""公开素数筛 Result 用于真实整数模型。 / Public prime-sieve Results feed a real integer model."""

from __future__ import annotations

import pytest

from ospf_python import _native
from ospf_python._binding.model import ConstraintSpec, MetaModelFloat64, VariableSpec
from ospf_python.math.ordinary.prime import primes_up_to


@pytest.mark.parametrize("solver", ("scip", "gurobi10", "gurobi11", "gurobi12"))
@pytest.mark.parametrize("limit", (10, 20, 29))
def test_prime_result_coefficients_solve_and_recheck(
    *, solver: str, limit: int
) -> None:
    if solver not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {solver}")
    coefficients = primes_up_to(limit).unwrap()
    capacity = sum(coefficients) - coefficients[-1]
    model = MetaModelFloat64.create("public-prime-sieve-resource-MILP").unwrap()
    try:
        variables = model.add_variables(
            [
                VariableSpec(name=f"prime-{prime}", kind="binary")
                for prime in coefficients
            ]
        ).unwrap()
        terms = list(zip(variables, coefficients, strict=True))
        model.add_constraints(
            [ConstraintSpec(name="capacity", terms=terms, relation="<=", rhs=capacity)]
        ).unwrap()
        model.set_objective(terms=terms, sense="maximize").unwrap()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL"
        counts = tuple(round(value) for value in report.values)
        assert report.values == pytest.approx(counts)
        assert all(value in (0, 1) for value in counts)
        actual = sum(
            prime * count for prime, count in zip(coefficients, counts, strict=True)
        )
        assert actual == capacity and report.objective == pytest.approx(capacity)
    finally:
        model.close().unwrap()
