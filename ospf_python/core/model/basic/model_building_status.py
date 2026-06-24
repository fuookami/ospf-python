"""模型构建状态枚举 / Model building status enumeration.

定义模型构建过程的可能结果。
Defines the possible outcomes of a model building process.
"""

from __future__ import annotations

import enum


class ModelBuildingStatus(enum.Enum):
    """模型构建状态 / Model building status.

    表示模型构建完成后的状态。
    Represents the status after model building completes.

    Attributes:
        value: 状态整数值 / The integer status value.
    """

    SUCCESS = 0
    """构建成功 / Build succeeded."""

    FAILED = 1
    """构建失败 / Build failed."""

    INFEASIBLE = 2
    """模型不可行 / Model is infeasible."""
