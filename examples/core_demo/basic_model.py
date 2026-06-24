"""Core 建模 demo / Core modeling demo.

演示 MetaModel 基本用法。
Demonstrates basic MetaModel usage.
"""

from __future__ import annotations

from ospf_python.core.model.mechanism.meta_model import MetaModel


def run_demo() -> None:
    """运行 core demo / Run core demo."""
    model = MetaModel(name="demo")
    print(f"Created model: {model.name}")
    print("Core demo completed successfully.")


if __name__ == "__main__":
    run_demo()
