"""束编组生成并行控制 / Bunch generation parallelism control.

管理束编组生成过程中的并行执行策略。
Manages parallel execution strategies during bunch generation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParallelismConfig:
    """并行配置 / Parallelism configuration.

    Attributes:
        max_workers: 最大并行工作线程数 / Max worker count.
        chunk_size: 每个工作线程的处理批次大小 /
            Processing batch size per worker.
        enabled: 是否启用并行 / Whether parallel is enabled.
    """

    max_workers: int = 4
    chunk_size: int = 100
    enabled: bool = True


@dataclass(frozen=True)
class WorkChunk:
    """工作分块 / Work chunk.

    表示分配给单个工作线程的数据块。
    Represents a data chunk assigned to a single worker.

    Attributes:
        chunk_index: 分块索引 / Chunk index.
        item_keys: 该分块的物料项列表 / Item keys in this chunk.
        worker_id: 分配的工作线程标识 / Assigned worker id.
    """

    chunk_index: int
    item_keys: tuple[str, ...] = ()
    worker_id: int = 0


@dataclass(frozen=True)
class BunchGenerationParallelism:
    """束编组生成并行控制 / Bunch generation parallelism control.

    将束编组生成任务分解为可并行执行的工作分块，管理
    分块策略和结果合并。
    Decomposes bunch generation tasks into parallelizable work
    chunks, managing chunking strategy and result merging.

    Attributes:
        config: 并行配置 / Parallelism config.
    """

    config: ParallelismConfig = ParallelismConfig()

    def split_work(
        self,
        item_keys: tuple[str, ...],
    ) -> tuple[WorkChunk, ...]:
        """将物料项列表分割为工作分块。

        Split item keys into work chunks.

        Args:
            item_keys: 物料项标识列表。/ Item key list.

        Returns:
            工作分块元组。/ Tuple of work chunks.
        """
        if not self.config.enabled:
            return (
                WorkChunk(
                    chunk_index=0,
                    item_keys=item_keys,
                    worker_id=0,
                ),
            )

        chunk_size = self.config.chunk_size
        chunks: list[WorkChunk] = []
        for i in range(0, len(item_keys), chunk_size):
            chunk_items = item_keys[i : i + chunk_size]
            worker_id = (i // chunk_size) % self.config.max_workers
            chunks.append(
                WorkChunk(
                    chunk_index=len(chunks),
                    item_keys=chunk_items,
                    worker_id=worker_id,
                )
            )
        return tuple(chunks)

    def recommended_worker_count(
        self,
        total_items: int,
    ) -> int:
        """推荐并行工作线程数。

        Recommend parallel worker count.

        Args:
            total_items: 物料项总数 / Total item count.

        Returns:
            推荐的工作线程数。/ Recommended worker count.
        """
        if not self.config.enabled or total_items <= 0:
            return 1
        ideal = max(1, total_items // self.config.chunk_size)
        return min(ideal, self.config.max_workers)

    def should_parallelize(
        self,
        total_items: int,
    ) -> bool:
        """判断是否应该并行化。

        Determine whether to parallelize.

        Args:
            total_items: 物料项总数 / Total item count.

        Returns:
            物料项数量超过分块大小时返回 True。
            True when item count exceeds chunk size.
        """
        return self.config.enabled and total_items > self.config.chunk_size

    @staticmethod
    def merge_chunk_keys(
        chunks: tuple[WorkChunk, ...],
    ) -> tuple[str, ...]:
        """合并所有分块的物料项标识。

        Merge all item keys from chunks.

        Args:
            chunks: 工作分块列表。/ Work chunk list.

        Returns:
            合并后的物料项标识元组。/ Merged item key tuple.
        """
        result: list[str] = []
        for chunk in chunks:
            result.extend(chunk.item_keys)
        return tuple(result)
