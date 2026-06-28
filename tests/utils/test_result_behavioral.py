"""Behavioral tests for utils.functional.result module.

Targets: Ok.map/flat_map/unwrap_or/on_success/on_failure/map_err,
Failed.map_err/flat_map/unwrap_or/on_success,
Fatal.map_err/on_failure/on_success/unwrap_or,
Success.map/flat_map/map_err/on_success/on_failure/unwrap_or,
Warn.map/map_err/flat_map/unwrap/unwrap_or/on_success/on_failure,
failed_from_code factory.
"""

from __future__ import annotations

import pytest

from ospf_python.utils.error import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional import (
    Failed,
    Fatal,
    Ok,
    Result,
    Success,
    Warn,
)
from ospf_python.utils.functional.result import failed_from_code


# Helper
def _err(code: ErrorCode = ErrorCode.NOT_FOUND, msg: str = "error") -> Err:
    return Err(_code=code, _message=msg)


class TestOkBehavior:
    """Ok 行为测试。/ Ok behavioral tests."""

    def test_map(self) -> None:
        """Ok.map 变换成功值。/ Ok.map transforms success value."""
        result = Ok(5).map(lambda x: x * 2)
        assert isinstance(result, Ok)
        assert result.value == 10

    def test_map_err_returns_self(self) -> None:
        """Ok.map_err 返回自身。/ Ok.map_err returns self."""
        ok = Ok(5)
        result = ok.map_err(lambda e: e)
        assert result is ok or (isinstance(result, Ok) and result.value == 5)

    def test_flat_map(self) -> None:
        """Ok.flat_map 链式操作。/ Ok.flat_map chains."""
        result = Ok(5).flat_map(lambda x: Ok(x * 3))
        assert isinstance(result, Ok)
        assert result.value == 15

    def test_flat_map_to_failed(self) -> None:
        """Ok.flat_map 可转为 Failed。/ Ok.flat_map can produce Failed."""
        result: Result[int] = Ok(5).flat_map(lambda x: Failed(_error=_err()))
        assert isinstance(result, Failed)

    def test_unwrap_or(self) -> None:
        """Ok.unwrap_or 返回值。/ Ok.unwrap_or returns value."""
        assert Ok(42).unwrap_or(0) == 42

    def test_on_failure_not_called(self) -> None:
        """Ok.on_failure 不调用回调。/ Ok.on_failure does not call callback."""
        log: list[str] = []
        Ok(5).on_failure(lambda e: log.append("called"))
        assert log == []

    def test_on_success_called(self) -> None:
        """Ok.on_success 调用回调。/ Ok.on_success calls callback."""
        log: list[int] = []
        Ok(5).on_success(lambda x: log.append(x))
        assert log == [5]

    def test_is_ok(self) -> None:
        """Ok.is_ok 返回 True。/ Ok.is_ok returns True."""
        assert Ok(1).is_ok() is True

    def test_is_failed(self) -> None:
        """Ok.is_failed 返回 False。/ Ok.is_failed returns False."""
        assert Ok(1).is_failed() is False


class TestFailedBehavior:
    """Failed 行为测试。/ Failed behavioral tests."""

    def test_map_short_circuits(self) -> None:
        """Failed.map 短路。/ Failed.map short-circuits."""
        f: Result[int] = Failed(_error=_err())
        result = f.map(lambda x: x * 2)
        assert isinstance(result, Failed)

    def test_map_err(self) -> None:
        """Failed.map_err 变换错误。/ Failed.map_err transforms error."""
        f: Result[int] = Failed(_error=_err(ErrorCode.NOT_FOUND, "old"))
        result = f.map_err(lambda e: _err(ErrorCode.TIMEOUT, "new"))
        assert isinstance(result, Failed)
        assert result.error.code is ErrorCode.TIMEOUT

    def test_flat_map_short_circuits(self) -> None:
        """Failed.flat_map 短路。/ Failed.flat_map short-circuits."""
        f: Result[int] = Failed(_error=_err())
        result = f.flat_map(lambda x: Ok(x * 2))
        assert isinstance(result, Failed)

    def test_unwrap_raises(self) -> None:
        """Failed.unwrap 抛异常。/ Failed.unwrap raises."""
        with pytest.raises(RuntimeError, match="unwrap"):
            Failed(_error=_err()).unwrap()

    def test_unwrap_or_returns_default(self) -> None:
        """Failed.unwrap_or 返回默认值。/ Failed.unwrap_or returns default."""
        f: Result[int] = Failed(_error=_err())
        assert f.unwrap_or(99) == 99

    def test_on_failure_called(self) -> None:
        """Failed.on_failure 调用回调。/ Failed.on_failure calls callback."""
        log: list[str] = []
        Failed(_error=_err(msg="test")).on_failure(lambda e: log.append(e.message))
        assert log == ["test"]

    def test_on_success_not_called(self) -> None:
        """Failed.on_success 不调用回调。/ Failed.on_success does not call."""
        log: list[str] = []
        Failed(_error=_err()).on_success(lambda x: log.append("called"))
        assert log == []

    def test_is_ok(self) -> None:
        """Failed.is_ok 返回 False。/ Failed.is_ok returns False."""
        assert Failed(_error=_err()).is_ok() is False

    def test_is_failed(self) -> None:
        """Failed.is_failed 返回 True。/ Failed.is_failed returns True."""
        assert Failed(_error=_err()).is_failed() is True


class TestFatalBehavior:
    """Fatal 行为测试。/ Fatal behavioral tests."""

    def test_map_short_circuits(self) -> None:
        """Fatal.map 短路。/ Fatal.map short-circuits."""
        f: Result[int] = Fatal(_errors=(_err(),))
        result = f.map(lambda x: x * 2)
        assert isinstance(result, Fatal)

    def test_map_err(self) -> None:
        """Fatal.map_err 变换所有错误。/ Fatal.map_err transforms all errors."""
        e1 = _err(ErrorCode.NOT_FOUND, "e1")
        e2 = _err(ErrorCode.TIMEOUT, "e2")
        f: Result[int] = Fatal(_errors=(e1, e2))
        result = f.map_err(lambda e: _err(e.code, "mapped"))
        assert isinstance(result, Fatal)
        assert len(result.errors) == 2
        assert result.errors[0].message == "mapped"
        assert result.errors[1].message == "mapped"

    def test_flat_map_short_circuits(self) -> None:
        """Fatal.flat_map 短路。/ Fatal.flat_map short-circuits."""
        f: Result[int] = Fatal(_errors=(_err(),))
        result = f.flat_map(lambda x: Ok(x * 2))
        assert isinstance(result, Fatal)

    def test_unwrap_raises(self) -> None:
        """Fatal.unwrap 抛异常。/ Fatal.unwrap raises."""
        with pytest.raises(RuntimeError, match="Fatal"):
            Fatal(_errors=(_err(),)).unwrap()

    def test_unwrap_or_returns_default(self) -> None:
        """Fatal.unwrap_or 返回默认值。/ Fatal.unwrap_or returns default."""
        f: Result[int] = Fatal(_errors=(_err(),))
        assert f.unwrap_or(99) == 99

    def test_on_failure_called_for_each_error(self) -> None:
        """Fatal.on_failure 对每个错误调用回调。/ Fatal.on_failure calls for each error."""
        e1 = _err(ErrorCode.NOT_FOUND, "e1")
        e2 = _err(ErrorCode.TIMEOUT, "e2")
        log: list[str] = []
        Fatal(_errors=(e1, e2)).on_failure(lambda e: log.append(e.message))
        assert log == ["e1", "e2"]

    def test_on_success_not_called(self) -> None:
        """Fatal.on_success 不调用回调。/ Fatal.on_success does not call."""
        log: list[str] = []
        Fatal(_errors=(_err(),)).on_success(lambda x: log.append("called"))
        assert log == []

    def test_errors_property(self) -> None:
        """Fatal.errors 属性。/ Fatal.errors property."""
        e1 = _err(ErrorCode.NOT_FOUND, "e1")
        f = Fatal(_errors=(e1,))
        assert len(f.errors) == 1
        assert f.errors[0].code is ErrorCode.NOT_FOUND

    def test_is_ok(self) -> None:
        """Fatal.is_ok 返回 False。/ Fatal.is_ok returns False."""
        assert Fatal(_errors=(_err(),)).is_ok() is False

    def test_is_failed(self) -> None:
        """Fatal.is_failed 返回 True。/ Fatal.is_failed returns True."""
        assert Fatal(_errors=(_err(),)).is_failed() is True


class TestSuccessBehavior:
    """Success 行为测试。/ Success behavioral tests."""

    def test_map(self) -> None:
        """Success.map 变换。/ Success.map transforms."""
        result = Success().map(lambda x: 42)
        assert isinstance(result, Ok)
        assert result.value == 42

    def test_map_err_returns_self(self) -> None:
        """Success.map_err 返回自身。/ Success.map_err returns self."""
        s = Success()
        result = s.map_err(lambda e: e)
        assert isinstance(result, Success)

    def test_flat_map(self) -> None:
        """Success.flat_map 链式操作。/ Success.flat_map chains."""
        result = Success().flat_map(lambda x: Ok(42))
        assert isinstance(result, Ok)
        assert result.value == 42

    def test_unwrap_returns_none(self) -> None:
        """Success.unwrap 返回 None。/ Success.unwrap returns None."""
        assert Success().unwrap() is None

    def test_unwrap_or_returns_none(self) -> None:
        """Success.unwrap_or 返回 None。/ Success.unwrap_or returns None."""
        assert Success().unwrap_or(None) is None

    def test_on_failure_not_called(self) -> None:
        """Success.on_failure 不调用回调。/ Success.on_failure does not call."""
        log: list[str] = []
        Success().on_failure(lambda e: log.append("called"))
        assert log == []

    def test_on_success_called(self) -> None:
        """Success.on_success 调用回调。/ Success.on_success calls callback."""
        log: list[object] = []
        Success().on_success(lambda x: log.append(x))
        assert log == [None]


class TestWarnBehavior:
    """Warn 行为测试。/ Warn behavioral tests."""

    def test_value_and_warning(self) -> None:
        """Warn 包含值和警告。/ Warn has value and warning."""
        w = Warn(_value=5, _warning=_err(ErrorCode.TIMEOUT, "slow"))
        assert w.value == 5
        assert w.warning.code is ErrorCode.TIMEOUT

    def test_is_ok(self) -> None:
        """Warn.is_ok 返回 True。/ Warn.is_ok returns True."""
        w = Warn(_value=5, _warning=_err())
        assert w.is_ok() is True

    def test_is_failed(self) -> None:
        """Warn.is_failed 返回 False。/ Warn.is_failed returns False."""
        w = Warn(_value=5, _warning=_err())
        assert w.is_failed() is False

    def test_is_warn(self) -> None:
        """Warn.is_warn 返回 True。/ Warn.is_warn returns True."""
        w = Warn(_value=5, _warning=_err())
        assert w.is_warn() is True

    def test_map_preserves_warning(self) -> None:
        """Warn.map 保留警告。/ Warn.map preserves warning."""
        w = Warn(_value=5, _warning=_err(ErrorCode.TIMEOUT, "slow"))
        result = w.map(lambda x: x * 2)
        assert isinstance(result, Warn)
        assert result.value == 10
        assert result.warning.code is ErrorCode.TIMEOUT

    def test_map_err_transforms_warning(self) -> None:
        """Warn.map_err 变换警告。/ Warn.map_err transforms warning."""
        w = Warn(_value=5, _warning=_err(ErrorCode.TIMEOUT, "old"))
        result = w.map_err(lambda e: _err(ErrorCode.OVERFLOW, "new"))
        assert isinstance(result, Warn)
        assert result.value == 5
        assert result.warning.code is ErrorCode.OVERFLOW

    def test_flat_map_delegates(self) -> None:
        """Warn.flat_map 委托到函数。/ Warn.flat_map delegates."""
        w = Warn(_value=5, _warning=_err())
        result = w.flat_map(lambda x: Ok(x * 3))
        assert isinstance(result, Ok)
        assert result.value == 15

    def test_unwrap_returns_value(self) -> None:
        """Warn.unwrap 返回值。/ Warn.unwrap returns value."""
        w = Warn(_value=7, _warning=_err())
        assert w.unwrap() == 7

    def test_unwrap_or_returns_value(self) -> None:
        """Warn.unwrap_or 返回值。/ Warn.unwrap_or returns value."""
        w = Warn(_value=7, _warning=_err())
        assert w.unwrap_or(0) == 7

    def test_on_failure_not_called(self) -> None:
        """Warn.on_failure 不调用回调。/ Warn.on_failure does not call."""
        log: list[str] = []
        Warn(_value=5, _warning=_err()).on_failure(lambda e: log.append("called"))
        assert log == []

    def test_on_success_called(self) -> None:
        """Warn.on_success 调用回调。/ Warn.on_success calls callback."""
        log: list[int] = []
        Warn(_value=5, _warning=_err()).on_success(lambda x: log.append(x))
        assert log == [5]


class TestFailedFromCode:
    """failed_from_code 工厂函数测试。/ failed_from_code factory tests."""

    def test_creates_failed_with_err(self) -> None:
        """failed_from_code 创建 Failed(Err)。/ Creates Failed with Err."""
        result = failed_from_code(ErrorCode.NOT_FOUND, "not here")
        assert isinstance(result, Failed)
        assert result.error.code is ErrorCode.NOT_FOUND
        assert result.error.message == "not here"

    def test_different_error_codes(self) -> None:
        """不同错误码。/ Different error codes."""
        result = failed_from_code(ErrorCode.TIMEOUT, "timed out")
        assert isinstance(result, Failed)
        assert result.error.code is ErrorCode.TIMEOUT
