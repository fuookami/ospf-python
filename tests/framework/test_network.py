"""Tests for network module.

网络模块测试。
"""

from __future__ import annotations

import pytest

from ospf_python.framework.network.response import Response

# -- Response --------------------------------------------------------


class TestResponseExtra:
    """Test Response edge cases."""

    def test_200_ok(self) -> None:
        """200 OK 响应 / 200 OK response."""
        resp = Response(
            status=200,
            body="OK",
            headers={},
        )
        assert resp.status == 200

    def test_404_not_found(self) -> None:
        """404 响应 / 404 response."""
        resp = Response(
            status=404,
            body="Not Found",
            headers={"content-type": "text/plain"},
        )
        assert resp.status == 404

    def test_500_server_error(self) -> None:
        """500 响应 / 500 response."""
        resp = Response(
            status=500,
            body="Internal Server Error",
            headers={},
        )
        assert resp.status == 500

    def test_empty_body(self) -> None:
        """空响应体 / Empty body."""
        resp = Response(status=204, body="", headers={})
        assert resp.body == ""

    def test_json_body(self) -> None:
        """JSON 响应体 / JSON body."""
        body = '{"key": "value", "count": 42}'
        resp = Response(
            status=200,
            body=body,
            headers={"content-type": "application/json"},
        )
        assert resp.body == body
        assert resp.headers["content-type"] == "application/json"

    def test_multiple_headers(self) -> None:
        """多响应头 / Multiple headers."""
        resp = Response(
            status=200,
            body="",
            headers={
                "content-type": "text/html",
                "cache-control": "no-cache",
                "x-request-id": "abc-123",
            },
        )
        assert len(resp.headers) == 3

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        resp = Response(status=200, body="ok", headers={})
        with pytest.raises(AttributeError):
            resp.status = 404  # type: ignore[misc]

    def test_empty_headers(self) -> None:
        """空响应头 / Empty headers."""
        resp = Response(status=200, body="ok", headers={})
        assert resp.headers == {}
