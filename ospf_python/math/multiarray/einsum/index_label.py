"""爱因斯坦求和索引标签。

Einstein summation index labels.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IndexLabel:
    """索引标签集合。

    A frozen collection of index labels for einsum subscripts.

    每个标签为单字符字符串，如 'i', 'j', 'k'。
    Each label is a single-character string like 'i', 'j', 'k'.

    Attributes:
        indices: 索引标签元组。/ Tuple of index labels.
    """

    indices: tuple[str, ...]

    def __post_init__(self) -> None:
        """校验索引标签合法性。

        Validate index labels are single characters.
        """
        for idx in self.indices:
            if len(idx) != 1:
                object.__setattr__(
                    self,
                    "indices",
                    tuple(c for c in idx),
                )

    @property
    def ndim(self) -> int:
        """获取索引维度数。/ Get number of index dimensions."""
        return len(self.indices)

    def __contains__(self, label: str) -> bool:
        """检查是否包含指定标签。

        Check whether a label is in this index set.

        Args:
            label: 待检查的标签。/ Label to check.

        Returns:
            是否包含。/ Whether contained.
        """
        return label in self.indices

    def __iter__(self) -> tuple[str, ...]:
        """迭代索引标签。/ Iterate over index labels."""
        return self.indices

    def __len__(self) -> int:
        """返回索引数量。/ Return number of indices."""
        return len(self.indices)
