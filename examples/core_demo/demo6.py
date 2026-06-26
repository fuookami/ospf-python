"""Demo 6: Solution extraction.

演示 6: 求解结果提取。

Shows how to extract, validate, and inspect solver
output values using SolveValue and SolveValueValidation.
"""

from __future__ import annotations

from ospf_python.core.model.intermediate.linear_triad_model import (
    LinearTriadModel,
)
from ospf_python.core.solver.mock_solver import MockSolver
from ospf_python.core.solver.value.solve_value import SolveValue
from ospf_python.core.solver.value.solve_value_validation import (
    SolveValueValidation,
)


def main() -> None:
    # Build and solve a model
    # 构建并求解模型
    model = LinearTriadModel(name="extraction_demo")
    model.variables = ["a", "b", "c"]
    model.objective = {"a": 1.0, "b": 1.0, "c": 1.0}
    model.constraints = {
        "sum": {"a": 1.0, "b": 1.0, "c": 1.0},
    }
    model.rhs = {"sum": 10.0}
    model.sense = {"sum": "<="}
    model.lower_bounds = {"a": 0.0, "b": 0.0, "c": 0.0}
    model.upper_bounds = {"a": 10.0, "b": 10.0, "c": 10.0}

    solver = MockSolver()
    output = solver.solve(model)

    # Extract SolveValue from output
    # 从输出中提取 SolveValue
    values: SolveValue = output.values
    print(f"Variable names: {values.variable_names}")
    print(f"Is empty: {values.is_empty}")

    # Individual value access
    # 单个值访问
    for name in values.variable_names:
        val = values.get(name)
        print(f"  {name} = {val}")

    # Default value for missing variables
    # 缺失变量的默认值
    missing = values.get("nonexistent", default=-1.0)
    assert missing == -1.0
    print(f"\nMissing variable default: {missing}")

    # Create a custom SolveValue and validate
    # 创建自定义 SolveValue 并验证
    clean = SolveValue(values={"x": 1.0, "y": 2.0})
    result = SolveValueValidation.validate(clean)
    assert result.is_valid
    print(f"\nClean validation: valid={result.is_valid}")

    # Validate with NaN
    # 验证含 NaN 的值
    dirty = SolveValue(values={"x": 1.0, "y": float("nan")})
    result_nan = SolveValueValidation.validate(dirty, allow_nan=False)
    assert not result_nan.is_valid
    print(f"NaN validation: valid={result_nan.is_valid}")
    for issue in result_nan.issues:
        print(f"  Issue: {issue}")

    # Validate with Inf (allowed)
    # 验证含 Inf 的值（允许）
    inf_val = SolveValue(values={"x": float("inf")})
    result_inf = SolveValueValidation.validate(inf_val, allow_inf=True)
    assert result_inf.is_valid
    print(f"Inf validation (allowed): valid={result_inf.is_valid}")

    print("\nDemo 6 completed successfully.")


if __name__ == "__main__":
    main()
