"""CSP1D 列生成服务 / CSP1D column generation service."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ospf_python.framework.csp1d.domain.material.model.shadow_price_map import (
    ShadowPriceMap,
)
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed, Ok, Result

if TYPE_CHECKING:
    from ospf_python.framework.csp1d.application.model.csp1d_solution import (
        Csp1dSolution,
    )


@dataclass(frozen=True)
class ColumnRecord:
    """列记录 / Column record.

    记录列生成中新增或移除的列信息。
    Records information about columns added or removed
    during column generation.

    Attributes:
        name: 列名称 / Column name.
        coefficients: 列系数 / Column coefficients.
        reduced_cost: 缩减成本 / Reduced cost.
    """

    name: str
    coefficients: tuple[float, ...]
    reduced_cost: float


class Csp1dColumnGeneration:
    """列生成生命周期管理 / Column generation lifecycle manager.

    管理列生成算法的完整生命周期，包括初始注册、
    增删列、刷新影子价格、终止和解提取。
    Manages the full lifecycle of the column generation
    algorithm, including initial registration, column
    addition/removal, shadow price refresh, finalization,
    and solution extraction.

    Attributes:
        _shadow_prices: 影子价格映射 / Shadow price map.
        _columns: 当前活跃列 / Currently active columns.
        _iteration: 当前迭代次数 / Current iteration count.
        _max_iterations: 最大迭代次数 / Maximum iterations.
        _converged: 是否已收敛 / Whether converged.
    """

    def __init__(
        self,
        *,
        max_iterations: int = 100,
    ) -> None:
        """初始化列生成管理器 / Initialize column generation manager.

        Args:
            max_iterations: 最大迭代次数 / Maximum iterations.
        """
        self._shadow_prices = ShadowPriceMap()
        self._columns: list[ColumnRecord] = []
        self._iteration: int = 0
        self._max_iterations: int = max_iterations
        self._converged: bool = False

    def register(
        self,
        initial_columns: tuple[ColumnRecord, ...],
    ) -> Result[None, str, object]:
        """注册初始列 / Register initial columns.

        在列生成开始前注册初始切割方案列。
        Registers initial cutting plan columns before
        column generation begins.

        Args:
            initial_columns: 初始列集合 / Initial column set.

        Returns:
            注册结果 / Registration result.
        """
        if not initial_columns:
            return Failed(
                ErrorCode.ILLEGAL_ARGUMENT,
                "初始列集合不能为空 / Initial columns must not be empty",
            )
        self._columns.extend(initial_columns)
        self._iteration = 0
        self._converged = False
        return Ok(None)

    def add_columns(
        self,
        new_columns: tuple[ColumnRecord, ...],
    ) -> Result[None, str, object]:
        """新增列 / Add new columns.

        向当前模型中追加新生成的切割方案列。
        Appends newly generated cutting plan columns
        to the current model.

        Args:
            new_columns: 待添加的列 / Columns to add.

        Returns:
            操作结果 / Operation result.
        """
        if not new_columns:
            return Ok(None)
        self._columns.extend(new_columns)
        return Ok(None)

    def remove_columns(
        self,
        column_names: tuple[str, ...],
    ) -> Result[None, str, object]:
        """移除列 / Remove columns.

        按名称移除不再有价值的切割方案列。
        Removes cutting plan columns by name that are
        no longer valuable.

        Args:
            column_names: 待移除的列名称 / Column names to remove.

        Returns:
            操作结果 / Operation result.
        """
        name_set = set(column_names)
        self._columns = [c for c in self._columns if c.name not in name_set]
        return Ok(None)

    def refresh_shadow_price(
        self,
        updater: Callable[[ShadowPriceMap], None],
    ) -> Result[None, str, object]:
        """刷新影子价格 / Refresh shadow prices.

        通过回调函数更新影子价格映射。
        Updates the shadow price map via a callback.

        Args:
            updater: 价格更新回调 / Price update callback.

        Returns:
            操作结果 / Operation result.
        """
        updater(self._shadow_prices)
        self._iteration += 1
        if self._iteration >= self._max_iterations:
            self._converged = True
        return Ok(None)

    def finalize(self) -> Result[None, str, object]:
        """终止列生成 / Finalize column generation.

        标记列生成迭代完成，准备进入最终 MILP 阶段。
        Marks column generation as complete, preparing
        for the final MILP phase.

        Returns:
            操作结果 / Operation result.
        """
        self._converged = True
        return Ok(None)

    def extract_solution(
        self,
        extractor: Callable[[], Csp1dSolution],
    ) -> Result[Csp1dSolution, str, object]:
        """提取解决方案 / Extract solution.

        从求解器结果中提取最终解决方案。
        Extracts the final solution from solver results.

        Args:
            extractor: 解提取回调 / Solution extraction callback.

        Returns:
            解决方案 / Solution.
        """
        solution = extractor()
        return Ok(solution)

    @property
    def iteration(self) -> int:
        """当前迭代次数 / Current iteration count."""
        return self._iteration

    @property
    def converged(self) -> bool:
        """是否已收敛 / Whether converged."""
        return self._converged

    @property
    def shadow_prices(self) -> ShadowPriceMap:
        """影子价格映射 / Shadow price map."""
        return self._shadow_prices

    @property
    def active_columns(self) -> tuple[ColumnRecord, ...]:
        """当前活跃列 / Currently active columns."""
        return tuple(self._columns)
