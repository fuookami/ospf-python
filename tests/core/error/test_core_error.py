"""CoreErrorCode 枚举测试。

测试核心模块错误码枚举的定义、唯一性和分类。
Tests CoreErrorCode enum definition, uniqueness, and
categorization.
"""

from __future__ import annotations

import pytest

from ospf_python.core.error.core_error import CoreErrorCode


class TestCoreErrorCodeGeneral:
    """通用错误码测试 / General error code tests."""

    def test_success_value_is_zero(self) -> None:
        """成功码值为 0。/ Success code value is 0."""
        assert CoreErrorCode.SUCCESS.value == 0

    def test_application_error_value_is_one(self) -> None:
        """应用错误码值为 1。/ Application error value is 1."""
        assert CoreErrorCode.APPLICATION_ERROR.value == 1

    def test_code_from_value(self) -> None:
        """通过值获取枚举成员。/ Get enum member from value."""
        assert CoreErrorCode(0) is CoreErrorCode.SUCCESS
        assert CoreErrorCode(6) is CoreErrorCode.NOT_FOUND

    def test_code_name_attribute(self) -> None:
        """枚举名称属性正确。/ Enum name attribute is correct."""
        assert CoreErrorCode.ILLEGAL_ARGUMENT.name == "ILLEGAL_ARGUMENT"

    def test_is_enum_member(self) -> None:
        """枚举成员类型正确。/ Enum member type is correct."""
        assert isinstance(CoreErrorCode.TIMEOUT, CoreErrorCode)


class TestCoreErrorCodeUniqueness:
    """错误码唯一性测试 / Error code uniqueness tests."""

    def test_all_codes_have_unique_values(self) -> None:
        """所有错误码值唯一。/ All error code values are unique."""
        values = [e.value for e in CoreErrorCode]
        assert len(values) == len(set(values))

    def test_invalid_code_value_raises(self) -> None:
        """无效值抛出 ValueError。/ Invalid value raises ValueError."""
        with pytest.raises(ValueError):
            CoreErrorCode(9999)


class TestCoreErrorCodeDomain:
    """领域错误码测试 / Domain error code tests."""

    def test_model_error_exists(self) -> None:
        """模型错误码存在。/ Model error code exists."""
        assert CoreErrorCode.MODEL_ERROR.value == 200

    def test_variable_error_exists(self) -> None:
        """变量错误码存在。/ Variable error code exists."""
        assert CoreErrorCode.VARIABLE_ERROR.value == 201

    def test_token_error_exists(self) -> None:
        """令牌错误码存在。/ Token error code exists."""
        assert CoreErrorCode.TOKEN_ERROR.value == 202

    def test_constraint_error_exists(self) -> None:
        """约束错误码存在。/ Constraint error code exists."""
        assert CoreErrorCode.CONSTRAINT_ERROR.value == 203

    def test_solver_error_exists(self) -> None:
        """求解器错误码存在。/ Solver error code exists."""
        assert CoreErrorCode.SOLVER_ERROR.value == 204

    def test_extraction_error_exists(self) -> None:
        """提取错误码存在。/ Extraction error code exists."""
        assert CoreErrorCode.EXTRACTION_ERROR.value == 205

    def test_domain_codes_start_at_200(self) -> None:
        """领域错误码从 200 开始。/ Domain codes start at 200."""
        domain_codes = [
            CoreErrorCode.MODEL_ERROR,
            CoreErrorCode.VARIABLE_ERROR,
            CoreErrorCode.TOKEN_ERROR,
            CoreErrorCode.CONSTRAINT_ERROR,
            CoreErrorCode.SOLVER_ERROR,
            CoreErrorCode.EXTRACTION_ERROR,
        ]
        for code in domain_codes:
            assert code.value >= 200

    def test_solver_codes_range(self) -> None:
        """求解器错误码在 100-104 范围。/ Solver codes in 100-104."""
        solver_codes = [
            CoreErrorCode.OPTIMIZATION_ERROR,
            CoreErrorCode.SOLVER_NOT_AVAILABLE,
            CoreErrorCode.MODEL_BUILD_FAILED,
            CoreErrorCode.SOLVE_FAILED,
            CoreErrorCode.NO_SOLUTION,
        ]
        for code in solver_codes:
            assert 100 <= code.value <= 104
