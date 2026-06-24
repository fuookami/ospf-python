"""MindOPT 求解器配置 / MindOPT solver configuration.

为 MindOPT 求解器提供专用配置。
Provides dedicated configuration for the MindOPT solver.
"""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.solver.config.solver_config import (
    SolverConfig,
)


@dataclass(frozen=True, kw_only=True)
class MindOPTSolverConfig(SolverConfig):
    """MindOPT 求解器配置 / MindOPT solver configuration.

    冻结数据类，封装 MindOPT 求解器的运行时参数。
    Frozen dataclass encapsulating MindOPT solver runtime
    parameters.

    Attributes:
        name: 配置名称 / The config name.
        time_limit: 时间限制（秒）/ Time limit in seconds.
        threads: 线程数 / Number of threads.
        log_to_console: 是否输出日志 / Whether to log to
            console.
    """

    name: str = "mindopt"
    """配置名称 / The config name."""

    time_limit: float = float("inf")
    """时间限制（秒）/ Time limit in seconds."""

    threads: int = 1
    """线程数 / Number of threads."""

    log_to_console: bool = False
    """是否输出日志 / Whether to log to console."""
