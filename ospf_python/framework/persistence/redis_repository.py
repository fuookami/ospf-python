"""Redis persistence plugin / Redis 持久化插件.

Provides Redis-based repository implementation.
"""

from __future__ import annotations

from typing import Any, TypeVar

from ospf_python.framework.persistence.repository import Repository

T = TypeVar("T")


class RedisRepository(Repository[T]):
    """Redis repository implementation.

    Redis 仓储实现。
    """

    def __init__(self, prefix: str, host: str = "localhost", port: int = 6379) -> None:
        """Initialize Redis repository.

        Args:
            prefix: Key prefix.
            host: Redis host.
            port: Redis port.
        """
        self._prefix = prefix
        self._host = host
        self._port = port
        self._client: Any = None

    def _get_client(self) -> Any:
        """Get Redis client."""
        if self._client is None:
            import redis

            self._client = redis.Redis(host=self._host, port=self._port)
        return self._client

    def _make_key(self, id: str) -> str:
        """Make Redis key."""
        return f"{self._prefix}:{id}"

    def find_by_id(self, id: str) -> T | None:
        """Find entity by ID."""
        client = self._get_client()
        data = client.get(self._make_key(id))
        if data is None:
            return None  # reason: key not found in Redis
        return data  # type: ignore[return-value]

    def save(self, entity: T) -> None:
        """Save entity."""
        client = self._get_client()
        # Simplified: use str representation
        client.set(self._make_key(str(entity)), str(entity))

    def delete(self, id: str) -> None:
        """Delete entity."""
        client = self._get_client()
        client.delete(self._make_key(id))

    def find_all(self) -> list[T]:
        """Find all entities."""
        client = self._get_client()
        keys = client.keys(f"{self._prefix}:*")
        results = []
        for key in keys:
            data = client.get(key)
            if data is not None:
                results.append(data)  # type: ignore[arg-type]
        return results
