"""Demo 13: Shadow price extraction.

演示 13: 影子价格提取。

Demonstrates TriadDualSolverSupport for extracting
dual values (shadow prices) from solved models.
"""

from __future__ import annotations

from ospf_python.core.model.intermediate.linear_triad_model import (
    LinearTriadModel,
)
from ospf_python.core.model.intermediate.triad_dual_solver_support import (
    TriadDualSolverSupport,
)


def main() -> None:
    # Build a model with multiple constraints
    # 构建具有多个约束的模型
    model = LinearTriadModel(name="shadow_price_demo")
    model.variables = ["x", "y"]
    model.objective = {"x": 1.0, "y": 2.0}
    model.constraints = {
        "resource_a": {"x": 2.0, "y": 1.0},
        "resource_b": {"x": 1.0, "y": 3.0},
        "min_output": {"x": 1.0, "y": 1.0},
    }
    model.rhs = {
        "resource_a": 20.0,
        "resource_b": 30.0,
        "min_output": 5.0,
    }
    model.sense = {
        "resource_a": "<=",
        "resource_b": "<=",
        "min_output": ">=",
    }
    model.lower_bounds = {"x": 0.0, "y": 0.0}
    model.upper_bounds = {"x": 100.0, "y": 100.0}

    # Simulate dual solution from a solver
    # 模拟来自求解器的对偶解
    raw_duals = {
        "resource_a": 0.5,
        "resource_b": 0.3,
        "min_output": -0.1,
    }

    # Extract dual values using the support class
    # 使用支持类提取对偶值
    dual_values = TriadDualSolverSupport.extract_dual_values(model, raw_duals)

    print("Shadow prices (dual values):")
    for cname, dual in dual_values.items():
        print(f"  {cname}: {dual:.4f}")

    # Verify all constraints have duals
    # 验证所有约束都有对偶值
    assert len(dual_values) == 3
    assert dual_values["resource_a"] == 0.5
    assert dual_values["resource_b"] == 0.3
    assert dual_values["min_output"] == -0.1

    # Missing dual defaults to 0.0
    # 缺失的对偶值默认为 0.0
    empty_duals: dict[str, float] = {}
    default_values = TriadDualSolverSupport.extract_dual_values(model, empty_duals)
    assert all(v == 0.0 for v in default_values.values())
    print(f"\nDefault duals (when empty): {default_values}")

    # Interpret shadow prices
    # 解释影子价格
    print("\nInterpretation:")
    for cname, dual in dual_values.items():
        if dual > 0:
            print(f"  {cname}: binding constraint, shadow price = {dual}")
        elif dual < 0:
            print(f"  {cname}: active lower bound, dual = {dual}")
        else:
            print(f"  {cname}: non-binding")

    print("\nDemo 13 completed successfully.")


if __name__ == "__main__":
    main()
