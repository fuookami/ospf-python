"""线性三元组弹性构建器 / Linear triad elastic builder.

为线性约束提供弹性变量支持。
Provides elastic variable support for linear constraints.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.core.model.intermediate.linear_triad_model import (
        LinearTriadModel,
    )


class LinearTriadElasticBuilder:
    """线性三元组弹性构建器 / Linear triad elastic builder.

    为硬约束添加弹性变量，使其可以在一定范围内被违反。
    Adds elastic variables to hard constraints so they can
    be violated within a certain range.

    Methods:
        add_elastic: 为指定约束添加弹性变量 / Add elastic
            variables to a specified constraint.
    """

    @staticmethod
    def add_elastic(
        model: LinearTriadModel,
        constraint_name: str,
        penalty: float = 1.0,
    ) -> None:
        """为指定约束添加弹性变量 / Add elastic variables.

        Args:
            model: 线性三元组模型 / The linear triad model.
            constraint_name: 约束名称 / The constraint name.
            penalty: 弹性惩罚系数 / The elastic penalty
                coefficient.
        """
        if constraint_name not in model.constraints:
            return
        row = model.constraints[constraint_name]
        elastic_name = f"elastic_{constraint_name}"
        row[elastic_name] = penalty
