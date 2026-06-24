"""本地文件系统对象存储端口 / Local filesystem object storage port.

实现基于本地文件系统的对象存储。
Implements object storage based on the local filesystem.
"""

from __future__ import annotations

import abc
from pathlib import Path


class LocalFileObjectStoragePort(abc.ABC):
    """本地文件系统对象存储端口 / Local filesystem object storage port.

    提供基于本地文件系统的对象读写能力。
    Provides object read/write capabilities based on
    the local filesystem.
    """

    @abc.abstractmethod
    def save(
        self,
        key: str,
        data: bytes,
        *,
        base_path: Path,
    ) -> Path:
        """保存对象 / Save object.

        Args:
            key: 对象键 / The object key.
            data: 对象数据 / The object data.
            base_path: 基础路径 / The base path.

        Returns:
            保存后的文件路径 / The saved file path.
        """
        ...

    @abc.abstractmethod
    def load(
        self,
        key: str,
        *,
        base_path: Path,
    ) -> bytes | None:
        """加载对象 / Load object.

        Args:
            key: 对象键 / The object key.
            base_path: 基础路径 / The base path.

        Returns:
            对象数据或 None / The object data or None.
        """
        ...

    @abc.abstractmethod
    def delete(
        self,
        key: str,
        *,
        base_path: Path,
    ) -> bool:
        """删除对象 / Delete object.

        Args:
            key: 对象键 / The object key.
            base_path: 基础路径 / The base path.

        Returns:
            删除成功返回 True / True if deletion succeeded.
        """
        ...

    @abc.abstractmethod
    def exists(
        self,
        key: str,
        *,
        base_path: Path,
    ) -> bool:
        """检查对象是否存在 / Check if object exists.

        Args:
            key: 对象键 / The object key.
            base_path: 基础路径 / The base path.

        Returns:
            存在时返回 True / True when the object exists.
        """
        ...
