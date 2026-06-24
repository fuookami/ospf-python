"""长方体视图类型。

Cuboid view type with offset.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ospf_python.math.geometry.point import Point3

if TYPE_CHECKING:
    from ospf_python.math.geometry.cuboid3 import Cuboid3


@dataclass(frozen=True)
class Cuboid3View:
    """长方体视图，支持带偏移的查看。

    Cuboid view with offset support.

    Attributes:
        cuboid: 底层长方体。/ Underlying cuboid.
        offset: 偏移向量。/ Offset vector.
    """

    cuboid: Cuboid3
    offset: Point3

    @property
    def origin(self) -> Point3:
        """视图原点（原点 + 偏移）。

        View origin (origin + offset).
        """
        return Point3(
            x=self.cuboid.origin.x + self.offset.x,
            y=self.cuboid.origin.y + self.offset.y,
            z=self.cuboid.origin.z + self.offset.z,
        )

    def contains(self, point: Point3) -> bool:
        """检查点是否在视图范围内。

        Check whether point is inside the view.

        Args:
            point: 待检查的点。/ Point to check.

        Returns:
            是否在视图内。/ Whether inside the view.
        """
        o = self.origin
        return (
            o.x <= point.x <= o.x + self.cuboid.width
            and o.y <= point.y <= o.y + self.cuboid.height
            and o.z <= point.z <= o.z + self.cuboid.depth
        )
