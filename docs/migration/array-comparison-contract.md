# 数组逻辑比较与协议边界 / Logical Comparison and Protocol Boundaries

## 受检比较 / Checked Comparison

私有 MultiArray、MutableMultiArray、MultiArrayView 及其可变子类提供
`equals(other, *, comparator=operator.eq) -> BindingResult[bool]`。
Python 仅分派存储/区域及适配用户比较器；Rust 编排两个上游逻辑快照和短路比较。
这不是公共 `__eq__` 的切换，不调用旧 NumPy 数组或索引算法。

These private methods compare logical coordinates using upstream Rust traversal. They expose
checked failures and user extension points without changing Python equality/hash protocols.

- 两侧必须为私有 Rust 引用存储或矩形视图，可跨 immutable/mutable/view 类型；标量与普通
  正轴 shape 均支持。非数组返回 ILLEGAL_ARGUMENT；惰性 mapped view 返回 NOT_SUPPORTED，
  必须先显式 materialize，不能偷偷执行用户映射函数来决定相等。
- 先验证比较器可调用和双方存储/区域有效，再比较 dims。dims 不同返回 Ok(False)，不调用
  元素比较器；包括同样总元素数但不同 rank/轴长度的情况。pending/cleared 不是“空数组”，
  即使 dims 不同也返回 FAILED_PRECONDITION，不以 False 掩盖失效。
- dims 相同后按逻辑 row-major 顺序比较对应坐标，忽略物理布局差异但不忽略坐标含义。
  首个 False 或失败立即停止，全部 True 才成功；scalar 有一次比较。
- 不因是同一数组、同一句柄、同一叶对象而跳过比较。NaN 默认不等于自身，signed zero
  默认相等；与 NumPy 的 equal_nan 或 Python list 的 identity shortcut 不是同一个合同。
- 默认 operator.eq 调用叶的 Python 相等协议；也可传二元 comparator，例如调用 Rust
  Rational.compare，再 map 成布尔结果。不会统一成 float、对叶做 hash 或读取 repr。
- 比较器可以返回内置 bool、NumPy bool，或单层 Ok 包装的相应值；NumPy bool 在边界转为
  内置 bool。返回 None/数字/数组/任意 truthy 对象/嵌套 Ok 均失败，不隐式调用 __bool__
  或把成功 unit 当 False。若确实需要外部 truth 协议，调用方应显式在 comparator 中适配。
- Failed/Fatal/Warn 立即停止并按现有回调合同保留原 Result 身份；不把 warning 当成功数据。
  普通 Exception 保留原对象/traceback，不格式化异常文本；进程控制 BaseException 传播。
  callback_index 是零基逻辑元素序号，不是参数编号或布尔规范化阶段编号。
- 非布尔返回值由规范化阶段生成 ILLEGAL_ARGUMENT 结果，再以 CALLBACK 失败传回；其
  callback_result 是该规范化失败。业务比较器本身返回的失败仍保留原对象与原领域错误。

默认比较存在精确内置类型优化：两叶为 exact int/float/bool/None/str/complex，或双方均为
exact bytes 时，在解锁后直接调用 CPython rich comparison，省去每叶 Python adapter 调度。
这是原有对象相等协议的执行路径，不实现新的数值算法，也不把任意数值对象降为 float。
不使用带全局 identity shortcut 的 RichCompareBool，确保同一 NaN 对象仍不相等。
bytes 与其他类型的比较仍走 adapter，保留 `-bb` 将 BytesWarning 升为异常时的上下文。
任何内置类型子类、NumPy scalar、其他对象或自定义 comparator 都保留完整回调路径。
原生请求携带完整逻辑 ordinal；即使前面跳过许多内置叶 adapter，后续失败的位置仍是
原始逻辑元素序号，而不是实际 Python 回调次数。

```python
from ospf_python._binding.multiarray import MultiArray, MutableMultiArray
from ospf_python.multiarray.shape import Shape2, StorageOrder

left = MultiArray.from_list(data=[[1, 2], [3, 4]], shape=Shape2(2, 2)).unwrap()
right = MutableMultiArray.from_list(
    data=[[1.0, 2.0], [3.0, 4.0]],
    shape=Shape2(2, 2, StorageOrder.COLUMN_MAJOR),
).unwrap()
assert left.equals(right).unwrap() is True
assert left is not right
```

## 快照、重入与所有权 / Snapshots, Reentry and Ownership

每次比较先取得两侧完整槽位引用快照，再执行任何用户比较器。原生可变批次写入不影响已取出
的槽位，叶对象自身可变状态仍共享，不承诺深对象状态事务或回滚比较器副作用。

同源两侧（包括浅复制共享句柄、源/视图和两个不同 offset 的视图）在**同一锁作用域**内取得
两个上游快照，来自同一槽位版本。使用源 Rust 存储身份判断，而不是 Python 门面身份；
快照取得后显式解锁，任何元素调用及快照验证/清理都在锁外。
区域遍历提取为共同 helper，沿用固定上游的受检矩形视图，不实现第二套坐标引擎。
完整数组在访问顺序等于物理存储顺序时，使用固定上游公开连续存储取得快照，避免每个槽位
重复坐标转换；其余顺序和区域仍使用上游访问迭代器，不手写布局重排。

不同源分别取得完整快照，不同时持有两把锁，不承诺跨源全局事务。即使两源的变化各自原子，
也不能从某次比较结果推导二者在整个时段始终相同。两源/区域均在回调前验证与读取；因此
形状不同时目前也会读取双方快照，这是明确的 O(N+M) 引用/内存成本，不是常数时间比较。

比较器可以读取、写入任一源，或等待另一线程完成写入，不在数组锁内执行，不增加持久
callback/元素缓存。返回的 Failed 若保留 traceback，自然会保活 traceback 引用的数据；
释放错误上下文后相关 Python/Rust 环仍须能回收。不以一次成功等值比较证明长期对象不可变。

## Python 公共协议的剩余决定 / Remaining Public Protocol Decisions

| 协议 / Protocol | 当前与切换要求 / Current state and cutover requirement |
| --- | --- |
| 私有 `__eq__` / `__hash__` | 仍为 identity/identity hash；显式 equals 不改变 dict/set 键语义 |
| 旧公共 immutable 值比较 | 目前按物理序列；切换应按逻辑坐标，不能无说明保留布局错误 |
| 旧公共 mutable 比较 | 仍为 identity；显式值比较与 Python 对象身份不能混为一谈 |
| 公共值 hash | raw-byte hash 已复现等值异 hash/外部写入改 hash；不得复刻。通用可变叶不能保证稳定值 hash，倾向令值相等容器不可哈希，实际切换及兼容说明尚未接通 |
| `__eq__` 的错误桥接 | bool/NotImplemented 的 Python 协议不能直接返回 Result，也不能把 Failed 强制成 False；失效状态、非布尔/Result 叶比较的协议适配须单独验收 |
| repr / 受检描述 | 私有 describe 已提供有界逻辑预览、布局/offset 标签和格式器错误/递归合同，见 array-description-contract.md；旧公共 repr 仍显示物理数据，私有 dataclass repr 仍显示 handle，公共格式/协议适配未切换 |
| 默认迭代 | 私有 iter_live/iter_snapshot 合同不变；公共默认 generator 的逐槽读取已独立委托原生 shared-storage 适配器，scalar 仅转换 np.generic，见 public-iteration-cutover.md；不是完整共享存储接管 |
| view 范围 | 私有显式 offset+shape 已受检；旧公共 offset view 仍宣称全源范围。裁剪有效 extent/拒越界、保留 rank 与 source alias 的公共适配尚未切换，不扩展成未经承诺的任意 slice |

尚未切换的协议项仍是门槛，不把本 equals 的通过记录成 hash/repr 或独立迭代切片的验收。
公开/私有类、ABC、泛型、共享 ndarray、旧 pickle 自动恢复、性能/资源和领域验收仍按总计划
推进。检查比较结果不提供数值精度域或所有数学操作的等价证明。

Tests cover all storage/view/layout pairings, logical-vs-physical differences, strict boolean results,
Result/exception provenance, NaN and signed zero, same-source offsets, reentrant and cross-thread writes,
GC/closure release, exact domain comparators and invalid lifecycles. The real solver contract compares
exact Fraction rows through Rust Rational while mutating the source, then explicitly converts a frozen
snapshot to Float64 for SCIP/Gurobi10. It is not a public protocol or performance cutover certificate.
