"""Utils 根模块测试 / Tests for utils root-level modules.

覆盖 library、system、time、uuid_v7。
Covers library, system, time, uuid_v7.
"""

from __future__ import annotations

import re
import time

from ospf_python.utils.library import Library
from ospf_python.utils.system import System
from ospf_python.utils.time import Time
from ospf_python.utils.uuid_v7 import UuidV7

# -- Library --


class TestLibrary:
    """Library 元信息测试。"""

    def test_name(self) -> None:
        """库名称正确。"""
        lib = Library()
        assert lib.name == "ospf-python"

    def test_version(self) -> None:
        """版本号正确。"""
        lib = Library()
        assert lib.version == "0.1.0"

    def test_frozen(self) -> None:
        """不可变。"""
        lib = Library()
        try:
            lib.name = "other"  # type: ignore[misc]
            raise AssertionError("Should raise FrozenInstanceError")
        except AttributeError:
            pass

    def test_equality(self) -> None:
        """相同属性相等。"""
        assert Library() == Library()


# -- System --


class TestSystem:
    """System 工具测试。"""

    def test_current_time_millis_type(self) -> None:
        """返回整数。"""
        result = System.current_time_millis()
        assert isinstance(result, int)

    def test_current_time_millis_range(self) -> None:
        """时间戳在合理范围内。"""
        result = System.current_time_millis()
        now = time.time() * 1000
        assert abs(result - now) < 1000

    def test_nano_time_type(self) -> None:
        """返回整数。"""
        result = System.nano_time()
        assert isinstance(result, int)

    def test_nano_time_monotonic(self) -> None:
        """单调递增。"""
        t1 = System.nano_time()
        t2 = System.nano_time()
        assert t2 >= t1

    def test_gc(self) -> None:
        """gc 不抛异常。"""
        System.gc()

    def test_millis_per_sec(self) -> None:
        """常量正确。"""
        assert System._MILLIS_PER_SEC == 1000


# -- Time --


class TestTime:
    """Time 工具测试。"""

    def test_now_type(self) -> None:
        """返回 datetime。"""
        from datetime import datetime

        assert isinstance(Time.now(), datetime)

    def test_today_type(self) -> None:
        """返回 date。"""
        from datetime import date

        assert isinstance(Time.today(), date)

    def test_format_dt_default(self) -> None:
        """默认格式化。"""
        from datetime import datetime

        dt = datetime(2024, 3, 15, 10, 30, 0)
        result = Time.format_dt(dt)
        assert result == "2024-03-15 10:30:00"

    def test_format_dt_custom(self) -> None:
        """自定义格式化。"""
        from datetime import datetime

        dt = datetime(2024, 3, 15, 10, 30, 0)
        result = Time.format_dt(dt, pattern="%Y/%m/%d")
        assert result == "2024/03/15"

    def test_parse_dt_default(self) -> None:
        """默认解析。"""
        dt = Time.parse_dt("2024-03-15 10:30:00")
        assert dt.year == 2024
        assert dt.month == 3
        assert dt.day == 15
        assert dt.hour == 10
        assert dt.minute == 30

    def test_parse_dt_custom(self) -> None:
        """自定义解析。"""
        dt = Time.parse_dt("2024/03/15", pattern="%Y/%m/%d")
        assert dt.year == 2024
        assert dt.month == 3

    def test_format_parse_roundtrip(self) -> None:
        """格式化/解析往返。"""
        from datetime import datetime

        dt = datetime(2025, 12, 25, 8, 0, 0)
        s = Time.format_dt(dt)
        dt2 = Time.parse_dt(s)
        assert dt2 == dt


# -- UuidV7 --


class TestUuidV7:
    """UuidV7 生成器测试。"""

    def test_generate_format(self) -> None:
        """生成的 UUID 格式正确。"""
        uuid_str = UuidV7.generate()
        pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        assert re.match(pattern, uuid_str) is not None

    def test_generate_unique(self) -> None:
        """连续生成不重复。"""
        uuids = {UuidV7.generate() for _ in range(100)}
        assert len(uuids) == 100

    def test_version_bits(self) -> None:
        """第 13 位为 '7'（版本号）。"""
        uuid_str = UuidV7.generate()
        assert uuid_str[14] == "7"

    def test_variant_bits(self) -> None:
        """第 17 位为 '8', '9', 'a', 或 'b'（变体 1）。"""
        uuid_str = UuidV7.generate()
        assert uuid_str[19] in "89ab"

    def test_from_timestamp_format(self) -> None:
        """from_timestamp 格式正确。"""
        ts = 1700000000000
        uuid_str = UuidV7.from_timestamp(ts)
        pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        assert re.match(pattern, uuid_str) is not None

    def test_from_timestamp_ordering(self) -> None:
        """较早时间戳生成的 UUID 排序在前。"""
        uuid1 = UuidV7.from_timestamp(1000000000000)
        uuid2 = UuidV7.from_timestamp(2000000000000)
        assert uuid1 < uuid2

    def test_from_timestamp_deterministic_prefix(self) -> None:
        """时间戳部分正确嵌入前 48 位。"""
        ts = 1700000000000
        uuid_str = UuidV7.from_timestamp(ts)
        ts_hex = format(ts, "012x")
        assert uuid_str[:8] + uuid_str[9:13] == ts_hex[:8] + ts_hex[8:12]
