"""BPP3D demo — 3D 装箱示例 / 3D bin packing example."""

from __future__ import annotations

from ospf_python.framework.bpp3d.domain.item.model.item import Item
from ospf_python.framework.bpp3d.infrastructure.container import Container


def run_demo() -> None:
    """运行 BPP3D demo / Run BPP3D demo."""
    container = Container(width=10.0, height=10.0, depth=10.0)
    item = Item(item_key="item1", width=2.0, height=2.0, depth=2.0, quantity=5)
    print(f"Container: {container.width}x{container.height}x{container.depth}")
    print(f"Item: {item.item_key} ({item.width}x{item.height}x{item.depth})")
    print("BPP3D demo completed successfully.")


if __name__ == "__main__":
    run_demo()
