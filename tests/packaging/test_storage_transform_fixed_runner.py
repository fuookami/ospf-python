"""Storage-transform fixed-runner policy contracts."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = ROOT / "benchmarks" / "storage_transform_fixed_runner.py"


def _load_runner() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "storage_transform_fixed_runner",
        RUNNER_PATH,
    )
    if spec is None or spec.loader is None:
        raise AssertionError("fixed runner module cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_policy_registers_complete_matrix_and_seed() -> None:
    """The policy must cover all 96 rows and every resource family."""
    runner = _load_runner()
    policy = runner._load_policy()

    rows = (
        len(policy["counts"])
        * len(policy["domains"])
        * 2
        * len(policy["orders"])
        * len(policy["methods"])
    )
    assert rows == policy["expected_rows"] == 96
    assert policy["seed"] == 278177592
    assert policy["gated_count"] >= policy["gated_minimum"]
    assert policy["threshold"] == 1.15


def test_seeded_values_are_independent_and_reproducible() -> None:
    """Each call must rebuild the same independently owned input."""
    runner = _load_runner()
    policy = runner._load_policy()
    first = runner._values(domain="int16", count=64, seed=policy["seed"])
    second = runner._values(domain="int16", count=64, seed=policy["seed"])

    assert first.tolist() == second.tolist()
    assert not np.shares_memory(first, second)


def test_short_smoke_cannot_be_accepted() -> None:
    """A smoke run must never satisfy fixed-runner or long-soak gates."""
    runner = _load_runner()
    policy = runner._load_policy()
    rows = [
        {"count": policy["gated_count"], "ratio": 1.0}
        for _ in range(policy["expected_rows"])
    ]
    resources = [{"passed": True} for _ in range(8)]

    assessment = runner._assess(
        policy=policy,
        rows=rows,
        resources=resources,
        runner_matches=False,
        extension_matches=False,
        rounds=1,
        soak_seconds=30,
    )

    assert not assessment["accepted"]
    assert not assessment["checks"]["declared_fixed_runner"]
    assert not assessment["checks"]["extension_hash_matches"]
    assert not assessment["checks"]["two_or_more_rounds"]
    assert not assessment["checks"]["ten_minute_soak"]


def test_complete_preregistered_evidence_is_accepted() -> None:
    """The acceptance predicate requires every preregistered condition."""
    runner = _load_runner()
    policy = runner._load_policy()
    rows = [
        {"count": policy["gated_count"], "ratio": 1.0}
        for _ in range(policy["expected_rows"] * 2)
    ]
    resources = [{"passed": True} for _ in range(8)]

    assessment = runner._assess(
        policy=policy,
        rows=rows,
        resources=resources,
        runner_matches=True,
        extension_matches=True,
        rounds=2,
        soak_seconds=600,
    )

    assert assessment["accepted"]
    assert not assessment["gated_failures"]
