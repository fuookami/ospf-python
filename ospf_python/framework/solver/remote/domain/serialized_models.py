"""序列化模型 / Serialized models.

定义远程求解的序列化数据模型。
Defines serialized data models for remote solving.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SerializedModel:
    """序列化模型 / Serialized model.

    模型的序列化表示，用于网络传输。
    Serialized representation of a model for network transfer.

    Attributes:
        format: 序列化格式 / The serialization format.
        data: 序列化数据 / The serialized data.
        checksum: 数据校验和 / The data checksum.
    """

    format: str
    data: bytes
    checksum: str = ""


@dataclass(frozen=True)
class SerializedResult:
    """序列化结果 / Serialized result.

    结果的序列化表示，用于网络传输。
    Serialized representation of a result for network transfer.

    Attributes:
        format: 序列化格式 / The serialization format.
        data: 序列化数据 / The serialized data.
        task_id: 关联任务标识 / The associated task identifier.
    """

    format: str
    data: bytes
    task_id: str = ""
