"""三类公开三值逻辑的完整有限域与协议合同。 / Complete finite-domain and protocol contracts for three public trivalent types."""

from __future__ import annotations

import ast
import copy
import enum
import gc
import inspect
import itertools
import pickle
import weakref
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, get_origin, get_type_hints

import pytest

from ospf_python import _native
from ospf_python._binding.result import BindingResult, FailureContext
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
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed, Ok, Result

FAMILIES = ("root", "balanced", "ordinary")
AND = ((0, 1, 2), (1, 1, 1), (2, 1, 2))
OR = ((0, 0, 0), (0, 1, 2), (0, 2, 2))
NOT = (1, 0, 2)


def members(family: str) -> tuple[Any, Any, Any]:
    values = tuple(
        {"root": Trivalent, "balanced": BalancedTrivalent, "ordinary": Ordinary}[family]
    )
    return values[0], values[1], values[2]


def call(*, family: str, operation: str, left: Any, right: Any = None) -> Any:
    if family == "ordinary":
        if operation == "and":
            return Ordinary.__and__(left, right)
        if operation == "or":
            return Ordinary.__or__(left, right)
        return Ordinary.__invert__(left)
    functions: dict[str, Callable[..., BindingResult[Any]]] = (
        {"and": and_, "or": or_, "not": not_}
        if family == "root"
        else {"and": balanced_and, "or": balanced_or, "not": balanced_not}
    )
    return (
        functions[operation](left)
        if operation == "not"
        else functions[operation](left, right)
    )


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("operation", ("and", "or"))
@pytest.mark.parametrize(
    ("left", "right"), tuple(itertools.product(range(3), repeat=2))
)
def test_complete_binary_truth_tables(
    *, family: str, operation: str, left: int, right: int
) -> None:
    values = members(family)
    result = call(
        family=family, operation=operation, left=values[left], right=values[right]
    )
    assert isinstance(result, Ok) and isinstance(result, Result)
    assert result.unwrap() is values[(AND if operation == "and" else OR)[left][right]]


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("state", range(3))
def test_complete_not_truth_table(*, family: str, state: int) -> None:
    values = members(family)
    result = call(family=family, operation="not", left=values[state])
    assert isinstance(result, Ok) and result.unwrap() is values[NOT[state]]


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize(("a", "b", "c"), tuple(itertools.product(range(3), repeat=3)))
def test_complete_ternary_algebra(*, family: str, a: int, b: int, c: int) -> None:
    values = members(family)
    x, y, z = values[a], values[b], values[c]

    def binary(*, operation: str, left: Any, right: Any) -> Any:
        return call(family=family, operation=operation, left=left, right=right).unwrap()

    def negate(value: Any) -> Any:
        return call(family=family, operation="not", left=value).unwrap()

    for operation in ("and", "or"):
        assert binary(operation=operation, left=x, right=y) is binary(
            operation=operation, left=y, right=x
        )
        assert binary(
            operation=operation,
            left=binary(operation=operation, left=x, right=y),
            right=z,
        ) is binary(
            operation=operation,
            left=x,
            right=binary(operation=operation, left=y, right=z),
        )
        assert binary(operation=operation, left=x, right=x) is x
    assert negate(negate(x)) is x
    assert negate(binary(operation="and", left=x, right=y)) is binary(
        operation="or", left=negate(x), right=negate(y)
    )
    assert negate(binary(operation="or", left=x, right=y)) is binary(
        operation="and", left=negate(x), right=negate(y)
    )
    assert binary(
        operation="and", left=x, right=binary(operation="or", left=y, right=z)
    ) is binary(
        operation="or",
        left=binary(operation="and", left=x, right=y),
        right=binary(operation="and", left=x, right=z),
    )
    assert binary(
        operation="or", left=x, right=binary(operation="and", left=y, right=z)
    ) is binary(
        operation="and",
        left=binary(operation="or", left=x, right=y),
        right=binary(operation="or", left=x, right=z),
    )
    assert (
        binary(operation="and", left=x, right=binary(operation="or", left=x, right=y))
        is x
    )
    assert (
        binary(operation="or", left=x, right=binary(operation="and", left=x, right=y))
        is x
    )


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("state", range(3))
@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
def test_enum_identity_copy_pickle_and_metadata(
    *, family: str, state: int, protocol: int
) -> None:
    owner = members(family)[state]
    kind = type(owner)
    assert issubclass(kind, enum.Enum)
    assert kind(owner.value) is owner and kind[owner.name] is owner
    assert pickle.loads(pickle.dumps(owner, protocol=protocol)) is owner
    assert copy.copy(owner) is owner and copy.deepcopy(owner) is owner
    assert owner in {owner: True} and bool(owner) is True
    assert str(owner) == f"{kind.__name__}.{owner.name}"
    assert repr(owner) == f"<{kind.__name__}.{owner.name}: {owner.value!r}>"
    assert (
        owner.value
        == (
            ("true", "false", "balanced")
            if family == "balanced"
            else ("true", "false", "unknown")
        )[state]
    )


@pytest.mark.parametrize("state", range(3))
def test_ordinary_optional_bool_and_identity_properties(state: int) -> None:
    owner = members("ordinary")[state]
    result = owner.to_bool()
    assert isinstance(result, Ok) and result.unwrap() is (True, False, None)[state]
    assert (owner.is_true, owner.is_false, owner.is_unknown) == tuple(
        state == i for i in range(3)
    )


@pytest.mark.parametrize("state", range(3))
def test_same_spelling_families_do_not_merge(state: int) -> None:
    values = [members(family)[state] for family in FAMILIES]
    assert len(set(values)) == 3
    assert all(a is not b and a != b for a, b in itertools.combinations(values, 2))


class NoProtocol:
    """无效对象不应触发任何协议。 / Invalid objects must not trigger protocols."""

    def __bool__(self) -> bool:
        raise AssertionError("truth protocol was invoked")

    def __eq__(self, other: object) -> bool:
        raise AssertionError("equality protocol was invoked")

    def __hash__(self) -> int:
        raise AssertionError("hash protocol was invoked")

    def __repr__(self) -> str:
        raise AssertionError("repr protocol was invoked")

    def __str__(self) -> str:
        raise AssertionError("string protocol was invoked")


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("operation", ("and", "or", "not"))
@pytest.mark.parametrize(
    "invalid_kind",
    ("true", "false", "none", "int", "str", "list", "foreign", "hostile", "forged"),
)
def test_invalid_left_has_no_implicit_protocol(
    *, family: str, operation: str, invalid_kind: str
) -> None:
    values = members(family)
    foreign = members("balanced" if family != "balanced" else "root")[0]
    invalid = {
        "true": True,
        "false": False,
        "none": None,
        "int": 1,
        "str": "true",
        "list": [],
        "foreign": foreign,
        "hostile": NoProtocol(),
        "forged": object.__new__(type(values[0])),
    }[invalid_kind]
    result = call(family=family, operation=operation, left=invalid, right=values[0])
    assert (
        isinstance(result, Failed) and result.error.code is ErrorCode.ILLEGAL_ARGUMENT
    )
    assert result.error.value.callback_exception is None


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("operation", ("and", "or"))
@pytest.mark.parametrize("state", range(3))
@pytest.mark.parametrize("invalid_kind", ("none", "false", "foreign", "hostile"))
def test_invalid_right_is_rejected_even_for_absorbing_left(
    *, family: str, operation: str, state: int, invalid_kind: str
) -> None:
    invalid = {
        "none": None,
        "false": False,
        "foreign": members("balanced" if family != "balanced" else "root")[1],
        "hostile": NoProtocol(),
    }[invalid_kind]
    result = call(
        family=family, operation=operation, left=members(family)[state], right=invalid
    )
    assert (
        isinstance(result, Failed) and result.error.code is ErrorCode.ILLEGAL_ARGUMENT
    )
    assert result.error.value.callback_exception is None


@pytest.mark.parametrize("family", FAMILIES)
def test_invalid_inputs_are_not_retained_by_failure(family: str) -> None:
    value = NoProtocol()
    reference = weakref.ref(value)
    result = call(family=family, operation="and", left=members(family)[0], right=value)
    assert isinstance(result, Failed)
    del value
    gc.collect()
    assert reference() is None


class UnformattableError(Exception):
    """保留异常而不格式化。 / Retain exceptions without formatting."""

    def __str__(self) -> str:
        raise AssertionError("error string was requested")


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("operation", ("and", "or", "not"))
@pytest.mark.parametrize(
    "error_type",
    (
        RuntimeError,
        TypeError,
        MemoryError,
        UnformattableError,
        KeyboardInterrupt,
        SystemExit,
        GeneratorExit,
    ),
)
def test_original_transport_errors_and_baseexceptions(
    *,
    monkeypatch: pytest.MonkeyPatch,
    family: str,
    operation: str,
    error_type: type[BaseException],
) -> None:
    error = error_type("original")
    try:
        raise error
    except BaseException:
        traceback = error.__traceback__

    def broken(**kwargs: Any) -> Any:
        raise error

    monkeypatch.setattr(_native, "_trivalent", broken)
    values = members(family)
    if not isinstance(error, Exception):
        with pytest.raises(error_type) as caught:
            call(family=family, operation=operation, left=values[0], right=values[1])
        assert caught.value is error
    else:
        result = call(
            family=family, operation=operation, left=values[0], right=values[1]
        )
        assert isinstance(result, Failed) and isinstance(
            result.error.value, FailureContext
        )
        assert result.error.value.callback_exception is error
        assert result.error.code is (
            ErrorCode.RESOURCE_EXHAUSTED
            if isinstance(error, MemoryError)
            else ErrorCode.APPLICATION_ERROR
        )
    node = error.__traceback__
    while node is not None and node is not traceback:
        node = node.tb_next
    assert node is traceback


def test_every_natural_call_reaches_native_without_python_truth_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = _native._trivalent
    observed: list[str] = []

    def record(**kwargs: Any) -> Any:
        observed.append(kwargs["operation"])
        return original(**kwargs)

    monkeypatch.setattr(_native, "_trivalent", record)
    for family in FAMILIES:
        values = members(family)
        for operation in ("and", "or"):
            for left, right in itertools.product(values, repeat=2):
                assert call(
                    family=family, operation=operation, left=left, right=right
                ).is_ok()
        for value in values:
            assert call(family=family, operation="not", left=value).is_ok()
    for value in Ordinary:
        assert value.to_bool().is_ok()
    assert len(observed) == 66 and observed.count("bool") == 3


@pytest.mark.parametrize(
    "owner", (None, True, Trivalent.TRUE), ids=("none", "bool", "foreign")
)
def test_optional_bool_rejects_nonmembers(owner: Any) -> None:
    result = Ordinary.to_bool(owner)
    assert (
        isinstance(result, Failed) and result.error.code is ErrorCode.ILLEGAL_ARGUMENT
    )


@pytest.mark.parametrize(
    "error_type",
    (
        RuntimeError,
        MemoryError,
        UnformattableError,
        KeyboardInterrupt,
        SystemExit,
        GeneratorExit,
    ),
)
def test_optional_bool_preserves_transport_errors(
    *, monkeypatch: pytest.MonkeyPatch, error_type: type[BaseException]
) -> None:
    error = error_type("original")

    def broken(**kwargs: Any) -> Any:
        raise error

    monkeypatch.setattr(_native, "_trivalent", broken)
    if not isinstance(error, Exception):
        with pytest.raises(error_type) as caught:
            Ordinary.UNKNOWN.to_bool()
        assert caught.value is error
    else:
        result = Ordinary.UNKNOWN.to_bool()
        assert (
            isinstance(result, Failed)
            and result.error.value.callback_exception is error
        )
        assert result.error.code is (
            ErrorCode.RESOURCE_EXHAUSTED
            if isinstance(error, MemoryError)
            else ErrorCode.APPLICATION_ERROR
        )


@pytest.mark.parametrize("operation", ("", "xor", "NOT", "not", "bool"))
def test_private_invalid_operation_and_arity(operation: str) -> None:
    value, failure = _native._trivalent(operation=operation, left=True, right=False)
    assert value is None and failure is not None
    assert failure.category == "ILLEGAL_ARGUMENT"


@pytest.mark.parametrize(
    "value",
    (1, 0, "true", (), NoProtocol()),
    ids=("one", "zero", "str", "tuple", "hostile"),
)
def test_private_transport_is_strict_without_truth_conversion(value: Any) -> None:
    for arguments in ((value, None), (None, value)):
        output, failure = _native._trivalent(
            operation="and", left=arguments[0], right=arguments[1]
        )
        assert (
            output is None
            and failure is not None
            and failure.category == "ILLEGAL_ARGUMENT"
        )


def test_private_unknown_is_success_not_failure_sentinel() -> None:
    output, failure = _native._trivalent(operation="not", left=None, right=None)
    assert output is None and failure is None
    result = not_(Trivalent.UNKNOWN)
    assert isinstance(result, Ok) and result.unwrap() is Trivalent.UNKNOWN


def test_concurrent_repeated_calls_have_no_cross_family_state() -> None:
    def work(index: int) -> bool:
        family = FAMILIES[index % 3]
        values = members(family)
        for i, j in itertools.product(range(3), repeat=2):
            assert (
                call(
                    family=family, operation="and", left=values[i], right=values[j]
                ).unwrap()
                is values[AND[i][j]]
            )
            assert (
                call(
                    family=family, operation="or", left=values[i], right=values[j]
                ).unwrap()
                is values[OR[i][j]]
            )
        return True

    with ThreadPoolExecutor(max_workers=6) as pool:
        assert all(pool.map(work, range(120)))


def test_public_return_annotations_are_existing_result() -> None:
    for function in (
        and_,
        or_,
        not_,
        balanced_and,
        balanced_or,
        balanced_not,
        Ordinary.__and__,
        Ordinary.__or__,
        Ordinary.__invert__,
        Ordinary.to_bool,
    ):
        assert get_origin(get_type_hints(function)["return"]) is BindingResult


def test_old_truth_tables_and_branch_kernels_are_removed() -> None:
    for module_name in (
        "ospf_python.math.trivalent",
        "ospf_python.math.ordinary.trivalent",
    ):
        module = __import__(module_name, fromlist=["_"])
        tree = ast.parse(Path(inspect.getfile(module)).read_text(encoding="utf-8"))
        assert not any(isinstance(node, ast.Dict) for node in ast.walk(tree))
        assert not any(isinstance(node, (ast.If, ast.Match)) for node in ast.walk(tree))
