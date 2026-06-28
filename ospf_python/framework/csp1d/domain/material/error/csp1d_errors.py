"""CSP1D 领域错误收集。

收集和管理 CSP1D 领域操作中产生的错误。
Collects and manages errors from CSP1D domain operations.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Csp1dErrors:
    """CSP1D 错误收集器 / CSP1D error collector.

    收集 CSP1D 领域操作过程中产生的错误信息，
    用于批量报告和诊断。
    Collects error messages produced during CSP1D
    domain operations, used for batch reporting
    and diagnostics.

    Attributes:
        messages: 错误消息列表。
            Error messages.
        context: 错误上下文标识。
            Error context identifier.
    """

    messages: tuple[str, ...] = ()
    """错误消息列表 / Error messages."""

    context: str = ""
    """错误上下文标识 / Error context identifier."""

    @staticmethod
    def create(
        *,
        context: str = "",
    ) -> Csp1dErrors:
        """创建空错误收集器。

        Create empty error collector.

        Args:
            context: 错误上下文标识。
                Error context identifier.

        Returns:
            错误收集器实例。
            Error collector instance.
        """
        return Csp1dErrors(context=context)

    def add(
        self,
        message: str,
    ) -> Csp1dErrors:
        """添加错误消息，返回新实例。

        Add error message, return new instance.

        Args:
            message: 错误消息。
                Error message.

        Returns:
            包含新消息的错误收集器实例。
            Error collector with new message.
        """
        return Csp1dErrors(
            messages=self.messages + (message,),
            context=self.context,
        )

    def merge(
        self,
        other: Csp1dErrors,
    ) -> Csp1dErrors:
        """合并另一个错误收集器，返回新实例。

        Merge another error collector, return new instance.

        Args:
            other: 另一个错误收集器。
                Another error collector.

        Returns:
            合并后的错误收集器实例。
            Merged error collector instance.
        """
        return Csp1dErrors(
            messages=self.messages + other.messages,
            context=self.context,
        )

    @property
    def has_errors(self) -> bool:
        """判断是否有错误。

        Check if there are errors.

        Returns:
            有错误消息时返回 True。
            True when there are error messages.
        """
        return len(self.messages) > 0

    @property
    def count(self) -> int:
        """获取错误数量。

        Get error count.

        Returns:
            错误消息数量。
            Number of error messages.
        """
        return len(self.messages)

    def first(self) -> str | None:
        """获取第一条错误消息。

        Get the first error message.

        Returns:
            第一条错误消息，无错误时返回 None。
            First error message, None when no errors.
        """
        return self.messages[0] if self.messages else None

    def to_text(self) -> str:
        """将所有错误消息转换为文本。

        Convert all error messages to text.

        Returns:
            以换行符分隔的错误消息文本。
            Error messages joined by newlines.
        """
        return "\n".join(self.messages)
