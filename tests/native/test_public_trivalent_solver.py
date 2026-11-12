"""三值逻辑Result驱动真实Rust资源模型。 / Trivalent Results drive real Rust resource models."""

from __future__ import annotations

import pytest

from ospf_python import _native
from ospf_python._binding.model import ConstraintSpec, MetaModelFloat64, VariableSpec
from ospf_python.math.ordinary.trivalent import Trivalent as Ordinary
from ospf_python.math.trivalent import (
    BalancedTrivalent,
    Trivalent,
    and_,
    balanced_and,
    balanced_not,
    balanced_or,
    not_,
    or_,
)


@pytest.mark.parametrize("family", ("root", "balanced", "ordinary"))
@pytest.mark.parametrize("solver", ("scip", "gurobi10", "gurobi11", "gurobi12"))
def test_logical_eligibility_solves_and_rechecks(*, family: str, solver: str) -> None:
    if solver not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {solver}")
    if family == "root":
        states = [
            and_(Trivalent.TRUE, Trivalent.TRUE).unwrap(),
            or_(Trivalent.FALSE, Trivalent.FALSE).unwrap(),
            not_(Trivalent.FALSE).unwrap(),
        ]
        eligible = [state is Trivalent.TRUE for state in states]
    elif family == "balanced":
        balanced_states = [
            balanced_and(BalancedTrivalent.TRUE, BalancedTrivalent.TRUE).unwrap(),
            balanced_or(BalancedTrivalent.FALSE, BalancedTrivalent.FALSE).unwrap(),
            balanced_not(BalancedTrivalent.FALSE).unwrap(),
        ]
        eligible = [state is BalancedTrivalent.TRUE for state in balanced_states]
    else:
        ordinary_states = [
            (Ordinary.TRUE & Ordinary.TRUE).unwrap(),
            (Ordinary.FALSE | Ordinary.FALSE).unwrap(),
            (~Ordinary.FALSE).unwrap(),
        ]
        eligible = [state.to_bool().unwrap() is True for state in ordinary_states]
    assert eligible == [True, False, True]
    model = MetaModelFloat64.create("public-trivalent-eligibility-MILP").unwrap()
    try:
        variables = model.add_variables(
            [
                VariableSpec(
                    name=f"item-{index}", kind="binary", upper=1 if allowed else 0
                )
                for index, allowed in enumerate(eligible)
            ]
        ).unwrap()
        terms = list(zip(variables, (2, 3, 5), strict=True))
        model.add_constraints(
            [ConstraintSpec(name="capacity", terms=terms, relation="<=", rhs=5)]
        ).unwrap()
        model.set_objective(terms=terms, sense="maximize").unwrap()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL"
        assert report.values == pytest.approx((0, 0, 1))
        assert report.objective == pytest.approx(5)
        assert all(
            value <= int(allowed)
            for value, allowed in zip(report.values, eligible, strict=True)
        )
    finally:
        model.close().unwrap()
