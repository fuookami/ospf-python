# 公开形状合同 / Public Shape Contract

## 当前边界 / Current Boundary

公开 `ospf_python.multiarray.Shape1–4/DynShape` 仍是原有 Python dataclass，
`Shape` 仍是 runtime-checkable Protocol。类型、字段与构造校验不变，未添加隐藏原生字段或缓存。
`size`（Shape1 的单字段读取除外）、步长和宽松扁平索引的默认计算已接通原生候选，
删除对应 Python 乘积循环、步长循环和生成器点积。完整性能、发行及数组权威切换仍待验收，
本合同不是整个公共 Shape 或数组替换已经完成的声明。

The public dataclass identities and protocol remain unchanged. Arithmetic now delegates
to a native candidate without persistent alternate metadata; this does not certify the
full public shape/array cutover, performance budgets or installed distributions.

## 原生计算与依赖方向 / Native Arithmetic and Dependency Direction

- 正的机器范围内置整数元数据由固定 Rust 形状计算：固定二维至四维 `size` 使用
  `Shape<2/3/4>.len()`；动态 `size` 先完整校验轴与容量，再按最多四个因子组合
  固定上游形状的长度。该分组是绑定适配，不是直接调用完整 `DynShape.len()`，
  不分配随 rank 增长的维度或 offsets。公开稠密步长也按四轴组合固定上游
  `Shape<4>.offsets()`，再将组间偏移量合并；这不是直接调用完整 `DynShape.offsets()`。
  标准布局且坐标有效的稠密索引同样逐组调用固定上游 `Shape<4>.index_of()`，并
  组合组间索引与步长；它不是直接调用完整 `DynShape.index_of()`。原生数组形状
  仍使用 `DynShape`。
- 已在 Windows 低内存独立进程验证 10 万个正轴以及包含零、负数和大整数的动态
  `size`；需要分配大结果时收到 `MemoryError`，而非 Rust 分配失败终止进程。
  另测试 300 万正轴的两种稠密步长布局，tuple 分配失败返回 `MemoryError`；输出
  tuple 和元素使用可返回失败的 Python C API，不使用会在分配失败时 panic 的 PyO3
  快捷构造。两布局的 10 万轴预构造索引和 100 万轴公开索引在指定限额下成功返回
  或收到 `MemoryError`，不再因这些稠密路径中的 rank 级 Rust 向量分配终止进程。
  这些测试不代表任意输入或平台的 OOM 安全。前一候选的完整动态形状在
  100 万轴约增加 16.3 MiB 工作集峰值。固定形状稀疏算术、稀疏步长及其他动态形状
  路径仍可能分配失败并终止进程；这是未关闭的资源缺口，见 `rust-gaps.md` 的 RG-010。
- 公开计算与原生数组 `Shape` 构造共用 `shape_metadata` 的逐轴稠密容量校验，保留
  首个失败的类别与检查顺序。精确内置整数 tuple 直接读取机器整数，不预先逐项
  分配 BigInt；有效标准索引按固定形状分组计算，单位轴布局也须正确辨认。
  仅在机器边界不适用时显式转为任意精度兼容算术，不放宽稠密容量限制。
- 超出稠密机器范围的整数只作为稀疏元数据，不截断、不分配虚构缓冲，不声称固定
  上游已经支持任意精度稠密索引。宽松点积中每项与累计结果均可用 `i128` 精确表达时，
  使用不分配 rank 级向量的受检 Rust 整数运算；输出通过可返回失败的 Python C API
  发布。超界或中间溢出时逐对执行 Rust BigInt 点积，不再收集按 rank 增长的 BigInt
  向量；BigInt 输入转换、运算及结果发布仍有不可恢复分配风险。固定稀疏 `size`
  和步长也使用 BigInt；动态 `size` 的非稠密整数暂时走 CPython 原地乘法
  协议，以使 Python 分配失败可恢复。这是兼容过渡而非 Rust 精确整数内核，不能据此
  验收完整 Rust 切换。
- 旧宽松索引仍返回 int，保留有符号坐标、短坐标和额外坐标截断的兼容点积。它不是
  新受检索引的正确性合同；新 `at`/`set_at` 等 Result 入口继续遵守独立严格合同。
- 任意外部数值和序列保留原乘法/反射乘法、DynShape 的原地乘法、逐轴读取顺序、
  未使用端轴不读取，以及原生成器操作数的保活和耗尽清理。点积仍由 CPython `sum`
  处理补偿浮点求和；内部操作抛出的 StopIteration 转为带原 cause/context 的 RuntimeError，
  其他异常与 BaseException 原样传播，不格式化、不创建第二套业务错误体系。
- 原生计算只持有单次调用参数和临时 Rust 形状；Python dataclass 字段仍是兼容门面的
  元数据输入，不建立可变镜像或持久 size/stride 缓存。完整数组存储权威另有门禁。
- 包门面通过按需自然导出消除基础 shape 反向初始化 array/binding 消费者的循环。
  `__all__`、`dir()`、通配符导出、类型检查和深层模块对象身份保持；只改变加载时机，
  未添加备用 backend。私有 storage/transpose 绑定可以在公共数组之前独立导入。

The native adapter has no additional mutable shape state. Exact dense integer metadata uses
the pinned upstream. Sparse dynamic size temporarily uses CPython's in-place multiplication
protocol for recoverable allocation failures, not a Rust integer kernel. Permissive exact-int
dot products use checked Rust `i128` without rank-sized allocation when all terms and partial
sums fit; unbounded values and intermediate overflow use pairwise Rust BigInt without
rank-sized vectors, but BigInt conversions and operations can still abort on OOM. External Python
numeric protocols remain extension boundaries. Lazy package
exports remove the dependency cycle without renaming public types or changing pickle paths.
Public arithmetic and native array shape construction share a first-failure-preserving
dense capacity guard. Exact built-in integer tuples avoid eager BigInt allocation, and
standard dense indices compose fixed upstream shapes without probing both layouts.
Dense dynamic size, public dense strides and valid standard indices compose fixed upstream
shape results without rank-sized Rust allocations; none is a direct full `DynShape`
operation. The output tuple and its integers use fallible Python C API allocation. Fixed sparse
arithmetic and other dynamic-shape paths can still allocate and abort on OOM; RG-010 remains open.

## 必须保留或明确决策的合同 / Contracts to Preserve or Decide

| 能力 / Capability | 合同 / Contract |
| --- | --- |
| 导入身份 | 包入口与深层 shape 模块的同名类为同一对象 |
| 构造与工厂 | 保留既有位置参数及 storage_order 默认值；Shape3/4.of 的历史位置调用不在无关切片中强制改为 keyword-only |
| dataclass | 字段顺序、asdict/astuple/replace、`__match_args__` 与冻结字段保持；不可把原生句柄变成公开 dataclass 字段 |
| 相等与哈希 | dataclass 以实际类型及字段比较；普通子类与基类即使字段相同也不相等，hash 与字段 tuple 一致 |
| repr 与模式匹配 | 保留自然类名、字段名、StorageOrder 与位置匹配 |
| 继承 | 工厂保留 cls；普通子类额外实例状态和下游 frozen dataclass 字段不能丢失 |
| copy / pickle | 所有解释器 pickle protocol、浅/深复制可恢复类型及行为；旧仅公开字段 protocol-0 payload 必须可读取 |
| 标量 | `DynShape(())` 为 size=1、ndim=0、strides=()，唯一合法坐标为空 tuple |
| 大尺寸 | 当前任意精度 Python 整数尺寸能用于稀疏元数据；不是所有 shape.size 都对应已分配的稠密缓冲 |
| 自定义协议映射 | 自定义 flat_index/strides 可能不是标准行列布局，不能只读取 dims/order 就声称等价 |

## Raw 字段权威与恢复边界 / Raw Field Authority and Restoration

`frozen=True` 限制普通属性赋值，不意味着实例元数据不可变。现有公开形状没有 slots，
`vars(shape)` 返回实际实例字典。保留该字典的调用方可以直接修改维度或 storage_order；
后续 size、strides、flat_index、相等、hash 以及新的受检原生快照均须读取当前字段。
不能根据已通过的构造校验、旧 hash、对象身份或 frozen 标记复用跨调用的维度/步长证明。
对有下游数值协议的字段，普通字段读取也不构成其值在以后调用中稳定的证明。

`object.__setattr__(shape, "__dict__", replacement)` 同样是现有低层行为：新字典成为
当前字段输入，旧字典的别名不再控制该对象。浅复制拥有另一个实例字典，但其初始字段值
仍共享原对象；只修改浅复制的字典不得改变原对象。这里描述恢复/兼容边界，
不建议应用绕过 frozen，不承诺对变更前后的可变对象进行安全哈希容器操作。

进入受检稠密接口时，必须重新校验本次字段。先前取得的原生 Shape 是独立快照，
不能因当前 raw 字段改变而同步更新，也不能反过来把该快照当成原对象的常驻权威。
无效字段须在新受检调用中按 Result 返回失败；恢复有效字段后仍须能重新调用。
公共数组共享同一个 shape 时，其新受检访问须看到该 shape 的当前维度。

仅公开字段的旧状态可通过 `object.__new__(cls)` 加字典填充建立，并在 deepcopy 和
pickle protocols 0–5 下恢复，而不调用公共构造器。直接将门面改为带 PyO3 原生布局的
基类不是无损替换：即使该基类支持 subclass、dict 和 weakref，标准 object 分配器及
旧 `copyreg._reconstructor(cls, object, None)` 仍拒绝这种布局。新增状态恢复钩子
不能单独修复旧 payload 在填充状态前使用旧分配器的失败；须先证明旧入口可用，或取得
明确的兼容政策变更，不得把“新对象可以构造/新 pickle 可读”当作旧状态兼容证据。

shape 与 `vars(shape)` 同时作为恢复图根时，旧 deepcopy/pickle 并不保证恢复后的
`shape.__dict__` 就是那个独立字典根；不能凭空将此身份提升为旧合同。
这不削弱已明确承诺的字段值、字段对象别名、下游状态或数组/缓冲图身份要求。

因此后续验证合并只允许消费**本次调用内**受检、不可变、拥有其整数元数据的 Rust 证明；
外部属性、整数协议和迭代仍按既定顺序实际执行。证明不得持有 Python owner/叶、跨调用
信任 raw 字段或增加可变镜像；全零 offset 也不得为生成一个不会使用的计划重复分配形状。
这条局部设计约束不等于公共状态已由 Rust 接管，不豁免完整数组/Shape 的切换门槛。

Frozen assignment is not an immutability proof. Raw dictionary changes and replacement
remain observable by future calls; shallow copies rebind independently. Dense native
snapshots are independent, freshly validated values, not persistent mirrors. A PyO3
layout base rejects the existing object allocator and legacy object reconstructor, even
when subclassing and instance dictionaries are enabled. Restoring new-format pickles
alone cannot prove compatibility with the old allocator. Restoration does not promise
that a separately rooted instance dictionary becomes the restored shape's actual dict.
Any future validation reuse must be limited to an owned, checked Rust value within one
call, preserving external protocol order and the existing identity-region fast path.
These constraints do not certify complete native state ownership or performance.

`tests/multiarray/test_public_shape_authority.py` 与既有
`test_shape_compatibility.py`、`test_shape_arithmetic.py` 共同维护这些边界。

## 不能机械切换的差异 / Non-Drop-In Differences

### 大尺寸不是单纯错误输入 / Unbounded Metadata Is a Real Capability

`DynShape((2**128, 3))` 及 `BlockMultiArray` 可以只存一个远端坐标而不分配稠密数组。
固定 Rust `DynShape` 使用 usize，当前桥接还限制总 size <= sys.maxsize 以符合 Python 长度协议。
把所有公开形状构造都改成该限制会删除已有稀疏能力，不能在绑定构造中悄然处理。
后续须明确区分任意精度的稀疏坐标/元数据与可寻址稠密 Rust 形状，或取得明确的范围变更决策。

### 索引错误合同 / Index Error Contract

旧 `flat_index(*indices) -> int` 不验证维数或范围，`zip(strict=False)` 会截断坐标。
在 shape=(10,20,30) 上，`flat_index(1)`、`flat_index(0,20,0)` 都为 600，
`flat_index(-1,0,0)` 为 -600；这不是新接口应复制的正确索引语义。

严格 Rust 入口返回现有 Result：错误维数/类型为 ILLEGAL_ARGUMENT，越界为 OUT_OF_RANGE。
不能把返回 int 的公开方法偷偷替换为 Result，不能添加业务异常来掩盖错误处理政策，
也不能在 Rust 失败后回退旧 Python 算法。公开数组及其 get/set/view 调用方要按同一错误合同迁移，
不能只改一个 helper 并声称整项完成。

## 已实现的组合路径 / Implemented Composition Path

公共数组新增 Result 入口 `at` / `set_at` 同样复用固定 Rust 形状坐标检查，保持原 ndarray
共享，且要求自定义类型/子类显式确认标准布局，见 `public-array-access.md`。
这不更改本模块 dataclass 或旧 flat_index/get/set 的签名。原生计算候选仍须独立验收。

```python
from ospf_python._binding.multiarray import RationalMultiArray, Shape
from ospf_python._binding.numeric import RationalArray
from ospf_python.multiarray import Shape2, StorageOrder

public_shape = Shape2(2, 3, StorageOrder.COLUMN_MAJOR)
snapshot = Shape.from_shape(public_shape).unwrap()
values = RationalArray.create([(i, 17) for i in range(6)]).unwrap()
array = RationalMultiArray.create(values=values, shape=public_shape).unwrap()
assert snapshot.strides() == (1, 2)
assert array.at((1, 2)).unwrap().as_integer_ratio() == (5, 17)
```

- 内置公开形状可直接传入原生数组工厂；其 dims/order 经完整机器范围检查后创建独立 Rust 形状。
- 适配不读取旧 size/strides/flat_index，不执行旧索引算法，不改变源类的字段、pickle 或状态。
- 大尺寸只在进入原生稠密边界时返回 Failed，原有稀疏元数据对象仍可正常使用。
- 自定义类型及子类默认拒绝自动映射。调用方需显式
  `Shape.from_shape(source, standard_layout=True)`，确认使用 dims/order 的标准布局，
  **不是**保留任意自定义索引映射。随后把所得原生快照传入数组工厂。
- 自定义属性作为外部代码边界捕获普通异常并转 Result；不吞 KeyboardInterrupt/SystemExit。
  只读取 dims/order 各一次，不调用用户 size/strides/flat_index；自定义源负责提供一致元数据。
- 原生快照不持有源 Python 对象；源修改/销毁不影响已有 Rust 数组，不产生跨语言可变共享。

`tests/native/test_multiarray.py` 验证以上边界，`tests/native/test_solver_boundary.py`
验证公开 Shape2 -> 原生非对称精确系数矩阵 -> 显式 Float64 检查 -> 真实后端最优解。

## 性能与公开切换条件 / Performance and Cutover Conditions

`benchmarks/test_public_shape_hot_path.py` 增加五类公开形状、两布局、三档坐标数的30个
完整流程 oracle：计入构造、size、strides、全部索引和结果发布。旧版本比较必须使用
迁移前冻结的形状类及枚举，不能把已经接通原生计算的公开 Shape 作为假旧基线。
机器整数路径避免预先 BigInt 转换和双布局重建，仍计入临时形状及 FFI 开销；
正确性通过不能代替完整流程、固定 runner 预算或发行验收。

`benchmarks/test_native_shape_hot_path.py` 在小/中/大三档坐标批次、两种存储顺序上分离测量：
公开/原生构造、公开形状快照、步长读取、标量索引、批量索引及包含形状构造的流程。
所有计时结果由 NumPy 独立验证；旧公开路径没有新 Result/边界检查，差异须据实披露。

原生步长/批量路径更快不代表标量调用、构造或领域总耗时全部通过预算。
公开原子切换仍须解决大尺寸能力与非 Result 错误合同，验证自定义映射处置、pickle 迁移、
性能/资源预算及公开数组调用方，再删除对应旧计算；本组合适配不构成删除依据。
