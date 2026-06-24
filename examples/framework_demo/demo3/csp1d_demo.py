"""CSP1D demo — 一维下料示例 / 1D cutting stock example.

演示 CSP1D 框架基本用法。
Demonstrates basic CSP1D framework usage.
"""

from __future__ import annotations

from ospf_python.framework.csp1d.application.model.csp1d_problem_builder import (
    Csp1dProblemBuilder,
)


def run_demo() -> None:
    """运行 CSP1D demo / Run CSP1D demo."""
    builder = Csp1dProblemBuilder()

    # 添加材料 / Add materials
    builder.add_material(name="steel_100", width=100.0, length=1000.0, cost=10.0)
    builder.add_material(name="steel_120", width=120.0, length=1000.0, cost=12.0)

    # 添加产品 / Add products
    builder.add_product(name="part_a", width=30.0, length=500.0, demand=10)
    builder.add_product(name="part_b", width=40.0, length=500.0, demand=8)
    builder.add_product(name="part_c", width=50.0, length=500.0, demand=5)

    # 添加机器 / Add machines
    builder.add_machine(name="cutter_1", max_width=100.0, cut_loss=2.0)

    problem = builder.build()
    print(
        f"Problem: {len(problem.materials)} materials, {len(problem.products)} products"
    )
    print("CSP1D demo completed successfully.")


if __name__ == "__main__":
    run_demo()
