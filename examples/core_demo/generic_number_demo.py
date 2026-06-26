"""Generic Number Demo — 泛型数值演示.

演示泛型数值的使用方式。
Demonstrates usage of generic numbers.
"""

from __future__ import annotations

from ospf_python.core.variable.any_variable import AnyVariable
from ospf_python.core.variable.type import VariableType
from ospf_python.core.variable.variable_range import VariableRange


def run() -> None:
    """运行泛型数值演示 / Run generic number demo."""
    x = AnyVariable(
        name="x",
        index=0,
        type=VariableType.CONTINUOUS,
        bounds=VariableRange(lower=0.0, upper=10.0),
    )
    print(f"Variable: {x.name}, type: {x.type}")

    y = AnyVariable(
        name="y",
        index=1,
        type=VariableType.INTEGER,
        bounds=VariableRange(lower=0, upper=100),
    )
    print(f"Integer variable: {y.name}")

    print("Generic number demo completed successfully")


if __name__ == "__main__":
    run()
