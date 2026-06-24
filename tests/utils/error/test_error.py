"""Error 层次结构测试。

测试 ErrorCode 枚举、Error 抽象基类及其实现：
Err、LazyErr、ExErr、LazyExErr、ApplicationException。
"""

from __future__ import annotations

import pytest

from ospf_python.utils.error import (
    ApplicationException,
    Err,
    Error,
    ErrorCode,
    ExErr,
    LazyErr,
    LazyExErr,
)

# ---------------------------------------------------------------------------
# ErrorCode 测试
# ---------------------------------------------------------------------------


class TestErrorCode:
    """ErrorCode 枚举基本行为测试。"""

    def test_success_code_value_is_zero(self) -> None:
        assert ErrorCode.SUCCESS.value == 0

    def test_application_error_code_value_is_one(self) -> None:
        assert ErrorCode.APPLICATION_ERROR.value == 1

    def test_all_codes_have_unique_values(self) -> None:
        values = [e.value for e in ErrorCode]
        assert len(values) == len(set(values))

    def test_code_from_value(self) -> None:
        assert ErrorCode(0) is ErrorCode.SUCCESS
        assert ErrorCode(6) is ErrorCode.NOT_FOUND

    def test_code_name_attribute(self) -> None:
        assert ErrorCode.ILLEGAL_ARGUMENT.name == "ILLEGAL_ARGUMENT"

    def test_invalid_code_value_raises(self) -> None:
        with pytest.raises(ValueError):
            ErrorCode(999)

    def test_solver_error_codes_start_at_100(self) -> None:
        solver_codes = [
            ErrorCode.OPTIMIZATION_ERROR,
            ErrorCode.SOLVER_NOT_AVAILABLE,
            ErrorCode.MODEL_BUILD_FAILED,
            ErrorCode.SOLVE_FAILED,
            ErrorCode.NO_SOLUTION,
        ]
        for code in solver_codes:
            assert code.value >= 100

    def test_code_is_enum_member(self) -> None:
        assert isinstance(ErrorCode.TIMEOUT, ErrorCode)


# ---------------------------------------------------------------------------
# Err 测试
# ---------------------------------------------------------------------------


class TestErr:
    """Err 基本错误类型测试。"""

    def test_create_err(self) -> None:
        err = Err(
            _code=ErrorCode.ILLEGAL_ARGUMENT,
            _message="bad input",
        )
        assert err.code is ErrorCode.ILLEGAL_ARGUMENT
        assert err.message == "bad input"

    def test_err_str_format(self) -> None:
        err = Err(
            _code=ErrorCode.NOT_FOUND,
            _message="item missing",
        )
        assert str(err) == "[NOT_FOUND] item missing"

    def test_err_is_frozen(self) -> None:
        err = Err(
            _code=ErrorCode.TIMEOUT,
            _message="timed out",
        )
        with pytest.raises(AttributeError):
            err._message = "changed"  # type: ignore[misc]

    def test_err_equality(self) -> None:
        err1 = Err(
            _code=ErrorCode.NOT_FOUND,
            _message="x",
        )
        err2 = Err(
            _code=ErrorCode.NOT_FOUND,
            _message="x",
        )
        assert err1 == err2

    def test_err_inequality_different_code(self) -> None:
        err1 = Err(
            _code=ErrorCode.NOT_FOUND,
            _message="x",
        )
        err2 = Err(
            _code=ErrorCode.TIMEOUT,
            _message="x",
        )
        assert err1 != err2

    def test_err_inequality_different_message(self) -> None:
        err1 = Err(
            _code=ErrorCode.NOT_FOUND,
            _message="a",
        )
        err2 = Err(
            _code=ErrorCode.NOT_FOUND,
            _message="b",
        )
        assert err1 != err2

    def test_err_is_error_subclass(self) -> None:
        err = Err(
            _code=ErrorCode.SUCCESS,
            _message="ok",
        )
        assert isinstance(err, Error)


# ---------------------------------------------------------------------------
# LazyErr 测试
# ---------------------------------------------------------------------------


class TestLazyErr:
    """LazyErr 惰性错误类型测试。"""

    def test_message_is_lazily_evaluated(self) -> None:
        call_count = 0

        def compute() -> str:
            nonlocal call_count
            call_count += 1
            return "lazy msg"

        err = LazyErr(
            _code=ErrorCode.OVERFLOW,
            _message_fn=compute,
        )
        assert call_count == 0
        assert err.message == "lazy msg"
        assert call_count == 1

    def test_str_triggers_lazy_evaluation(self) -> None:
        err = LazyErr(
            _code=ErrorCode.UNDERFLOW,
            _message_fn=lambda: "computed",
        )
        assert str(err) == "[UNDERFLOW] computed"

    def test_lazy_err_is_frozen(self) -> None:
        err = LazyErr(
            _code=ErrorCode.TIMEOUT,
            _message_fn=lambda: "t",
        )
        with pytest.raises(AttributeError):
            err._code = ErrorCode.SUCCESS  # type: ignore[misc]

    def test_lazy_err_is_error_subclass(self) -> None:
        err = LazyErr(
            _code=ErrorCode.CANCELLED,
            _message_fn=lambda: "c",
        )
        assert isinstance(err, Error)


# ---------------------------------------------------------------------------
# ExErr 测试
# ---------------------------------------------------------------------------


class TestExErr:
    """ExErr 附带值错误类型测试。"""

    def test_create_ex_err_with_value(self) -> None:
        err = ExErr(
            _code=ErrorCode.NOT_FOUND,
            _message="missing key",
            value="abc",
        )
        assert err.code is ErrorCode.NOT_FOUND
        assert err.message == "missing key"
        assert err.value == "abc"

    def test_ex_err_with_numeric_value(self) -> None:
        err = ExErr(
            _code=ErrorCode.OUT_OF_RANGE,
            _message="index out of bounds",
            value=42,
        )
        assert err.value == 42

    def test_ex_err_str_format(self) -> None:
        err = ExErr(
            _code=ErrorCode.ALREADY_EXIST,
            _message="duplicate",
            value=None,
        )
        assert str(err) == "[ALREADY_EXIST] duplicate"

    def test_ex_err_is_error_subclass(self) -> None:
        err = ExErr(
            _code=ErrorCode.NOT_FOUND,
            _message="m",
            value=0,
        )
        assert isinstance(err, Error)

    def test_ex_err_equality(self) -> None:
        err1 = ExErr(
            _code=ErrorCode.NOT_FOUND,
            _message="m",
            value=10,
        )
        err2 = ExErr(
            _code=ErrorCode.NOT_FOUND,
            _message="m",
            value=10,
        )
        assert err1 == err2


# ---------------------------------------------------------------------------
# LazyExErr 测试
# ---------------------------------------------------------------------------


class TestLazyExErr:
    """LazyExErr 惰性附带值错误类型测试。"""

    def test_message_lazily_evaluated_with_value(self) -> None:
        call_count = 0

        def compute() -> str:
            nonlocal call_count
            call_count += 1
            return "lazy ex"

        err = LazyExErr(
            _code=ErrorCode.RESOURCE_EXHAUSTED,
            _message_fn=compute,
            value=[1, 2, 3],
        )
        assert call_count == 0
        assert err.message == "lazy ex"
        assert err.value == [1, 2, 3]
        assert call_count == 1

    def test_lazy_ex_err_str(self) -> None:
        err = LazyExErr(
            _code=ErrorCode.DATA_LOSS,
            _message_fn=lambda: "lost",
            value=0,
        )
        assert str(err) == "[DATA_LOSS] lost"

    def test_lazy_ex_err_is_error_subclass(self) -> None:
        err = LazyExErr(
            _code=ErrorCode.ABORTED,
            _message_fn=lambda: "a",
            value=None,
        )
        assert isinstance(err, Error)


# ---------------------------------------------------------------------------
# ApplicationException 测试
# ---------------------------------------------------------------------------


class TestApplicationException:
    """ApplicationException 应用级异常测试。"""

    def test_create_application_exception(self) -> None:
        exc = ApplicationException(
            _code=ErrorCode.APPLICATION_ERROR,
            _message="something broke",
        )
        assert exc.code is ErrorCode.APPLICATION_ERROR
        assert exc.message == "something broke"

    def test_str_format(self) -> None:
        exc = ApplicationException(
            _code=ErrorCode.PERMISSION_DENIED,
            _message="no access",
        )
        assert str(exc) == "[PERMISSION_DENIED] no access"

    def test_is_error_subclass(self) -> None:
        exc = ApplicationException(
            _code=ErrorCode.UNAUTHENTICATED,
            _message="login required",
        )
        assert isinstance(exc, Error)

    def test_is_frozen(self) -> None:
        exc = ApplicationException(
            _code=ErrorCode.FAILED_PRECONDITION,
            _message="precondition",
        )
        with pytest.raises(AttributeError):
            exc._message = "changed"  # type: ignore[misc]

    def test_equality(self) -> None:
        exc1 = ApplicationException(
            _code=ErrorCode.PARSING_FAILED,
            _message="bad json",
        )
        exc2 = ApplicationException(
            _code=ErrorCode.PARSING_FAILED,
            _message="bad json",
        )
        assert exc1 == exc2
