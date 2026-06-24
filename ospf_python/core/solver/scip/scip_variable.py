"""SCIP 变量包装器 / SCIP variable wrapper.

封装 pyscipopt.Variable 对象，提供统一访问接口。
Wraps a pyscipopt.Variable object with a uniform access
interface.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyscipopt import Variable as ScipVar


@dataclass(frozen=True)
class ScipVariable:
    """SCIP 变量包装器 / SCIP variable wrapper.

    冻结数据类，持有对 pyscipopt 变量的引用并提供
    便捷访问属性。
    Frozen dataclass holding a reference to a pyscipopt
    variable with convenience access properties.

    Attributes:
        var: 底层 SCIP 变量 / The underlying SCIP variable.
        name: 变量名称 / Variable name.
        lb: 下界 / Lower bound.
        ub: 上界 / Upper bound.
        vtype: 变量类型 / Variable type.
    """

    var: ScipVar
    """底层 SCIP 变量 / The underlying SCIP variable."""

    name: str = ""
    """变量名称 / Variable name."""

    lb: float = 0.0
    """下界 / Lower bound."""

    ub: float = float("inf")
    """上界 / Upper bound."""

    vtype: str = "CONTINUOUS"
    """变量类型 / Variable type."""

    @property
    def is_integer(self) -> bool:
        """是否为整数变量 / Whether integer variable.

        Returns:
            整数或二进制变量时返回 True / True when
            integer or binary variable.
        """
        return self.vtype in ("INTEGER", "BINARY")

    @property
    def is_binary(self) -> bool:
        """是否为二进制变量 / Whether binary variable.

        Returns:
            二进制变量时返回 True / True when binary
            variable.
        """
        return self.vtype == "BINARY"

    @property
    def is_continuous(self) -> bool:
        """是否为连续变量 / Whether continuous variable.

        Returns:
            连续变量时返回 True / True when continuous
            variable.
        """
        return self.vtype == "CONTINUOUS"

    @staticmethod
    def from_scip_var(
        var: ScipVar,
    ) -> ScipVariable:
        """从 SCIP 变量创建包装器 / Create wrapper from
        SCIP variable.

        Args:
            var: SCIP 变量 / The SCIP variable.

        Returns:
            ScipVariable 实例 / ScipVariable instance.
        """
        vtype = var.vtype()
        return ScipVariable(
            var=var,
            name=var.name,
            lb=var.getLbOriginal(),
            ub=var.getUbOriginal(),
            vtype=vtype,
        )
