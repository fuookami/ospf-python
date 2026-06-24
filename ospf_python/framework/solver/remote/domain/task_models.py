"""任务模型 / Task models.

定义远程求解的任务数据模型。
Defines task data models for remote solving.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TaskInfo:
    """任务信息 / Task information.

    描述远程求解任务的元数据。
    Describes metadata of a remote solve task.

    Attributes:
        task_id: 任务标识 / The task identifier.
        status: 任务状态 / The task status.
        created_at: 创建时间 / The creation time.
        updated_at: 更新时间 / The last update time.
    """

    task_id: str
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class TaskResult:
    """任务结果 / Task result.

    描述远程求解任务的执行结果。
    Describes the execution result of a remote solve task.

    Attributes:
        task_id: 任务标识 / The task identifier.
        success: 是否成功 / Whether the task succeeded.
        result_data: 结果数据 / The result data.
        error_message: 错误信息 / The error message.
    """

    task_id: str
    success: bool
    result_data: bytes = b""
    error_message: str = ""
