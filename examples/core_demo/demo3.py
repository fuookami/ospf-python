"""Demo 3: Constraint creation and registration.

演示 3: 约束的创建与注册。

Shows Constraint, MetaConstraint, and LinearConstraintInput
usage with all three constraint signs.
"""

from __future__ import annotations

from ospf_python.core.model.basic.constraint_priority import ConstraintPriority
from ospf_python.core.model.basic.constraint_sign import ConstraintSign
from ospf_python.core.model.mechanism.constraint import Constraint
from ospf_python.core.model.mechanism.linear_constraint_input import (
    LinearConstraintInput,
)
from ospf_python.core.model.mechanism.meta_constraint import MetaConstraint
from ospf_python.core.model.mechanism.meta_model import MetaModel


def main() -> None:
    model = MetaModel(name="constraint_demo")

    # --- Constraint with LE sign ---
    # --- 小于等于约束 ---
    c_le = Constraint(
        name="budget",
        expr="3*x + 5*y",
        sign=ConstraintSign.LE,
        rhs=100.0,
    )
    model.register_constraint("budget", c_le)
    print(f"Constraint: {c_le.name}  sign={c_le.sign.value}  rhs={c_le.rhs}")

    # --- Constraint with GE sign ---
    # --- 大于等于约束 ---
    c_ge = Constraint(
        name="min_output",
        expr="2*x + y",
        sign=ConstraintSign.GE,
        rhs=20.0,
    )
    model.register_constraint("min_output", c_ge)
    print(f"Constraint: {c_ge.name}  sign={c_ge.sign.value}  rhs={c_ge.rhs}")

    # --- Constraint with EQ sign ---
    # --- 等式约束 ---
    c_eq = Constraint(
        name="balance",
        expr="x - y",
        sign=ConstraintSign.EQ,
        rhs=0.0,
    )
    model.register_constraint("balance", c_eq)
    print(f"Constraint: {c_eq.name}  sign={c_eq.sign.value}  rhs={c_eq.rhs}")

    # --- MetaConstraint with priority ---
    # --- 带优先级的元约束 ---
    mc = MetaConstraint(
        name="soft_cap",
        expr="x + y",
        sign=ConstraintSign.LE,
        rhs=50.0,
        priority=ConstraintPriority.PREFERRED,
    )
    model.register_constraint("soft_cap", mc)
    print(f"MetaConstraint: {mc.name}  priority={mc.priority.name}")

    # --- LinearConstraintInput (structured input) ---
    # --- 线性约束输入（结构化输入） ---
    lci = LinearConstraintInput(
        name="resource_limit",
        coefficients={"x": 2.0, "y": 3.0, "z": 1.0},
        sign=ConstraintSign.LE,
        rhs=60.0,
    )
    model.register_constraint("resource_limit", lci)
    print(f"LinearConstraintInput: {lci.name}  coeffs={lci.coefficients}")

    # Verify total registered
    # 验证注册总数
    assert len(model.constraints) == 5
    print(f"\nTotal constraints registered: {len(model.constraints)}")

    # Lookup
    # 查找
    found = model.find_constraint("budget")
    assert found is not None
    print(f"Found constraint 'budget': {found}")

    print("\nDemo 3 completed successfully.")


if __name__ == "__main__":
    main()
