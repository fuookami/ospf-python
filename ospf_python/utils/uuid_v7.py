"""UUIDv7 生成工具 / UUIDv7 generation utilities.

对应 Kotlin 端 UUIDv7 data object。
Mirrors the Kotlin ``UUIDv7`` data object.

UUIDv7 (RFC 9562) 将 Unix 毫秒时间戳嵌入前 48 位，
保证全局有序且适合数据库主键。
UUIDv7 (RFC 9562) embeds a Unix-millisecond timestamp in the
leading 48 bits, ensuring lexicographic ordering and suitability
as database primary keys.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class UuidV7:
    """UUIDv7 生成器 / UUIDv7 generator.

    提供符合 RFC 9562 的 v7 UUID 生成功能。
    Provides v7 UUID generation compliant with RFC 9562.

    Attributes:
        _VERSION_BITS: 版本位（0111 = 7） / Version bits (0111 = 7).
        _VARIANT_BITS: 变体位（10xx） / Variant bits (10xx).
    """

    _VERSION_BITS: int = 0x7
    _VARIANT_BITS: int = 0x8  # 变体 1 的高两位 / High 2 bits of variant 1

    @staticmethod
    def generate() -> str:
        """生成一个 UUIDv7 字符串。

        Generates a UUIDv7 string.
        前 48 位为当前 Unix 毫秒时间戳，后续位随机填充。
        The leading 48 bits hold the current Unix-millisecond
        timestamp; remaining bits are random.

        Returns:
            小写带连字符的 UUID 字符串。/ Lowercase hyphenated UUID string.
        """
        ts = int(time.time() * 1000)
        return UuidV7.from_timestamp(ts)

    @staticmethod
    def from_timestamp(ts: int) -> str:
        """从给定时间戳创建 UUIDv7 字符串。

        Creates a UUIDv7 string from the given timestamp.

        Args:
            ts: Unix 毫秒时间戳 / Unix timestamp in milliseconds.

        Returns:
            小写带连字符的 UUID 字符串。/ Lowercase hyphenated UUID string.
        """
        # 时间戳占前 48 位 / Timestamp occupies the leading 48 bits
        ts_bytes = ts.to_bytes(6, byteorder="big")

        # 剩余 10 字节随机填充 / Fill remaining 10 bytes randomly
        rand_bytes = os.urandom(10)

        # 组合 16 字节 / Assemble 16 bytes
        raw = bytearray(16)
        raw[0:6] = ts_bytes
        raw[6:16] = rand_bytes

        # 设置版本号（第 7 字节高 4 位 = 0111） /
        # Set version (byte 7 high nibble = 0111)
        raw[6] = (raw[6] & 0x0F) | (UuidV7._VERSION_BITS << 4)

        # 设置变体（第 9 字节高 2 位 = 10） /
        # Set variant (byte 9 high 2 bits = 10)
        raw[8] = (raw[8] & 0x3F) | (UuidV7._VARIANT_BITS << 4)

        # 转换为标准连字符格式 / Convert to standard hyphenated format
        hex_str = raw.hex()
        return (
            f"{hex_str[0:8]}-{hex_str[8:12]}-{hex_str[12:16]}"
            f"-{hex_str[16:20]}-{hex_str[20:32]}"
        )
