"""爱因斯坦求和下标解析器。

Einstein summation subscript parser.
"""

from __future__ import annotations

from ospf_python.math.multiarray.einsum.einsum_error import (
    EinsumError,
)
from ospf_python.math.multiarray.einsum.index_label import IndexLabel


def parse_einsum(
    subscripts: str,
) -> tuple[list[IndexLabel], IndexLabel] | EinsumError:
    """解析爱因斯坦求和下标字符串。

    Parse einsum subscript string like "ij,jk->ik" into
    input index labels and output index labels.

    Args:
        subscripts: 下标字符串，格式为 "ij,jk->ik"。
            / Subscript string, format "ij,jk->ik".

    Returns:
        (输入索引标签列表, 输出索引标签) 或错误。
        (Input index labels, output index labels) or error.
    """
    stripped = subscripts.replace(" ", "")

    if "->" in stripped:
        parts = stripped.split("->", 1)
        if len(parts) != 2:
            return EinsumError(
                message=(
                    f"无效的下标格式: {subscripts}"
                    f" / Invalid subscript format: {subscripts}"
                )
            )
        input_part, output_part = parts
    else:
        # 无显式输出，推断输出为未重复的字母
        # No explicit output, infer from non-repeated letters
        input_part = stripped
        output_part = ""

    input_labels: list[IndexLabel] = []
    for operand_str in input_part.split(","):
        if not operand_str:
            return EinsumError(
                message=(
                    f"空操作数下标: {subscripts}"
                    f" / Empty operand subscript: {subscripts}"
                )
            )
        chars = tuple(operand_str)
        input_labels.append(IndexLabel(indices=chars))

    if output_part:
        output_chars = tuple(output_part)
    else:
        # 推断输出：输入中仅出现一次的字符
        # Infer output: chars appearing exactly once
        all_chars: list[str] = []
        for label in input_labels:
            all_chars.extend(label.indices)
        seen_once = []
        seen_set: set[str] = set()
        seen_multi: set[str] = set()
        for c in all_chars:
            if c in seen_set:
                seen_multi.add(c)
            else:
                seen_set.add(c)
                seen_once.append(c)
        output_chars = tuple(c for c in seen_once if c not in seen_multi)

    output_label = IndexLabel(indices=output_chars)
    return input_labels, output_label
