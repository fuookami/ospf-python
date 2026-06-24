"""张量表达式。

Parsed tensor expression with input and output indices.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.math.multiarray.einsum.index_label import IndexLabel


@dataclass(frozen=True)
class TensorExpr:
    """已解析的张量表达式。

    A parsed tensor expression containing input and output
    index labels.

    Attributes:
        inputs: 输入操作数的索引标签列表。
            Index labels for each input operand.
        output: 输出操作数的索引标签。
            Index labels for the output.
    """

    inputs: tuple[IndexLabel, ...]
    output: IndexLabel

    @property
    def num_operands(self) -> int:
        """获取操作数数量。/ Get number of operands."""
        return len(self.inputs)

    @property
    def all_input_indices(self) -> tuple[str, ...]:
        """获取所有输入索引（含重复）。

        Get all input indices (including duplicates).
        """
        result: list[str] = []
        for label in self.inputs:
            result.extend(label.indices)
        return tuple(result)

    @property
    def free_indices(self) -> tuple[str, ...]:
        """获取自由索引（出现在输出中的索引）。

        Get free indices (those appearing in the output).
        """
        return self.output.indices

    @property
    def summation_indices(self) -> tuple[str, ...]:
        """获取求和索引（不出现在输出中的输入索引）。

        Get summation indices (input indices not in output).
        """
        free = set(self.free_indices)
        seen: set[str] = set()
        result: list[str] = []
        for idx in self.all_input_indices:
            if idx not in free and idx not in seen:
                seen.add(idx)
                result.append(idx)
        return tuple(result)

    def __repr__(self) -> str:
        """返回字符串表示。/ Return string representation."""
        in_str = ",".join("".join(lbl.indices) for lbl in self.inputs)
        out_str = "".join(self.output.indices)
        return f"TensorExpr({in_str}->{out_str})"
