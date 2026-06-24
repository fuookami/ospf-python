"""COPT 约束包装器 / COPT constraint wrapper.

封装 coptpy.Constr 对象，提供统一访问接口。
Wraps a coptpy.Constr object with a uniform access
interface.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import coptpy


@dataclass(frozen=True)
class CoptConstraint:
    """COPT 约束包装器 / COPT constraint wrapper.

    冻结数据类，持有对 coptpy 约束的引用并提供
    便捷访问属性。
    Frozen dataclass holding a reference to a coptpy
    constraint with convenience access properties.

    Attributes:
        constr: 底层 coptpy 约束 / The underlying
            coptpy constraint.
        name: 约束名称 / Constraint name.
        sense: 约束方向 / Constraint sense.
        rhs: 右端值 / Right-hand side value.
    """

    constr: coptpy.Constr  # type: ignore[attr-defined, name-defined]
    """底层 coptpy 约束 / The underlying coptpy
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
    def from_copt_constr(
        constr: coptpy.Constr,  # type: ignore[attr-defined]
    ) -> CoptConstraint:
        """从 coptpy 约束创建包装器 / Create wrapper
        from coptpy constraint.

        Args:
            constr: coptpy 约束 / The coptpy constraint.

        Returns:
            CoptConstraint 实例 / CoptConstraint instance.
        """
        sense_map: dict[str, str] = {
            "<": "<=",
            ">": ">=",
            "=": "=",
        }
        raw_sense = constr.sense
        return CoptConstraint(
            constr=constr,
            name=constr.name,
            sense=sense_map.get(raw_sense, raw_sense),
            rhs=constr.rhs,
        )
