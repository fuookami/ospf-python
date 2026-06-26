"""CSP 列生成 demo — 对齐 Kotlin Main.kt 99 行。

CSP Column Generation demo — aligned with Kotlin Main.kt (99 lines).
"""

from __future__ import annotations

from ospf_python.framework.csp1d.application.service.csp1d_column_generation import (
    ColumnRecord,
    Csp1dColumnGeneration,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.full_sum_generator import (
    FullSumGenerator,
)
from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.n_same_generator import (
    NSameGenerator,
)


def run_demo() -> dict[str, object]:
    """运行 CSP 列生成 demo / Run CSP column generation demo.

    对齐 Kotlin Main.kt 参数：
    - rawLength = 1000
    - 4 产品需求：(450, 97), (360, 610), (310, 395), (140, 211)
    """
    raw_length = 1000.0
    products: list[tuple[str, float, int]] = [
        ("part_a", 450.0, 97),
        ("part_b", 360.0, 610),
        ("part_c", 310.0, 395),
        ("part_d", 140.0, 211),
    ]

    cg = Csp1dColumnGeneration()

    full_sum_gen = FullSumGenerator()
    initial_plans = full_sum_gen.generate(
        material_length=raw_length,
        products=products,
    )

    initial_columns = tuple(
        ColumnRecord(
            name=f"init_{i}",
            coefficients=tuple(plan.get(p[0], 0) for p in products),
            reduced_cost=0.0,
        )
        for i, plan in enumerate(initial_plans)
    )

    if initial_columns:
        cg.register(initial_columns)

    max_iterations = 50
    for _ in range(max_iterations):
        if cg.converged:
            break
        cg.refresh_shadow_price(lambda sp: None)

        n_same_gen = NSameGenerator()
        new_plans = n_same_gen.generate(
            material_length=raw_length,
            products=products,
        )
        if not new_plans:
            break

        new_columns = tuple(
            ColumnRecord(
                name=f"col_{cg.iteration}_{i}",
                coefficients=tuple(plan.get(p[0], 0) for p in products),
                reduced_cost=0.0,
            )
            for i, plan in enumerate(new_plans)
        )
        cg.add_columns(new_columns)

    cg.finalize()

    return {
        "iterations": cg.iteration,
        "converged": cg.converged,
        "columns": len(cg.active_columns),
    }


if __name__ == "__main__":
    result = run_demo()
    print(f"Iterations: {result['iterations']}")
    print(f"Converged: {result['converged']}")
    print(f"Columns: {result['columns']}")
    print("CSP column generation demo completed successfully.")
