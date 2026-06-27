"""迁移一致性测试 / Migration Consistency Tests.

验证 Python 实现与 Kotlin/Rust 行为对齐。
Verifies Python implementation aligns with Kotlin/Rust behavior.
"""

from __future__ import annotations

import pytest

from ospf_python.core.model.basic.constraint_sign import ConstraintSign
from ospf_python.core.model.basic.registration_status import RegistrationStatus
from ospf_python.core.model.mechanism.meta_model import MetaModel
from ospf_python.core.variable.any_variable import AnyVariable
from ospf_python.core.variable.type import VariableType
from ospf_python.core.variable.variable_range import VariableRange
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Ok


@pytest.mark.migration_consistency
class TestResultTypeAlignment:
    """验证 Result 类型与 Kotlin 对齐。"""

    def test_ok_creation(self) -> None:
        """Ok 创建成功。"""
        result = Ok(42)
        assert result.is_ok()
        assert not result.is_failed()
        assert result.unwrap() == 42

    def test_failed_creation(self) -> None:
        """Failed 创建失败。"""
        err = Err(ErrorCode.ILLEGAL_ARGUMENT, "test error")
        result = Failed(err)
        assert not result.is_ok()
        assert result.is_failed()

    def test_result_map(self) -> None:
        """Result map 操作。"""
        result = Ok(10)
        mapped = result.map(lambda x: x * 2)
        assert mapped.unwrap() == 20

    def test_result_flat_map(self) -> None:
        """Result flat_map 操作。"""
        result = Ok(10)
        flat_mapped = result.flat_map(lambda x: Ok(x + 5))
        assert flat_mapped.unwrap() == 15


@pytest.mark.migration_consistency
class TestMetaModelAlignment:
    """验证 MetaModel 与 Kotlin 对齐。"""

    def test_register_variable(self) -> None:
        """变量注册。"""
        model = MetaModel(name="test")
        var = AnyVariable(
            name="x",
            index=0,
            type=VariableType.CONTINUOUS,
            bounds=VariableRange(lower=0.0, upper=10.0),
        )
        result = model.register_variable("x", var)
        assert result == RegistrationStatus.REGISTERED
        assert model.find_variable("x") is not None

    def test_register_constraint(self) -> None:
        """约束注册。"""
        model = MetaModel(name="test")
        result = model.register_constraint("c1", object())
        assert result == RegistrationStatus.REGISTERED
        assert model.find_constraint("c1") is not None

    def test_register_objective(self) -> None:
        """目标注册。"""
        model = MetaModel(name="test")
        result = model.register_objective("obj1", object())
        assert result == RegistrationStatus.REGISTERED

    def test_duplicate_variable_registration(self) -> None:
        """重复变量注册返回 ALREADY_EXISTS。"""
        model = MetaModel(name="test")
        var = AnyVariable(name="x", index=0, type=VariableType.CONTINUOUS)
        model.register_variable("x", var)
        result = model.register_variable("x", var)
        assert result == RegistrationStatus.ALREADY_EXISTS


@pytest.mark.migration_consistency
class TestVariableTypeAlignment:
    """验证变量类型与 Kotlin 对齐。"""

    def test_continuous_variable(self) -> None:
        """连续变量。"""
        var = AnyVariable(
            name="x",
            index=0,
            type=VariableType.CONTINUOUS,
            bounds=VariableRange(lower=0.0, upper=10.0),
        )
        assert var.type == VariableType.CONTINUOUS
        assert var.bounds.lower == 0.0
        assert var.bounds.upper == 10.0

    def test_integer_variable(self) -> None:
        """整数变量。"""
        var = AnyVariable(
            name="y",
            index=1,
            type=VariableType.INTEGER,
            bounds=VariableRange(lower=0, upper=100),
        )
        assert var.type == VariableType.INTEGER

    def test_binary_variable(self) -> None:
        """二进制变量。"""
        var = AnyVariable(
            name="z",
            index=2,
            type=VariableType.BINARY,
        )
        assert var.type == VariableType.BINARY


@pytest.mark.migration_consistency
class TestSolverInterfaceAlignment:
    """验证求解器接口与 Kotlin 对齐。"""

    def test_solver_status_enum(self) -> None:
        """求解器状态枚举。"""
        from ospf_python.core.solver.output.solver_status import SolverStatus

        assert SolverStatus.OPTIMAL is not None
        assert SolverStatus.INFEASIBLE is not None
        assert SolverStatus.UNBOUNDED is not None
        assert SolverStatus.TIMEOUT is not None
        assert SolverStatus.ERROR is not None

    def test_solve_options_defaults(self) -> None:
        """求解选项默认值。"""
        from ospf_python.core.solver.solve_options import SolveOptions

        options = SolveOptions()
        assert options.time_limit > 0
        assert isinstance(options.verbose, bool)


@pytest.mark.migration_consistency
class TestConstraintSignAlignment:
    """验证约束符号与 Kotlin 对齐。"""

    def test_constraint_signs(self) -> None:
        """约束符号枚举。"""
        assert ConstraintSign.LE is not None
        assert ConstraintSign.GE is not None
        assert ConstraintSign.EQ is not None
