"""三维位置定义 / 3D position definition.

航空器货舱内物品的三维坐标位置定义。
3D coordinate position definition for items within
an aircraft cargo hold.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Position:
    """三维位置 / 3D position.

    描述货舱内某个物件的三维坐标及所属甲板。
    Describes the 3D coordinates of an object within
    a cargo hold, associated with a deck.

    Attributes:
        x: 纵向坐标 (m) / Longitudinal coordinate (m).
        y: 横向坐标 (m) / Lateral coordinate (m).
        z: 垂向坐标 (m) / Vertical coordinate (m).
        deck_id: 所属甲板标识 / Associated deck identifier.
    """

    x: float
    """纵向坐标 (m) / Longitudinal coordinate (m)."""

    y: float
    """横向坐标 (m) / Lateral coordinate (m)."""

    z: float
    """垂向坐标 (m) / Vertical coordinate (m)."""

    deck_id: str
    """所属甲板标识 / Associated deck identifier."""

    @staticmethod
    def create(
        *,
        x: float,
        y: float,
        z: float,
        deck_id: str,
    ) -> Position:
        """创建位置实例 / Create position instance.

        Args:
            x: 纵向坐标 / Longitudinal coordinate.
            y: 横向坐标 / Lateral coordinate.
            z: 垂向坐标 / Vertical coordinate.
            deck_id: 所属甲板标识 / Deck identifier.

        Returns:
            位置实例 / Position instance.
        """
        return Position(x=x, y=y, z=z, deck_id=deck_id)

    @staticmethod
    def origin(*, deck_id: str) -> Position:
        """创建原点位置 / Create origin position.

        Args:
            deck_id: 所属甲板标识 / Deck identifier.

        Returns:
            原点位置实例 / Origin position instance.
        """
        return Position(x=0.0, y=0.0, z=0.0, deck_id=deck_id)

    def distance_to(self, other: Position) -> float:
        """计算到另一个位置的欧氏距离 / Calculate Euclidean distance to another position.

        仅当两个位置在同一甲板时有效。
        Only valid when both positions are on the same deck.

        Args:
            other: 目标位置 / Target position.

        Returns:
            欧氏距离 (m) / Euclidean distance (m).
        """
        return float(
            (
                (self.x - other.x) ** 2
                + (self.y - other.y) ** 2
                + (self.z - other.z) ** 2
            )
            ** 0.5
        )

    def translated(
        self,
        *,
        dx: float = 0.0,
        dy: float = 0.0,
        dz: float = 0.0,
    ) -> Position:
        """创建平移后的位置 / Create translated position.

        Args:
            dx: 纵向偏移 / Longitudinal offset.
            dy: 横向偏移 / Lateral offset.
            dz: 垂向偏移 / Vertical offset.

        Returns:
            平移后的新位置实例 / New translated position instance.
        """
        return Position(
            x=self.x + dx,
            y=self.y + dy,
            z=self.z + dz,
            deck_id=self.deck_id,
        )

    def is_same_deck(self, other: Position) -> bool:
        """判断是否在同一甲板 / Check if on the same deck.

        Args:
            other: 另一个位置 / Another position.

        Returns:
            同一甲板时为 True / True if on the same deck.
        """
        return self.deck_id == other.deck_id
