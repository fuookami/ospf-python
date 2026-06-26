"""Demo 1: Basic MetaModel creation and variable registration.

演示 1: 基本 MetaModel 创建与变量注册。

Shows how to create a MetaModel instance and register
variables, constraints, and objectives.
"""

from __future__ import annotations

from ospf_python.core.model.basic.constraint_sign import ConstraintSign
from ospf_python.core.model.basic.registration_status import RegistrationStatus
from ospf_python.core.model.mechanism.constraint import Constraint
from ospf_python.core.model.mechanism.meta_model import MetaModel
from ospf_python.core.variable.any_variable import AnyVariable


def main() -> None:
    # Create a MetaModel with a descriptive name
    # 创建带有描述性名称的 MetaModel
    model = MetaModel(name="basic_demo")
    print(f"Created model: {model.name}")

    # Register continuous variables
    # 注册连续变量
    x = AnyVariable.continuous(name="x", index=0, lower=0.0, upper=10.0)
    y = AnyVariable.continuous(name="y", index=1, lower=0.0, upper=10.0)

    status_x = model.register_variable("x", x)
    status_y = model.register_variable("y", y)
    print(f"Register x: {status_x}")  # REGISTERED
    print(f"Register y: {status_y}")  # REGISTERED

    # Attempting duplicate registration returns ALREADY_EXISTS
    # 尝试重复注册返回 ALREADY_EXISTS
    status_dup = model.register_variable("x", x)
    print(f"Register x again: {status_dup}")  # ALREADY_EXISTS
    assert status_dup is RegistrationStatus.ALREADY_EXISTS

    # Register a constraint: x + y <= 15
    # 注册约束: x + y <= 15
    c1 = Constraint(name="c1", expr="x + y", sign=ConstraintSign.LE, rhs=15.0)
    model.register_constraint("c1", c1)

    # Register an objective
    # 注册目标函数
    model.register_objective("obj", {"type": "minimize", "expr": "x + 2*y"})

    # Inspect the model
    # 检查模型
    print(f"Variables:    {len(model.variables)}")
    print(f"Constraints:  {len(model.constraints)}")
    print(f"Objectives:   {len(model.objectives)}")

    # Lookup registered objects
    # 查找已注册对象
    found = model.find_variable("x")
    assert found is not None
    print(f"Found variable x: {found}")

    missing = model.find_variable("z")
    assert missing is None
    print(f"Variable z not found: {missing is None}")

    print("\nDemo 1 completed successfully.")


if __name__ == "__main__":
    main()
