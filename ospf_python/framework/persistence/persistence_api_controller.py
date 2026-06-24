"""持久化 API 控制器 / Persistence API controller.

定义持久化操作的抽象控制器接口。
Defines the abstract controller interface for persistence operations.
"""

from __future__ import annotations

import abc
from typing import Any


class PersistenceApiController(abc.ABC):
    """持久化 API 控制器 / Persistence API controller.

    提供持久化操作的统一抽象接口，支持 CRUD 操作。
    Provides a unified abstract interface for persistence
    operations, supporting CRUD operations.
    """

    @abc.abstractmethod
    def save(self, entity: Any) -> Any:
        """保存实体 / Save entity.

        Args:
            entity: 要保存的实体 / The entity to save.

        Returns:
            保存后的实体 / The saved entity.
        """
        ...

    @abc.abstractmethod
    def find_by_id(self, entity_id: Any) -> Any:
        """按 ID 查找实体 / Find entity by ID.

        Args:
            entity_id: 实体标识 / The entity identifier.

        Returns:
            查找到的实体，不存在时返回 None /
            The found entity, or None if not exists.
        """
        ...

    @abc.abstractmethod
    def delete(self, entity_id: Any) -> bool:
        """删除实体 / Delete entity.

        Args:
            entity_id: 实体标识 / The entity identifier.

        Returns:
            删除成功时返回 True / True if deletion succeeded.
        """
        ...

    @abc.abstractmethod
    def find_all(self) -> list[Any]:
        """查找所有实体 / Find all entities.

        Returns:
            所有实体列表 / List of all entities.
        """
        ...
