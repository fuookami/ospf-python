"""CSP1D 切割方案并行生成。

提供并行化的切割方案生成策略。
Parallelism support for cutting plan generation.
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass(frozen=True)
class GenerationParallelism:
    """切割方案并行生成 / Parallel generation.

    管理切割方案并行生成的配置和执行。
    针对不同材料的方案生成可独立并行。
    Manages configuration and execution of parallel
    cutting plan generation. Generation for different
    materials can run independently in parallel.

    Attributes:
        max_workers: 最大并行工作线程数。
            Maximum parallel worker threads.
        use_process_pool: 是否使用进程池。
            Whether to use process pool.
        chunk_size: 每个并行任务的材料批次大小。
            Material batch size per parallel task.
    """

    max_workers: int = 4
    """最大并行工作线程数 / Maximum parallel workers."""

    use_process_pool: bool = False
    """是否使用进程池 / Whether to use process pool."""

    chunk_size: int = 1
    """材料批次大小 / Material batch size."""

    def execute_parallel[T, R](
        self,
        *,
        items: list[T],
        task: Callable[[T], R],
    ) -> list[R]:
        """并行执行任务。

        Execute tasks in parallel.

        Args:
            items: 待处理的项目列表。
                List of items to process.
            task: 对每个项目执行的任务函数。
                Task function to execute for each item.

        Returns:
            任务结果列表。
            List of task results.
        """
        if self.max_workers <= 1 or len(items) <= 1:
            return [task(item) for item in items]

        results: list[R] = [None] * len(items)  # type: ignore[list-item]
        with ProcessPoolExecutor(
            max_workers=self.max_workers,
        ) as executor:
            future_to_index = {
                executor.submit(task, item): idx for idx, item in enumerate(items)
            }
            for future in as_completed(future_to_index):
                idx = future_to_index[future]
                results[idx] = future.result()
        return results

    def chunk_items[T](
        self,
        items: list[T],
    ) -> list[list[T]]:
        """将项目分块。

        Chunk items into batches.

        Args:
            items: 待分块的项目列表。
                List of items to chunk.

        Returns:
            分块后的列表。
            List of item chunks.
        """
        if self.chunk_size <= 1:
            return [[item] for item in items]
        return [
            items[i : i + self.chunk_size]
            for i in range(0, len(items), self.chunk_size)
        ]

    @property
    def is_parallel(self) -> bool:
        """判断是否启用并行。

        Check if parallelism is enabled.

        Returns:
            并行数大于 1 时返回 True。
            True when max workers > 1.
        """
        return self.max_workers > 1

    @staticmethod
    def sequential() -> GenerationParallelism:
        """创建顺序执行配置。

        Create sequential execution configuration.

        Returns:
            单线程并行配置。
            Single-thread parallelism config.
        """
        return GenerationParallelism(max_workers=1)

    @staticmethod
    def with_workers(
        *,
        max_workers: int,
    ) -> GenerationParallelism:
        """创建指定并行数的配置。

        Create config with specified parallelism.

        Args:
            max_workers: 最大并行数。
                Maximum parallel workers.

        Returns:
            并行配置。
            Parallelism config.
        """
        return GenerationParallelism(max_workers=max_workers)
