"""迁移操作 / Migration operation.

管理多岛模型中的个体迁移。
Manages individual migration in island models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.core.solver.heuristic.population import (
        Population,
    )


@dataclass
class Migration:
    """迁移操作 / Migration operation.

    在多个种群间执行个体迁移。
    Executes individual migration between populations.

    Attributes:
        rate: 迁移概率 / Migration rate.
        size: 迁移数量 / Migration size.
    """

    rate: float = 0.1
    """迁移概率 / Migration rate."""

    size: int = 1
    """迁移数量 / Migration size."""

    def migrate(
        self,
        source: Population,
        destination: Population,
    ) -> None:
        """执行迁移 / Execute migration.

        Args:
            source: 源种群 / Source population.
            destination: 目标种群 / Destination population.
        """
