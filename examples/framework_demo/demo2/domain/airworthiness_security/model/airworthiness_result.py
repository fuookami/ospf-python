"""适航验证结果 / Airworthiness validation result.

定义适航安全验证的结果数据结构。
Defines the result data structure for airworthiness
security validation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AirworthinessResult:
    """适航验证结果 / Airworthiness validation result.

    汇总适航安全验证的最终状态、违规列表和各项余量，
    供上层应用决策使用。
    Summarizes the final status, violation list, and margins
    of airworthiness security validation for upper-layer
    application decision-making.

    Attributes:
        status: 验证状态(pass/fail/warning) /
            Validation status (pass/fail/warning).
        violations: 违规描述元组 /
            Tuple of violation descriptions.
        margins: 各项余量字典(键->余量值) /
            Dict of margins (key -> margin value).
    """

    status: str
    violations: tuple[str, ...]
    margins: dict[str, float]

    @staticmethod
    def create_pass(
        margins: dict[str, float] | None = None,
    ) -> AirworthinessResult:
        """创建通过结果 / Create pass result.

        Args:
            margins: 余量信息。/ Margin information.

        Returns:
            状态为 pass 的结果。
            Result with pass status.
        """
        return AirworthinessResult(
            status="pass",
            violations=(),
            margins=margins or {},
        )

    @staticmethod
    def create_fail(
        violations: tuple[str, ...],
        margins: dict[str, float] | None = None,
    ) -> AirworthinessResult:
        """创建失败结果 / Create fail result.

        Args:
            violations: 违规描述。/ Violation descriptions.
            margins: 余量信息。/ Margin information.

        Returns:
            状态为 fail 的结果。
            Result with fail status.
        """
        return AirworthinessResult(
            status="fail",
            violations=violations,
            margins=margins or {},
        )

    @staticmethod
    def create_warning(
        violations: tuple[str, ...],
        margins: dict[str, float] | None = None,
    ) -> AirworthinessResult:
        """创建警告结果 / Create warning result.

        Args:
            violations: 警告描述。/ Warning descriptions.
            margins: 余量信息。/ Margin information.

        Returns:
            状态为 warning 的结果。
            Result with warning status.
        """
        return AirworthinessResult(
            status="warning",
            violations=violations,
            margins=margins or {},
        )

    @property
    def is_pass(self) -> bool:
        """是否通过 / Is pass.

        Returns:
            状态为 pass 则返回 True。
            True if status is pass.
        """
        return self.status == "pass"

    @property
    def is_fail(self) -> bool:
        """是否失败 / Is fail.

        Returns:
            状态为 fail 则返回 True。
            True if status is fail.
        """
        return self.status == "fail"

    @property
    def is_warning(self) -> bool:
        """是否警告 / Is warning.

        Returns:
            状态为 warning 则返回 True。
            True if status is warning.
        """
        return self.status == "warning"

    @property
    def violation_count(self) -> int:
        """违规数量 / Violation count.

        Returns:
            违规条目数。
            Number of violation entries.
        """
        return len(self.violations)

    def has_violation(self, keyword: str) -> bool:
        """检查是否包含特定违规。

        Check whether a specific violation is present.

        Args:
            keyword: 违规关键词。/ Violation keyword.

        Returns:
            若任一违规描述包含关键词则返回 True。
            True if any violation description contains the keyword.
        """
        return any(keyword in v for v in self.violations)

    def margin_for(self, key: str) -> float | None:
        """获取指定键的余量 / Get margin for key.

        Args:
            key: 余量键。/ Margin key.

        Returns:
            对应余量值，不存在返回 None。
            Margin value, or None if not found.
        """
        return self.margins.get(key)

    def worst_margin(self) -> float | None:
        """获取最差余量 / Get worst margin.

        Returns:
            所有余量中的最小值，无余量返回 None。
            Minimum of all margins; None if no margins.
        """
        if not self.margins:
            return None
        return min(self.margins.values())

    def merge(self, other: AirworthinessResult) -> AirworthinessResult:
        """合并两个结果 / Merge two results.

        合并规则：任一为 fail 则 fail；任一为 warning 则 warning。

        Args:
            other: 另一个结果。/ Another result.

        Returns:
            合并后的新结果。
            New merged result.
        """
        merged_violations = self.violations + other.violations
        merged_margins = {**self.margins, **other.margins}

        if self.is_fail or other.is_fail:
            new_status = "fail"
        elif self.is_warning or other.is_warning:
            new_status = "warning"
        else:
            new_status = "pass"

        return AirworthinessResult(
            status=new_status,
            violations=merged_violations,
            margins=merged_margins,
        )
