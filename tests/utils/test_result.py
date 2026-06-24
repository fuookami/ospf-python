"""Result / ExResult 类型测试。

测试 Result、Ok、Failed、Fatal、Success、Warn 以及
ExResult 的 map、flat_map、unwrap、on_failure 等操作。
"""

from __future__ import annotations

import pytest

from ospf_python.utils.error import ErrorCode
from ospf_python.utils.functional import (
    Failed,
    Fatal,
    Ok,
    Result,
    Success,
    Warn,
)


class TestOk:
    """Ok 成功结果测试。"""

    def test_ok_is_result(self) -> None:
        assert isinstance(Ok(42), Result)

    def test_ok_value(self) -> None:
        ok = Ok(42)
        assert ok.value == 42

    def test_ok_str(self) -> None:
        assert "42" in str(Ok(42))


class TestFailed:
    """Failed 失败结果测试。"""

    def test_failed_has_error(self) -> None:
        from ospf_python.utils.error import Err

        err = Err(_code=ErrorCode.NOT_FOUND, _message="x")
        f = Failed(_error=err)
        assert f.error.code is ErrorCode.NOT_FOUND


class TestFatal:
    """Fatal 致命错误结果测试。"""

    def test_fatal_is_result(self) -> None:
        from ospf_python.utils.error import Err

        err = Err(_code=ErrorCode.DATA_LOSS, _message="fatal")
        assert isinstance(Fatal(_errors=(err,)), Result)

    def test_fatal_has_errors(self) -> None:
        from ospf_python.utils.error import Err

        err = Err(_code=ErrorCode.DATA_LOSS, _message="fatal")
        f = Fatal(_errors=(err,))
        assert len(f.errors) == 1
        assert f.errors[0].code is ErrorCode.DATA_LOSS


class TestSuccess:
    """Success 成功结果测试。"""

    def test_success_is_result(self) -> None:
        assert isinstance(Success(), Result)

    def test_success_unwrap_returns_none(self) -> None:
        assert Success().unwrap() is None


class TestWarn:
    """Warn 带警告的成功结果测试。"""

    def test_warn_has_value_and_warning(self) -> None:
        from ospf_python.utils.error import Err

        warn_err = Err(
            _code=ErrorCode.TIMEOUT,
            _message="slow",
        )
        w = Warn(_value=5, _warning=warn_err)
        assert w.value == 5
        assert w.warning.code is ErrorCode.TIMEOUT


class TestResultMap:
    """Result 的 map / flat_map 测试。"""

    def test_map_on_ok(self) -> None:
        result = Ok(5).map(lambda x: x * 2)
        assert isinstance(result, Ok)
        assert result.value == 10

    def test_map_on_failed(self) -> None:
        from ospf_python.utils.error import Err

        err = Err(_code=ErrorCode.NOT_FOUND, _message="x")
        result: Result[int] = Failed(_error=err)
        mapped = result.map(lambda x: x * 2)
        assert isinstance(mapped, Failed)


class TestResultUnwrap:
    """Result 的 unwrap 测试。"""

    def test_unwrap_ok(self) -> None:
        assert Ok(42).unwrap() == 42

    def test_unwrap_failed_raises(self) -> None:
        from ospf_python.utils.error import Err

        err = Err(_code=ErrorCode.NOT_FOUND, _message="x")
        with pytest.raises(RuntimeError):
            Failed(_error=err).unwrap()


class TestResultOnFailure:
    """Result 的 on_failure 回调测试。"""

    def test_on_failure_called_on_failed(self) -> None:
        from ospf_python.utils.error import Err

        log: list[str] = []
        err = Err(_code=ErrorCode.NOT_FOUND, _message="x")
        Failed(_error=err).on_failure(lambda e: log.append(e.message))
        assert log == ["x"]

    def test_on_failure_not_called_on_ok(self) -> None:
        log: list[str] = []
        Ok(42).on_failure(lambda e: log.append("called"))
        assert log == []
