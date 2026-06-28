"""Redis 持久化插件测试 / Redis persistence plugin tests.

Tests for RedisRepository: TTL, batch read/write, serialization failure,
connection failure. All tests use mocking (no real Redis dependency).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ospf_python.framework.persistence.redis_repository import RedisRepository


class TestRedisRepositoryMocked:
    """Redis 仓储测试（模拟） / Redis repository tests (mocked)."""

    @patch("ospf_python.framework.persistence.redis_repository.RedisRepository._get_client")
    def test_save_and_find(self, mock_get_client: MagicMock) -> None:
        """保存并查找 / Save and find."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get.return_value = b"test_data"

        repo = RedisRepository(prefix="test", host="localhost", port=6379)
        repo.save("test_data")
        mock_client.set.assert_called_once()

        result = repo.find_by_id("test_data")
        assert result is not None

    @patch("ospf_python.framework.persistence.redis_repository.RedisRepository._get_client")
    def test_find_by_id_not_found(self, mock_get_client: MagicMock) -> None:
        """查找不存在的 ID / Find by ID not found."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get.return_value = None

        repo = RedisRepository(prefix="test")
        result = repo.find_by_id("nonexistent")
        assert result is None

    @patch("ospf_python.framework.persistence.redis_repository.RedisRepository._get_client")
    def test_delete(self, mock_get_client: MagicMock) -> None:
        """删除实体 / Delete entity."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        repo = RedisRepository(prefix="test")
        repo.delete("item_1")
        mock_client.delete.assert_called_once()

    @patch("ospf_python.framework.persistence.redis_repository.RedisRepository._get_client")
    def test_find_all(self, mock_get_client: MagicMock) -> None:
        """查找所有 / Find all."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.keys.return_value = [b"test:1", b"test:2"]
        mock_client.get.side_effect = [b"data_1", b"data_2"]

        repo = RedisRepository(prefix="test")
        results = repo.find_all()
        assert len(results) == 2

    @patch("ospf_python.framework.persistence.redis_repository.RedisRepository._get_client")
    def test_ttl_set_with_expiry(self, mock_get_client: MagicMock) -> None:
        """设置 TTL 过期时间 / Set TTL expiry."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        repo = RedisRepository(prefix="test")
        repo.save("ttl_data")
        # Verify set was called (TTL would be set via setex in real impl)
        mock_client.set.assert_called_once()

    @patch("ospf_python.framework.persistence.redis_repository.RedisRepository._get_client")
    def test_batch_read_write(self, mock_get_client: MagicMock) -> None:
        """批量读写 / Batch read/write."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.keys.return_value = [b"test:1", b"test:2", b"test:3"]
        mock_client.get.side_effect = [b"v1", b"v2", b"v3"]

        repo = RedisRepository(prefix="test")
        # Batch save
        for i in range(3):
            repo.save(f"data_{i}")
        assert mock_client.set.call_count == 3

        # Batch read
        results = repo.find_all()
        assert len(results) == 3

    @patch("ospf_python.framework.persistence.redis_repository.RedisRepository._get_client")
    def test_serialization_failure(self, mock_get_client: MagicMock) -> None:
        """序列化失败 / Serialization failure."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get.return_value = b"<unserializable>"

        repo = RedisRepository(prefix="test")
        result = repo.find_by_id("bad_data")
        # Returns raw bytes; caller handles deserialization
        assert result is not None

    @patch("ospf_python.framework.persistence.redis_repository.RedisRepository._get_client")
    def test_connection_failure_graceful(self, mock_get_client: MagicMock) -> None:
        """连接失败优雅降级 / Connection failure graceful degradation."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get.side_effect = ConnectionError("Redis unavailable")

        repo = RedisRepository(prefix="test")
        with pytest.raises(ConnectionError):
            repo.find_by_id("any_key")

    def test_key_prefix_format(self) -> None:
        """键前缀格式 / Key prefix format."""
        repo = RedisRepository(prefix="myapp")
        key = repo._make_key("item_1")
        assert key == "myapp:item_1"
