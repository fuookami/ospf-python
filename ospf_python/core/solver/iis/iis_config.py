"""IIS 配置 / IIS configuration.

配置不可约不可行子系统 (IIS) 的计算参数。
Configures Irreducible Infeasible Subsystem (IIS)
computation parameters.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class IISConfig:
    """IIS 配置 / IIS configuration.

    冻结数据类，封装 IIS 计算的运行时参数。
    Frozen dataclass encapsulating IIS computation
    runtime parameters.

    Attributes:
        time_limit: 时间限制（秒）/ Time limit in seconds.
        max_iterations: 最大迭代次数 / Maximum iterations.
        verbose: 是否详细输出 / Whether to emit verbose
            output.
    """

    time_limit: float = 300.0
    """时间限制（秒）/ Time limit in seconds."""

    max_iterations: int = 1000
    """最大迭代次数 / Maximum iterations."""

    verbose: bool = False
    """是否详细输出 / Whether to emit verbose output."""
