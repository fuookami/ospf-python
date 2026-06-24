"""框架求解选项 / Framework solve options.

定义框架层求解器的配置选项。
Defines configuration options for framework layer solvers.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FrameworkSolveOptions:
    """框架求解选项 / Framework solve options.

    配置求解器的行为参数，如超时、精度等。
    Configures solver behavior parameters such as
    timeout, precision, etc.

    Attributes:
        timeout_seconds: 超时秒数 / Timeout in seconds.
        tolerance: 容差 / Optimality tolerance.
        max_iterations: 最大迭代次数 / Maximum iterations.
        verbose: 是否输出详细信息 / Whether to output verbose info.
    """

    timeout_seconds: float = 3600.0
    tolerance: float = 1e-6
    max_iterations: int = 10000
    verbose: bool = False
