"""爱因斯坦求和模块测试。

Einstein summation module tests.

测试 einsum 解析、IndexLabel、TensorExpr、
以及基本 einsum 运算。
Tests einsum parsing, IndexLabel, TensorExpr,
and basic einsum operations.
"""

from __future__ import annotations

from ospf_python.math.multiarray.einsum.einsum import einsum
from ospf_python.math.multiarray.einsum.einsum_error import (
    EinsumError,
)
from ospf_python.math.multiarray.einsum.einsum_parser import (
    parse_einsum,
)
from ospf_python.math.multiarray.einsum.index_label import (
    IndexLabel,
)
from ospf_python.math.multiarray.einsum.operations import (
    diagonal,
    tensordot,
    trace,
)
from ospf_python.math.multiarray.einsum.tensor_expr import (
    TensorExpr,
)
from ospf_python.multiarray.multi_array import MultiArray
from ospf_python.multiarray.shape import DynShape

# ── IndexLabel ────────────────────────────────────────────────────


class TestIndexLabel:
    """索引标签测试。"""

    def test_creation(self) -> None:
        """创建索引标签。/ Create index label."""
        label = IndexLabel(indices=("i", "j"))
        assert label.ndim == 2

    def test_contains(self) -> None:
        """包含检查。/ Contains check."""
        label = IndexLabel(indices=("i", "j", "k"))
        assert "i" in label
        assert "z" not in label

    def test_len(self) -> None:
        """长度。/ Length."""
        label = IndexLabel(indices=("a", "b"))
        assert len(label) == 2

    def test_frozen(self) -> None:
        """不可变性。/ Immutability."""
        label = IndexLabel(indices=("x",))
        assert label.indices == ("x",)


# ── Einsum parser ─────────────────────────────────────────────────


class TestEinsumParser:
    """einsum 解析器测试。"""

    def test_parse_matrix_multiply(self) -> None:
        """解析矩阵乘法下标。/ Parse matmul subscripts."""
        result = parse_einsum("ij,jk->ik")
        assert not isinstance(result, EinsumError)
        inputs, output = result
        assert len(inputs) == 2
        assert inputs[0].indices == ("i", "j")
        assert inputs[1].indices == ("j", "k")
        assert output.indices == ("i", "k")

    def test_parse_trace(self) -> None:
        """解析迹下标。/ Parse trace subscripts."""
        result = parse_einsum("ii->")
        assert not isinstance(result, EinsumError)
        inputs, output = result
        assert len(inputs) == 1
        assert output.indices == ()

    def test_parse_inner_product(self) -> None:
        """解析内积下标。/ Parse inner product subscripts."""
        result = parse_einsum("i,i->")
        assert not isinstance(result, EinsumError)
        inputs, output = result
        assert len(inputs) == 2

    def test_parse_no_output(self) -> None:
        """无显式输出推断。/ Infer output without arrow."""
        result = parse_einsum("ij,jk")
        assert not isinstance(result, EinsumError)
        inputs, output = result
        assert len(inputs) == 2

    def test_parse_elementwise(self) -> None:
        """解析逐元素乘法。/ Parse elementwise mul."""
        result = parse_einsum("ij,ij->ij")
        assert not isinstance(result, EinsumError)
        inputs, output = result
        assert len(inputs) == 2
        assert output.indices == ("i", "j")

    def test_parse_empty_operand(self) -> None:
        """空操作数错误。/ Empty operand error."""
        result = parse_einsum(",ij->i")
        assert isinstance(result, EinsumError)


# ── TensorExpr ────────────────────────────────────────────────────


class TestTensorExpr:
    """张量表达式测试。"""

    def test_creation(self) -> None:
        """创建张量表达式。/ Create tensor expr."""
        expr = TensorExpr(
            inputs=(
                IndexLabel(indices=("i", "j")),
                IndexLabel(indices=("j", "k")),
            ),
            output=IndexLabel(indices=("i", "k")),
        )
        assert expr.num_operands == 2

    def test_free_indices(self) -> None:
        """自由索引。/ Free indices."""
        expr = TensorExpr(
            inputs=(
                IndexLabel(indices=("i", "j")),
                IndexLabel(indices=("j", "k")),
            ),
            output=IndexLabel(indices=("i", "k")),
        )
        assert set(expr.free_indices) == {"i", "k"}

    def test_summation_indices(self) -> None:
        """求和索引。/ Summation indices."""
        expr = TensorExpr(
            inputs=(
                IndexLabel(indices=("i", "j")),
                IndexLabel(indices=("j", "k")),
            ),
            output=IndexLabel(indices=("i", "k")),
        )
        assert set(expr.summation_indices) == {"j"}

    def test_repr(self) -> None:
        """字符串表示。/ String representation."""
        expr = TensorExpr(
            inputs=(
                IndexLabel(indices=("i", "j")),
                IndexLabel(indices=("j", "k")),
            ),
            output=IndexLabel(indices=("i", "k")),
        )
        r = repr(expr)
        assert "ij,jk->ik" in r


# ── Einsum operations ─────────────────────────────────────────────


def _make_2x2(
    data: list[float],
) -> MultiArray[float, DynShape]:
    """创建 2x2 数组。/ Create 2x2 array."""
    shape = DynShape(dims=(2, 2))
    import numpy as np

    return MultiArray(shape, np.array(data, dtype=np.float64))


def _make_3x3(
    data: list[float],
) -> MultiArray[float, DynShape]:
    """创建 3x3 数组。/ Create 3x3 array."""
    shape = DynShape(dims=(3, 3))
    import numpy as np

    return MultiArray(shape, np.array(data, dtype=np.float64))


class TestEinsumOperations:
    """einsum 操作测试。"""

    def test_trace_2x2(self) -> None:
        """2x2 矩阵迹。/ 2x2 matrix trace."""
        arr = _make_2x2([1.0, 2.0, 3.0, 4.0])
        assert trace(arr) == 5.0

    def test_trace_3x3(self) -> None:
        """3x3 矩阵迹。/ 3x3 matrix trace."""
        arr = _make_3x3([1.0, 0.0, 0.0, 0.0, 2.0, 0.0, 0.0, 0.0, 3.0])
        assert trace(arr) == 6.0

    def test_diagonal(self) -> None:
        """对角线提取。/ Diagonal extraction."""
        arr = _make_2x2([1.0, 2.0, 3.0, 4.0])
        diag = diagonal(arr)
        assert diag.size == 2
        assert diag.get(0) == 1.0
        assert diag.get(1) == 4.0

    def test_tensordot(self) -> None:
        """张量收缩。/ Tensor contraction."""
        a = _make_2x2([1.0, 2.0, 3.0, 4.0])
        b = _make_2x2([5.0, 6.0, 7.0, 8.0])
        result = tensordot(a, b, axes=1)
        assert result.ndim == 2

    def test_einsum_matmul(self) -> None:
        """einsum 矩阵乘法。/ einsum matrix multiply."""
        a = _make_2x2([1.0, 0.0, 0.0, 1.0])
        b = _make_2x2([5.0, 6.0, 7.0, 8.0])
        result = einsum("ij,jk->ik", a, b)
        assert not isinstance(result, EinsumError)
        assert isinstance(result, MultiArray)
        assert result.get(0, 0) == 5.0
        assert result.get(1, 1) == 8.0

    def test_einsum_trace(self) -> None:
        """einsum 迹。/ einsum trace."""
        arr = _make_2x2([1.0, 2.0, 3.0, 4.0])
        result = einsum("ii->", arr)
        assert not isinstance(result, EinsumError)
        assert result == 5.0

    def test_einsum_operand_mismatch(self) -> None:
        """操作数数量不匹配。/ Operand count mismatch."""
        a = _make_2x2([1.0, 2.0, 3.0, 4.0])
        result = einsum("ij,jk->ik", a)
        assert isinstance(result, EinsumError)

    def test_einsum_dimension_mismatch(self) -> None:
        """维度不匹配。/ Dimension mismatch."""
        a = _make_2x2([1.0, 2.0, 3.0, 4.0])
        b = _make_2x2([5.0, 6.0, 7.0, 8.0])
        result = einsum("ijk,jk->ik", a, b)
        assert isinstance(result, EinsumError)

    def test_einsum_invalid_subscripts(self) -> None:
        """无效下标格式。/ Invalid subscript format."""
        a = _make_2x2([1.0, 2.0, 3.0, 4.0])
        result = einsum("->->->", a)
        assert isinstance(result, EinsumError)
