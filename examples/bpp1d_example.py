"""BPP1D 示例 / BPP1D example.

基本一维装箱：使用 FFD 算法将物品装入箱中。
Basic 1D bin packing: pack items into bins using FFD algorithm.
"""

from ospf_python.framework.bpp1d.domain.item.model.item import Item
from ospf_python.framework.bpp1d.domain.solution.service.bin_packer import BinPacker

items = (
    Item.create(item_key="a", width=4.0, height=1.0),
    Item.create(item_key="b", width=3.0, height=1.0),
    Item.create(item_key="c", width=6.0, height=1.0),
    Item.create(item_key="d", width=2.0, height=1.0),
)

packer = BinPacker.create(bin_capacity=10.0)
solution = packer.pack(items)

print(f"物品数: {solution.total_items}")  # 物品数: 4
print(f"箱数: {solution.bin_count}")       # 箱数: 2
print(f"填充率: {solution.average_fill_rate:.2f}")  # 填充率
