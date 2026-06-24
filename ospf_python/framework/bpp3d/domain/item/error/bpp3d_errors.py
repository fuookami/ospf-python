"""BPP3D 错误码 / BPP3D error codes.

定义 BPP3D 物品域的错误码。
Defines error codes for BPP3D item domain.
"""

from __future__ import annotations

import enum


class Bpp3dErrors(enum.Enum):
    """BPP3D 错误码 / BPP3D error codes.

    描述 BPP3D 物品域可能出现的错误。
    Describes possible errors in BPP3D item domain.

    Attributes:
        ITEM_NOT_FOUND: 物品未找到 / Item not found.
        CONTAINER_FULL: 容器已满 / Container full.
        INVALID_DIMENSION: 无效尺寸 / Invalid dimension.
        INVALID_QUANTITY: 无效数量 / Invalid quantity.
        PLACEMENT_FAILED: 放置失败 / Placement failed.
        NO_FEASIBLE_SOLUTION: 无可行解 / No feasible solution.
    """

    ITEM_NOT_FOUND = "item_not_found"
    """物品未找到 / Item not found."""

    CONTAINER_FULL = "container_full"
    """容器已满 / Container full."""

    INVALID_DIMENSION = "invalid_dimension"
    """无效尺寸 / Invalid dimension."""

    INVALID_QUANTITY = "invalid_quantity"
    """无效数量 / Invalid quantity."""

    PLACEMENT_FAILED = "placement_failed"
    """放置失败 / Placement failed."""

    NO_FEASIBLE_SOLUTION = "no_feasible_solution"
    """无可行解 / No feasible solution."""
