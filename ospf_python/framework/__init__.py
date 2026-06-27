"""优化应用框架 / Optimization application framework.

提供装箱、切割、调度等领域的建模与求解框架。
Provides modeling and solving frameworks for bin packing,
cutting stock, scheduling, and related domains.
"""

from ospf_python.framework import bpp1d as bpp1d
from ospf_python.framework import bpp2d as bpp2d
from ospf_python.framework import bpp3d as bpp3d
from ospf_python.framework import csp1d as csp1d
from ospf_python.framework import csp2d as csp2d
from ospf_python.framework import (
    gantt_scheduling as gantt_scheduling,
)
from ospf_python.framework import log as log
from ospf_python.framework import model as model
from ospf_python.framework import network as network
from ospf_python.framework import (
    network_scheduling as network_scheduling,
)
from ospf_python.framework import persistence as persistence
from ospf_python.framework import solver as solver

__all__ = [
    "bpp1d",
    "bpp2d",
    "bpp3d",
    "csp1d",
    "csp2d",
    "gantt_scheduling",
    "log",
    "model",
    "network",
    "network_scheduling",
    "persistence",
    "solver",
]
