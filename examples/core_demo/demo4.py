"""Demo 4: Objective function setup.

演示 4: 目标函数设置。

Demonstrates registering single and multiple objective
functions with the MetaModel.
"""

from __future__ import annotations

from ospf_python.core.model.basic.model_file_format import ModelFileFormat
from ospf_python.core.model.basic.multi_object import MultiObject
from ospf_python.core.model.mechanism.meta_model import MetaModel
from ospf_python.core.model.mechanism.meta_model_export_support import (
    MetaModelExportSupport,
)


def main() -> None:
    model = MetaModel(name="objective_demo")

    # Register a single minimization objective
    # 注册单个最小化目标
    obj_min = {"type": "minimize", "coefficients": {"x": 1.0, "y": 2.0}}
    status = model.register_objective("min_cost", obj_min)
    print(f"Registered 'min_cost': {status}")

    # Register a maximization objective
    # 注册最大化目标
    obj_max = {"type": "maximize", "coefficients": {"x": 3.0, "y": 1.0}}
    status = model.register_objective("max_profit", obj_max)
    print(f"Registered 'max_profit': {status}")

    # Multi-objective wrapper combining both
    # 多目标包装器组合两者
    multi = MultiObject(
        objectives=(obj_min, obj_max),
        weights=(0.6, 0.4),
    )
    model.register_objective("multi", multi)
    print(f"Multi-objective weights: {multi.weights}")
    print(f"Multi-objective count: {len(multi.objectives)}")

    # Verify objectives are registered
    # 验证目标已注册
    assert len(model.objectives) == 3
    print(f"\nTotal objectives: {len(model.objectives)}")

    # Export model summary
    # 导出模型摘要
    summary = MetaModelExportSupport.export(model, ModelFileFormat.LP)
    print(f"\nModel export:\n{summary}")

    print("\nDemo 4 completed successfully.")


if __name__ == "__main__":
    main()
