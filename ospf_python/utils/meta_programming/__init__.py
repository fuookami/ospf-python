"""元编程工具 / Meta-programming utilities.

包含惰性委托、名称转换和命名系统。
Contains lazy delegates, name transfer, and naming systems.
"""

from ospf_python.utils.meta_programming.lazy_delegate import (
    LazyDelegate,
    SelfLazyDelegate,
    SuspendLazy,
)
from ospf_python.utils.meta_programming.name_transfer import (
    NameTransfer,
    NameTransferCacheKey,
)
from ospf_python.utils.meta_programming.naming_system import NamingSystem

__all__ = [
    "LazyDelegate",
    "NameTransfer",
    "NameTransferCacheKey",
    "NamingSystem",
    "SelfLazyDelegate",
    "SuspendLazy",
]
