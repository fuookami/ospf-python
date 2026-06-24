"""CSP1D 解方案增强服务 / CSP1D solution enrichment service."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.csp1d.application.model.csp1d_solution import (
        Csp1dSolution,
    )


class Csp1dSolutionEnrichment:
    """解方案增强服务 / Solution enrichment service.

    为解决方案附加额外的 KPI、trace 和渲染信息。
    Attaches additional KPIs, traces, and rendering
    information to the solution.

    Attributes:
        _kpi_data: KPI 数据 / KPI data.
        _trace_data: 追踪数据 / Trace data.
        _render_data: 渲染数据 / Render data.
    """

    def __init__(self) -> None:
        """初始化增强服务 / Initialize enrichment service."""
        self._kpi_data: dict[str, float] = {}
        self._trace_data: list[str] = []
        self._render_data: dict[str, object] = {}

    def add_kpi(
        self,
        name: str,
        value: float,
    ) -> None:
        """添加 KPI 指标 / Add a KPI metric.

        Args:
            name: 指标名称 / Metric name.
            value: 指标值 / Metric value.
        """
        self._kpi_data[name] = value

    def add_trace(self, message: str) -> None:
        """添加追踪信息 / Add trace message.

        Args:
            message: 追踪消息 / Trace message.
        """
        self._trace_data.append(message)

    def set_render_data(
        self,
        key: str,
        value: object,
    ) -> None:
        """设置渲染数据 / Set render data.

        Args:
            key: 数据键 / Data key.
            value: 数据值 / Data value.
        """
        self._render_data[key] = value

    def enrich(
        self,
        solution: Csp1dSolution,
    ) -> EnrichedSolution:
        """增强解决方案 / Enrich the solution.

        Args:
            solution: 原始解决方案 / Original solution.

        Returns:
            增强后的解决方案 / Enriched solution.
        """
        return EnrichedSolution(
            solution=solution,
            kpi_data=dict(self._kpi_data),
            trace_data=tuple(self._trace_data),
            render_data=dict(self._render_data),
        )

    def clear(self) -> None:
        """清空增强数据 / Clear enrichment data."""
        self._kpi_data.clear()
        self._trace_data.clear()
        self._render_data.clear()


class EnrichedSolution:
    """增强后的解决方案 / Enriched solution.

    包含原始解决方案及附加的 KPI、追踪和渲染信息。
    Contains the original solution plus attached KPIs,
    traces, and rendering information.

    Attributes:
        solution: 原始解决方案 / Original solution.
        kpi_data: KPI 数据 / KPI data.
        trace_data: 追踪数据 / Trace data.
        render_data: 渲染数据 / Render data.
    """

    def __init__(
        self,
        *,
        solution: Csp1dSolution,
        kpi_data: dict[str, float],
        trace_data: tuple[str, ...],
        render_data: dict[str, object],
    ) -> None:
        """初始化增强解决方案 / Initialize enriched solution.

        Args:
            solution: 原始解决方案 / Original solution.
            kpi_data: KPI 数据 / KPI data.
            trace_data: 追踪数据 / Trace data.
            render_data: 渲染数据 / Render data.
        """
        self._solution = solution
        self._kpi_data = kpi_data
        self._trace_data = trace_data
        self._render_data = render_data

    @property
    def solution(self) -> Csp1dSolution:
        """原始解决方案 / Original solution."""
        return self._solution

    @property
    def kpi_data(self) -> dict[str, float]:
        """KPI 数据 / KPI data."""
        return dict(self._kpi_data)

    @property
    def trace_data(self) -> tuple[str, ...]:
        """追踪数据 / Trace data."""
        return self._trace_data

    @property
    def render_data(self) -> dict[str, object]:
        """渲染数据 / Render data."""
        return dict(self._render_data)
