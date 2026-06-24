"""对象存储端口 / Object storage port.

定义对象存储的抽象端口接口。
Defines the abstract port interface for object storage.
"""

from __future__ import annotations

import abc


class ObjectStoragePort(abc.ABC):
    """对象存储端口 / Object storage port.

    提供对象存储的读写抽象接口。
    Provides read/write abstract interface for object storage.
    """

    @abc.abstractmethod
    def put(
        self,
        bucket: str,
        key: str,
        data: bytes,
    ) -> bool:
        """存储对象 / Put object.

        Args:
            bucket: 存储桶 / The bucket name.
            key: 对象键 / The object key.
            data: 对象数据 / The object data.

        Returns:
            存储成功返回 True / True if storage succeeded.
        """
        ...

    @abc.abstractmethod
    def get(
        self,
        bucket: str,
        key: str,
    ) -> bytes | None:
        """获取对象 / Get object.

        Args:
            bucket: 存储桶 / The bucket name.
            key: 对象键 / The object key.

        Returns:
            对象数据或 None / The object data or None.
        """
        ...

    @abc.abstractmethod
    def delete(
        self,
        bucket: str,
        key: str,
    ) -> bool:
        """删除对象 / Delete object.

        Args:
            bucket: 存储桶 / The bucket name.
            key: 对象键 / The object key.

        Returns:
            删除成功返回 True / True if deletion succeeded.
        """
        ...

    @abc.abstractmethod
    def list_keys(
        self,
        bucket: str,
        prefix: str = "",
    ) -> list[str]:
        """列出对象键 / List object keys.

        Args:
            bucket: 存储桶 / The bucket name.
            prefix: 键前缀 / The key prefix.

        Returns:
            对象键列表 / List of object keys.
        """
        ...
