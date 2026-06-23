"""Tests for ospf_python.utils.error module."""

from ospf_python.utils.error import (
    Err,
    Error,
    ErrorCode,
    ExErr,
    LazyErr,
)


class TestErrorCode:
    """Tests for ErrorCode enumeration."""

    def test_error_codes_exist(self) -> None:
        """Verify all standard error codes exist."""
        assert ErrorCode.ILLEGAL_ARGUMENT is not None
        assert ErrorCode.ILLEGAL_STATE is not None
        assert ErrorCode.NOT_FOUND is not None
        assert ErrorCode.NOT_IMPLEMENTED is not None
        assert ErrorCode.NOT_SUPPORTED is not None
        assert ErrorCode.APPLICATION_FAILED is not None
        assert ErrorCode.APPLICATION_ERROR is not None
        assert ErrorCode.DATA_CORRUPTED is not None
        assert ErrorCode.DATA_CONFLICT is not None
        assert ErrorCode.DATA_MISSING is not None
        assert ErrorCode.IO_ERROR is not None
        assert ErrorCode.NETWORK_ERROR is not None
        assert ErrorCode.TIMEOUT is not None
        assert ErrorCode.SOLVER_ERROR is not None
        assert ErrorCode.SOLVER_INFEASIBLE is not None
        assert ErrorCode.SOLVER_UNBOUNDED is not None
        assert ErrorCode.SOLVER_TIMEOUT is not None
        assert ErrorCode.OTHER is not None

    def test_error_code_values(self) -> None:
        """Verify error code string values."""
        assert ErrorCode.ILLEGAL_ARGUMENT.value == "ILLEGAL_ARGUMENT"
        assert ErrorCode.APPLICATION_FAILED.value == "APPLICATION_FAILED"
        assert ErrorCode.SOLVER_ERROR.value == "SOLVER_ERROR"

    def test_error_code_unique(self) -> None:
        """Verify all error codes are unique."""
        values = [code.value for code in ErrorCode]
        assert len(values) == len(set(values))


class TestError:
    """Tests for Error base class."""

    def test_error_creation(self) -> None:
        """Test creating an Error."""
        error = Error(ErrorCode.ILLEGAL_ARGUMENT, "Invalid input")
        assert error.code == ErrorCode.ILLEGAL_ARGUMENT
        assert error.message == "Invalid input"

    def test_error_equality(self) -> None:
        """Test Error equality."""
        error1 = Error(ErrorCode.ILLEGAL_ARGUMENT, "Invalid input")
        error2 = Error(ErrorCode.ILLEGAL_ARGUMENT, "Invalid input")
        error3 = Error(ErrorCode.NOT_FOUND, "Not found")
        assert error1 == error2
        assert error1 != error3

    def test_error_hash(self) -> None:
        """Test Error hashing."""
        error1 = Error(ErrorCode.ILLEGAL_ARGUMENT, "Invalid input")
        error2 = Error(ErrorCode.ILLEGAL_ARGUMENT, "Invalid input")
        assert hash(error1) == hash(error2)

    def test_error_repr(self) -> None:
        """Test Error repr."""
        error = Error(ErrorCode.ILLEGAL_ARGUMENT, "Invalid input")
        assert "ILLEGAL_ARGUMENT" in repr(error)
        assert "Invalid input" in repr(error)

    def test_error_str(self) -> None:
        """Test Error string representation."""
        error = Error(ErrorCode.ILLEGAL_ARGUMENT, "Invalid input")
        assert str(error) == "[ILLEGAL_ARGUMENT] Invalid input"


class TestErr:
    """Tests for Err class."""

    def test_err_creation(self) -> None:
        """Test creating an Err."""
        err = Err(ErrorCode.NOT_FOUND, "Resource not found")
        assert err.code == ErrorCode.NOT_FOUND
        assert err.message == "Resource not found"

    def test_err_is_error(self) -> None:
        """Test Err is instance of Error."""
        err = Err(ErrorCode.NOT_FOUND, "Resource not found")
        assert isinstance(err, Error)


class TestLazyErr:
    """Tests for LazyErr class."""

    def test_lazy_err_creation(self) -> None:
        """Test creating a LazyErr."""
        called = False

        def message_fn() -> str:
            nonlocal called
            called = True
            return "Lazy message"

        err = LazyErr(ErrorCode.APPLICATION_ERROR, message_fn)
        assert not called  # Message not computed yet
        assert err.message == "Lazy message"
        assert called  # Message computed on access

    def test_lazy_err_caches_message(self) -> None:
        """Test LazyErr caches the computed message."""
        call_count = 0

        def message_fn() -> str:
            nonlocal call_count
            call_count += 1
            return f"Message {call_count}"

        err = LazyErr(ErrorCode.APPLICATION_ERROR, message_fn)
        _ = err.message
        _ = err.message
        assert call_count == 1  # Only called once


class TestExErr:
    """Tests for ExErr class."""

    def test_ex_err_creation(self) -> None:
        """Test creating an ExErr."""
        err = ExErr(ErrorCode.DATA_CORRUPTED, "Data corrupted", {"field": "value"})
        assert err.code == ErrorCode.DATA_CORRUPTED
        assert err.message == "Data corrupted"
        assert err.value == {"field": "value"}

    def test_ex_err_is_error(self) -> None:
        """Test ExErr is instance of Error."""
        err = ExErr(ErrorCode.DATA_CORRUPTED, "Data corrupted", None)
        assert isinstance(err, Error)

    def test_ex_err_repr(self) -> None:
        """Test ExErr repr."""
        err = ExErr(ErrorCode.DATA_CORRUPTED, "Data corrupted", 42)
        assert "DATA_CORRUPTED" in repr(err)
        assert "42" in repr(err)

    def test_ex_err_str(self) -> None:
        """Test ExErr string representation."""
        err = ExErr(ErrorCode.DATA_CORRUPTED, "Data corrupted", 42)
        assert str(err) == "[DATA_CORRUPTED] Data corrupted (value=42)"
