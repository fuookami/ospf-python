"""解上下文 / Solution context.

管理 BPP1D 解的注册与查询。
Manages registration and lookup of BPP1D solutions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.bpp1d.domain.solution.model.solution import (
        Solution,
    )


@dataclass(frozen=True)
class SolutionContext:
    """解上下文 / Solution context.

    持有已注册解的字典，支持注册和查询操作。
    Holds a dictionary of registered solutions, supporting
    registration and lookup operations.

    Attributes:
        solutions: 已注册解映射（键 -> 解）/
            Registered solutions mapping (key -> solution).
    """

    solutions: dict[str, Solution] = field(
        default_factory=dict,
    )
    """已注册解映射 / Registered solutions mapping."""

    @staticmethod
    def create(
        *,
        solutions: dict[str, Solution] | None = None,
    ) -> SolutionContext:
        """创建解上下文 / Create solution context.

        Args:
            solutions: 初始解映射，默认空 /
                Initial solutions mapping, default empty.

        Returns:
            解上下文实例 / SolutionContext instance.
        """
        return SolutionContext(
            solutions=dict(solutions) if solutions else {},
        )

    def register(
        self,
        solution: Solution,
    ) -> SolutionContext:
        """注册解 / Register solution.

        Args:
            solution: 要注册的解 / Solution to register.

        Returns:
            包含新解的上下文 / Context with the new solution.
        """
        new_solutions = dict(self.solutions)
        new_solutions[solution.solution_key] = solution
        return SolutionContext(solutions=new_solutions)

    def get(self, solution_key: str) -> Solution | None:
        """查询解 / Lookup solution.

        Args:
            solution_key: 解键 / Solution key.

        Returns:
            解实例或 None / Solution instance or None.
        """
        return self.solutions.get(solution_key)

    def get_best(self) -> Solution | None:
        """获取最优解 / Get best solution.

        Returns:
            目标函数值最小的解，或 None。
            Solution with smallest objective value, or None.
        """
        if not self.solutions:
            return None
        return min(
            self.solutions.values(),
            key=lambda s: s.objective_value,
        )

    def get_all(self) -> tuple[Solution, ...]:
        """获取所有解 / Get all solutions.

        Returns:
            所有已注册解的元组。
            Tuple of all registered solutions.
        """
        return tuple(self.solutions.values())

    @property
    def count(self) -> int:
        """解数量 / Solution count.

        Returns:
            已注册解的数量。
            Number of registered solutions.
        """
        return len(self.solutions)
