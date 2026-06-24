"""Worker 池内部数据结构 / Worker pool internal data structures.

定义并行操作中任务和结果的内部数据类。
Defines internal dataclasses for tasks and results in
parallel operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

# T: 任务输入类型 / Task input type
T = TypeVar("T")

# U: 任务输出类型 / Task output type
U = TypeVar("U")


@dataclass(frozen=True)
class WorkerPoolTask(Generic[T]):
    """Worker 池任务 / Worker pool task.

    封装一个待执行的任务，包含索引和输入数据。
    Wraps a pending task with its index and input data.

    Attributes:
        index: 任务在原始列表中的索引 / Task index in the
            original list.
        item: 任务输入数据 / The task input data.
    """

    index: int
    item: T


@dataclass(frozen=True)
class WorkerPoolResult(Generic[U]):
    """Worker 池结果 / Worker pool result.

    封装一个已完成任务的结果，包含索引和输出数据。
    Wraps a completed task result with its index and output
    data.

    Attributes:
        index: 任务在原始列表中的索引 / Task index in the
            original list.
        result: 任务输出数据 / The task output data.
    """

    index: int
    result: U
