"""BPP2D 错误码枚举 / BPP2D error code enumeration.

定义二维装箱领域的语义化错误码。
Defines semantic error codes for the 2D bin packing domain.
"""

from __future__ import annotations

import enum


class Bpp2dErrors(enum.Enum):
    """BPP2D 错误码 / BPP2D error codes.

    用于标识二维装箱过程中各类错误的语义化枚举。
    Semantic enumeration identifying various error
    categories during 2D bin packing.

    Attributes:
        value: 错误码字符串标识 / Error code string identifier.
    """

    ITEM_NOT_FOUND = "item_not_found"
    """物品未找到 / Item not found."""

    CONSTRAINT_NOT_FOUND = "constraint_not_found"
    """约束未找到 / Constraint not found."""

    INVALID_DIMENSION = "invalid_dimension"
    """无效尺寸 / Invalid dimension."""

    INVALID_POSITION = "invalid_position"
    """无效位置 / Invalid position."""

    OVERLAP_DETECTED = "overlap_detected"
    """检测到重叠 / Overlap detected."""

    BOUNDARY_VIOLATED = "boundary_violated"
    """边界违规 / Boundary violated."""

    WEIGHT_LIMIT_EXCEEDED = "weight_limit_exceeded"
    """超出重量限制 / Weight limit exceeded."""

    NO_FEASIBLE_SOLUTION = "no_feasible_solution"
    """无可行解 / No feasible solution."""

    DUPLICATE_ITEM = "duplicate_item"
    """重复物品 / Duplicate item."""

    PACKING_FAILED = "packing_failed"
    """装箱失败 / Packing failed."""

    @property
    def description(self) -> str:
        """获取错误描述 / Get error description.

        Returns:
            中英文错误描述 / Bilingual error description.
        """
        return _DESCRIPTIONS.get(self, self.value)


_DESCRIPTIONS: dict[Bpp2dErrors, str] = {
    Bpp2dErrors.ITEM_NOT_FOUND: "物品未找到 / Item not found",
    Bpp2dErrors.CONSTRAINT_NOT_FOUND: "约束未找到 / Constraint not found",
    Bpp2dErrors.INVALID_DIMENSION: "无效尺寸 / Invalid dimension",
    Bpp2dErrors.INVALID_POSITION: "无效位置 / Invalid position",
    Bpp2dErrors.OVERLAP_DETECTED: "检测到重叠 / Overlap detected",
    Bpp2dErrors.BOUNDARY_VIOLATED: "边界违规 / Boundary violated",
    Bpp2dErrors.WEIGHT_LIMIT_EXCEEDED: ("超出重量限制 / Weight limit exceeded"),
    Bpp2dErrors.NO_FEASIBLE_SOLUTION: "无可行解 / No feasible solution",
    Bpp2dErrors.DUPLICATE_ITEM: "重复物品 / Duplicate item",
    Bpp2dErrors.PACKING_FAILED: "装箱失败 / Packing failed",
}
