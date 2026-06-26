"""Demo 2: Linear variable creation with bounds.

演示 2: 带边界约束的线性变量创建。

Demonstrates VariableRange factories and AnyVariable
creation with various bound configurations.
"""

from __future__ import annotations

from ospf_python.core.variable.any_variable import AnyVariable
from ospf_python.core.variable.variable_range import VariableRange


def main() -> None:
    # VariableRange factories
    # VariableRange 工厂方法
    nn = VariableRange.non_negative()  # [0, +inf)
    unit = VariableRange.unit()  # [0, 1]
    fixed = VariableRange.fixed(5.0)  # [5, 5]
    custom = VariableRange.create(lower=-10.0, upper=10.0)

    print(f"Non-negative: [{nn.lower}, {nn.upper}]")
    print(f"Unit:         [{unit.lower}, {unit.upper}]")
    print(f"Fixed(5):     [{fixed.lower}, {fixed.upper}]")
    print(f"Custom:       [{custom.lower}, {custom.upper}]")

    # Range properties and methods
    # 范围属性和方法
    assert nn.contains(0.0)
    assert nn.contains(999.0)
    assert not nn.contains(-1.0)
    assert unit.width == 1.0
    assert not fixed.is_unbounded()
    assert VariableRange().is_unbounded()

    # Create variables with bounds
    # 创建带边界的变量
    x = AnyVariable.continuous(name="x", index=0, lower=0.0, upper=100.0)
    y = AnyVariable.continuous(name="y", index=1, lower=-50.0, upper=50.0)

    print(f"\nVariable x: {x}")
    print(f"  type={x.type.value}, bounds=[{x.bounds.lower}, {x.bounds.upper}]")
    print(f"Variable y: {y}")
    print(f"  type={y.type.value}, bounds=[{y.bounds.lower}, {y.bounds.upper}]")

    # Verify bounds containment
    # 验证边界包含
    assert x.bounds.contains(50.0)
    assert not x.bounds.contains(-1.0)
    assert y.bounds.contains(0.0)

    # Default bounds are unbounded
    # 默认边界是无界的
    z = AnyVariable.continuous(name="z", index=2)
    assert z.bounds.is_unbounded()
    print(f"\nVariable z: bounds=[{z.bounds.lower}, {z.bounds.upper}] (unbounded)")

    print("\nDemo 2 completed successfully.")


if __name__ == "__main__":
    main()
