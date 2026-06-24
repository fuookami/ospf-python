"""放置类型 / Placement typing.

BPP3D 中放置的类型定义。
Placement type definition in BPP3D.
"""

from __future__ import annotations

import enum


class PlacementTyping(enum.Enum):
    """放置类型枚举 / Placement type enumeration.

    描述物品放置的类型。
    Describes the type of item placement.

    Attributes:
        FIXED: 固定放置 / Fixed placement.
        FREE: 自由放置 / Free placement.
        CONSTRAINED: 约束放置 / Constrained placement.
    """

    FIXED = "fixed"
    """固定放置 / Fixed placement."""

    FREE = "free"
    """自由放置 / Free placement."""

    CONSTRAINED = "constrained"
    """约束放置 / Constrained placement."""
