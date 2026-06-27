"""Persistence module / 持久化模块.

Provides repository pattern implementations for data persistence.
"""

from ospf_python.framework.persistence.redis_repository import RedisRepository
from ospf_python.framework.persistence.repository import Repository
from ospf_python.framework.persistence.sqlite_repository import SQLiteRepository

__all__ = [
    "Repository",
    "SQLiteRepository",
    "RedisRepository",
]
