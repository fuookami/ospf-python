"""Demo 16 — 多目标优化 / Multi-objective Optimization.

演示多目标优化的建模方法。
Demonstrates multi-objective optimization modeling approach.
"""

from __future__ import annotations

from ospf_python.core.model.basic.constraint_sign import (
    ConstraintSign,
)
from ospf_python.core.model.mechanism.constraint import (
    Constraint,
)
from ospf_python.core.model.mechanism.meta_model import (
    MetaModel,
)
from ospf_python.core.variable.any_variable import (
    AnyVariable,
)


def run() -> None:
    """运行 Demo 16 / Run Demo 16."""
    model = MetaModel(name="multi_obj_demo")

    x = AnyVariable.continuous(name="x", index=0, lower=0.0)
    y = AnyVariable.continuous(name="y", index=1, lower=0.0)

    model.register_variable("x", x)
    model.register_variable("y", y)

    # Register objectives
    model.register_objective("min_cost", {"type": "minimize", "expr": "x + 2*y"})
    model.register_objective(
        "max_quality", {"type": "maximize", "expr": "0.5*x + 1.5*y"}
    )

    # Register constraints
    c1 = Constraint(name="resource", expr="x + y", sign=ConstraintSign.LE, rhs=100.0)
    model.register_constraint("resource", c1)

    print(f"Model: {model.name}")
    print(f"Objectives: {len(model.objectives)}")
    print(f"Constraints: {len(model.constraints)}")
    print("Demo 16 completed: multi-objective optimization demonstrated")


if __name__ == "__main__":
    run()
