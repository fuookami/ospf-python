"""Result 与 unwrap 边界政策合同 / Result and unwrap boundary-policy contracts."""

from __future__ import annotations

import pytest

from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Fatal, Ok, Warn


def _error(message: str = "expected failure") -> Err[ErrorCode]:
    return Err(_code=ErrorCode.FAILED_PRECONDITION, _message=message)


def test_unwrap_is_an_explicit_precondition_escape_hatch() -> None:
    failed = Failed(_error=_error("single"))

    with pytest.raises(RuntimeError, match="Failed.*single"):
        failed.unwrap()

    assert failed.error.message == "single"


def test_fatal_unwrap_raises_the_existing_runtime_contract() -> None:
    fatal = Fatal(_errors=(_error("first"), _error("second")))

    with pytest.raises(RuntimeError, match="Fatal.*first.*second"):
        fatal.unwrap()

    assert tuple(error.message for error in fatal.errors) == ("first", "second")


def test_unwrap_or_never_calls_the_success_path_for_failures() -> None:
    assert Ok(7).unwrap_or(0) == 7
    assert Failed(_error=_error()).unwrap_or(9) == 9
    assert Fatal(_errors=(_error(),)).unwrap_or(11) == 11
    assert Warn(_value=13, _warning=_error()).unwrap_or(0) == 13


def test_user_mapping_exceptions_are_not_swallowed_or_rewrapped() -> None:
    error = ValueError("user callback")

    def fail(_: int) -> int:
        raise error

    with pytest.raises(ValueError) as caught:
        Ok(1).map(fail)

    assert caught.value is error


def test_failure_callbacks_are_not_run_after_an_earlier_failure() -> None:
    calls: list[str] = []
    failed = Failed(_error=_error())

    result = failed.flat_map(lambda value: Ok(calls.append(str(value))))

    assert result is failed
    assert calls == []


def test_results_are_frozen_value_objects() -> None:
    ok = Ok(1)
    failed = Failed(_error=_error())

    with pytest.raises(AttributeError):
        ok._value = 2  # type: ignore[misc]
    with pytest.raises(AttributeError):
        failed._error = _error()  # type: ignore[misc]
