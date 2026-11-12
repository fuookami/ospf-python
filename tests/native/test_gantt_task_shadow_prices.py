"""Fixed-revision Gantt task shadow-price boundary contracts."""

from __future__ import annotations

import pytest

from ospf_python import _native


def test_task_shadow_prices_use_task_algorithm_duals() -> None:
    prices, failure = _native._task_shadow_prices(
        task_count=2,
        dual_values=[0.0, -2.5],
        constraint_name_to_index={
            "task_compilation_0": 0,
            "task_compilation_1": 1,
            "capacity": 2,
        },
    )

    assert failure is None
    assert prices == {1: -2.5}


def test_task_shadow_prices_ignore_rows_outside_the_dual_vector() -> None:
    prices, failure = _native._task_shadow_prices(
        task_count=2,
        dual_values=[4.0],
        constraint_name_to_index={
            "task_compilation_0": 1,
            "task_compilation_1": 0,
        },
    )

    assert failure is None
    assert prices == {1: 4.0}


def test_task_shadow_prices_are_deterministically_ordered() -> None:
    prices, failure = _native._task_shadow_prices(
        task_count=3,
        dual_values=[3.0, 1.0, 2.0],
        constraint_name_to_index={
            "task_compilation_2": 2,
            "task_compilation_0": 0,
            "task_compilation_1": 1,
        },
    )

    assert failure is None
    assert list(prices or {}) == [0, 1, 2]


def test_task_shadow_prices_reject_negative_task_count() -> None:
    with pytest.raises(OverflowError):
        _native._task_shadow_prices(
            task_count=-1,
            dual_values=[],
            constraint_name_to_index={},
        )
