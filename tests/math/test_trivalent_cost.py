"""三值自然调用只发布一次既有Result。 / Natural trivalent calls publish the existing Result exactly once."""

from __future__ import annotations

import itertools
import operator
from collections.abc import Callable
from typing import Any

import pytest

from ospf_python import _native
from ospf_python._binding import result as transport
from ospf_python._binding import trivalent as adapter
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
from ospf_python.utils.functional import result as functional


def record_publications(monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    """在所有既有发布点记录Ok，不替换Result类型。 / Record Ok at existing publication sites without replacing the Result family.

    Args:
        monkeypatch: 测试作用域替换。 / Test-scoped replacement.

    Returns:
        每个实际发布的成功值。 / Each actually published successful value.
    """
    original = functional.Ok
    published: list[Any] = []

    def create(value: Any) -> Any:
        published.append(value)
        return original(value)

    monkeypatch.setattr(functional, "Ok", create)
    monkeypatch.setattr(transport, "Ok", create)
    monkeypatch.setattr(adapter, "Ok", create, raising=False)
    return published


@pytest.mark.parametrize("family", ("root", "balanced", "ordinary"))
@pytest.mark.parametrize("operation", ("and", "or", "not"))
def test_all_finite_results_have_one_publication(
    *, monkeypatch: pytest.MonkeyPatch, family: str, operation: str
) -> None:
    values = tuple(
        {"root": Trivalent, "balanced": BalancedTrivalent, "ordinary": Ordinary}[family]
    )
    functions: dict[str, Callable[..., Any]] = (
        {"and": operator.and_, "or": operator.or_, "not": operator.invert}
        if family == "ordinary"
        else {"and": and_, "or": or_, "not": not_}
        if family == "root"
        else {"and": balanced_and, "or": balanced_or, "not": balanced_not}
    )
    arguments = (
        [(value,) for value in values]
        if operation == "not"
        else list(itertools.product(values, repeat=2))
    )
    published = record_publications(monkeypatch)
    outputs = [functions[operation](*args).unwrap() for args in arguments]
    assert len(published) == len(arguments)
    assert all(
        actual is expected for actual, expected in zip(published, outputs, strict=True)
    )
    assert all(any(value is member for member in values) for value in outputs)


def test_all_optional_bool_results_have_one_publication(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    published = record_publications(monkeypatch)
    outputs = [value.to_bool().unwrap() for value in Ordinary]
    assert len(published) == 3
    assert all(
        actual is expected for actual, expected in zip(published, outputs, strict=True)
    )
    assert outputs == [True, False, None]


def test_invalid_members_do_not_reach_native_or_publish_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    published = record_publications(monkeypatch)

    def forbidden(**kwargs: Any) -> Any:
        pytest.fail("非法输入不应抵达FFI / Invalid members must not reach FFI")

    monkeypatch.setattr(_native, "_trivalent", forbidden)
    invalid: Any = None
    foreign: Any = BalancedTrivalent.FALSE
    for member in (Trivalent.TRUE, Trivalent.FALSE, Trivalent.UNKNOWN):
        assert and_(member, invalid).is_failed()
        assert or_(member, foreign).is_failed()
        assert not_(invalid).is_failed()
    foreign = Trivalent.TRUE
    assert Ordinary.to_bool(foreign).is_failed()
    assert published == []
