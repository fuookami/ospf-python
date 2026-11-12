"""Fixed-revision finite-pool task reduced-cost contracts."""

from __future__ import annotations

import math

from ospf_python import _native


def test_reduced_cost_uses_all_rows_and_strict_tolerance() -> None:
    improving, failure = _native._task_improving_columns(
        columns=[
            ("boundary", 2.5, {"task": 1.0}),
            ("improve", 1.0, {"task": 1.0, "capacity": 2.0}),
        ],
        dual_values={"task": 2.5, "capacity": 0.25},
        tolerance=0.5,
    )

    assert failure is None
    assert improving == {"boundary": False, "improve": True}


def test_reduced_cost_keeps_sub_tolerance_difference_exact() -> None:
    improving, failure = _native._task_improving_columns(
        columns=[
            ("boundary", 0.5, {"task": 1.0}),
            ("tiny", math.nextafter(0.5, 0.0), {"task": 1.0}),
        ],
        dual_values={"task": 1.0},
        tolerance=0.5,
    )

    assert failure is None
    assert improving == {"boundary": False, "tiny": True}


def test_reduced_cost_requires_a_dual_for_every_candidate_row() -> None:
    improving, failure = _native._task_improving_columns(
        columns=[("column", 1.0, {"missing": 1.0})],
        dual_values={},
        tolerance=0.0,
    )

    assert improving is None
    assert failure is not None
    assert failure.category == "ILLEGAL_ARGUMENT"
    assert "missing" in failure.message


def test_reduced_cost_rejects_duplicate_keys_and_invalid_tolerance() -> None:
    duplicate, failure = _native._task_improving_columns(
        columns=[
            ("column", 1.0, {}),
            ("column", 0.5, {}),
        ],
        dual_values={},
        tolerance=0.0,
    )
    assert duplicate is None
    assert failure is not None
    assert failure.category == "ILLEGAL_ARGUMENT"

    for tolerance in (-1.0, math.nan, math.inf):
        improving, failure = _native._task_improving_columns(
            columns=[],
            dual_values={},
            tolerance=tolerance,
        )
        assert improving is None
        assert failure is not None
        assert failure.category == "ILLEGAL_ARGUMENT"
