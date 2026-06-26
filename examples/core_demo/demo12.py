"""Demo 12: Constraint matrix operations.

演示 12: 约束矩阵操作。

Demonstrates Cell (sparse matrix), LinearTriadModel
constraint matrix manipulation, and elastic variable support.
"""

from __future__ import annotations

from ospf_python.core.model.intermediate.cell import Cell
from ospf_python.core.model.intermediate.linear_triad_elastic_builder import (
    LinearTriadElasticBuilder,
)
from ospf_python.core.model.intermediate.linear_triad_model import (
    LinearTriadModel,
)


def main() -> None:
    # --- Sparse matrix cells ---
    # --- 稀疏矩阵单元 ---
    cells = [
        Cell(row=0, col=0, value=3.0),
        Cell(row=0, col=1, value=5.0),
        Cell(row=1, col=0, value=1.0),
        Cell(row=1, col=1, value=-2.0),
    ]

    print("Sparse matrix cells:")
    for c in cells:
        print(f"  [{c.row},{c.col}] = {c.value}")

    # Build a matrix from cells
    # 从单元构建矩阵
    matrix: dict[tuple[int, int], float] = {}
    for c in cells:
        matrix[(c.row, c.col)] = c.value

    assert matrix[(0, 0)] == 3.0
    assert matrix[(1, 1)] == -2.0
    print(f"\nMatrix entries: {len(matrix)}")

    # --- LinearTriadModel constraint matrix ---
    # --- LinearTriadModel 约束矩阵 ---
    model = LinearTriadModel(name="matrix_demo")
    model.variables = ["x", "y", "z"]
    model.constraints = {
        "c1": {"x": 2.0, "y": 3.0},
        "c2": {"x": 1.0, "z": -1.0},
    }
    model.rhs = {"c1": 10.0, "c2": 5.0}
    model.sense = {"c1": "<=", "c2": ">="}

    print("\nConstraint matrix:")
    for cname, coeffs in model.constraints.items():
        terms = " + ".join(f"{v}*{k}" for k, v in coeffs.items())
        print(f"  {cname}: {terms} {model.sense[cname]} {model.rhs[cname]}")

    # --- Elastic variable support ---
    # --- 弹性变量支持 ---
    print("\nBefore elastic:")
    print(f"  c1 coefficients: {model.constraints['c1']}")

    LinearTriadElasticBuilder.add_elastic(model, "c1", penalty=10.0)

    print("After elastic on c1:")
    print(f"  c1 coefficients: {model.constraints['c1']}")
    assert "elastic_c1" in model.constraints["c1"]
    assert model.constraints["c1"]["elastic_c1"] == 10.0

    # Add elastic to non-existent constraint (no-op)
    # 对不存在的约束添加弹性（无操作）
    LinearTriadElasticBuilder.add_elastic(model, "nonexistent")
    print("\nElastic on nonexistent constraint: no-op (no error)")

    print("\nDemo 12 completed successfully.")


if __name__ == "__main__":
    main()
