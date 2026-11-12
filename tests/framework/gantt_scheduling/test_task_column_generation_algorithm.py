"""Public pinned task column-generation facade tests."""

from __future__ import annotations

from typing import Any

import pytest

from ospf_python import _native
from ospf_python._binding.gantt_task import (
    TaskPricingBatch as NativeTaskPricingBatch,
)
from ospf_python.framework.gantt_scheduling.application.service.task import (
    TaskColumnGenerationAlgorithm,
    TaskPricingBatch,
)


def test_public_facade_owns_the_pinned_algorithm_without_duplicate_state() -> None:
    algorithm = TaskColumnGenerationAlgorithm.create(
        task_count=2,
        executor_count=2,
    ).unwrap()
    assert isinstance(algorithm, TaskColumnGenerationAlgorithm)
    assert TaskPricingBatch is NativeTaskPricingBatch
    assert algorithm.add_columns([(0, 0, 1.0), (1, 1, 2.0)]).unwrap() == [
        (0, 0, 1.0),
        (1, 1, 2.0),
    ]
    assert algorithm.solve_lp(solver="unknown").is_failed()


@pytest.mark.parametrize("solver", ("gurobi10",))
def test_public_facade_solves_and_certifies_through_the_rust_algorithm(
    solver: str,
) -> None:
    if solver not in _native.build_info()["native_solvers"].split(","):
        pytest.skip(f"Rust backend not compiled: {solver}")

    algorithm = TaskColumnGenerationAlgorithm.create(
        task_count=2,
        executor_count=2,
    ).unwrap()
    algorithm.add_columns([(0, 0, 1.0), (1, 1, 2.0)]).unwrap()
    report = algorithm.solve_lp(solver=solver).unwrap()
    assert report.is_optimal
    assert report.objective == pytest.approx(3.0)

    seen: dict[str, Any] = {}

    def policy(request: dict[str, Any]) -> dict[str, Any]:
        seen.update(request)
        return {
            "columns": [],
            "completion": "EXHAUSTED",
            "no_improving_columns": True,
        }

    batch = algorithm.generate(policy).unwrap()
    assert batch.columns == []
    assert batch.global_scope
    assert batch.no_improving_columns is True
    assert algorithm.certified_lower_bound().unwrap() == pytest.approx(3.0)
    assert seen["verified_duals"] is True
