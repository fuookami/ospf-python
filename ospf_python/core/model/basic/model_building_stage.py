"""模型构建阶段枚举 / Model building stage enumeration.

定义优化模型从初始化到求解的各阶段。
Defines the stages of an optimization model from
initialization to solving.
"""

from __future__ import annotations

import enum


class ModelBuildingStage(enum.Enum):
    """模型构建阶段 / Model building stage.

    跟踪模型在构建和求解生命周期中的当前位置。
    Tracks the current position of a model in its build
    and solve lifecycle.

    Attributes:
        value: 阶段整数值 / The integer stage value.
    """

    INIT = 0
    """初始化 / Initialized."""

    REGISTERING = 1
    """注册变量和约束中 / Registering variables and constraints."""

    BUILDING = 2
    """构建模型中 / Building the model."""

    SOLVING = 3
    """求解中 / Solving."""

    EXTRACTING = 4
    """提取结果中 / Extracting results."""
