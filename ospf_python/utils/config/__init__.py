"""配置模块 / Configuration module.

提供版本信息等全局配置。
Provides global configuration such as version info.
"""

from ospf_python.utils.config.version import VERSION, Version

__all__ = [
    "VERSION",
    "Version",
]
