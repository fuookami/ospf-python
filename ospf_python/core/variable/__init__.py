"""核心变量模块 / Core variable module.

提供变量类型、变量项和变量范围定义。
Provides variable types, variable items, and variable range
definitions.
"""

from ospf_python.core.variable.abstract_variable_item import (
    AbstractVariableItem,
)
from ospf_python.core.variable.any_variable import AnyVariable
from ospf_python.core.variable.type import VariableType
from ospf_python.core.variable.variable_combination_item import (
    VariableCombinationItem,
)
from ospf_python.core.variable.variable_independent_item import (
    VariableIndependentItem,
)
from ospf_python.core.variable.variable_range import VariableRange

__all__ = [
    "AbstractVariableItem",
    "AnyVariable",
    "VariableCombinationItem",
    "VariableIndependentItem",
    "VariableRange",
    "VariableType",
]
