"""三维形状抽象基类。

3D shape abstract base class.
"""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.math.geometry.box3 import Box3


class Shape3(abc.ABC):
    """三维形状的抽象基类。

    Abstract base class for 3D shapes.

    所有三维形状需实现体积和包围盒方法。
    All 3D shapes must implement volume and
    bounding box methods.
    """

    @abc.abstractmethod
    def volume(self) -> float:
        """计算体积。

        Compute volume.

        Returns:
            体积值。/ Volume value.
        """

    @abc.abstractmethod
    def bounding_box(self) -> Box3:
        """获取轴对齐包围盒。

        Get axis-aligned bounding box.

        Returns:
            包围盒。/ Bounding box.
        """
