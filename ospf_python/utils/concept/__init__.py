"""概念协议层 / Concept protocol layer.

提供可复制、可移动、可索引、可交换等基础协议。
Provides fundamental protocols: copyable, movable, indexed,
and swappable.
"""

from ospf_python.utils.concept.clone import Copyable, Movable
from ospf_python.utils.concept.indexed import (
    AutoIndexed,
    Indexed,
    IndexedImpl,
    ManualIndexed,
)
from ospf_python.utils.concept.move import Movable as MovableReExport
from ospf_python.utils.concept.swap import Swappable

__all__ = [
    "AutoIndexed",
    "Copyable",
    "Indexed",
    "IndexedImpl",
    "ManualIndexed",
    "Movable",
    "MovableReExport",
    "Swappable",
]
