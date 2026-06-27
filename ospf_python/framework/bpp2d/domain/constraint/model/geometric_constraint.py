"""几何约束模型 / Geometric constraint model.

定义二维装箱中的几何约束。
Defines geometric constraints for 2D bin packing.
"""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.framework.bpp2d.domain.constraint.model.constraint_base import (
    ConstraintBase,
    ConstraintType,
)


@dataclass(frozen=True)
class GeometricConstraint(ConstraintBase):
    """几何约束 / Geometric constraint.

    约束物品在容器中的几何放置条件。
    Constrains geometric placement conditions of items
    within a container.

    Attributes:
        constraint_key: 约束标识 / Constraint identifier.
        item_keys: 受约束物品键 / Constrained item keys.
        min_x: 最小 x 坐标 / Minimum x coordinate.
        max_x: 最大 x 坐标 / Maximum x coordinate.
        min_y: 最小 y 坐标 / Minimum y coordinate.
        max_y: 最大 y 坐标 / Maximum y coordinate.
        no_overlap: 是否禁止重叠 / Whether overlap is
            forbidden.
    """

    constraint_key: str
    """约束标识 / Constraint identifier."""

    item_keys: tuple[str, ...] = ()
    """受约束物品键 / Constrained item keys."""

    min_x: float = 0.0
    """最小 x 坐标，默认 0 / Minimum x, default 0."""

    max_x: float = float("inf")
    """最大 x 坐标，默认无穷大 / Max x, default inf."""

    min_y: float = 0.0
    """最小 y 坐标，默认 0 / Minimum y, default 0."""

    max_y: float = float("inf")
    """最大 y 坐标，默认无穷大 / Max y, default inf."""

    no_overlap: bool = True
    """是否禁止重叠，默认是 / No overlap, default yes."""

    @staticmethod
    def create(
        *,
        constraint_key: str,
        item_keys: tuple[str, ...] = (),
        min_x: float = 0.0,
        max_x: float = float("inf"),
        min_y: float = 0.0,
        max_y: float = float("inf"),
        no_overlap: bool = True,
    ) -> GeometricConstraint:
        """创建几何约束 / Create geometric constraint.

        Args:
            constraint_key: 约束标识 / Constraint identifier.
            item_keys: 受约束物品键 / Constrained item keys.
            min_x: 最小 x / Minimum x.
            max_x: 最大 x / Maximum x.
            min_y: 最小 y / Minimum y.
            max_y: 最大 y / Maximum y.
            no_overlap: 禁止重叠 / No overlap.

        Returns:
            几何约束实例 / GeometricConstraint instance.
        """
        return GeometricConstraint(
            constraint_key=constraint_key,
            item_keys=item_keys,
            min_x=min_x,
            max_x=max_x,
            min_y=min_y,
            max_y=max_y,
            no_overlap=no_overlap,
        )

    @property
    def constraint_type(self) -> ConstraintType:
        """获取约束类型 / Get constraint type.

        Returns:
            几何类型 / Geometric type.
        """
        return ConstraintType.GEOMETRIC

    @property
    def allowed_width(self) -> float:
        """获取允许的宽度范围 / Get allowed width range.

        Returns:
            max_x 减 min_x / Max x minus min x.
        """
        if self.max_x == float("inf"):
            return float("inf")
        return self.max_x - self.min_x

    @property
    def allowed_height(self) -> float:
        """获取允许的高度范围 / Get allowed height range.

        Returns:
            max_y 减 min_y / Max y minus min y.
        """
        if self.max_y == float("inf"):
            return float("inf")
        return self.max_y - self.min_y

    def applies_to(self, item_key: str) -> bool:
        """检查是否适用于指定物品 / Check if applies to item.

        当 item_keys 为空时，适用于所有物品。
        When item_keys is empty, applies to all items.

        Args:
            item_key: 物品键 / Item key.

        Returns:
            适用于该物品返回 True / True if applies.
        """
        if not self.item_keys:
            return True
        return item_key in self.item_keys

    def check_placement(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
    ) -> bool:
        """检查放置是否满足约束 / Check placement satisfies.

        验证物品放置在允许的几何范围内。
        Verifies the item placement is within the allowed
        geometric bounds.

        Args:
            x: 放置 x 坐标 / Placement x coordinate.
            y: 放置 y 坐标 / Placement y coordinate.
            width: 物品宽度 / Item width.
            height: 物品高度 / Item height.

        Returns:
            满足约束返回 True / True if satisfied.
        """
        if x < self.min_x:
            return False
        if y < self.min_y:
            return False
        if x + width > self.max_x:
            return False
        return not y + height > self.max_y
