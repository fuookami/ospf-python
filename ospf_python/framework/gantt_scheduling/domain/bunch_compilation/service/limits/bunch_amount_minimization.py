"""束编组数量最小化 / Bunch amount minimization.

生成最小化束编组数量的目标函数数据，减少束编组总数以
降低切换和管理成本。
Generates objective function data for minimizing the number
of bunch groups, reducing total bunch count to lower switching
and management costs.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AmountObjectiveTerm:
    """数量目标函数项 / Amount objective function term.

    表示目标函数中一个束编组数量的加权项。
    Represents a weighted term of bunch count in the
    objective function.

    Attributes:
        bunch_key: 束编组标识 / Bunch identifier.
        weight: 权重系数 / Weight coefficient.
        variable_name: 关联变量名 / Associated variable name.
    """

    bunch_key: str
    weight: float
    variable_name: str


@dataclass(frozen=True)
class BunchAmountMinimization:
    """束编组数量最小化 / Bunch amount minimization.

    构建最小化束编组使用数量的目标函数项，鼓励调度方案
    使用更少的束编组。适用于希望合并小批次、减少束编组
    切换次数的场景。
    Builds objective function terms for minimizing the number
    of bunch groups used, encouraging scheduling plans with
    fewer bunches. Applicable when the goal is to merge small
    batches and reduce bunch switching frequency.

    Attributes:
        objective_name: 目标函数名称 / Objective function name.
        default_weight: 默认权重 / Default weight.
    """

    objective_name: str = "bunch_amount_min"
    default_weight: float = 1.0

    def build_objective_terms(
        self,
        bunch_keys: tuple[str, ...],
        weights: dict[str, float] | None = None,
    ) -> tuple[AmountObjectiveTerm, ...]:
        """构建目标函数项。

        Build objective function terms for all bunch keys.

        Args:
            bunch_keys: 束编组标识列表。/ Bunch key list.
            weights: 自定义权重映射。/ Custom weight mapping.

        Returns:
            目标函数项元组。/ Tuple of objective terms.
        """
        effective_weights = weights or {}
        terms: list[AmountObjectiveTerm] = []
        for bk in bunch_keys:
            weight = effective_weights.get(
                bk,
                self.default_weight,
            )
            if weight > 0.0:
                terms.append(
                    AmountObjectiveTerm(
                        bunch_key=bk,
                        weight=weight,
                        variable_name=self._var_name(bk),
                    )
                )
        return tuple(terms)

    def objective_name_for(
        self,
        bunch_key: str,
    ) -> str:
        """生成束编组特定的目标函数名称。

        Generate bunch-specific objective function name.

        Args:
            bunch_key: 束编组标识。/ Bunch identifier.

        Returns:
            目标函数名称。/ Objective function name.
        """
        return f"{self.objective_name}_{bunch_key}"

    def _var_name(self, bunch_key: str) -> str:
        """生成变量名称 / Generate variable name.

        Args:
            bunch_key: 束编组标识。/ Bunch identifier.

        Returns:
            变量名称字符串。/ Variable name string.
        """
        return f"amount_{bunch_key}"
