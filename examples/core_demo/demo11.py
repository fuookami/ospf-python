"""Demo 11: Benders decomposition basics.

演示 11: Benders 分解基础。

Demonstrates the Benders decomposition pattern using
MechanismModelCutSupport for managing feasibility and
optimality cuts.
"""

from __future__ import annotations

from ospf_python.core.model.intermediate.linear_triad_model import (
    LinearTriadModel,
)
from ospf_python.core.model.mechanism.mechanism_model_cut_support import (
    MechanismModelCutSupport,
)
from ospf_python.core.solver.mock_solver import MockSolver
from ospf_python.core.solver.output.solver_status import SolverStatus


def build_master() -> LinearTriadModel:
    """Build the Benders master problem.

    构建 Benders 主问题。
    """
    master = LinearTriadModel(name="benders_master")
    master.variables = ["x", "theta"]
    master.objective = {"x": 2.0, "theta": 1.0}
    master.constraints = {
        "x_lb": {"x": 1.0},
    }
    master.rhs = {"x_lb": 0.0}
    master.sense = {"x_lb": ">="}
    master.lower_bounds = {"x": 0.0, "theta": -1e6}
    master.upper_bounds = {"x": 100.0, "theta": 1e6}
    return master


def solve_subproblem(x_val: float) -> tuple[float, dict[str, float]]:
    """Solve the subproblem for a given x value.

    求解给定 x 值的子问题。

    Returns:
        (sub_obj, dual_values)
    """
    # Simple sub: minimize y s.t. y >= 2*x_val, y >= 0
    # 简单子问题: minimize y s.t. y >= 2*x_val, y >= 0
    sub = LinearTriadModel(name="sub")
    sub.variables = ["y"]
    sub.objective = {"y": 1.0}
    sub.constraints = {"link": {"y": 1.0}}
    sub.rhs = {"link": 2.0 * x_val}
    sub.sense = {"link": ">="}
    sub.lower_bounds = {"y": 0.0}
    sub.upper_bounds = {"y": 1e6}

    solver = MockSolver()
    result = solver.solve(sub)

    if result.status is SolverStatus.OPTIMAL:
        # Dual of y >= 2*x is 1.0 when binding
        # y >= 2*x 的对偶值在绑定时为 1.0
        dual = {"link": 1.0}
        return result.objective, dual
    return float("inf"), {}


def main() -> None:
    master = build_master()
    solver = MockSolver()
    cut_manager = MechanismModelCutSupport()

    max_iterations = 5
    tolerance = 1e-4

    for iteration in range(max_iterations):
        result = solver.solve(master)
        if result.status is not SolverStatus.OPTIMAL:
            print(f"Iteration {iteration}: master infeasible")
            break

        x_val = result.values.get("x")
        theta_val = result.values.get("theta")
        master_obj = result.objective
        print(
            f"Iteration {iteration}: x={x_val:.4f}, theta={theta_val:.4f}, obj={master_obj:.4f}"
        )

        # Solve subproblem
        # 求解子问题
        sub_obj, duals = solve_subproblem(x_val)
        print(f"  Subproblem obj: {sub_obj:.4f}")

        # Check convergence
        # 检查收敛性
        if sub_obj - theta_val <= tolerance:
            print("Converged -- optimal solution found.")
            break

        # Add optimality cut: theta >= sub_obj + dual * (x - x_val)
        # 添加最优性切割: theta >= sub_obj + dual * (x - x_val)
        cut = {
            "type": "optimality",
            "expr": f"theta >= {sub_obj:.4f} + {duals.get('link', 0.0):.4f}*(x - {x_val:.4f})",
        }
        cut_manager.add_cut(cut)

        # Add cut as constraint to master
        # 将切割作为约束添加到主问题
        cut_name = f"opt_cut_{iteration}"
        master.constraints[cut_name] = {"theta": 1.0, "x": -duals.get("link", 0.0)}
        master.rhs[cut_name] = sub_obj - duals.get("link", 0.0) * x_val
        master.sense[cut_name] = ">="

    print(f"\nTotal cuts added: {cut_manager.cut_count}")
    print(f"Final master variables: {master.variables}")

    print("\nDemo 11 completed successfully.")


if __name__ == "__main__":
    main()
