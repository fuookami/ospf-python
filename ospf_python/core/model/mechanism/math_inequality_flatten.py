"""数学不等式扁平化 / Math inequality flattening.

将嵌套的不等式表达式扁平化为标准形式。
Flattens nested inequality expressions into
standard form.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MathInequalityFlatten:
    """数学不等式扁平化器 / Math inequality flattener.

    将复杂的嵌套不等式表达式递归展开为线性三元组。
    Recursively expands complex nested inequality expressions
    into linear triads.

    Attributes:
        terms: 展开后的项列表（变量名, 系数） / List of
            expanded terms (variable name, coefficient).
        constant: 常数项 / The constant term.
    """

    terms: dict[str, float] = field(default_factory=dict)
    constant: float = 0.0

    def add_term(
        self,
        variable: str,
        coefficient: float,
    ) -> None:
        """添加项 / Add a term.

        Args:
            variable: 变量名 / The variable name.
            coefficient: 系数 / The coefficient.
        """
        current = self.terms.get(variable, 0.0)
        self.terms[variable] = current + coefficient

    def add_constant(self, value: float) -> None:
        """添加常数 / Add a constant.

        Args:
            value: 常数值 / The constant value.
        """
        self.constant += value
