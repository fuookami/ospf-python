"""系统级工具方法 / System-level utility methods.

对应 Kotlin 端 System data object。
Mirrors the Kotlin ``System`` data object.
"""

from __future__ import annotations

import gc
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class System:
    """系统工具类 / System utility class.

    提供高精度计时与垃圾回收提示等底层方法。
    Provides high-resolution timing and garbage-collection hints.

    Attributes:
        _MILLIS_PER_SEC: 每秒毫秒数 / Milliseconds per second.
        _NANOS_PER_MILLI: 每毫秒纳秒数 / Nanoseconds per millisecond.
    """

    _MILLIS_PER_SEC: int = 1000
    _NANOS_PER_MILLI: int = 1_000_000

    @staticmethod
    def current_time_millis() -> int:
        """返回当前 Unix 时间戳（毫秒）。

        Returns the current Unix timestamp in milliseconds.

        Returns:
            当前时间戳（毫秒）。/ Current timestamp in millis.
        """
        return int(time.time() * System._MILLIS_PER_SEC)

    @staticmethod
    def nano_time() -> int:
        """返回高分辨率单调计时器值（纳秒）。

        Returns a high-resolution monotonic timer value in nanoseconds.
        仅适用于间隔测量，不表示墙钟时间。
        Suitable only for elapsed-time measurement, not wall-clock time.

        Returns:
            单调计时器值（纳秒）。/ Monotonic timer value in nanoseconds.
        """
        return time.perf_counter_ns()

    @staticmethod
    def gc() -> None:
        """提示 Python 运行时执行垃圾回收。

        Hints the Python runtime to perform garbage collection.
        实际回收时机由解释器决定。
        Actual reclamation timing is determined by the interpreter.
        """
        gc.collect()
