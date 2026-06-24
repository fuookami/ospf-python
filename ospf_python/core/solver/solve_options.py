"""求解选项 / Solve options.

配置求解器行为的冻结数据类。
Frozen dataclass configuring solver behaviour.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SolveOptions:
    """求解选项 / Solve options.

    冻结数据类，封装求解器运行时参数。
    Frozen dataclass encapsulating solver runtime parameters.

    Attributes:
        time_limit: 时间限制（秒）/ Time limit in seconds.
        gap_tolerance: 间隙容差 / Gap tolerance.
        verbose: 是否输出详细日志 / Whether to emit verbose
            logging.
        threads: 线程数 / Number of threads.
        seed: 随机种子 / Random seed.
    """

    time_limit: float = float("inf")
    """时间限制（秒）/ Time limit in seconds."""

    gap_tolerance: float = 1e-4
    """间隙容差 / Gap tolerance."""

    verbose: bool = False
    """是否输出详细日志 / Whether to emit verbose logging."""

    threads: int = 1
    """线程数 / Number of threads."""

    seed: int = 42
    """随机种子 / Random seed."""

    def with_time_limit(
        self,
        limit: float,
    ) -> SolveOptions:
        """创建带新时间限制的选项副本 / Create copy with
        new time limit.

        Args:
            limit: 新时间限制 / New time limit in seconds.

        Returns:
            新的求解选项 / New solve options instance.
        """
        return SolveOptions(
            time_limit=limit,
            gap_tolerance=self.gap_tolerance,
            verbose=self.verbose,
            threads=self.threads,
            seed=self.seed,
        )

    def with_verbose(
        self,
        verbose: bool,
    ) -> SolveOptions:
        """创建带新日志设置的选项副本 / Create copy with
        new verbose setting.

        Args:
            verbose: 是否输出详细日志 / Whether to emit
                verbose logging.

        Returns:
            新的求解选项 / New solve options instance.
        """
        return SolveOptions(
            time_limit=self.time_limit,
            gap_tolerance=self.gap_tolerance,
            verbose=verbose,
            threads=self.threads,
            seed=self.seed,
        )
