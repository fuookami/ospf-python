"""三值逻辑完整自然调用，不冒充性能验收。 / Complete natural trivalent calls, not performance acceptance."""

from __future__ import annotations

from typing import Any

import pytest

from ospf_python.math.ordinary import Trivalent as Ordinary
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
@pytest.mark.parametrize("operation", ("and", "or", "not"))
def test_complete_public_trivalent_call(
    *, benchmark: Any, family: str, operation: str
) -> None:
    if family == "root":
        calls = {
            "and": lambda: and_(Trivalent.FALSE, Trivalent.UNKNOWN).unwrap(),
            "or": lambda: or_(Trivalent.FALSE, Trivalent.UNKNOWN).unwrap(),
            "not": lambda: not_(Trivalent.UNKNOWN).unwrap(),
        }
        expected = Trivalent.FALSE if operation == "and" else Trivalent.UNKNOWN
    elif family == "balanced":
        calls = {
            "and": lambda: balanced_and(
                BalancedTrivalent.FALSE, BalancedTrivalent.BALANCED
            ).unwrap(),
            "or": lambda: balanced_or(
                BalancedTrivalent.FALSE, BalancedTrivalent.BALANCED
            ).unwrap(),
            "not": lambda: balanced_not(BalancedTrivalent.BALANCED).unwrap(),
        }
        expected = (
            BalancedTrivalent.FALSE
            if operation == "and"
            else BalancedTrivalent.BALANCED
        )
    else:
        calls = {
            "and": lambda: (Ordinary.FALSE & Ordinary.UNKNOWN).unwrap(),
            "or": lambda: (Ordinary.FALSE | Ordinary.UNKNOWN).unwrap(),
            "not": lambda: (~Ordinary.UNKNOWN).unwrap(),
        }
        expected = Ordinary.FALSE if operation == "and" else Ordinary.UNKNOWN
    assert benchmark(calls[operation]) is expected
