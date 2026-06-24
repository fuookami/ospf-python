"""MindOPT 约束包装器 / MindOPT constraint wrapper.

封装 mindoptpy.Constr 对象，提供统一访问接口。
Wraps a mindoptpy.Constr object with a uniform access
interface.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import mindoptpy


@dataclass(frozen=True)
class MindOPTConstraint:
    """MindOPT 约束包装器 / MindOPT constraint wrapper.

    冻结数据类，持有对 mindoptpy 约束的引用并提供
    便捷访问属性。
    Frozen dataclass holding a reference to a mindoptpy
    constraint with convenience access properties.

    Attributes:
        constr: 底层 mindoptpy 约束 / The underlying
            mindoptpy constraint.
        name: 约束名称 / Constraint name.
        sense: 约束方向 / Constraint sense.
        rhs: 右端值 / Right-hand side value.
    """

    constr: mindoptpy.Constr
    """底层 mindoptpy 约束 / The underlying mindoptpy
    constraint."""

    name: str = ""
    """约束名称 / Constraint name."""

    sense: str = "<="
    """约束方向 / Constraint sense (<=, >=, ==)."""

    rhs: float = 0.0
    """右端值 / Right-hand side value."""

    @property
    def is_equality(self) -> bool:
        """是否为等式约束 / Whether equality constraint.

        Returns:
            等式约束时返回 True / True when equality
            constraint.
        """
        return self.sense == "="

    @property
    def is_inequality(self) -> bool:
        """是否为不等式约束 / Whether inequality
        constraint.

        Returns:
            不等式约束时返回 True / True when inequality
            constraint.
        """
        return self.sense in ("<=", ">=")

    @property
    def is_less_equal(self) -> bool:
        """是否为小于等于约束 / Whether less-equal
        constraint.

        Returns:
            小于等于约束时返回 True / True when
            less-equal constraint.
        """
        return self.sense == "<="

    @property
    def is_greater_equal(self) -> bool:
        """是否为大于等于约束 / Whether greater-equal
        constraint.

        Returns:
            大于等于约束时返回 True / True when
            greater-equal constraint.
        """
        return self.sense == ">="

    @staticmethod
    def from_mindopt_constr(
        constr: mindoptpy.Constr,
    ) -> MindOPTConstraint:
        """从 mindoptpy 约束创建包装器 / Create wrapper
        from mindoptpy constraint.

        Args:
            constr: mindoptpy 约束 / The mindoptpy
                constraint.

        Returns:
            MindOPTConstraint 实例 / MindOPTConstraint
            instance.
        """
        sense_map: dict[str, str] = {
            "<": "<=",
            ">": ">=",
            "=": "=",
        }
        raw_sense = constr.sense
        return MindOPTConstraint(
            constr=constr,
            name=constr.name,
            sense=sense_map.get(raw_sense, raw_sense),
            rhs=constr.rhs,
        )
