"""带容差的数值。

Toleranced value.

本模块只做转发：唯一实现是 ``ospf_python.math.ordinary.toleranced.Toleranced``。
这里曾有一份独立副本，它的 ``__eq__`` 按容差比较而 ``__hash__`` 按精确字段比较，
导致 ``a == b`` 为真却 ``b in {a}`` 为假；按容差的相等不具备传递性，本来就不能参与
哈希契约。需要容差比较时用 ``contains`` / ``overlaps``。

This module only re-exports: the single implementation lives in
``ospf_python.math.ordinary.toleranced.Toleranced``. An independent copy used to live here whose
``__eq__`` compared within tolerance while ``__hash__`` compared exact fields, so ``a == b``
could be true while ``b in {a}`` was false. Tolerance-based equality is not transitive and
therefore cannot satisfy the hash contract. Use ``contains`` / ``overlaps`` for tolerance.
"""

from __future__ import annotations

from ospf_python.math.ordinary.toleranced import Toleranced

__all__ = ["Toleranced"]
