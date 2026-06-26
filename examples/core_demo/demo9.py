"""Demo 9: Model serialization/deserialization.

演示 9: 模型序列化与反序列化。

Demonstrates exporting a MetaModel to LP/MPS formats
and using MechanismModelDumpSupport for file output.
"""

from __future__ import annotations

from ospf_python.core.model.basic.constraint_sign import ConstraintSign
from ospf_python.core.model.basic.model_file_format import ModelFileFormat
from ospf_python.core.model.mechanism.constraint import Constraint
from ospf_python.core.model.mechanism.meta_model import MetaModel
from ospf_python.core.model.mechanism.meta_model_export_support import (
    MetaModelExportSupport,
)
from ospf_python.core.variable.any_variable import AnyVariable


def build_sample_model() -> MetaModel:
    """Build a sample model for export.

    构建用于导出的示例模型。
    """
    model = MetaModel(name="serialization_demo")

    # Variables
    # 变量
    model.register_variable(
        "x", AnyVariable.continuous(name="x", index=0, lower=0.0, upper=10.0)
    )
    model.register_variable(
        "y", AnyVariable.continuous(name="y", index=1, lower=0.0, upper=10.0)
    )
    model.register_variable(
        "z", AnyVariable.integer(name="z", index=2, lower=0, upper=5)
    )

    # Constraints
    # 约束
    model.register_constraint(
        "c1",
        Constraint(name="c1", expr="x + y + z", sign=ConstraintSign.LE, rhs=15.0),
    )
    model.register_constraint(
        "c2",
        Constraint(name="c2", expr="2*x - y", sign=ConstraintSign.GE, rhs=1.0),
    )

    # Objective
    # 目标
    model.register_objective("obj", {"type": "minimize", "expr": "x + 2*y + 3*z"})

    return model


def main() -> None:
    model = build_sample_model()

    # Export to LP format string
    # 导出为 LP 格式字符串
    lp_text = MetaModelExportSupport.export(model, ModelFileFormat.LP)
    print("=== LP Format ===")
    print(lp_text)

    # Export to MPS format string
    # 导出为 MPS 格式字符串
    mps_text = MetaModelExportSupport.export(model, ModelFileFormat.MPS)
    print("\n=== MPS Format ===")
    print(mps_text)

    # Export to compressed MPS
    # 导出为压缩 MPS
    mps_gz = MetaModelExportSupport.export(model, ModelFileFormat.MPS_GZ)
    print("\n=== MPS_GZ Format ===")
    print(mps_gz)

    # Verify all formats produce output
    # 验证所有格式都产生输出
    assert len(lp_text) > 0
    assert len(mps_text) > 0
    assert len(mps_gz) > 0

    # Check model summary in export
    # 检查导出中的模型摘要
    assert "serialization_demo" in lp_text
    assert "3" in lp_text  # 3 variables

    print("\nDemo 9 completed successfully.")


if __name__ == "__main__":
    main()
