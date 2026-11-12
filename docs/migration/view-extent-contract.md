# 视图有效范围与旧字段桥接 / View Extents and Legacy Field Bridge

## 受检剩余区域 / Checked Remaining Regions

私有 `MultiArray.view`、`MutableMultiArray.view` 和矩形 view 的 `view` 接受
`offsets=None, shape=None`，所有参数仍是 keyword-only，返回既有 Result。

- `offsets=None` 表示每轴起点为零；显式 tuple 必须包含 rank 个非 bool 整数。
  显式空 tuple 仅对 scalar 合法，不把它与 None 或其他 false 值混同。
- `shape=None` 在 native crate 内推导 `source_dim - offset`；必须每轴非空，继承当前源
  storage order。负数、超机器整数、offset 等于/超过轴长、rank 不符均失败。
  空区域不在当前正轴稠密 shape 合同内，不能靠 usize 下溢产生巨大范围。
- 显式 shape 仍是同 rank、同 order、非空且不越界的受检区域；省略 offset 可表示从零开始
  的截断区域。原有显式 offsets/shape 调用行为不变。
- 嵌套省略 shape 时，只覆盖**当前父区域**内的剩余部分，不能延伸到最终源剩余范围。
  原生组合相对 offset；门面保活最终源，不保存中间元素缓存或 Python 索引生成器。
- 仅范围差值和 offset 投影是绑定的防护代码；shape/strides/index/物化遍历仍委托固定 Rust。
  不更新 Rust revision，不调用有 RG-004 缺陷的任意轴映射。
- scalar `()` 的零偏移剩余区域仍为一个叶；singleton 和高 rank 不依赖 Python 递归。
  mutable view 保留同一 Rust 权威存储，写回、live 读取、GC 和对象图合同不变。

These are metadata-only views with checked suffix extents. They do not allocate element
snapshots or change the existing explicit-region, ownership, iteration or storage contracts.

## 旧视图显式复制 / Explicit Legacy View Copy

`MultiArrayView.from_legacy_state(*, payload, copy, standard_layout=False)` 接受已经解码的
内置 dict，字段必须恰为 `_source`、`_offsets`。这不是读取 pickle 字节的接口，也不是
公共 `__setstate__`。与数组旧字段桥接一样，只能处理可信来源。

```python
import numpy as np

from ospf_python._binding.multiarray import MultiArrayView
from ospf_python.multiarray.multi_array import MultiArray
from ospf_python.multiarray.multi_array_view import MultiArrayView as PublicView
from ospf_python.multiarray.shape import Shape2, StorageOrder

source = MultiArray(Shape2(2, 3, StorageOrder.COLUMN_MAJOR), np.arange(6))
old = PublicView(source, offsets=(1, 1))
new = MultiArrayView.from_legacy_state(payload=vars(old), copy=True).unwrap()
assert new.shape.dims == (1, 2)
assert new.to_list().unwrap() == [[3, 5]]
```

- `_source` 必须是**精确内置**公开 MultiArray/MutableMultiArray；其 vars 按
  `legacy-array-bridge.md` 的 `_shape/_data` 合同复制。未知字段、子类、嵌套旧 view、
  mapped view 或任意 duck type 拒绝，不能静默丢失扩展状态、递归或执行旧回调。
  自定义 shape 仍需显式 `standard_layout=True`，不调用它的旧索引算法。
- `_offsets` 必须是实际旧字段中的整数 tuple。它不是构造参数；None、list、缺失字段
  不按默认零值容错。有效剩余范围由上述 Rust 路径推导，不复制旧 advertised shape。
- `copy` 必须显式传入 bool。False 返回 NOT_SUPPORTED；True 复制**整个源**到一个独立
  immutable Rust 引用存储，然后创建只读基础 MultiArrayView，不是 mutable/shared view。
  该静态入口始终返回基础只读 view，不隐式构造调用方子类或丢失其扩展字段。
- 不调用旧 `get/flat_index/materialize`，也不调用叶的 item/iter/truth。源旧字段的物理
  顺序、NumPy scalar 类型、Result/None/不透明对象身份保留，读取不做旧 scalar.item 转换。
  这是显式导入合同，不冒充公共 get 的原样行为。
- 新 view 不保留旧数组、view 或 ndarray，除非叶上原本存在回边；不会重定位叶的 owner。
  整个复制源（含区域外叶）由 view 保活，空间为 O(source size)，并非 O(region size)。
  需要只保留区域时可显式 materialize 后释放原 view；不会自动破坏 source alias 语义。
- 外部缓冲写入不影响新槽位。不同导入各自复制源，不自动保留原图中多个 view 的 source
  alias；copy/deepcopy/pickle 的新图合同见 `array-state-contract.md`。
  不保持旧 dtype 赋值约束，不自动恢复旧公共 pickle，不声称解决仍被旧 ndarray 保留的环。
- 非法 metadata 不发布 view，源不变。该入口先取源快照再受检区域；失败可有临时 O(N)
  快照成本，但不持久保留其叶。外部 NumPy 写线程/自定义 shape 属性由调用方同步。

Public views still advertise the full source shape; their shape/get authority remains pending.
The ordinary public materialize operation now has a checked remaining-region native candidate
and explicitly returns the existing Result; see `public-view-materialization.md`. That storage-copy
operation is distinct from this explicit Rust-owned import and does not certify full public state,
callback, scalar-conversion, lifecycle or distribution acceptance.

## 验证与剩余门槛 / Verification and Remaining Gates

`tests/native/test_view_extent_bridge.py` 验证两布局、两存储类型、scalar/singleton/嵌套范围、
越界/超大整数/非法类型、高 rank、物理旧字段/strided 源、全 pickle protocol、独立所有权、
叶身份、禁止旧内核调用、失败/扩展状态拒绝、GC 环及并发读取。
导入后的只读 view 另覆盖 copy/deepcopy 和全部 pickle protocol 0–5，验证复制源的独立
所有权、范围、内容及共享源语义；该证据关闭 DTO/copy/pickle 门槛，不关闭公共
view/source 权威、自动旧 pickle 或完整性能/发行验收。
真实 solver 合同用带 padding 的 Fraction 旧 offset view 导入有效 `(2,3)` 区域，显式通过
Rust Rational/Float64 检查后注册；padding 和随后旧缓冲的写入不能进入模型。
发行 smoke 同时验证两种布局的剩余区域、nested offset 与显式复制政策。

共享 ndarray、公共默认入口/错误/scalar/泛型与旧自动恢复、mapped callback、数学消费者、
领域闭环及完整性能/资源预算仍未完成。不能凭本桥接删除公共 view 或其旧源内核。
