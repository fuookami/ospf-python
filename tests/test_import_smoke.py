"""包级别导入冒烟测试 / Package-level import smoke tests.

验证所有公开导入均可正常工作。
Verifies that all public imports work correctly.
"""

from __future__ import annotations


def test_import_core_types() -> None:
    """验证核心类型导入 / Verify core type imports."""
    from ospf_python.core import (
        AnyVariable,
        ConstraintSign,
        LinearSolver,
        MetaModel,
        Solver,
        SolverOutput,
        SolverStatus,
        VariableRange,
        VariableType,
    )

    assert MetaModel is not None
    assert ConstraintSign is not None
    assert AnyVariable is not None
    assert VariableType is not None
    assert VariableRange is not None
    assert Solver is not None
    assert LinearSolver is not None
    assert SolverOutput is not None
    assert SolverStatus is not None


def test_import_core_solver() -> None:
    """验证求解器子模块导入 / Verify solver submodule imports."""
    from ospf_python.core.solver import (
        LinearSolver,
        MockSolver,
        Solver,
        SolverOutput,
        SolverStatus,
    )

    assert Solver is not None
    assert LinearSolver is not None
    assert MockSolver is not None
    assert SolverOutput is not None
    assert SolverStatus is not None


def test_import_core_variable() -> None:
    """验证变量子模块导入 / Verify variable submodule imports."""
    from ospf_python.core.variable import (
        AbstractVariableItem,
        AnyVariable,
        VariableRange,
        VariableType,
    )

    assert AnyVariable is not None
    assert VariableType is not None
    assert VariableRange is not None
    assert AbstractVariableItem is not None


def test_import_framework_submodules() -> None:
    """验证框架子模块导入 / Verify framework submodule imports."""
    from ospf_python.framework import (
        bpp1d,
        bpp2d,
        bpp3d,
        csp1d,
        csp2d,
        gantt_scheduling,
        log,
        model,
        network,
        network_scheduling,
        persistence,
        solver,
    )

    assert bpp1d is not None
    assert bpp2d is not None
    assert bpp3d is not None
    assert csp1d is not None
    assert csp2d is not None
    assert gantt_scheduling is not None
    assert log is not None
    assert model is not None
    assert network is not None
    assert network_scheduling is not None
    assert persistence is not None
    assert solver is not None


def test_import_framework_solver() -> None:
    """验证框架求解器导入 / Verify framework solver imports."""
    from ospf_python.framework.solver import (
        ColumnGenerationSolver,
        FrameworkSolveOptions,
    )

    assert ColumnGenerationSolver is not None
    assert FrameworkSolveOptions is not None


def test_import_framework_persistence() -> None:
    """验证持久化模块导入 / Verify persistence module imports."""
    from ospf_python.framework.persistence import (
        Repository,
    )

    assert Repository is not None


def test_import_math_types() -> None:
    """验证数学类型导入 / Verify math type imports."""
    from ospf_python.math import (
        CanonicalMonomial,
        CanonicalPolynomial,
        Symbol,
    )

    assert Symbol is not None
    assert CanonicalMonomial is not None
    assert CanonicalPolynomial is not None


def test_import_math_symbol() -> None:
    """验证符号子模块导入 / Verify symbol submodule imports."""
    from ospf_python.math.symbol import (
        Category,
        DimensionedSymbol,
        Symbol,
        SymbolIdentity,
        SymbolQuantity,
    )

    assert Symbol is not None
    assert SymbolIdentity is not None
    assert SymbolQuantity is not None
    assert Category is not None
    assert DimensionedSymbol is not None


def test_import_math_monomial() -> None:
    """验证单项式导入 / Verify monomial imports."""
    from ospf_python.math.symbol.monomial import (
        CanonicalMonomial,
        LinearMonomial,
        QuadraticMonomial,
    )

    assert CanonicalMonomial is not None
    assert LinearMonomial is not None
    assert QuadraticMonomial is not None


def test_import_math_polynomial() -> None:
    """验证多项式导入 / Verify polynomial imports."""
    from ospf_python.math.symbol.polynomial import (
        CanonicalPolynomial,
        LinearPolynomial,
        QuadraticPolynomial,
        var,
    )

    assert CanonicalPolynomial is not None
    assert LinearPolynomial is not None
    assert QuadraticPolynomial is not None
    assert var is not None


def test_import_math_geometry() -> None:
    """验证几何模块导入 / Verify geometry module imports."""
    from ospf_python.math.geometry import (
        Box2,
        Box3,
        Point,
        Vector,
    )

    assert Point is not None
    assert Vector is not None
    assert Box2 is not None
    assert Box3 is not None


def test_import_math_combinatorics() -> None:
    """验证组合数学导入 / Verify combinatorics imports."""
    from ospf_python.math.combinatorics import (
        combinations,
        permutations,
    )

    assert combinations is not None
    assert permutations is not None


def test_import_math_ordinary() -> None:
    """验证常用数学类型导入 / Verify ordinary math imports."""
    from ospf_python.math.ordinary import (
        Scale,
        Toleranced,
        Trivalent,
    )

    assert Scale is not None
    assert Toleranced is not None
    assert Trivalent is not None


def test_import_utils_error() -> None:
    """验证错误处理导入 / Verify error handling imports."""
    from ospf_python.utils import (
        ApplicationException,
        Error,
        ErrorCode,
    )

    assert Error is not None
    assert ErrorCode is not None
    assert ApplicationException is not None


def test_import_utils_functional() -> None:
    """验证函数式工具导入 / Verify functional utility imports."""
    from ospf_python.utils import (
        Condition,
        Either,
        Eq,
        Left,
        Ok,
        Ord,
        Result,
        Right,
        Variant2,
    )

    assert Condition is not None
    assert Either is not None
    assert Eq is not None
    assert Left is not None
    assert Right is not None
    assert Ok is not None
    assert Result is not None
    assert Ord is not None
    assert Variant2 is not None


def test_import_utils_concept() -> None:
    """验证概念协议导入 / Verify concept protocol imports."""
    from ospf_python.utils import (
        Copyable,
        Indexed,
        Movable,
        Swappable,
    )

    assert Copyable is not None
    assert Movable is not None
    assert Indexed is not None
    assert Swappable is not None


def test_import_utils_context() -> None:
    """验证上下文模块导入 / Verify context module imports."""
    from ospf_python.utils import (
        Context,
        ContextKey,
        ContextVar,
    )

    assert Context is not None
    assert ContextKey is not None
    assert ContextVar is not None


def test_import_utils_parallel() -> None:
    """验证并行工具导入 / Verify parallel utility imports."""
    from ospf_python.utils import (
        ChannelGuard,
        WorkerPoolResult,
        WorkerPoolTask,
    )

    assert ChannelGuard is not None
    assert WorkerPoolResult is not None
    assert WorkerPoolTask is not None


def test_import_utils_serialization() -> None:
    """验证序列化工具导入 / Verify serialization imports."""
    from ospf_python.utils import (
        JsonNamingPolicy,
        from_csv,
        to_csv,
    )

    assert JsonNamingPolicy is not None
    assert from_csv is not None
    assert to_csv is not None


def test_import_utils_config() -> None:
    """验证配置模块导入 / Verify config module imports."""
    from ospf_python.utils import (
        VERSION,
        Version,
    )

    assert VERSION is not None
    assert Version is not None


def test_import_multiarray() -> None:
    """验证多维数组模块导入 / Verify multiarray module imports."""
    from ospf_python.multiarray import (
        DataFrame,
        MultiArray,
        Shape,
        Vector,
    )

    assert MultiArray is not None
    assert Shape is not None
    assert Vector is not None
    assert DataFrame is not None


def test_import_quantities() -> None:
    """验证物理量模块导入 / Verify quantities module imports."""
    from ospf_python.quantities import (
        Dimensions,
        Quantity,
    )

    assert Dimensions is not None
    assert Quantity is not None


def test_import_math_expression() -> None:
    """验证表达式模块导入 / Verify expression module imports."""
    from ospf_python.math.symbol.expression import (
        BinaryExpression,
        BooleanExpression,
        Expression,
        ScalarExpression,
    )

    assert Expression is not None
    assert BinaryExpression is not None
    assert BooleanExpression is not None
    assert ScalarExpression is not None


def test_import_framework_model() -> None:
    """验证框架模型导入 / Verify framework model imports."""
    from ospf_python.framework.model import (
        Pipeline,
        ShadowPrice,
    )

    assert Pipeline is not None
    assert ShadowPrice is not None


def test_import_framework_log() -> None:
    """验证日志模块导入 / Verify log module imports."""
    from ospf_python.framework.log import (
        LogContext,
        LogRecord,
    )

    assert LogContext is not None
    assert LogRecord is not None
