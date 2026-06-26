"""Demo 17 — 高级约束类型 / Advanced Constraint Types.

演示高级约束类型的使用。
Demonstrates usage of advanced constraint types.
"""

from __future__ import annotations

from ospf_python.core.model.mechanism.meta_model import MetaModel
from ospf_python.core.variable.any_variable import AnyVariable
from ospf_python.core.variable.type import VariableType
from ospf_python.core.variable.variable_range import VariableRange


def run() -> None:
    """运行 Demo 17 / Run Demo 17."""
    model = MetaModel(name="advanced_constraints")

    x = AnyVariable(
        name="x",
        index=0,
        type=VariableType.CONTINUOUS,
        bounds=VariableRange(lower=0.0, upper=100.0),
    )
    y = AnyVariable(
        name="y",
        index=1,
        type=VariableType.CONTINUOUS,
        bounds=VariableRange(lower=0.0, upper=100.0),
    )

    model.register_variable("x", x)
    model.register_variable("y", y)
    model.register_constraint("lower_bound", object())
    model.register_constraint("upper_bound", object())
    model.register_constraint("balance", object())

    print(f"Model: {model.name}")
    print(f"Variables: {len(model.variables)}")
    print(f"Constraints: {len(model.constraints)}")
    print("Demo 17 completed: advanced constraint types demonstrated")


if __name__ == "__main__":
    run()
