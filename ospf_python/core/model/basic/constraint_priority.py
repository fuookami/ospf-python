"""约束优先级枚举 / Constraint priority enumeration.

定义模型约束的优先级层次，用于约束松弛和冲突解决。
Defines priority levels for model constraints, used in
constraint relaxation and conflict resolution.
"""

from __future__ import annotations

import enum


class ConstraintPriority(enum.Enum):
    """约束优先级 / Constraint priority.

    约束优先级决定了在模型不可行时哪些约束可以被松弛。
    Constraint priority determines which constraints may be
    relaxed when the model is infeasible.

    Attributes:
        value: 优先级整数值 / The integer priority value.
    """

    REQUIRED = 0
    """必需约束 / Required constraint.

    不可松弛，违反即不可行。
    Cannot be relaxed; violation means infeasible.
    """

    PREFERRED = 1
    """首选约束 / Preferred constraint.

    优先满足，但可在必要时松弛。
    Satisfied preferentially, but may be relaxed if needed.
    """

    OPTIONAL = 2
    """可选约束 / Optional constraint.

    仅在不影响其他约束时满足。
    Satisfied only when it does not affect other constraints.
    """
