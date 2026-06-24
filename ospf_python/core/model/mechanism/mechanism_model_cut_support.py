"""机制模型切割支持 / Mechanism model cut support.

为机制模型提供切割平面的支持。
Provides cutting plane support for mechanism models.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MechanismModelCutSupport:
    """机制模型切割支持 / Mechanism model cut support.

    管理模型中的切割平面添加和维护。
    Manages the addition and maintenance of cutting planes
    in a model.

    Attributes:
        cuts: 已添加的切割平面列表 / List of added cutting
            planes.
    """

    cuts: list[object] = field(default_factory=list)

    def add_cut(self, cut: object) -> None:
        """添加切割平面 / Add a cutting plane.

        Args:
            cut: 切割平面对象 / The cutting plane object.
        """
        self.cuts.append(cut)

    def clear_cuts(self) -> None:
        """清除所有切割平面 / Clear all cutting planes."""
        self.cuts.clear()

    @property
    def cut_count(self) -> int:
        """切割平面数量 / Number of cutting planes."""
        return len(self.cuts)
