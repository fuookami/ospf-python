"""CSP1D 机器模型 / CSP1D machine model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Machine:
    """切割机器定义 / Cutting machine definition.

    描述切割设备的能力参数，包括最大加工宽度和切割损耗。
    Describes the capability parameters of a cutting
    device, including max processing width and cut loss.

    Attributes:
        name: 机器名称 / Machine name.
        max_width: 最大加工宽度 / Maximum processing width.
        cut_loss: 切割损耗宽度 / Width lost per cut operation.
    """

    name: str
    max_width: float
    cut_loss: float
