"""冗余分析结果 / Redundancy analysis result.

定义系统冗余度分析的结果数据结构。
Defines the result data structure for system redundancy
analysis.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RedundancyResult:
    """冗余分析结果 / Redundancy analysis result.

    汇总系统冗余度分析的系统标识、冗余等级和关键组件，
    供上层应用决策使用。
    Summarizes the system identifier, redundancy level,
    and critical components of redundancy analysis for
    upper-layer application decision-making.

    Attributes:
        system_id: 系统标识 / System identifier.
        redundancy_level: 冗余等级(0=无冗余, 1=单冗余,
            2=双冗余, 3+=三冗余以上) /
            Redundancy level (0=none, 1=single, 2=double,
            3+=triple+).
        critical_components: 关键组件标识元组 /
            Tuple of critical component identifiers.
        compliant: 是否满足冗余要求 /
            Whether redundancy requirements are met.
        violations: 违反描述元组 /
            Tuple of violation descriptions.
    """

    system_id: str
    redundancy_level: int
    critical_components: tuple[str, ...]
    compliant: bool = True
    violations: tuple[str, ...] = ()

    @staticmethod
    def create_compliant(
        *,
        system_id: str,
        redundancy_level: int,
        critical_components: tuple[str, ...] = (),
    ) -> RedundancyResult:
        """创建合规结果 / Create compliant result.

        Args:
            system_id: 系统标识 / System identifier.
            redundancy_level: 冗余等级 / Redundancy level.
            critical_components: 关键组件 / Critical components.

        Returns:
            合规的冗余结果 / Compliant redundancy result.
        """
        return RedundancyResult(
            system_id=system_id,
            redundancy_level=redundancy_level,
            critical_components=critical_components,
            compliant=True,
            violations=(),
        )

    @staticmethod
    def create_non_compliant(
        *,
        system_id: str,
        redundancy_level: int,
        critical_components: tuple[str, ...] = (),
        violations: tuple[str, ...] = (),
    ) -> RedundancyResult:
        """创建不合规结果 / Create non-compliant result.

        Args:
            system_id: 系统标识 / System identifier.
            redundancy_level: 冗余等级 / Redundancy level.
            critical_components: 关键组件 / Critical components.
            violations: 违反描述 / Violation descriptions.

        Returns:
            不合规的冗余结果 / Non-compliant redundancy result.
        """
        return RedundancyResult(
            system_id=system_id,
            redundancy_level=redundancy_level,
            critical_components=critical_components,
            compliant=False,
            violations=violations,
        )

    @property
    def has_critical_components(self) -> bool:
        """是否有关键组件 / Has critical components.

        Returns:
            存在关键组件时返回 True。
            True if critical components exist.
        """
        return len(self.critical_components) > 0

    @property
    def is_redundant(self) -> bool:
        """是否具有冗余 / Is redundant.

        Returns:
            冗余等级大于 0 时返回 True。
            True if redundancy level is greater than 0.
        """
        return self.redundancy_level > 0

    @property
    def violation_count(self) -> int:
        """违规数量 / Violation count.

        Returns:
            违规条目数 / Number of violation entries.
        """
        return len(self.violations)

    def has_violation(self, keyword: str) -> bool:
        """检查是否包含特定违规。

        Check whether a specific violation is present.

        Args:
            keyword: 违规关键词 / Violation keyword.

        Returns:
            若任一违规描述包含关键词则返回 True。
            True if any violation contains the keyword.
        """
        return any(keyword in v for v in self.violations)

    def merge(self, other: RedundancyResult) -> RedundancyResult:
        """合并两个结果 / Merge two results.

        合并规则：任一不合规则不合规；取较低冗余等级。

        Args:
            other: 另一个结果 / Another result.

        Returns:
            合并后的新结果 / New merged result.
        """
        merged_violations = self.violations + other.violations
        merged_components = tuple(
            dict.fromkeys(self.critical_components + other.critical_components)
        )
        return RedundancyResult(
            system_id=self.system_id,
            redundancy_level=min(
                self.redundancy_level,
                other.redundancy_level,
            ),
            critical_components=merged_components,
            compliant=self.compliant and other.compliant,
            violations=merged_violations,
        )
