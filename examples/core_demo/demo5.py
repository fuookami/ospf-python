"""Demo 5: MetaModel solve with MockSolver.

演示 5: 使用 MockSolver 求解 MetaModel。

Builds a LinearTriadModel from scratch and solves it
using the MockSolver to demonstrate the solve pipeline.
"""

from __future__ import annotations

from ospf_python.core.model.intermediate.linear_triad_model import (
    LinearTriadModel,
)
from ospf_python.core.solver.mock_solver import MockSolver
from ospf_python.core.solver.output.solver_status import SolverStatus
from ospf_python.core.solver.solve_options import SolveOptions


def main() -> None:
    # Build a simple LP: minimize x + 2*y
    #   subject to: x + y >= 4, x >= 1, y >= 1
    # 构建简单 LP: minimize x + 2*y
    #   约束: x + y >= 4, x >= 1, y >= 1
    model = LinearTriadModel(name="simple_lp")
    model.variables = ["x", "y"]
    model.objective = {"x": 1.0, "y": 2.0}
    model.constraints = {
        "c1": {"x": 1.0, "y": 1.0},
        "c2": {"x": 1.0},
        "c3": {"y": 1.0},
    }
    model.rhs = {"c1": 4.0, "c2": 1.0, "c3": 1.0}
    model.sense = {"c1": ">=", "c2": ">=", "c3": ">="}
    model.lower_bounds = {"x": 0.0, "y": 0.0}
    model.upper_bounds = {"x": 100.0, "y": 100.0}

    # Create solver with options
    # 创建求解器和选项
    solver = MockSolver(supports_int=True)
    options = SolveOptions(time_limit=60.0, verbose=True)

    print(f"Solver: {solver.name}")
    print(f"Supports integer: {solver.supports_integer()}")
    print(f"Time limit: {options.time_limit}s")

    # Solve
    # 求解
    output = solver.solve(model, options=options)

    print(f"\nStatus:    {output.status.name}")
    print(f"Optimal:   {output.is_optimal}")
    print(f"Infeasible: {output.is_infeasible}")
    print(f"Objective: {output.objective}")

    if output.is_optimal:
        print("Values:")
        for name in output.values.variable_names:
            print(f"  {name} = {output.values.get(name)}")

    # Verify result
    # 验证结果
    assert output.status is SolverStatus.OPTIMAL
    assert output.values.get("x") >= 1.0
    assert output.values.get("y") >= 1.0

    print("\nDemo 5 completed successfully.")


if __name__ == "__main__":
    main()
