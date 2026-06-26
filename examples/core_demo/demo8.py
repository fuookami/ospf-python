"""Demo 8: Coefficient operations.

演示 8: 系数操作。

Demonstrates MathInequalityFlatten, DumpHelpers
coefficient formatting, and MechanismModelFlt64Conversion.
"""

from __future__ import annotations

from ospf_python.core.model.intermediate.dump_helpers import DumpHelpers
from ospf_python.core.model.mechanism.math_inequality_flatten import (
    MathInequalityFlatten,
)
from ospf_python.core.model.mechanism.mechanism_model_flt64_conversion import (
    MechanismModelFlt64Conversion,
)


def main() -> None:
    # --- MathInequalityFlatten ---
    # --- 数学不等式扁平化 ---
    flat = MathInequalityFlatten()
    flat.add_term("x", 3.0)
    flat.add_term("y", 5.0)
    flat.add_term("x", 2.0)  # accumulates: x becomes 5.0
    flat.add_constant(10.0)

    print("Flattened inequality:")
    for var, coeff in flat.terms.items():
        print(f"  {var}: {coeff}")
    print(f"  constant: {flat.constant}")
    assert flat.terms["x"] == 5.0
    assert flat.terms["y"] == 5.0
    assert flat.constant == 10.0

    # Build another flatten for a different constraint
    # 为不同约束构建另一个扁平化
    flat2 = MathInequalityFlatten()
    flat2.add_term("a", 1.5)
    flat2.add_term("b", -2.0)
    flat2.add_term("c", 0.5)
    flat2.add_constant(-3.0)

    print(f"\nSecond flatten: terms={dict(flat2.terms)}, constant={flat2.constant}")

    # --- DumpHelpers ---
    # --- 转储辅助工具 ---
    print("\nCoefficient formatting:")
    print(f"  format_coefficient(3.0)    = '{DumpHelpers.format_coefficient(3.0)}'")
    print(f"  format_coefficient(3.14)   = '{DumpHelpers.format_coefficient(3.14)}'")
    print(f"  format_coefficient(0.001)  = '{DumpHelpers.format_coefficient(0.001)}'")

    print("\nSign formatting:")
    for sign in ["<=", ">=", "=="]:
        print(f"  format_sign('{sign}') = '{DumpHelpers.format_sign(sign)}'")

    # --- MechanismModelFlt64Conversion ---
    # --- Flt64 转换 ---
    print("\nFlt64 conversion:")
    raw_coeffs = {"x": 1, "y": 2.5, "z": 3}
    converted = MechanismModelFlt64Conversion.convert_coefficients(raw_coeffs)
    for k, v in converted.items():
        print(f"  {k}: {v} (type={type(v).__name__})")
        assert isinstance(v, float)

    val = MechanismModelFlt64Conversion.convert_value(42)
    assert isinstance(val, float)
    assert val == 42.0
    print(f"\nconvert_value(42) = {val}")

    print("\nDemo 8 completed successfully.")


if __name__ == "__main__":
    main()
