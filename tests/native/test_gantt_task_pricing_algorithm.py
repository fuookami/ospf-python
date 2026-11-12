"""Pinned complete-domain task pricing through the PyO3 bridge."""

from __future__ import annotations

from typing import Any

import pytest

from ospf_python import _native
from ospf_python._binding.gantt_task import TaskPricingAlgorithm
from ospf_python.utils.functional.result import Failed


@pytest.fixture
def solver() -> str:
    name = "gurobi10"
    if name not in _native.build_info()["native_solvers"].split(","):
        pytest.skip("Rust backend not compiled: gurobi10")
    return name


def _algorithm() -> TaskPricingAlgorithm:
    algorithm = TaskPricingAlgorithm.create(
        task_count=2,
        executor_count=2,
    ).unwrap()
    assert algorithm.add_columns([(0, 0, 1.0), (1, 1, 2.0)]).unwrap() == [
        (0, 0, 1.0),
        (1, 1, 2.0),
    ]
    return algorithm


@pytest.mark.parametrize(
    "completion",
    ("EXHAUSTED", "BUDGET_LIMIT", "INTERRUPTED", "HEURISTIC"),
)
def test_only_exhausted_with_no_improvement_certifies_the_lp_bound(
    solver: str, completion: str
) -> None:
    algorithm = _algorithm()
    report = algorithm.solve_lp(solver=solver).unwrap()
    assert report.is_optimal
    assert report.has_incumbent
    assert report.objective == pytest.approx(3.0)

    seen: dict[str, Any] = {}

    def policy(request: dict[str, Any]) -> dict[str, Any]:
        seen.update(request)
        return {
            "columns": [],
            "completion": completion,
            "no_improving_columns": True,
        }

    batch = algorithm.generate(policy).unwrap()
    assert batch.columns == []
    assert batch.completion == completion
    assert batch.global_scope
    assert batch.no_improving_columns is True
    assert batch.children == 0
    assert algorithm.completion() == completion
    bound = algorithm.certified_lower_bound().unwrap()
    if completion == "EXHAUSTED":
        assert bound == pytest.approx(3.0)
    else:
        assert bound is None

    assert seen["global"] is True
    assert seen["verified_duals"] is True
    assert seen["tasks"] == [0, 1]
    assert seen["executor_slots"] == [(0, 0), (1, 0)]
    assert seen["shadow_prices"] == {
        0: pytest.approx(1.0),
        1: pytest.approx(2.0),
    }
    assert {
        "task_compilation_0",
        "task_compilation_1",
        "executor_compilation_0",
        "executor_compilation_1",
    } <= seen["row_duals"].keys()


def test_new_priced_columns_invalidate_the_old_bound_and_completion(
    solver: str,
) -> None:
    algorithm = _algorithm()
    algorithm.solve_lp(solver=solver).unwrap()
    algorithm.generate(
        lambda _: {
            "columns": [],
            "completion": "EXHAUSTED",
            "no_improving_columns": True,
        }
    ).unwrap()
    assert algorithm.certified_lower_bound().unwrap() == pytest.approx(3.0)

    assert algorithm.add_priced_columns([(0, 1, 0.5)]).unwrap() == [(0, 1, 0.5)]
    assert algorithm.certified_lower_bound().unwrap() is None
    assert algorithm.completion() is None


def test_invalid_column_batch_is_rejected_without_changing_the_model(
    solver: str,
) -> None:
    algorithm = _algorithm()
    result = algorithm.add_priced_columns([(0, 1, 0.5), (0, 2, 0.0)])
    assert isinstance(result, Failed)
    assert result.error.code.name == "ILLEGAL_ARGUMENT"

    report = algorithm.solve_lp(solver=solver).unwrap()
    assert report.objective == pytest.approx(3.0)
    algorithm.generate(
        lambda _: {
            "columns": [],
            "completion": "EXHAUSTED",
            "no_improving_columns": True,
        }
    ).unwrap()
    assert algorithm.certified_lower_bound().unwrap() == pytest.approx(3.0)


@pytest.mark.parametrize("case", ("invalid-completion", "policy-error"))
def test_invalid_policy_results_are_structured_failures(case: str) -> None:
    algorithm = _algorithm()

    def policy(_: dict[str, Any]) -> dict[str, Any]:
        if case == "policy-error":
            raise RuntimeError("policy exploded")
        return {
            "columns": [],
            "completion": "UNKNOWN",
            "no_improving_columns": True,
        }

    result = algorithm.generate(policy)
    assert isinstance(result, Failed)
    assert result.error.code.name == "ILLEGAL_ARGUMENT"
    assert "Task-pricing policy failed" in result.error.message
