"""甲板定义 / Deck definition.

航空器货舱甲板定义。
Aircraft cargo hold deck definition.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DeckPosition(Enum):
    """甲板位置 / Deck position.

    描述甲板在航空器中的位置。
    Describes the deck position within an aircraft.
    """

    UPPER = "upper"
    """上层甲板 / Upper deck."""

    LOWER = "lower"
    """下层甲板 / Lower deck."""


@dataclass(frozen=True)
class Deck:
    """甲板 / Deck.

    描述航空器货舱中的一个甲板层，包含尺寸和承载能力。
    Describes a deck level in an aircraft cargo hold,
    with dimensions and load capacity.

    Attributes:
        deck_id: 甲板标识 / Deck identifier.
        aircraft_type: 关联机型 / Associated aircraft type.
        width: 甲板宽度 (m) / Deck width (m).
        height: 甲板净高 (m) / Deck clear height (m).
        depth: 甲板纵深 (m) / Deck depth (m).
        max_load: 最大承载重量 (kg) / Maximum load capacity (kg).
        position: 甲板位置 / Deck position.
    """

    deck_id: str
    """甲板标识 / Deck identifier."""

    aircraft_type: str
    """关联机型 / Associated aircraft type."""

    width: float
    """甲板宽度 (m) / Deck width (m)."""

    height: float
    """甲板净高 (m) / Deck clear height (m)."""

    depth: float
    """甲板纵深 (m) / Deck depth (m)."""

    max_load: float
    """最大承载重量 (kg) / Maximum load capacity (kg)."""

    position: DeckPosition
    """甲板位置 / Deck position."""

    @staticmethod
    def create(
        *,
        deck_id: str,
        aircraft_type: str,
        width: float,
        height: float,
        depth: float,
        max_load: float,
        position: DeckPosition = DeckPosition.LOWER,
    ) -> Deck:
        """创建甲板实例 / Create deck instance.

        Args:
            deck_id: 甲板标识 / Deck identifier.
            aircraft_type: 关联机型 / Associated aircraft type.
            width: 甲板宽度 / Deck width.
            height: 甲板净高 / Deck clear height.
            depth: 甲板纵深 / Deck depth.
            max_load: 最大承载重量 / Max load capacity.
            position: 甲板位置，默认下层 / Position, default lower.

        Returns:
            甲板实例 / Deck instance.
        """
        return Deck(
            deck_id=deck_id,
            aircraft_type=aircraft_type,
            width=width,
            height=height,
            depth=depth,
            max_load=max_load,
            position=position,
        )

    @property
    def volume(self) -> float:
        """甲板可用体积 / Deck available volume.

        Returns:
            宽 x 高 x 深 (m^3) / Width x Height x Depth (m^3).
        """
        return self.width * self.height * self.depth

    @property
    def floor_area(self) -> float:
        """甲板底面积 / Deck floor area.

        Returns:
            宽 x 深 (m^2) / Width x Depth (m^2).
        """
        return self.width * self.depth

    def with_max_load(self, max_load: float) -> Deck:
        """创建不同承载量的甲板 / Create deck with different max load.

        Args:
            max_load: 新最大承载重量 / New max load capacity.

        Returns:
            新甲板实例 / New deck instance.
        """
        return Deck(
            deck_id=self.deck_id,
            aircraft_type=self.aircraft_type,
            width=self.width,
            height=self.height,
            depth=self.depth,
            max_load=max_load,
            position=self.position,
        )
