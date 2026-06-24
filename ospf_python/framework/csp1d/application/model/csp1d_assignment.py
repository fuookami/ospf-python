"""CSP1D 切割分配模型 / CSP1D cutting assignment model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Csp1dAssignment:
    """切割分配结果 / Cutting assignment result.

    描述一条切割分配记录：使用指定材料和切割方案，
    执行若干次以满足生产需求。
    Describes a single cutting assignment record: uses
    the specified material and cutting plan, executed
    a given number of times to meet production demand.

    Attributes:
        material: 所用原材料名称 / Name of the material used.
        cutting_plan: 切割方案名称 / Name of the cutting plan.
        quantity: 执行次数 / Number of times to execute.
        waste: 余料总量 / Total waste produced.
    """

    material: str
    cutting_plan: str
    quantity: int
    waste: float
