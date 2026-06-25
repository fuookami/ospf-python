"""资源类型枚举 / Resource type enumeration.

定义甘特调度中可用的资源类型。
Defines available resource types in gantt scheduling.
"""

from __future__ import annotations

import enum


class ResourceType(enum.Enum):
    """资源类型 / Resource type.

    甘特调度中的资源分类，用于区分不同种类的生产资源。
    Resource categories in gantt scheduling, used to distinguish
    different kinds of production resources.

    Attributes:
        value: 枚举值 / The enum value.
    """

    MACHINE = "machine"
    """机器设备 / Machine equipment."""

    WORKER = "worker"
    """人工劳动力 / Human worker."""

    TOOL = "tool"
    """工装夹具 / Tool or fixture."""

    MATERIAL = "material"
    """原材料 / Raw material."""
