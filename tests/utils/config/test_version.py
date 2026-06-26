"""版本信息模块测试。

Tests for version module: Version dataclass and
VERSION singleton.
"""

from __future__ import annotations

import pytest

from ospf_python.utils.config.version import VERSION, Version


class TestVersion:
    """Version 测试。/ Version tests."""

    def test_default_values(self) -> None:
        """默认版本号。/ Default version numbers."""
        v = Version()
        assert v.MAJOR == 0
        assert v.MINOR == 1
        assert v.PATCH == 0

    def test_custom_values(self) -> None:
        """自定义版本号。/ Custom version numbers."""
        v = Version(MAJOR=2, MINOR=3, PATCH=4)
        assert v.MAJOR == 2
        assert v.MINOR == 3
        assert v.PATCH == 4

    def test_version_string(self) -> None:
        """版本字符串。/ Version string."""
        v = Version(MAJOR=1, MINOR=2, PATCH=3)
        assert v.version_string == "1.2.3"

    def test_str(self) -> None:
        """str 表示。/ str representation."""
        v = Version()
        assert str(v) == "0.1.0"

    def test_frozen(self) -> None:
        """frozen dataclass。/ frozen dataclass."""
        v = Version()
        with pytest.raises(AttributeError):
            v.MAJOR = 1  # type: ignore[misc]


class TestVersionSingleton:
    """VERSION 单例测试。/ VERSION singleton tests."""

    def test_version_singleton_exists(self) -> None:
        """VERSION 单例存在。/ VERSION singleton exists."""
        assert VERSION is not None
        assert isinstance(VERSION, Version)

    def test_version_singleton_default(self) -> None:
        """VERSION 使用默认值。/ VERSION uses defaults."""
        assert VERSION.version_string == "0.1.0"


class TestConfigInit:
    """config __init__ 测试。/ config __init__ tests."""

    def test_imports(self) -> None:
        """从 config 模块导入。/ Import from config module."""
        from ospf_python.utils.config import VERSION as IMPORTED_VERSION
        from ospf_python.utils.config import Version as VersionCls

        assert IMPORTED_VERSION is VERSION
        assert VersionCls is Version
