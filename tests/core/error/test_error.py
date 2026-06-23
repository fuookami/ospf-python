"""Tests for ospf_python.core.error module."""

from ospf_python.core.error import CoreErrorCode


class TestCoreErrorCode:
    """Tests for CoreErrorCode."""

    def test_variable_errors(self) -> None:
        """Test variable error codes."""
        assert CoreErrorCode.VARIABLE_NOT_FOUND is not None
        assert CoreErrorCode.VARIABLE_ALREADY_EXISTS is not None
        assert CoreErrorCode.VARIABLE_INVALID_BOUNDS is not None

    def test_model_errors(self) -> None:
        """Test model error codes."""
        assert CoreErrorCode.MODEL_NOT_SOLVED is not None
        assert CoreErrorCode.MODEL_INFEASIBLE is not None
        assert CoreErrorCode.MODEL_UNBOUNDED is not None
        assert CoreErrorCode.MODEL_ERROR is not None

    def test_constraint_errors(self) -> None:
        """Test constraint error codes."""
        assert CoreErrorCode.CONSTRAINT_NOT_FOUND is not None
        assert CoreErrorCode.CONSTRAINT_INVALID is not None

    def test_objective_errors(self) -> None:
        """Test objective error codes."""
        assert CoreErrorCode.OBJECTIVE_NOT_SET is not None
        assert CoreErrorCode.OBJECTIVE_INVALID is not None

    def test_solver_errors(self) -> None:
        """Test solver error codes."""
        assert CoreErrorCode.SOLVER_NOT_AVAILABLE is not None
        assert CoreErrorCode.SOLVER_ERROR is not None
        assert CoreErrorCode.SOLVER_TIMEOUT is not None

    def test_token_errors(self) -> None:
        """Test token error codes."""
        assert CoreErrorCode.TOKEN_NOT_FOUND is not None
        assert CoreErrorCode.TOKEN_INVALID is not None

    def test_values(self) -> None:
        """Test error code values."""
        assert CoreErrorCode.VARIABLE_NOT_FOUND.value == "VARIABLE_NOT_FOUND"
        assert CoreErrorCode.MODEL_INFEASIBLE.value == "MODEL_INFEASIBLE"
