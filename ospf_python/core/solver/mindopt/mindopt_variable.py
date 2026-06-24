"""MindOPT 变量包装器 / MindOPT variable wrapper.

封装 mindoptpy.Var 对象，提供统一访问接口。
Wraps a mindoptpy.Var object with a uniform access
interface.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import mindoptpy


@dataclass(frozen=True)
class MindOPTVariable:
    """MindOPT 变量包装器 / MindOPT variable wrapper.

    冻结数据类，持有对 mindoptpy 变量的引用并提供
    便捷访问属性。
    Frozen dataclass holding a reference to a mindoptpy
    variable with convenience access properties.

    Attributes:
        var: 底层 mindoptpy 变量 / The underlying
            mindoptpy variable.
        name: 变量名称 / Variable name.
        lb: 下界 / Lower bound.
        ub: 上界 / Upper bound.
        vtype: 变量类型 / Variable type.
    """

    var: mindoptpy.Var
    """底层 mindoptpy 变量 / The underlying mindoptpy
    variable."""

    name: str = ""
    """变量名称 / Variable name."""

    lb: float = 0.0
    """下界 / Lower bound."""

    ub: float = float("inf")
    """上界 / Upper bound."""

    vtype: str = "C"
    """变量类型 / Variable type (C/B/I/S/N)."""

    @property
    def is_integer(self) -> bool:
        """是否为整数变量 / Whether integer variable.

        Returns:
            整数或二进制变量时返回 True / True when
            integer or binary variable.
        """
        return self.vtype in ("I", "B")

    @property
    def is_binary(self) -> bool:
        """是否为二进制变量 / Whether binary variable.

        Returns:
            二进制变量时返回 True / True when binary
            variable.
        """
        return self.vtype == "B"

    @property
    def is_continuous(self) -> bool:
        """是否为连续变量 / Whether continuous variable.

        Returns:
            连续变量时返回 True / True when continuous
            variable.
        """
        return self.vtype == "C"

    @staticmethod
    def from_mindopt_var(
        var: mindoptpy.Var,
    ) -> MindOPTVariable:
        """从 mindoptpy 变量创建包装器 / Create wrapper
        from mindoptpy variable.

        Args:
            var: mindoptpy 变量 / The mindoptpy variable.

        Returns:
            MindOPTVariable 实例 / MindOPTVariable
            instance.
        """
        return MindOPTVariable(
            var=var,
            name=var.name,
            lb=var.lb,
            ub=var.ub,
            vtype=var.vtype,
        )
