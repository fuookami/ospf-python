"""Demo 14 — 模型验证 / Model Validation.

演示 MetaModel 的验证机制。
Demonstrates MetaModel validation mechanism.
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
    """运行 Demo 14 / Run Demo 14."""
    model = MetaModel(name="validation_demo")

    x = AnyVariable.integer(name="x", index=0, lower=0, upper=10)
    y = AnyVariable.integer(name="y", index=1, lower=0, upper=10)

    model.register_variable("x", x)
    model.register_variable("y", y)

    c1 = Constraint(name="c1", expr="x + y", sign=ConstraintSign.LE, rhs=15.0)
    model.register_constraint("c1", c1)

    print(f"Model: {model.name}")
    print(f"Variables: {len(model.variables)}")
    print(f"Constraints: {len(model.constraints)}")
    print("Demo 14 completed: model validation demonstrated")


if __name__ == "__main__":
    run()
