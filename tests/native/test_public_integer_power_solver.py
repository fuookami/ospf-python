"""公开整数幂Result用于真实Rust资源模型。 / Public integer-power Results feed real Rust resource models."""

from __future__ import annotations

import pytest

from ospf_python import _native
from ospf_python._binding.model import ConstraintSpec, MetaModelFloat64, VariableSpec
from ospf_python.math.ordinary.pow import pow_int


@pytest.mark.parametrize("solver", ("scip", "gurobi10", "gurobi11", "gurobi12"))
@pytest.mark.parametrize("base", (2, 3, 5))
def test_power_coefficients_solve_and_recheck(*, solver: str, base: int) -> None:
    if solver not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {solver}")
    coefficients = [pow_int(base, exp).unwrap() for exp in (1, 2, 3)]
    capacity = sum(coefficients[:-1])
    model = MetaModelFloat64.create("public-integer-power-resource-MILP").unwrap()
    try:
        variables = model.add_variables(
            [VariableSpec(name=f"power-{index}", kind="binary") for index in range(3)]
        ).unwrap()
        terms = list(zip(variables, coefficients, strict=True))
        model.add_constraints(
            [ConstraintSpec(name="capacity", terms=terms, relation="<=", rhs=capacity)]
        ).unwrap()
        model.set_objective(terms=terms, sense="maximize").unwrap()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL"
        counts = tuple(round(value) for value in report.values)
        assert report.values == pytest.approx(counts) and all(
            value in (0, 1) for value in counts
        )
        actual = sum(
            coefficient * count
            for coefficient, count in zip(coefficients, counts, strict=True)
        )
        assert actual == capacity and report.objective == pytest.approx(capacity)
    finally:
        model.close().unwrap()
