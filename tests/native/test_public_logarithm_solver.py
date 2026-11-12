"""公开对数Result生成真实Rust模型系数。 / Public logarithm Results generate real Rust model coefficients."""

from __future__ import annotations

import pytest

from ospf_python import _native
from ospf_python._binding.model import ConstraintSpec, MetaModelFloat64, VariableSpec
from ospf_python.math.ordinary.log import log_base


@pytest.mark.parametrize("solver", ("scip", "gurobi10", "gurobi11", "gurobi12"))
@pytest.mark.parametrize("base", (2, 10, 1 << 1024), ids=("binary", "decimal", "wide"))
def test_logarithmic_coefficients_solve_and_recheck(*, solver: str, base: int) -> None:
    if solver not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {solver}")
    coefficients = [log_base(base**power, base).unwrap() for power in (1, 2, 4)]
    assert coefficients == pytest.approx([1, 2, 4])
    model = MetaModelFloat64.create("public-logarithmic-resource-MILP").unwrap()
    try:
        variables = model.add_variables(
            [VariableSpec(name=f"log-{index}", kind="binary") for index in range(3)]
        ).unwrap()
        terms = list(zip(variables, coefficients, strict=True))
        model.add_constraints(
            [ConstraintSpec(name="capacity", terms=terms, relation="<=", rhs=3)]
        ).unwrap()
        model.set_objective(terms=terms, sense="maximize").unwrap()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL"
        assert report.values == pytest.approx([1, 1, 0])
        assert report.objective == pytest.approx(3)
        assert sum(
            coefficient * count
            for coefficient, count in zip(coefficients, report.values, strict=True)
        ) == pytest.approx(3)
    finally:
        model.close().unwrap()
