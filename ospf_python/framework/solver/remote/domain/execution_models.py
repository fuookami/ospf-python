"""执行模型 / Execution models.

定义远程求解的执行模型。
Defines execution models for remote solving.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExecutionRequest:
    """执行请求 / Execution request.

    描述远程求解的执行请求。
    Describes an execution request for remote solving.

    Attributes:
        model_data: 模型数据 / The model data.
        solver_type: 求解器类型 / The solver type.
        options: 求解选项 / The solve options.
    """

    model_data: bytes
    solver_type: str
    options: dict[str, Any]


@dataclass(frozen=True)
class ExecutionResponse:
    """执行响应 / Execution response.

    描述远程求解的执行响应。
    Describes an execution response from remote solving.

    Attributes:
        task_id: 任务标识 / The task identifier.
        status: 任务状态 / The task status.
        message: 附加信息 / Additional message.
    """

    task_id: str
    status: str
    message: str = ""
