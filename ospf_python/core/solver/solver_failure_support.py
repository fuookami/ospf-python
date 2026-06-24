"""求解器失败支持 / Solver failure support.

提供求解器失败场景的处理支持。
Provides handling support for solver failure scenarios.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ospf_python.core.error.core_error import CoreErrorCode


@dataclass(frozen=True)
class SolverFailureInfo:
    """求解器失败信息 / Solver failure information.

    记录求解器失败的详细信息。
    Records detailed information about a solver failure.

    Attributes:
        code: 错误码 / Error code.
        message: 错误消息 / Error message.
        details: 附加详情 / Additional details.
    """

    code: CoreErrorCode = CoreErrorCode.SOLVE_FAILED
    """错误码 / Error code."""

    message: str = ""
    """错误消息 / Error message."""

    details: tuple[str, ...] = field(
        default_factory=tuple,
    )
    """附加详情 / Additional details."""


class SolverFailureSupport:
    """求解器失败支持 / Solver failure support.

    提供标准化的失败信息创建和分类方法。
    Provides standardised failure information creation
    and classification methods.
    """

    @staticmethod
    def create_failure_info(
        *,
        code: CoreErrorCode = CoreErrorCode.SOLVE_FAILED,
        message: str = "",
        details: tuple[str, ...] = (),
    ) -> SolverFailureInfo:
        """创建失败信息 / Create failure info.

        Args:
            code: 错误码 / Error code.
            message: 错误消息 / Error message.
            details: 附加详情 / Additional details.

        Returns:
            失败信息实例 / Failure info instance.
        """
        return SolverFailureInfo(
            code=code,
            message=message,
            details=details,
        )

    @staticmethod
    def is_solver_unavailable(
        info: SolverFailureInfo,
    ) -> bool:
        """判断求解器是否不可用 / Check whether solver is
        unavailable.

        Args:
            info: 失败信息 / Failure info.

        Returns:
            求解器不可用返回 True / True when solver is
            unavailable.
        """
        return info.code is CoreErrorCode.SOLVER_NOT_AVAILABLE

    @staticmethod
    def is_model_error(
        info: SolverFailureInfo,
    ) -> bool:
        """判断是否为模型错误 / Check whether it is a
        model error.

        Args:
            info: 失败信息 / Failure info.

        Returns:
            模型错误返回 True / True when it is a model
            error.
        """
        return info.code is CoreErrorCode.MODEL_BUILD_FAILED
