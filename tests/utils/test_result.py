"""Tests for ospf_python.utils.result module."""

import pytest

from ospf_python.utils.error import Err, ErrorCode, ExErr
from ospf_python.utils.result import (
    Failed,
    Fatal,
    Ok,
    Warn,
    failed,
    fatal,
    ok,
    pipe,
    run,
    warn,
)


class TestOk:
    """Tests for Ok result."""

    def test_ok_creation(self) -> None:
        """Test creating an Ok result."""
        result = ok(42)
        assert result.value == 42

    def test_ok_is_ok(self) -> None:
        """Test Ok.is_ok() returns True."""
        result = ok(42)
        assert result.is_ok() is True
        assert result.is_failed() is False

    def test_ok_map(self) -> None:
        """Test Ok.map() transforms value."""
        result = ok(42)
        mapped = result.map(lambda x: x * 2)
        assert isinstance(mapped, Ok)
        assert mapped.value == 84

    def test_ok_map_error(self) -> None:
        """Test Ok.map_error() is no-op."""
        result = ok(42)
        mapped = result.map_error(lambda e: Err(ErrorCode.OTHER, "transformed"))
        assert mapped is result

    def test_ok_on_failure(self) -> None:
        """Test Ok.on_failure() is no-op."""
        called = False

        def side_effect(error):
            nonlocal called
            called = True

        result = ok(42)
        returned = result.on_failure(side_effect)
        assert not called
        assert returned is result

    def test_ok_unwrap(self) -> None:
        """Test Ok.unwrap() returns value."""
        result = ok(42)
        assert result.unwrap() == 42

    def test_ok_unwrap_or(self) -> None:
        """Test Ok.unwrap_or() returns value."""
        result = ok(42)
        assert result.unwrap_or(0) == 42

    def test_ok_repr(self) -> None:
        """Test Ok repr."""
        result = ok(42)
        assert repr(result) == "Ok(42)"


class TestFailed:
    """Tests for Failed result."""

    def test_failed_creation(self) -> None:
        """Test creating a Failed result."""
        error = Err(ErrorCode.ILLEGAL_ARGUMENT, "Invalid input")
        result = failed(error)
        assert result.error is error

    def test_failed_is_failed(self) -> None:
        """Test Failed.is_failed() returns True."""
        error = Err(ErrorCode.ILLEGAL_ARGUMENT, "Invalid input")
        result = failed(error)
        assert result.is_ok() is False
        assert result.is_failed() is True

    def test_failed_map(self) -> None:
        """Test Failed.map() is no-op."""
        error = Err(ErrorCode.ILLEGAL_ARGUMENT, "Invalid input")
        result = failed(error)
        mapped = result.map(lambda x: x * 2)
        assert mapped is result

    def test_failed_map_error(self) -> None:
        """Test Failed.map_error() transforms error."""
        error = Err(ErrorCode.ILLEGAL_ARGUMENT, "Invalid input")
        result = failed(error)
        mapped = result.map_error(lambda e: Err(ErrorCode.NOT_FOUND, "Not found"))
        assert isinstance(mapped, Failed)
        assert mapped.error.code == ErrorCode.NOT_FOUND

    def test_failed_on_failure(self) -> None:
        """Test Failed.on_failure() calls side effect."""
        captured_error = None

        def side_effect(error):
            nonlocal captured_error
            captured_error = error

        error = Err(ErrorCode.ILLEGAL_ARGUMENT, "Invalid input")
        result = failed(error)
        returned = result.on_failure(side_effect)
        assert captured_error is error
        assert returned is result

    def test_failed_unwrap_raises(self) -> None:
        """Test Failed.unwrap() raises ValueError."""
        error = Err(ErrorCode.ILLEGAL_ARGUMENT, "Invalid input")
        result = failed(error)
        with pytest.raises(ValueError, match="Unwrap failed"):
            result.unwrap()

    def test_failed_unwrap_or(self) -> None:
        """Test Failed.unwrap_or() returns default."""
        error = Err(ErrorCode.ILLEGAL_ARGUMENT, "Invalid input")
        result = failed(error)
        assert result.unwrap_or(0) == 0

    def test_failed_repr(self) -> None:
        """Test Failed repr."""
        error = Err(ErrorCode.ILLEGAL_ARGUMENT, "Invalid input")
        result = failed(error)
        assert "ILLEGAL_ARGUMENT" in repr(result)


class TestFatal:
    """Tests for Fatal result."""

    def test_fatal_creation(self) -> None:
        """Test creating a Fatal result."""
        error1 = Err(ErrorCode.ILLEGAL_ARGUMENT, "Error 1")
        error2 = Err(ErrorCode.NOT_FOUND, "Error 2")
        result = fatal([error1, error2])
        assert len(result.errors) == 2

    def test_fatal_is_failed(self) -> None:
        """Test Fatal.is_failed() returns True."""
        error = Err(ErrorCode.ILLEGAL_ARGUMENT, "Error")
        result = fatal([error])
        assert result.is_ok() is False
        assert result.is_failed() is True

    def test_fatal_map(self) -> None:
        """Test Fatal.map() is no-op."""
        error = Err(ErrorCode.ILLEGAL_ARGUMENT, "Error")
        result = fatal([error])
        mapped = result.map(lambda x: x * 2)
        assert mapped is result

    def test_fatal_map_error(self) -> None:
        """Test Fatal.map_error() transforms all errors."""
        error1 = Err(ErrorCode.ILLEGAL_ARGUMENT, "Error 1")
        error2 = Err(ErrorCode.NOT_FOUND, "Error 2")
        result = fatal([error1, error2])
        mapped = result.map_error(
            lambda e: Err(ErrorCode.OTHER, f"Transformed: {e.message}")
        )
        assert isinstance(mapped, Fatal)
        assert len(mapped.errors) == 2
        assert all(e.code == ErrorCode.OTHER for e in mapped.errors)

    def test_fatal_on_failure(self) -> None:
        """Test Fatal.on_failure() calls side effect for each error."""
        captured_errors = []

        def side_effect(error):
            captured_errors.append(error)

        error1 = Err(ErrorCode.ILLEGAL_ARGUMENT, "Error 1")
        error2 = Err(ErrorCode.NOT_FOUND, "Error 2")
        result = fatal([error1, error2])
        returned = result.on_failure(side_effect)
        assert len(captured_errors) == 2
        assert returned is result

    def test_fatal_unwrap_raises(self) -> None:
        """Test Fatal.unwrap() raises ValueError."""
        error = Err(ErrorCode.ILLEGAL_ARGUMENT, "Error")
        result = fatal([error])
        with pytest.raises(ValueError, match="Unwrap fatal"):
            result.unwrap()

    def test_fatal_unwrap_or(self) -> None:
        """Test Fatal.unwrap_or() returns default."""
        error = Err(ErrorCode.ILLEGAL_ARGUMENT, "Error")
        result = fatal([error])
        assert result.unwrap_or(0) == 0


class TestWarn:
    """Tests for Warn result."""

    def test_warn_creation(self) -> None:
        """Test creating a Warn result."""
        warning = Err(ErrorCode.OTHER, "Warning message")
        result = warn(42, warning)
        assert result.value == 42
        assert result.warning is warning

    def test_warn_is_ok(self) -> None:
        """Test Warn.is_ok() returns True."""
        warning = Err(ErrorCode.OTHER, "Warning message")
        result = warn(42, warning)
        assert result.is_ok() is True
        assert result.is_failed() is False

    def test_warn_map(self) -> None:
        """Test Warn.map() transforms value."""
        warning = Err(ErrorCode.OTHER, "Warning message")
        result = warn(42, warning)
        mapped = result.map(lambda x: x * 2)
        assert isinstance(mapped, Warn)
        assert mapped.value == 84
        assert mapped.warning is warning

    def test_warn_map_error(self) -> None:
        """Test Warn.map_error() transforms warning."""
        warning = Err(ErrorCode.OTHER, "Warning message")
        result = warn(42, warning)
        mapped = result.map_error(lambda e: Err(ErrorCode.OTHER, "Transformed"))
        assert isinstance(mapped, Warn)
        assert mapped.value == 42
        assert mapped.warning.message == "Transformed"

    def test_warn_on_failure(self) -> None:
        """Test Warn.on_failure() calls side effect with warning."""
        captured_warning = None

        def side_effect(error):
            nonlocal captured_warning
            captured_warning = error

        warning = Err(ErrorCode.OTHER, "Warning message")
        result = warn(42, warning)
        returned = result.on_failure(side_effect)
        assert captured_warning is warning
        assert returned is result

    def test_warn_unwrap(self) -> None:
        """Test Warn.unwrap() returns value."""
        warning = Err(ErrorCode.OTHER, "Warning message")
        result = warn(42, warning)
        assert result.unwrap() == 42

    def test_warn_unwrap_or(self) -> None:
        """Test Warn.unwrap_or() returns value."""
        warning = Err(ErrorCode.OTHER, "Warning message")
        result = warn(42, warning)
        assert result.unwrap_or(0) == 42


class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_ok_factory(self) -> None:
        """Test ok factory function."""
        result = ok(42)
        assert isinstance(result, Ok)
        assert result.value == 42

    def test_failed_factory_with_code(self) -> None:
        """Test failed factory with ErrorCode."""
        result = failed(ErrorCode.ILLEGAL_ARGUMENT, "Invalid input")
        assert isinstance(result, Failed)
        assert result.error.code == ErrorCode.ILLEGAL_ARGUMENT
        assert result.error.message == "Invalid input"

    def test_failed_factory_with_error(self) -> None:
        """Test failed factory with Error object."""
        error = Err(ErrorCode.NOT_FOUND, "Not found")
        result = failed(error)
        assert isinstance(result, Failed)
        assert result.error is error

    def test_failed_factory_with_exerr(self) -> None:
        """Test failed factory creates ExErr when value provided."""
        result = failed(ErrorCode.DATA_CORRUPTED, "Corrupted", {"field": "value"})
        assert isinstance(result, Failed)
        assert isinstance(result.error, ExErr)
        assert result.error.value == {"field": "value"}

    def test_fatal_factory_with_code(self) -> None:
        """Test fatal factory with ErrorCode."""
        result = fatal(ErrorCode.APPLICATION_ERROR, "Fatal error")
        assert isinstance(result, Fatal)
        assert len(result.errors) == 1
        assert result.errors[0].code == ErrorCode.APPLICATION_ERROR

    def test_fatal_factory_with_errors(self) -> None:
        """Test fatal factory with list of errors."""
        error1 = Err(ErrorCode.ILLEGAL_ARGUMENT, "Error 1")
        error2 = Err(ErrorCode.NOT_FOUND, "Error 2")
        result = fatal([error1, error2])
        assert isinstance(result, Fatal)
        assert len(result.errors) == 2

    def test_warn_factory(self) -> None:
        """Test warn factory function."""
        result = warn(42, ErrorCode.OTHER, "Warning")
        assert isinstance(result, Warn)
        assert result.value == 42
        assert result.warning.code == ErrorCode.OTHER

    def test_warn_factory_with_error(self) -> None:
        """Test warn factory with Error object."""
        warning = Err(ErrorCode.OTHER, "Warning")
        result = warn(42, warning)
        assert isinstance(result, Warn)
        assert result.warning is warning


class TestRun:
    """Tests for run function."""

    def test_run_all_success(self) -> None:
        """Test run with all successful operations."""
        result = run(
            lambda: ok(1),
            lambda: ok(2),
            last_block=lambda: ok(3),
        )
        assert isinstance(result, Ok)
        assert result.value == 3

    def test_run_short_circuits_on_failure(self) -> None:
        """Test run stops on first failure."""
        called = False

        def should_not_be_called():
            nonlocal called
            called = True
            return ok(3)

        result = run(
            lambda: ok(1),
            lambda: failed(ErrorCode.ILLEGAL_ARGUMENT, "Failed"),
            should_not_be_called,
            last_block=lambda: ok(4),
        )
        assert isinstance(result, Failed)
        assert not called

    def test_run_no_last_block(self) -> None:
        """Test run without last_block returns Ok(None)."""
        result = run(
            lambda: ok(1),
            lambda: ok(2),
        )
        assert isinstance(result, Ok)
        assert result.value is None


class TestPipe:
    """Tests for pipe function."""

    def test_pipe_success(self) -> None:
        """Test pipe with successful transformations."""
        result = pipe(
            ok(1),
            lambda x: ok(x + 1),
            lambda x: ok(x * 2),
            last_fn=lambda x: ok(x + 10),
        )
        assert isinstance(result, Ok)
        assert result.value == 14  # (1 + 1) * 2 + 10

    def test_pipe_short_circuits_on_failure(self) -> None:
        """Test pipe stops on first failure."""
        called = False

        def should_not_be_called(x):
            nonlocal called
            called = True
            return ok(x + 100)

        result = pipe(
            ok(1),
            lambda x: failed(ErrorCode.ILLEGAL_ARGUMENT, "Failed"),
            should_not_be_called,
            last_fn=lambda x: ok(x + 10),
        )
        assert isinstance(result, Failed)
        assert not called

    def test_pipe_initial_failure(self) -> None:
        """Test pipe with initial failure."""
        result = pipe(
            failed(ErrorCode.NOT_FOUND, "Not found"),
            lambda x: ok(x + 1),
            last_fn=lambda x: ok(x * 2),
        )
        assert isinstance(result, Failed)

    def test_pipe_no_last_fn(self) -> None:
        """Test pipe without last_fn returns last result."""
        result = pipe(
            ok(1),
            lambda x: ok(x + 1),
        )
        assert isinstance(result, Ok)
        assert result.value == 2
