# 旧数组字段桥接 / Legacy Array Field Bridge

## 范围 / Scope

私有 `MultiArray.from_legacy_state` 和 `MutableMultiArray.from_legacy_state` 将已经读取的
旧 `_shape/_data` 字段显式复制到 Rust 引用存储。它们不加载 pickle 字节、不替换公共类，
也不是公共 `__setstate__`。旧 pickle 目前仍恢复为旧公共类，然后调用方可以选择显式导入。
只读取可信 pickle；字段校验不是反序列化安全沙箱。

These private factories copy already-decoded legacy fields into Rust reference storage.
They do not load pickle bytes, replace public classes or implement public state restoration.

```python
import numpy as np

from ospf_python._binding.multiarray import MultiArray
from ospf_python.multiarray.shape import Shape2, StorageOrder

state = {
    "_shape": Shape2(2, 3, StorageOrder.COLUMN_MAJOR),
    "_data": np.arange(6, dtype=np.int16),
}
result = MultiArray.from_legacy_state(payload=state, copy=True)
assert result.unwrap().at((0, 1)).unwrap() == 2
```

## 输入与所有权 / Input and Ownership

- `payload` 必须是仅含 `_shape`、`_data` 的内置 dict；缺失/未知字段、dict 子类直接拒绝。
  子类附加字段不能静默丢弃；调用方须单独制定它们的迁移方式。
- `_shape` 由现有 `Shape.from_shape` 受检快照；内置公开形状直接支持，其他形状须显式
  `standard_layout=True`。不调用旧 `flat_index`、strides 或旧数组 get。
- `_data` 必须是一维内置 ndarray，数量严格匹配 shape.size。即使元素总数相等，也不自动
  reshape 多维输入，因为旧字段合同是物理序列。scalar 形状 `()` 仍需要一个元素的一维数组。
- 一维序列按目标 shape 的**物理存储顺序**输入固定 Rust builder，不按逻辑 C-order 重解释。
  这是它与 `from_numpy` 的关键区别：后者依据 ndarray 自身的多维坐标读取。
- 通过公共批量访问复用的原生 raw 收集器取得该一维序列，不再调用 `_numpy_snapshot`
  的 ravel/list 或重复创建一维形状；见 `public-array-access.md`。raw 模式不执行 scalar.item，
  仍只发布完整成功结果；外部协议失败以保留原异常的 Result 返回。
- `copy` 必须显式传入 bool。True 创建独立槽位，False 返回 NOT_SUPPORTED；不根据只读标记、
  连续性或引用计数暗中改成复制。标准 dtype 范围沿用 `from_numpy`，structured/void 拒绝。
- 支持正/负步长、广播 stride=0 和只读输入；保留逐项 NumPy scalar 类型、object 叶的原始身份，
  不调用任意叶的 item/iter/array/序列化协议，不将 Fraction/领域对象统一为 float。
- 返回数组不保留输入 ndarray 或 dict；但叶若指回旧 ndarray/数组，仍保留该回边。
  导入不自动 deepcopy 或重定位对象图，也不承诺解决原有 NumPy object 环。
- 不保存 ndarray dtype 作为新容器的约束。可变新数组可接受任何 Python 叶，后续赋值不会进行
  旧 dtype 的截断/溢出/广播，不会写回旧缓冲。dtype 与 scalar 类型不是同一个合同。
- 外部 ndarray 写线程与 shape 属性变更由调用方同步；本入口不提供跨 NumPy/自定义协议的事务。

The input is a flat physical sequence. Layout conversion and publication remain in pinned Rust;
NumPy is used only to extract a boundary snapshot, never as the new mathematical kernel.
This import preserves scalar types and object identity, not persistent dtype casting or buffer aliases.

## 共享存储仍是切换门槛 / Shared Storage Remains a Cutover Gate

旧矩形 view 的 `_source/_offsets` 现有独立显式 `MultiArrayView.from_legacy_state(copy=True)`，
详见 `view-extent-contract.md`。它复制整个内置公开源后由 Rust 推导 offset 后的有效范围，
不调用旧 get/materialize；不自动恢复公共 pickle、共享缓冲或 source alias 图。

| 路径 / Path | 当前政策 / Current policy |
| --- | --- |
| 公共 `MultiArray(shape, data)` / 可变构造 | 仍是原实现，直接共享输入 ndarray，未改为快照 |
| 私有 `from_numpy(copy=True)` | 显式按 ndarray 坐标取得独立引用快照 |
| 私有 `from_legacy_state(copy=True)` | 显式按旧物理序列取得独立引用快照 |
| 上述两个私有入口的 `copy=False` | NOT_SUPPORTED，无隐式 fallback |
| 公共旧字段 pickle 自动恢复为原生类 | 未接通，不由本导入入口冒充完成 |

共享模式若继续承诺，必须独立实现并验收，而不是给 Rust-owned Vec 再挂一个 NumPy 镜像：

1. 外部输入保留唯一权威存储，native shape 负责受检坐标。读取、写回、外部修改可见性与
   resize/shape/dtype/writeable 变化后的失效政策都必须明确。
2. 区分标量数值缓冲和 object 缓冲。只保活 ndarray 并不足以让 ndarray -> payload -> facade
   的非 GC 跟踪边可见；不能声称现有 Rust 逐槽 GC 自动修复共享 object 环。
3. 不能缓存 object 叶镜像再把它当作共享数据；外部替换会使镜像及 GC 图失真。
   不能在 `__traverse__` 中调用任意 Python/NumPy API 来临时补齐引用。
4. 不使用 unchecked raw pointer、unsafe Send 或跨 GIL 借用来绕过所有权；GIL 本身不构成
   NumPy 外部写线程的通用同步证明。性能/线程/GC/只读与非法 metadata 均须有测试。
5. 若决定改变公共共享语义，须作为明确兼容变更提供说明、调用方迁移及测试，不能把私有
   copy=True 的通过记录成共享行为已替换。当前没有作出退役共享 API 的决定。

## 直接消费者审查 / Direct Consumer Review

| 文件 / File | 实际依赖 / Actual dependency | 切换要求 / Required replacement |
| --- | --- | --- |
| `math/multiarray/fast_sum.py` | `_data.reshape(dims)` + np.sum；全量结果转 float | 原生轴归约/数值域合同，列布局与 scalar 结果验证 |
| `math/multiarray/multi_array_extensions.py` | `_data.reshape(dims)` + np.dot/matmul/逐元素计算 | Rust dot/matmul/广播与 dtype/精确域政策，禁止门面换名后继续 NumPy 计算 |
| `math/multiarray/einsum/einsum.py` | `_as_np` 读取 `_data`，np.einsum；scalar 转 float | 原生 contraction 与 parser/错误/轴验证合同 |
| `math/multiarray/einsum/operations.py` | 同样读取 `_data`，np.trace/diagonal/tensordot | 对角/收缩 Rust 路径，布局及结果数值域验收 |
| `multiarray/multi_array_view.py` | materialize 直接复制 source._data；mapped 通过 get 构建 ndarray | 区域范围/offset/惰性 callback 公共适配，不复刻忽略 offset 缺陷 |
| `multiarray/block_multi_array.py` | 不是 `_data` 读取者；用 np.full 构建 dense，旧 flat_index 写槽 | Rust fill + 受检批量写入，保留 sparse 大 shape 边界 |
| `multiarray/vector.py` | 不是 `_data` 读取者；Vector 是 `MultiArray[T, Shape1]` 别名 | 公共泛型/类型身份合同，不能误记为待替换的 NumPy 数学内核 |

上述是源码审查，不是能力切换验收；动态消费者和外部下游未被穷尽。
尤其公共 Vector 使用双泛型参数，当前私有门面使用单元素泛型，不能直接重导出替换。
既有 `_data.reshape(dims)` 隐含 C-order；不能用该实现作为列布局数学正确性的 oracle。

`dot`/`matmul`/`trace` 的固定上游同名函数已实测（2026-10-30）：上游秩域窄于 NumPy
（`matmul` 只收 2D×2D、`dot` 只收等长 1D、`trace` 只收方阵），位模式是朴素左结合累加
（与 NumPy/BLAS 差 1–25 ULP），且完整调用比值在 11 个自然规模里只有 `dot` 16384 达标，
而它只能靠已否决的按尺寸分支使用。所以上表要求的"迁到 Rust"目前被 RG-026 阻塞：
既不批准门面换名后继续用 NumPy，也不批准在绑定层另写等价内核。
证据见 `logs/p3/einsum-parity-audit/`。

Tests in `test_legacy_array_import.py` cover physical layout, decoded public pickle fields
for protocols 0-5, explicit ownership decisions, scalar identities, rejected metadata and
source release. The imported Rust array's own copy/deepcopy/pickle graph is covered in
`test_array_state.py`; DTO/copy/pickle closure does not certify automatic public state
restoration, shared buffers or a public class cutover.
The real-solver contract converts imported Fraction rows through Rust Rational and explicitly
checks Float64 conversion before registering the LP. Public sharing and automatic state restoration
remain separately unverified.
