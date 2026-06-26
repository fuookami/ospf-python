"""CSP1D MILP 模型封装 / CSP1D MILP model wrapper."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ospf_python.framework.csp1d.application.service.csp1d_final_milp_status import (
    Csp1dFinalMilpStatus,
)
from ospf_python.utils.functional.result import Ok, Result

if TYPE_CHECKING:
    from ospf_python.utils.error.error import Error


@dataclass(frozen=True)
class MilpVariable:
    """MILP 变量描述 / MILP variable descriptor.

    Attributes:
        name: 变量名 / Variable name.
        lower: 下界 / Lower bound.
        upper: 上界 / Upper bound.
        is_integer: 是否为整数变量 / Whether integer variable.
    """

    name: str
    lower: float = 0.0
    upper: float = float("inf")
    is_integer: bool = False


@dataclass(frozen=True)
class MilpConstraint:
    """MILP 约束描述 / MILP constraint descriptor.

    Attributes:
        name: 约束名 / Constraint name.
        coefficients: 系数字典 / Coefficients dict.
        sense: 约束方向（<=, >=, ==） / Constraint sense.
        rhs: 右端值 / Right-hand side value.
    """

    name: str
    coefficients: tuple[tuple[str, float], ...]
    sense: str
    rhs: float


class Csp1dMilp:
    """MILP 模型封装 / MILP model wrapper.

    封装混合整数线性规划模型的构建和管理。
    Wraps the construction and management of a mixed
    integer linear programming model.

    Attributes:
        _variables: 变量列表 / Variable list.
        _constraints: 约束列表 / Constraint list.
        _objective: 目标函数系数 / Objective coefficients.
        _status: 求解状态 / Solving status.
    """

    def __init__(self) -> None:
        """初始化空 MILP 模型 / Initialize empty MILP model."""
        self._variables: list[MilpVariable] = []
        self._constraints: list[MilpConstraint] = []
        self._objective: dict[str, float] = {}
        self._status: Csp1dFinalMilpStatus = Csp1dFinalMilpStatus.INFEASIBLE

    def add_variable(
        self,
        *,
        name: str,
        lower: float = 0.0,
        upper: float = float("inf"),
        is_integer: bool = False,
    ) -> Result[None, str, Error[Any]]:
        """添加变量 / Add a variable.

        Args:
            name: 变量名 / Variable name.
            lower: 下界 / Lower bound.
            upper: 上界 / Upper bound.
            is_integer: 是否整数 / Whether integer.

        Returns:
            操作结果 / Operation result.
        """
        self._variables.append(
            MilpVariable(
                name=name,
                lower=lower,
                upper=upper,
                is_integer=is_integer,
            )
        )
        return Ok(None)

    def add_constraint(
        self,
        *,
        name: str,
        coefficients: tuple[tuple[str, float], ...],
        sense: str,
        rhs: float,
    ) -> Result[None, str, Error[Any]]:
        """添加约束 / Add a constraint.

        Args:
            name: 约束名 / Constraint name.
            coefficients: 系数对 / Coefficient pairs.
            sense: 方向（<=, >=, ==） / Sense.
            rhs: 右端值 / Right-hand side.

        Returns:
            操作结果 / Operation result.
        """
        self._constraints.append(
            MilpConstraint(
                name=name,
                coefficients=coefficients,
                sense=sense,
                rhs=rhs,
            )
        )
        return Ok(None)

    def set_objective(
        self,
        coefficients: dict[str, float],
    ) -> Result[None, str, Error[Any]]:
        """设置目标函数 / Set objective function.

        Args:
            coefficients: 变量名到系数的映射 / Variable name
                to coefficient mapping.

        Returns:
            操作结果 / Operation result.
        """
        self._objective = dict(coefficients)
        return Ok(None)

    def set_status(self, status: Csp1dFinalMilpStatus) -> None:
        """设置求解状态 / Set solving status.

        Args:
            status: 求解状态 / Solving status.
        """
        self._status = status

    @property
    def variables(self) -> tuple[MilpVariable, ...]:
        """所有变量 / All variables."""
        return tuple(self._variables)

    @property
    def constraints(self) -> tuple[MilpConstraint, ...]:
        """所有约束 / All constraints."""
        return tuple(self._constraints)

    @property
    def objective(self) -> dict[str, float]:
        """目标函数系数 / Objective coefficients."""
        return dict(self._objective)

    @property
    def status(self) -> Csp1dFinalMilpStatus:
        """求解状态 / Solving status."""
        return self._status
