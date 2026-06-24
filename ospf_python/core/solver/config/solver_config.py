"""求解器配置抽象基类 / Solver config abstract base class.

定义所有求解器配置的公共接口。
Defines the common interface for all solver configurations.
"""

from __future__ import annotations

import abc


class SolverConfig(abc.ABC):
    """求解器配置抽象基类 / Abstract base class for solver configs.

    所有具体求解器配置必须实现名称属性和时间限制。
    All concrete solver configs must implement the name
    property and time limit.

    Attributes:
        name: 配置名称 / The config name.
        time_limit: 时间限制（秒）/ Time limit in seconds.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """获取配置名称 / Get the config name."""
        ...

    @property
    @abc.abstractmethod
    def time_limit(self) -> float:
        """获取时间限制 / Get the time limit.

        Returns:
            时间限制（秒）/ Time limit in seconds.
        """
        ...
