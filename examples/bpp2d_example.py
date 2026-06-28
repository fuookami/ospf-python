"""BPP2D 示例 / BPP2D example.

基本二维装箱：放置矩形物品。
Basic 2D bin packing: place rectangle items.
"""

from ospf_python.framework.bpp2d.domain.item.model.rectangle import Rectangle
from ospf_python.framework.bpp2d.domain.service.geometric_packer import GeometricPacker

rects = (
    Rectangle.create(item_key="r1", width=30.0, height=20.0),
    Rectangle.create(item_key="r2", width=15.0, height=15.0),
)

packer = GeometricPacker.create(container_width=100.0, container_height=100.0)

results = []
cursor_x = 0.0
for r in rects:
    placed = packer.place_rectangle(r, cursor_x, 0.0)
    if placed.is_ok():
        results.append(placed.unwrap())
        cursor_x += r.width

print(f"已放置: {len(results)} 个矩形")  # 已放置: 2
overlap = packer.check_no_overlap(tuple(results))
print(f"无重叠: {overlap.is_ok()}")       # 无重叠: True
