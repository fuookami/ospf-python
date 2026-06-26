"""Demo 7: Multiple variable types (continuous/integer/binary).

演示 7: 多种变量类型（连续/整数/二元）。

Demonstrates creating variables of all supported types
and using VariableIndependentItem for type queries.
"""

from __future__ import annotations

from ospf_python.core.variable.any_variable import AnyVariable
from ospf_python.core.variable.type import VariableType
from ospf_python.core.variable.variable_independent_item import (
    VariableIndependentItem,
)
from ospf_python.core.variable.variable_range import VariableRange


def main() -> None:
    # Continuous variable
    # 连续变量
    x = AnyVariable.continuous(name="x", index=0, lower=0.0, upper=10.0)
    assert x.type is VariableType.CONTINUOUS
    print(f"Continuous: {x}")

    # Integer variable
    # 整数变量
    n = AnyVariable.integer(name="n", index=1, lower=0, upper=100)
    assert n.type is VariableType.INTEGER
    print(f"Integer:    {n}")

    # Binary variable
    # 二元变量
    b = AnyVariable.binary(name="b", index=2)
    assert b.type is VariableType.BINARY
    assert b.bounds.lower == 0.0
    assert b.bounds.upper == 1.0
    print(f"Binary:     {b}")

    # VariableIndependentItem with type queries
    # 带类型查询的 VariableIndependentItem
    vi = VariableIndependentItem(
        name="z",
        type=VariableType.INTEGER,
        index=3,
        bounds=VariableRange(lower=0, upper=10),
    )
    assert vi.is_integer()
    assert not vi.is_binary()
    assert not vi.is_continuous()
    print(f"\nIndependent integer: {vi}")
    print(f"  is_integer={vi.is_integer()}, is_binary={vi.is_binary()}")

    vb = VariableIndependentItem(
        name="flag",
        type=VariableType.BINARY,
        index=4,
        bounds=VariableRange(lower=0, upper=1),
    )
    assert vb.is_binary()
    assert vb.is_integer()  # binary is also integer
    print(f"Independent binary: {vb}")
    print(f"  is_integer={vb.is_integer()}, is_binary={vb.is_binary()}")

    # Enumerate all variable types
    # 枚举所有变量类型
    print("\nAll VariableType values:")
    for vt in VariableType:
        print(f"  {vt.name} = {vt.value}")

    print("\nDemo 7 completed successfully.")


if __name__ == "__main__":
    main()
