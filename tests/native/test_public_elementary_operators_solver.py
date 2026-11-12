"""公开初等运算符Result生成真实Rust模型系数。 / Public elementary-operator Results generate real Rust model coefficients."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from ospf_python import _native
from ospf_python._binding.model import ConstraintSpec, MetaModelFloat64, VariableSpec
from ospf_python.math.operator.exp import exp2_op, exp10_op, exp_op
from ospf_python.math.operator.log import log2_op, log10_op, log_op
from ospf_python.math.operator.trigonometry import (
    acos_op,
    asin_op,
    atan_op,
    cos_op,
    sin_op,
    tan_op,
)

OPERATIONS: tuple[tuple[str, Callable[[float], object]], ...] = (
    ("exp", exp_op),
    ("exp2", exp2_op),
    ("exp10", exp10_op),
    ("ln", log_op),
    ("log2", log2_op),
    ("log10", log10_op),
    ("sin", sin_op),
    ("cos", cos_op),
    ("tan", tan_op),
    ("asin", asin_op),
    ("acos", acos_op),
    ("atan", atan_op),
)


@pytest.mark.parametrize("solver", ("scip", "gurobi10", "gurobi11", "gurobi12"))
@pytest.mark.parametrize(
    ("name", "operation"),
    OPERATIONS,
    ids=[name for name, _ in OPERATIONS],
)
def test_elementary_coefficients_solve_and_recheck(
    *, solver: str, name: str, operation: Callable[[float], object]
) -> None:
    if solver not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {solver}")
    coefficients = [
        operation(value).unwrap()  # type: ignore[union-attr]
        for value in (0.25, 0.5, 1.0)
    ]
    assert all(type(value) is float for value in coefficients)
    model = MetaModelFloat64.create(f"public-elementary-{name}-resource-MILP").unwrap()
    try:
        variables = model.add_variables(
            [VariableSpec(name=f"{name}-{index}", kind="binary") for index in range(3)]
        ).unwrap()
        terms = list(zip(variables, coefficients, strict=True))
        capacity = sum(coefficients)
        model.add_constraints(
            [
                ConstraintSpec(
                    name="coefficient-probe",
                    terms=terms,
                    relation="<=",
                    rhs=capacity,
                ),
                *(
                    ConstraintSpec(
                        name=f"anchor-{index}",
                        terms=[(variable, 1.0)],
                        relation="==",
                        rhs=1.0,
                    )
                    for index, variable in enumerate(variables)
                ),
            ]
        ).unwrap()
        model.set_objective(terms=terms, sense="maximize").unwrap()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL"
        assert report.values == pytest.approx([1, 1, 1])
        assert report.objective == pytest.approx(capacity)
    finally:
        model.close().unwrap()
