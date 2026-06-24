"""存储模型 / Storage models.

定义远程求解的存储数据模型。
Defines storage data models for remote solving.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class StorageObject:
    """存储对象 / Storage object.

    表示对象存储中的一个条目。
    Represents an entry in object storage.

    Attributes:
        key: 对象键 / The object key.
        size: 对象大小（字节） / The object size in bytes.
        created_at: 创建时间 / The creation time.
        content_type: 内容类型 / The content type.
    """

    key: str
    size: int
    created_at: datetime
    content_type: str = "application/octet-stream"


@dataclass(frozen=True)
class StorageReference:
    """存储引用 / Storage reference.

    引用存储中的对象，支持通过键访问。
    References an object in storage, accessible by key.

    Attributes:
        bucket: 存储桶名称 / The bucket name.
        key: 对象键 / The object key.
    """

    bucket: str
    key: str
