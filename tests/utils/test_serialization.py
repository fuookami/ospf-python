"""Serialization 模块测试 / Tests for serialization utilities.

覆盖 csv、date_time_serializer、duration_serializer、json。
Covers csv, date_time_serializer, duration_serializer, json.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from ospf_python.utils.meta_programming.naming_system import NamingSystem
from ospf_python.utils.serialization.csv import from_csv, to_csv
from ospf_python.utils.serialization.date_time_serializer import (
    deserialize_datetime,
    deserialize_timestamp,
    serialize_datetime,
    serialize_timestamp,
)
from ospf_python.utils.serialization.duration_serializer import (
    deserialize_duration,
    serialize_duration,
)
from ospf_python.utils.serialization.json import JsonNamingPolicy

# -- CSV --


@dataclass
class _Person:
    """测试用数据类 / Test dataclass."""

    name: str
    age: int


class TestCsv:
    """CSV 序列化测试。"""

    def test_to_csv_dicts(self) -> None:
        """字典列表序列化为 CSV。"""
        records = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        result = to_csv(records)
        assert "a,b" in result
        assert "1,2" in result
        assert "3,4" in result

    def test_to_csv_dataclass(self) -> None:
        """dataclass 实例序列化为 CSV。"""
        records = [_Person("Alice", 30), _Person("Bob", 25)]
        result = to_csv(records)
        assert "name,age" in result
        assert "Alice,30" in result

    def test_to_csv_empty(self) -> None:
        """空记录返回空字符串。"""
        assert to_csv([]) == ""

    def test_to_csv_custom_delimiter(self) -> None:
        """自定义分隔符。"""
        records = [{"x": 1, "y": 2}]
        result = to_csv(records, delimiter=";")
        assert "x;y" in result

    def test_from_csv_basic(self) -> None:
        """基本 CSV 反序列化。"""
        text = "name,age\nAlice,30\nBob,25\n"
        result = from_csv(text)
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[0]["age"] == "30"

    def test_from_csv_with_types(self) -> None:
        """带类型转换的 CSV 反序列化。"""
        text = "name,age\nAlice,30\n"
        result = from_csv(text, field_types={"age": int})
        assert result[0]["age"] == 30

    def test_from_csv_empty(self) -> None:
        """空文本返回空列表。"""
        assert from_csv("") == []
        assert from_csv("   ") == []

    def test_roundtrip(self) -> None:
        """序列化再反序列化保持数据一致。"""
        records = [{"x": "hello", "y": "world"}]
        csv_text = to_csv(records)
        result = from_csv(csv_text)
        assert result[0]["x"] == "hello"
        assert result[0]["y"] == "world"


# -- DateTime serializer --


class TestDateTimeSerializer:
    """日期时间序列化测试。"""

    def test_serialize_datetime(self) -> None:
        """序列化 datetime 为 ISO 格式。"""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = serialize_datetime(dt)
        assert "2024-01-15" in result
        assert "10:30:00" in result

    def test_deserialize_datetime(self) -> None:
        """从 ISO 格式反序列化 datetime。"""
        s = "2024-01-15T10:30:00"
        dt = deserialize_datetime(s)
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 15

    def test_datetime_roundtrip(self) -> None:
        """datetime 序列化/反序列化往返。"""
        dt = datetime(2025, 6, 1, 12, 0, 0, tzinfo=UTC)
        s = serialize_datetime(dt)
        dt2 = deserialize_datetime(s)
        assert dt2.year == dt.year
        assert dt2.month == dt.month
        assert dt2.day == dt.day

    def test_serialize_timestamp(self) -> None:
        """序列化 datetime 为 Unix 时间戳。"""
        dt = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        ts = serialize_timestamp(dt)
        assert isinstance(ts, float)

    def test_deserialize_timestamp(self) -> None:
        """从 Unix 时间戳反序列化。"""
        ts = 1704067200.0
        dt = deserialize_timestamp(ts)
        assert dt.year == 2024
        assert dt.tzinfo is not None


# -- Duration serializer --


class TestDurationSerializer:
    """时长序列化测试。"""

    def test_serialize_zero(self) -> None:
        """零时长序列化为 '0s'。"""
        assert serialize_duration(timedelta(0)) == "0s"

    def test_serialize_seconds(self) -> None:
        """纯秒数。"""
        assert serialize_duration(timedelta(seconds=30)) == "30s"

    def test_serialize_minutes(self) -> None:
        """分钟和秒。"""
        result = serialize_duration(timedelta(minutes=2, seconds=15))
        assert "2m" in result
        assert "15s" in result

    def test_serialize_hours(self) -> None:
        """小时。"""
        result = serialize_duration(timedelta(hours=3))
        assert result == "3h"

    def test_serialize_days(self) -> None:
        """天数。"""
        result = serialize_duration(timedelta(days=1, hours=2))
        assert "1d" in result
        assert "2h" in result

    def test_serialize_negative(self) -> None:
        """负时长带负号。"""
        result = serialize_duration(timedelta(seconds=-10))
        assert result.startswith("-")

    def test_serialize_fractional_seconds(self) -> None:
        """小数秒。"""
        result = serialize_duration(timedelta(seconds=1.5))
        assert "1.500s" in result

    def test_deserialize_zero(self) -> None:
        """反序列化 '0s'。"""
        assert deserialize_duration("0s") == timedelta(0)

    def test_deserialize_complex(self) -> None:
        """复合时长反序列化。"""
        result = deserialize_duration("1d2h30m15s")
        assert result.days == 1
        assert result.seconds == 2 * 3600 + 30 * 60 + 15

    def test_deserialize_negative(self) -> None:
        """负时长反序列化。"""
        result = deserialize_duration("-5s")
        assert result.total_seconds() == -5.0

    def test_deserialize_fractional(self) -> None:
        """小数秒反序列化。"""
        result = deserialize_duration("1.5s")
        assert abs(result.total_seconds() - 1.5) < 0.001

    def test_deserialize_empty(self) -> None:
        """空字符串返回零时长。"""
        assert deserialize_duration("") == timedelta(0)

    def test_roundtrip(self) -> None:
        """序列化/反序列化往返。"""
        td = timedelta(days=1, hours=2, minutes=30, seconds=45)
        s = serialize_duration(td)
        td2 = deserialize_duration(s)
        assert abs(td.total_seconds() - td2.total_seconds()) < 0.001


# -- JsonNamingPolicy --


class TestJsonNamingPolicy:
    """JSON 命名策略测试。"""

    def test_camel_case_keys(self) -> None:
        """snake_case 转 camelCase。"""
        policy = JsonNamingPolicy.camel_case()
        result = policy.apply_to_keys({"user_name": "Alice"})
        assert "userName" in result

    def test_snake_case_keys(self) -> None:
        """camelCase 转 snake_case。"""
        policy = JsonNamingPolicy.snake_case()
        result = policy.apply_to_keys({"userName": "Alice"})
        assert "user_name" in result

    def test_pascal_case_keys(self) -> None:
        """snake_case 转 PascalCase。"""
        policy = JsonNamingPolicy.pascal_case()
        result = policy.apply_to_keys({"user_name": "Alice"})
        assert "UserName" in result

    def test_nested_dict(self) -> None:
        """递归处理嵌套字典。"""
        policy = JsonNamingPolicy.camel_case()
        data = {"user_info": {"first_name": "Alice"}}
        result = policy.apply_to_keys(data)
        assert "userInfo" in result
        assert "firstName" in result["userInfo"]

    def test_list_in_dict(self) -> None:
        """递归处理列表中的字典。"""
        policy = JsonNamingPolicy.camel_case()
        data = {"items": [{"item_name": "x"}]}
        result = policy.apply_to_keys(data)
        assert "itemName" in result["items"][0]

    def test_custom_source_target(self) -> None:
        """自定义源和目标命名系统。"""
        policy = JsonNamingPolicy(
            source=NamingSystem.CAMEL_CASE,
            target=NamingSystem.PASCAL_CASE,
        )
        result = policy.apply_to_keys({"userName": "Alice"})
        assert "UserName" in result

    def test_value_preserved(self) -> None:
        """值在键名转换后保持不变。"""
        policy = JsonNamingPolicy.camel_case()
        result = policy.apply_to_keys({"my_key": 42})
        assert result["myKey"] == 42
