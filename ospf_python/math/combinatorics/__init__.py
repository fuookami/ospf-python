"""组合数学模块。

Combinatorics module.
"""

from ospf_python.math.combinatorics.combinations import (
    combinations,
)
from ospf_python.math.combinatorics.combinatorics_async import (
    combinations_async,
    permutations_async,
)
from ospf_python.math.combinatorics.cross import cross
from ospf_python.math.combinatorics.permutations import (
    permutations,
)

__all__ = [
    "combinations",
    "combinations_async",
    "cross",
    "permutations",
    "permutations_async",
]
