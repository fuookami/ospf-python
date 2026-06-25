"""更优束编组最大化 / Better bunch maximization.

生成最大化束编组质量的目标函数数据，优先选择质量更高的
束编组配置。
Generates objective function data for maximizing bunch quality,
preferring higher-quality bunch configurations.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QualityObjectiveTerm:
    """质量目标函数项 / Quality objective function term.

    表示目标函数中一个束编组质量的加权项。
    Represents a weighted term of bunch quality in the
    objective function.

    Attributes:
        bunch_key: 束编组标识 / Bunch identifier.
        weight: 权重系数 / Weight coefficient.
        quality_score: 质量得分 / Quality score.
        variable_name: 关联变量名 / Associated variable name.
    """

    bunch_key: str
    weight: float
    quality_score: float
    variable_name: str


@dataclass(frozen=True)
class BetterBunchMaximization:
    """更优束编组最大化 / Better bunch maximization.

    构建最大化束编组质量的目标函数项，鼓励调度方案选择
    质量得分更高的束编组配置。适用于存在多种可选束编组
    方案且希望优选最佳方案的场景。
    Builds objective function terms for maximizing bunch quality,
    encouraging scheduling plans that select higher-quality
    bunch configurations. Applicable when multiple bunch
    configurations are available and the best one is preferred.

    Attributes:
        objective_name: 目标函数名称 / Objective function name.
        default_weight: 默认权重 / Default weight.
    """

    objective_name: str = "better_bunch_max"
    default_weight: float = 1.0

    def build_objective_terms(
        self,
        bunch_keys: tuple[str, ...],
        quality_scores: dict[str, float],
        weights: dict[str, float] | None = None,
    ) -> tuple[QualityObjectiveTerm, ...]:
        """构建目标函数项。

        Build objective function terms for all bunch keys.

        Args:
            bunch_keys: 束编组标识列表。/ Bunch key list.
            quality_scores: 质量得分映射。/ Quality score mapping.
            weights: 自定义权重映射。/ Custom weight mapping.

        Returns:
            目标函数项元组。/ Tuple of objective terms.
        """
        effective_weights = weights or {}
        terms: list[QualityObjectiveTerm] = []
        for bk in bunch_keys:
            weight = effective_weights.get(
                bk,
                self.default_weight,
            )
            score = quality_scores.get(bk, 0.0)
            if weight > 0.0 and score > 0.0:
                terms.append(
                    QualityObjectiveTerm(
                        bunch_key=bk,
                        weight=weight,
                        quality_score=score,
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
        return f"quality_{bunch_key}"
