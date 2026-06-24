"""并行操作工具 / Parallel operation utilities.

提供基于 asyncio 的并行集合操作。
Provides asyncio-based parallel collection operations.
"""

from ospf_python.utils.parallel.all_any_none import (
    all_parallel,
    any_parallel,
    none_parallel,
)
from ospf_python.utils.parallel.associate import associate_parallel
from ospf_python.utils.parallel.channel_guard import ChannelGuard
from ospf_python.utils.parallel.common import WorkerPoolResult, WorkerPoolTask
from ospf_python.utils.parallel.count import count_parallel
from ospf_python.utils.parallel.filter import filter_parallel
from ospf_python.utils.parallel.find import find_parallel
from ospf_python.utils.parallel.flat_map import flat_map_parallel
from ospf_python.utils.parallel.fold import fold_parallel
from ospf_python.utils.parallel.map import map_parallel
from ospf_python.utils.parallel.max_min import max_parallel, min_parallel
from ospf_python.utils.parallel.min_max import MinMaxResult, min_max_parallel
from ospf_python.utils.parallel.thread_guard import Async

__all__ = [
    "Async",
    "ChannelGuard",
    "MinMaxResult",
    "WorkerPoolResult",
    "WorkerPoolTask",
    "all_parallel",
    "any_parallel",
    "associate_parallel",
    "count_parallel",
    "filter_parallel",
    "find_parallel",
    "flat_map_parallel",
    "fold_parallel",
    "map_parallel",
    "max_parallel",
    "min_max_parallel",
    "min_parallel",
    "none_parallel",
]
