"""精确单位选择的真实配置模型消费者。 / Real configuration consumer of unit-aware selection."""

from __future__ import annotations

import itertools
from fractions import Fraction
from typing import Any

import pytest

from ospf_python import _native
from ospf_python._binding.model import ConstraintSpec, MetaModelFloat64, VariableSpec
from ospf_python._binding.numeric import Rational
from ospf_python.math.combinatorics.combinations import combinations
from ospf_python.math.combinatorics.permutations import permutations
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.unit.length import METER


@pytest.mark.parametrize("solver", ["scip", "gurobi10", "gurobi11", "gurobi12"])
@pytest.mark.parametrize("ordered", [False, True])
@pytest.mark.parametrize("external", [False, True])
def test_exact_selections_feed_real_configuration_milp(
    *, solver: str, ordered: bool, external: bool
) -> None:
    if solver not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {solver}")
    leaves = [Quantity(Fraction(index, 2), METER) for index in (1, 2, 3)]

    class Source:
        def __len__(self) -> int:
            return len(leaves)

        def __getitem__(self, index: int) -> Quantity[Fraction]:
            return leaves[index]

    source: Any = Source() if external else leaves
    operation = permutations if ordered else combinations
    rows = operation(source, 2).unwrap()
    oracle = itertools.permutations if ordered else itertools.combinations
    indices = list(oracle(range(3), 2))
    for row, positions in zip(rows, indices, strict=True):
        assert all(
            value is leaves[index] for value, index in zip(row, positions, strict=True)
        )
    weights = [sum((leaf.value for leaf in row), Fraction()) for row in rows]
    scores = [row[0].value * 2 + row[1].value for row in rows]
    eligible = [index for index, weight in enumerate(weights) if weight <= 2]
    best = max(eligible, key=lambda index: scores[index])
    assert indices[best] == ((2, 0) if ordered else (0, 2))
    # 精度转换集中于求解边界，枚举保持物理量。 / Convert precision only at the solver boundary; enumeration retains quantities.
    numeric_weights = [
        Rational.from_value(value).unwrap().to_float().unwrap() for value in weights
    ]
    numeric_scores = [
        Rational.from_value(value).unwrap().to_float().unwrap() for value in scores
    ]
    model = MetaModelFloat64.create(
        "public-positional-selection-configurations-MILP"
    ).unwrap()
    try:
        variables = model.add_variables(
            [
                VariableSpec(name=f"configuration-{index}", kind="binary")
                for index in range(len(rows))
            ]
        ).unwrap()
        assert model.add_constraints(
            [
                ConstraintSpec(
                    name="capacity",
                    terms=list(zip(variables, numeric_weights, strict=True)),
                    relation="<=",
                    rhs=2,
                ),
                ConstraintSpec(
                    name="choose-one",
                    terms=[(variable, 1) for variable in variables],
                    relation="==",
                    rhs=1,
                ),
            ]
        ).is_ok()
        assert model.set_objective(
            terms=list(zip(variables, numeric_scores, strict=True)), sense="maximize"
        ).is_ok()
        report = model.solve(solver=solver).unwrap()
        assert report.solution_presence == "OPTIMAL"
        assert report.values == pytest.approx(
            tuple(int(index == best) for index in range(len(rows)))
        )
        assert report.objective == pytest.approx(float(scores[best]))
    finally:
        assert model.close().is_ok()
