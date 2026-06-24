"""SCIP 求解器配置 / SCIP solver configuration.

为 SCIP 求解器提供专用配置。
Provides dedicated configuration for the SCIP solver.
"""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.core.solver.config.solver_config import (
    SolverConfig,
)


@dataclass(frozen=True, kw_only=True)
class SCIPSolverConfig(SolverConfig):
    """SCIP 求解器配置 / SCIP solver configuration.

    冻结数据类，封装 SCIP 求解器的运行时参数。
    Frozen dataclass encapsulating SCIP solver runtime
    parameters.

    Attributes:
        name: 配置名称 / The config name.
        time_limit: 时间限制（秒）/ Time limit in seconds.
        threads: 线程数 / Number of threads.
        gap_tolerance: 间隙容差 / Gap tolerance.
        verbose: 是否详细输出 / Whether to emit verbose
            output.
    """

    name: str = "scip"
    """配置名称 / The config name."""

    time_limit: float = float("inf")
    """时间限制（秒）/ Time limit in seconds."""

    threads: int = 1
    """线程数 / Number of threads."""

    gap_tolerance: float = 1e-4
    """间隙容差 / Gap tolerance."""

    verbose: bool = False
    """是否详细输出 / Whether to emit verbose output."""
