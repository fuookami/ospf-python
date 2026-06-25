"""束编组顶层聚合 / Bunch compilation top-level aggregation.

组合束编组编译域的顶层视图，整合模型、约束和解分析。
Combines the top-level view of the bunch compilation domain,
integrating the model, constraints, and solution analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ospf_python.framework.gantt_scheduling.domain.bunch_compilation.model.bunch_compilation_model import (
    BunchCompilationModel,
)
from ospf_python.framework.gantt_scheduling.domain.bunch_compilation.service.solution_analyzer import (
    FeasibilityReport,
    SolutionAnalyzer,
    SolutionQuality,
)


@dataclass(frozen=True)
class Aggregation:
    """束编组顶层聚合 / Bunch compilation top-level aggregation.

    提供束编组编译域的顶层视图，整合模型数据、解分析器
    和可行性报告。作为域服务的统一入口。
    Provides a top-level view of the bunch compilation domain,
    integrating model data, solution analyzer, and feasibility
    reports. Serves as the unified entry point for domain
    services.

    Attributes:
        model: 束编组优化模型 / Bunch compilation model.
        analyzer: 解分析器 / Solution analyzer.
    """

    model: BunchCompilationModel = field(
        default_factory=BunchCompilationModel,
    )
    analyzer: SolutionAnalyzer = field(
        default_factory=SolutionAnalyzer,
    )

    def analyze_quality(self) -> SolutionQuality:
        """分析解质量 / Analyze solution quality.

        Returns:
            解质量指标。/ Solution quality metrics.
        """
        return self.analyzer.analyze_quality(
            self.model.aggregation,
        )

    def check_feasibility(self) -> FeasibilityReport:
        """检查可行性 / Check feasibility.

        Returns:
            可行性报告。/ Feasibility report.
        """
        return self.analyzer.check_feasibility(
            self.model.aggregation,
        )

    def is_feasible(self) -> bool:
        """检查是否可行 / Check whether feasible.

        Returns:
            若所有约束均可满足则返回 True。
            True if all constraints can be satisfied.
        """
        report = self.check_feasibility()
        return report.is_feasible

    def utilization_summary(self) -> dict[str, float]:
        """获取利用率摘要 / Get utilization summary.

        Returns:
            束编组标识到利用率的映射。
            Mapping from bunch key to utilization rate.
        """
        return self.analyzer.compute_utilization(
            self.model.aggregation,
        )

    def with_model(
        self,
        model: BunchCompilationModel,
    ) -> Aggregation:
        """创建不同模型的聚合副本。

        Create an aggregation copy with different model.

        Args:
            model: 新的模型。/ New model.

        Returns:
            模型更新后的聚合副本。/ Updated aggregation copy.
        """
        return Aggregation(
            model=model,
            analyzer=self.analyzer,
        )

    def with_analyzer(
        self,
        analyzer: SolutionAnalyzer,
    ) -> Aggregation:
        """创建不同分析器的聚合副本。

        Create an aggregation copy with different analyzer.

        Args:
            analyzer: 新的分析器。/ New analyzer.

        Returns:
            分析器更新后的聚合副本。/ Updated aggregation copy.
        """
        return Aggregation(
            model=self.model,
            analyzer=analyzer,
        )
