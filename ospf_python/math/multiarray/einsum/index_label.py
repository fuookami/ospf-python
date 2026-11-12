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

        三条校验：`indices` 必须是元组、每个标签必须是内置 `str` 且恰好一个字符。
        违反任一条都抛 `ValueError`。

        **为什么拒绝 `str` 本身**：`IndexLabel(indices="ij")` 的每个字符长度都是 1，
        所以只检查元素长度会让它**通过**校验，得到一个 `indices == "ij"` 的半坏对象——
        `ndim` 变成 2 看似正确，`__iter__` 却返回 `"ij"` 而不是 `("i","j")`，
        `__contains__` 变成子串匹配。这里连同类型一起校验，把这种情形也挡住。

        **历史**：这里曾在循环里用 `object.__setattr__` 把 `indices` 整个换成当前
        多字符标签拆开后的元组——它每命中一个就覆盖一次，于是
        `IndexLabel(indices=("ab", "c"))` 会得到 `("a", "b")`，**`"c"` 被丢掉**。
        本方法声明的是「校验」，所以改成报错而不是猜意图。

        Three checks: `indices` must be a tuple, and every label must be a builtin `str`
        of exactly one character; any violation raises `ValueError`.

        The `str` case is rejected explicitly: `IndexLabel(indices="ij")` has
        one-character elements, so a length-only check would *pass* it and leave
        `indices == "ij"` — `ndim` looks right (2) while `__iter__` returns `"ij"`
        instead of `("i", "j")` and `__contains__` silently becomes substring matching.

        History: the previous implementation replaced the whole `indices` tuple inside the
        loop, so `("ab", "c")` became `("a", "b")` — silently dropping `"c"`. The method
        is documented as validation, so it rejects instead of guessing intent.

        Raises:
            ValueError: `indices` 不是元组，或存在长度不为 1 的标签，或标签不是内置 `str`。
                / `indices` is not a tuple, a label is not exactly one character, or a
                label is not a builtin `str`.
        """
        if type(self.indices) is not tuple:
            raise ValueError(
                f"索引标签必须是元组，收到 {type(self.indices).__name__}"
                f" / index labels must be a tuple, got {type(self.indices).__name__}"
            )
        for idx in self.indices:
            if type(idx) is not str or len(idx) != 1:
                raise ValueError(
                    f"索引标签必须恰好一个字符的内置 str，收到 {idx!r}"
                    f" / index labels must be a builtin str of exactly one character,"
                    f" got {idx!r}"
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
