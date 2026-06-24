"""模型准备 / Modeling preparation.

为求解器提供模型预处理和准备功能。
Provides model preprocessing and preparation
functionality for solvers.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ModelingPreparation:
    """模型准备 / Modeling preparation.

    冻结数据类，封装求解前的模型准备步骤。
    Frozen dataclass encapsulating model preparation
    steps before solving.

    Attributes:
        variable_count: 变量数量 / Variable count.
        constraint_count: 约束数量 / Constraint count.
        is_prepared: 是否已准备好 / Whether prepared.
        warnings: 准备阶段警告 / Preparation warnings.
    """

    variable_count: int = 0
    """变量数量 / Variable count."""

    constraint_count: int = 0
    """约束数量 / Constraint count."""

    is_prepared: bool = False
    """是否已准备好 / Whether prepared."""

    warnings: tuple[str, ...] = field(
        default_factory=tuple,
    )
    """准备阶段警告 / Preparation warnings."""

    @staticmethod
    def empty() -> ModelingPreparation:
        """创建空准备实例 / Create empty preparation.

        Returns:
            空准备实例 / Empty preparation instance.
        """
        return ModelingPreparation()

    @staticmethod
    def create(
        *,
        variable_count: int,
        constraint_count: int,
        warnings: tuple[str, ...] = (),
    ) -> ModelingPreparation:
        """创建已准备的实例 / Create a prepared instance.

        Args:
            variable_count: 变量数量 / Variable count.
            constraint_count: 约束数量 / Constraint count.
            warnings: 警告信息 / Warnings.

        Returns:
            已准备的实例 / Prepared instance.
        """
        return ModelingPreparation(
            variable_count=variable_count,
            constraint_count=constraint_count,
            is_prepared=True,
            warnings=warnings,
        )

    @property
    def total_elements(self) -> int:
        """获取元素总数 / Get total element count.

        Returns:
            变量与约束之和 / Sum of variables and
            constraints.
        """
        return self.variable_count + self.constraint_count
