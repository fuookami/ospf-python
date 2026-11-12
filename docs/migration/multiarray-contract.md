# 多维数组边界合同 / Multiarray Boundary Contract

## 范围 / Scope

本合同覆盖私有 `_binding.multiarray` 中的形状、精确/通用/可变数组及矩形视图，依赖固定 revision
`119854756a0aeb66d2998055f96fa7175c7bfb37` 的 `ospf-rust-multiarray`。
不读取相邻 Rust 工作区，不切换或删除现有公开 `ospf_python.multiarray` API。

现有公开 Shape1–4/DynShape 可作为两类数组的 `create/reshape` 输入，
边界创建独立、受检的 Rust 形状快照；不是在数组中执行旧形状算法。
自定义类型/子类需通过 `Shape.from_shape(source, standard_layout=True)` 显式确认标准布局。
公开形状自身的无界尺寸、dataclass、pickle 与错误合同审查见 `public-shape-contract.md`。

This contract covers the private shape and immutable exact-array bridge, not a completed
replacement of the public generic/NumPy API. The adjacent Rust worktree is not a dependency.

## 权威状态与所有权 / State and Ownership

- `Shape` 持一个 Rust `DynShape`。维度、存储顺序、惰性步长均只有 Rust 一份。
  Python getter 返回独立 tuple，不缓存第二份形状。
- `RationalMultiArray` 持一个 Rust `MultiArray<BigRational, DynShape>`。
  构造从既有 `RationalArray` 克隆 Rust 精确值，不经 float、字符串或逐项 Python 对象。
- 构造、`at`、`shape`、`flatten`、布局转换和 `reshape` 均为独立所有权，
  不是 borrowed view；删除源批次、源形状或源数组不影响结果。
- 精确数组不保存 `PyObject` 元素，不引入 Python GC 环、跨语言可变别名、`unsafe Send`
  或 NumPy 双缓冲。耗时原生操作释放 GIL，不可变句柄允许并发读。

Rust is the sole container authority. Exact arrays own detached numeric values. Python-element
arrays instead retain identical element objects under the GC contract below; neither implies
mutable/view or zero-copy NumPy storage.

## Python 元素与 GC / Python Elements and GC

`MultiArray[T]` 持有一个上游 `MultiArray<Py<PyAny>, DynShape>`，不保存 Python list 或
NumPy 容器镜像。这里只承诺容器不可变，**不承诺元素不可变或深拷贝**。

- `create` 只接收内置 list，原子复制元素强引用；源列表后续清空/替换不影响存储。
  不隐式执行任意 iterable/list 子类回调，不接收 ndarray 以免伪装成共享缓冲。
- `at` 返回原元素，`None` 也是 `Ok(None)`，不作为失败哨兵。不调用元素比较、数值转换或复制协议。
- `flatten` 是独立 Python list，但其中每一项保持身份；布局转换/重塑拥有独立 Rust 存储，
  保留相同元素引用。元素自身改变会由所有持有者看到，不维护两份可变元素状态。
- 坐标遍历和重排委托固定上游 iterator/builder；PyO3 `Py` 不要求 Rust `Clone`，
  在持有 GIL 时 `clone_ref` 复制引用，再交给 Rust builder。重塑依旧严格同数目/同顺序。
- 原生类启用 GC：`__traverse__` 无分配地遍历每个实际存储槽，重复引用逐次访问。
  不穿透外部 ndarray 所有者，不手工猜测外部引用，不在 traverse 中 attach/call Python。
- frozen 原生对象使用 `Mutex<Option<...>>`；锁内仅借用/增加引用，不调用 Python 或释放 GIL。
  `__clear__` 先 take 发布已清理状态并解锁，然后才 drop 元素，避免 `__del__` 重入死锁。
  已清理对象的有效读取/转换返回 `FAILED_PRECONDITION`；形状元数据仍安全可读。clear 幂等。
- 正常 GC finalizer 可以重入和复活仍未清理的数组；复活后的引用仍保持身份，最终释放后可回收。
  Rust 单测直接触发 clear，在最后一个元素析构中重入 at，验证看到结构化失败而非锁死。

The native storage owns real Python GC edges, including duplicates. Container snapshots are
independent but elements are shared by identity. No Python callbacks or interpreter detachment
occur under the storage mutex; clearing releases it before decref/finalizer execution.
Tests cover reachable cycles, duplicate edges, resurrection, concurrent reads and bounded subprocess
finalizer reentry. This does not certify free-threaded CPython or arbitrary contained model handles.

## 可变存储与事务 / Mutable Storage and Transactions

`MutableMultiArray[T]` 使用与不可变容器相同的 Rust/GC 存储底座，但为独立原生类型，
不向不可变数组暴露修改方法。构造输入 list 是容器快照，不回传写入。

- `set(indices=..., value=...)` 和 `set_many(updates)` 只接受严格完整非负坐标。
  批次在第一次写入前完成全部校验；重复坐标明确 `ILLEGAL_ARGUMENT`，不采用隐式最后项覆盖。
- Rust 在同一 mutex 内通过上游 `IndexMut` 替换所有槽位，随后解锁才 drop 所有旧元素。
  不在锁内 decref、调用 Python 或释放 GIL；没有两份可变状态的同步问题。
- 失败不发布本批写入。用户对象析构的任意副作用不纳入回滚承诺：成功替换后，析构可观察
  **整批新状态**，也可发起另一次写入，因此函数返回时可能已存在后续重入事务。
- `flatten` / `to_immutable` 在同一锁作用域内复制引用，不能看到半批写入。
  `to_immutable` 拥有独立 Rust 容器；后续替换源槽位不改变快照，元素自身的可变性仍共享。
- GC 与 clear 复用真实逐槽遍历；clear 后有效读取和写入均返回 `FAILED_PRECONDITION`，
  释放旧元素时析构重入不会死锁。没有用 `unsafe Send` 或 GIL detach 规避生命周期。

Mutation has one Rust authority. A batch is validated before publication, publishes all slots under
one mutex and releases replaced references only after unlocking. Finalizers may observe the entire
published batch and begin later transactions; their external side effects are not rolled back.

## 矩形视图与 offset / Rectangular Views and Offsets

`MultiArrayView[T]` 的 Python 门面持有最终源门面及一个不可变 Rust 区域描述；
`MutableMultiArrayView[T]` 额外提供写入源的 set/set_many。没有第二份元素数组。

- `source.view(offsets=..., shape=...)` 显式指定每轴非负起点及正轴区域大小，
  必须保持源 rank 与存储顺序；标量 `offsets=(), shape.dims=()` 合法，singleton 轴不消失。
  在构造上游范围前检查 `extent <= source_dim` 和 `offset <= source_dim - extent`，避免溢出。
- 坐标先按区域形状受检，再由 Rust 投影到源；线性索引/步长仍由固定上游 Shape 计算。
  flatten/materialize 使用临时上游 `MultiArrayView::new_by_dummy` 和 `iter_with_order`，
  保留访问顺序及 offset。不会直接使用上游视图的单索引特殊语义代替多维坐标。
- 区域描述只有 Rust 元数据，不含 PyObject，也不保存跨调用的借用/自引用指针。
  每次访问在锁内建立临时 Rust view；门面的 `_source` 是普通、GC 可见的强引用。
  源变量销毁后视图继续有效；payload -> view -> source -> native -> payload 环可以回收。
- 子视图在 Rust 中组合偏移，仍持有最终源，不物化中间缓冲；可变写入对所有重叠视图立即可见。
- `materialize` 正确应用区域 offset，并返回独立不可变容器。旧 source=(2,3)、offset=(1,0)
  的物化忽略偏移缺陷不被复制；新接口要求合法区域如 shape=(1,3)，不继续暴露越界尾部。
- 原生区域描述按源形状/存储顺序校验，不是模型身份句柄；兼容形状可重用该描述。
  Python 视图的绑定源由 frozen 门面保持。尚不承诺步进/负步进 slice、转置或惰性 Python map。

Views retain their source through a normal Python GC edge. The Rust descriptor contains only
checked metadata, and borrowed upstream views exist only within a locked native call. Offset-aware
materialization is detached; mutable views write directly through to the original Rust storage.

## 显式 NumPy 快照 / Explicit NumPy Snapshots

两类通用数组均提供 `from_numpy(values=..., copy=True, storage_order=...)`：

- `copy` 必须显式传入；`False` 返回带边界来源的 `NOT_SUPPORTED`，绝不静默复制后冒称共享。
- 只接收精确内置 ndarray，不调用 `__array__` 或 ndarray 子类回调；memmap/子类需以后单独审查。
- 支持 bool、整数/无符号整数、浮点、复数、Unicode/bytes、datetime/timedelta 及 object dtype。
  标量读取保留 NumPy scalar 类型，object 项保留对象身份（包括 None），不转 float/Fraction。
  structured/void（包括记录中的 subarray 字段）的所有权与零长轴仍需独立审查，当前明确 Failed，
  不暗中降级；NumPy 已展开为普通多维数值数组的子数组按其实际 shape/dtype 处理。
- 按行坐标遍历取得元素后交给 Rust builder；C/F/转置/strided/负步长/广播/只读输入均为容器快照。
  不保留源 ndarray 缓冲；外部槽位写入不改变新数组，Rust 写入也不修改源。
  只读源创建的新可变容器仍可写，因为不是 borrowed view。
- 这不是对外部并发 NumPy/C 写入的全局原子快照承诺；调用方须同步外部写者。
  object 中任意嵌套的第三方不透明/非 GC 容器不会被递归修复；本存储只报告自己真实拥有的引用。

NumPy sharing remains unsupported rather than silently emulated. Snapshot ingestion preserves
reviewed NumPy scalar types and object identity, never retains an external data buffer and never
borrows a mutable ndarray while detached from the interpreter. Synchronizing external writers is
the caller's responsibility; this is not the public legacy constructor cutover.

## 形状与错误 / Shapes and Errors

- `dims` 为内置整数 tuple，拒绝 bool/float 和自定义 tuple 子类迭代回调，轴长必须大于零。
  坐标/偏移同样只接收内置 tuple，避免在校验阶段隐式执行用户迭代器。`()` 表示一个标量，size=1。
  零长轴尚未承诺；空一维 `RationalArray` 仍可用，但不能伪装成正轴多维数组。
- 所有轴长及乘积须能由原生机器整数表示，乘积不超过 `sys.maxsize`。
  在调用上游未检查乘法前防止溢出，不分配与 shape.size 相当的形状内存。
- `index_of` 必须给出完整非负坐标；不截断、不广播、不采用 Python 负索引。
  类型/维数错误为 `ILLEGAL_ARGUMENT`，越界为 `OUT_OF_RANGE`。
- Rust `vector_of` 不检查线性范围，绑定先检查 `0 <= index < size`，再委托逆映射。
  空 tuple 标量只有 offset=0 合法。
- `indices_of` 在一次 FFI 中转换批次；任意后续坐标失败，整体 Failed，不发布部分索引。
- 上游 `IndexCalculationError` 按 variant 映射，保留 source、原始 Rust code 和 INPUT 类别，
  不按英文消息猜测，不把 Rust 数值码直接当作 Python ErrorCode。
- 所有业务失败沿用现有三参数 sealed `Result`；不创建平行的结果类型或业务异常 API。

All potentially failing facade methods use the existing Result identity. Boundary checks
prevent upstream panic/unchecked behavior; they do not reimplement the array algorithms.

## 布局与重塑 / Layout and Reshape

输入 `RationalArray` 是线性精确批次，`access_order` 表示输入元素的**坐标遍历顺序**，
与 `shape.storage_order` 的**内部物理布局**分开。两者明确传入 Rust builder。
例如行遍历 `[0,1,2,3,4,5]`、shape=(2,3)、列存储时，内部序列为 `[0,3,1,4,2,5]`，
而坐标 (1,2) 仍为 5。

- `flatten(access_order=...)` 委托 Rust 遍历，返回该访问顺序的独立 `RationalArray`。
  因此可直接复用精确批量 sum/dot，不通过 NumPy float64。
- `to_storage_order` 委托 Rust 重排，保持所有坐标处的值不变。
- 构造前检查批次长度等于 size，避免上游 builder 的 assert。
- `reshape` 只接受**同元素数、同存储顺序**形状，保留存储线性序列。
  Rust 的通用 reshape 可截断或填充，但此处不暴露隐式数据丢失；布局改变必须显式调用转换。
- 所有操作不修改源。精确计算继续受 RG-003 性能门禁约束，不声称数组形状绑定已解决它。

Access order and storage layout are independent. Reshape preserves the storage sequence,
never pads/truncates, and never silently changes layout.

## 公共替换前尚待处理 / Public Cutover Prerequisites

| 现有合同 | 审查结果 / Remaining work |
| --- | --- |
| Shape1–4 / DynShape dataclass | 保留构造参数、字段、模式匹配、继承、copy/pickle、hash/repr；当前未切换 |
| 旧 `flat_index` | `zip(strict=False)` 会静默接受错误维数；不能把此缺陷当作新严格入口的行为标准。公开变更需单独兼容决定 |
| NumPy 构造与 `_data` | 旧构造直接共享 ndarray；需决定 copy/borrow、dtype、strided/object 数组、写入权限和释放生命周期 |
| MutableMultiArray / views | 私有 Rust 可变存储/矩形视图、反轴转置及 map/flat_map 已具备合同；公开签名、完整 slice/映射视图及兼容切换仍待验收 |
| transpose / materialize / flat_map | 私有反轴转置、offset 物化及显式 shape 映射有合同；旧签名/布局和 RG-004 任意轴映射问题须分别审查，不盲目复刻或静默修复 |
| 通用 Python 元素、领域变量 | 私有引用存储/GC 已有合同；公开适配、Python callback、跨模型句柄和值域支持矩阵仍待验收，不能统一降成 Rational 或 Float64 |
| BlockMultiArray / DataFrame / indices / einsum | 尚无本次验收；必须分别对齐再删除旧实现 |
| 性能、序列化、发行 | 需代表性批量预算、公开 wire/pickle 决策和完整已安装发行验收 |

补充审查已实际复现，而非仅代码猜测：旧构造对 strided ndarray 保持共享，
外部修改会改变所谓不可变数组的读取，Mutable 写入会回传外部 base；reshape 则独立复制。
NumPy object 元素保持 Python 对象身份，但 ndarray -> payload -> array 环未被 GC 回收。
另外，source=(2,3)、offset=(1,0) 的视图 get(0,0)=3，materialize 后 get(0,0)=0。
后两项是生命周期/语义缺陷，不应锁定为兼容正确行为。

通用原生元素数组必须有可验证的 GC 遍历/清理，不能持一个未被 GC 正确感知的 NumPy object
所有者并声称已解决循环，也不能把两份可变缓冲同步当作所有权方案。
共享 ndarray 的兼容处置、只读输入错误与公开 get/set 的 Result 合同须一并审查。

可执行合同还包括 `tests/native/test_array_views.py` 的可变事务/矩形视图/NumPy 快照、
`tests/native/test_object_multiarray.py` 的通用引用存储/GC，以及
`tests/native/test_multiarray.py`：NumPy 独立精确对象 oracle、标量/多维、
行列存储 × 行列访问、严格批量索引、溢出、无部分输出、生命周期和并发读。
这些测试证明本切片，不证明整个公共数组迁移完成。

`tests/native/test_solver_boundary.py` 的精确矩阵组合合同把两种存储布局接入真实后端：
系数按坐标读取并显式通过 `Rational.to_float()` 精度检查后注册到 Float64 模型，
SCIP/Gurobi10 解出相同最优目标和值，且源精确矩阵/成本未变。
这验证可组合边界，不意味着所有精确数值可由 Float64 solver 无损接受，也不替代泛型领域闭环。

其中通用可变数组组合从 object ndarray 导入 Fraction，视图批量修改带 padding 的非对称
矩阵 RHS 后按 offset 物化；再次修改源不会改变用于注册的快照。系数/成本仍经显式受检转换，
SCIP/Gurobi10 两种布局均验证相同最优解，且外部 ndarray 未被 Rust 写入修改。

## 转置与映射回调 / Transpose and Mapping Callbacks

以下仅适用于私有通用 `MultiArray`、`MutableMultiArray` 及两种矩形 view，
输出始终是独立的不可变 `MultiArray`，不切换公共旧入口。

- `transpose()` 反转全部轴并翻转 storage order；标量仍为标量。
  沿原物理顺序复制引用，委托固定 Rust Shape/builder，无 Python 坐标重排。
  对象 identity 保留，输出容器与 mutable source 独立；连续转置两次恢复原布局/坐标。
  不支持任意轴参数或共享转置视图；上游 mapped view 的 RG-004 单独保留。
- `map(callback, *, access_order=...)` 保持输入 shape、storage order 和逐坐标对应。
  Rust 以指定访问顺序取得完整槽位快照，解锁后调用 Python adapter，再通过上游 builder
  一次发布结果。它是 Python 回调桥接，并非调用上游并不存在的通用 map 算法。
- `flat_map(callback, *, shape=..., access_order=...)` 要求显式有效输出形状。
  Python adapter 仅将返回 iterable 转为传输 list，Rust 拼接并按同一 access order
  交给 builder；目标 storage order 独立。超长立即停止，不足在最终验收失败，均不发布部分数组。
  iterable 必须有限；不承诺对无限 generator 的中断/限额控制。
- 普通值/`Ok(value)` 为成功，`None`/`Ok(None)`/`Success()` 在 map 中表示 None。
  仅解包一层，`Ok(Result(...))` 可将 Result 当作元素保存。
  `Failed`/`Fatal`/`Warn` 停止调用并返回 CALLBACK Failed，不默默吞掉警告或其 payload；
  `FailureContext.callback_result` 保留原 Result identity，`callback_index` 为零基访问序号。
- 外部 callable/iterable 的普通 Exception 转 CALLBACK Failed，保留原始异常和 traceback，
  不执行异常 `__str__`；KeyboardInterrupt/SystemExit 等 BaseException 原样传播。
  这些协议异常不改写为业务失败。失败输出的临时引用在锁外释放。
- callback 不被原生对象持久保存；用户显式保留失败 Result 时也会保留其异常 traceback，
  应按普通 Python 错误上下文管理其生命周期。相关 Python/Rust 引用环必须可被 GC 回收。
- 回调可读取、再次映射或修改源；外层输入槽位来自调用开始的完整快照。
  不 deepcopy 元素，不回滚用户回调的外部副作用，元素自身的可变状态仍共享。
  槽位批量写入与快照互斥，但锁内不调用 Python、不释放 GIL。

`tests/native/test_array_operations.py` 验证布局/访问顺序、scalar/多维、对象身份、
回调 Result/异常、失败停止与清理、析构/GC、重入和并发槽位快照。
真实 solver 组合把转置后 Fraction 矩阵通过返回 Result 的受检转换映射到 Float64，
再 flat_map 并注册 LP；不绕过数值精度检查，也不据此声称精确 solver 泛型闭环完成。

These are private snapshot operations, not a public array cutover. Callback side effects
are not rolled back; native output publication is all-or-nothing. Arbitrary mapped-view
permutations remain gated by RG-004 in the pinned upstream.

公开数组/惰性映射的有效行为基线、已复现缺陷和私有 `MappedMultiArrayView` 的 live-read /
snapshot-materialize 合同见 `public-array-contract.md`。它保活源与回调但不缓存结果，
不等同于本节 eager map 或 RG-004 的轴映射。

## 归约与 Python 容器协议 / Fold and Python Container Protocols

私有通用 `MultiArray`、`MutableMultiArray` 和两种矩形 view 提供以下受检操作。
这些私有快照操作不是公共 live 接口的直接替代。公共 reduce 与 eager map/flat_map
已独立升级为 Result，默认迭代也已接通共享原生协议，见对应 public-*-cutover.md；
旧 get/to_list 与共享 ndarray 存储合同仍独立保留。

- `reduce(callback, *, access_order=ROW_MAJOR)` 在一次 FFI 中通过固定上游 iterator
  取得完整槽位快照，解锁后在 Rust 编排左结合二元用户操作。Python adapter 仅把 Rust
  给出的内置 pair 转为 `callback(left, right)`，不在 Python 中遍历数组。
  这是 Python 用户扩展点的归约桥接，不声称固定上游提供通用 Python callback reduce，
  也不取代 `RationalArray.sum/dot` 等纯 Rust 数值路径。
- 第一个元素是初始累加值；N 个元素执行 N-1 次回调，没有隐式零值或类型转换。
  当前受检稠密 shape 的元素数至少为 1；空输入不在本合同中。
  scalar/singleton 原样返回首元素且不执行回调，但入口仍预先验证 callable 和 access order。
  首元素若是 Result/None，仍是普通数据，不因其类型自动解包或误判失败。
- 每次回调的 plain/Ok/Success、Failed/Fatal/Warn、异常/进程控制规则与 map 相同。
  `callback_index=0` 表示第一次二元调用（组合第 0/1 个访问元素），不是第一个输入元素。
  失败立即停止，不发布暂存累加值；保留原 Result/异常身份，不吞 Warning。
  若失败的 traceback 持有其累加参数，按普通 Python 异常上下文规则保活；释放后须可回收。
  所有回调及暂存累加值的析构都在源锁外，允许重入读取/写入/再次归约。
- `to_list()` 委托上游行访问取得快照，Rust 仅把此序列包装成嵌套内置 list，
  不在 Python 复制坐标引擎。任意布局都保持逻辑坐标，正确应用 view offset。
  标量返回原元素（包括 None/list），其余 rank 返回新容器结构；元素身份和 NumPy scalar
  类型不变，不调用叶元素的 item/iter/len，不 deepcopy，不执行 dtype 推断。
  容器构建是迭代式的，不依赖 Python/Rust 递归层数；结构可独立修改，不回写源槽位。
- `iter_snapshot(*, access_order=ROW_MAJOR)` 用既有受检 flatten 一次取得独立 list DTO，
  然后返回标准 list iterator。所有可能的原生读取失败在迭代器发布前以 Result 返回，
  不在每次 next 做 FFI；耗尽仍按标准 StopIteration 协议。
  这是显式 O(N) 引用快照，不是 live iterator、零拷贝或共享缓冲承诺。
  源后续槽位写入不影响快照，但可变叶元素仍共享；标准迭代器保活快照到耗尽/释放，
  iterator -> list -> payload -> iterator 环应可被 Python GC 回收。

`tests/native/test_array_fold.py` 覆盖行列布局/访问、scalar/非对称/深 rank、offset views、
非结合操作、单层 Result 转义、None 累加、原失败身份和调用序号、暂存析构重入、
traceback/iterator GC、NumPy 类型保留和并发原子槽位快照。
真实 solver 组合使用通用数组保存 Rust Rational，reduce 回调调用其 Rust add，
得到精确成本缩放因子；通过 iter_snapshot 和 view.to_list 抽取并显式受检转换后注册 LP。
这只验证可组合边界，不证明所有数值域/领域/性能预算完成。

All three operations publish complete snapshots/results only. They do not silently
change the legacy public interfaces, coerce leaf types, or roll back callback side effects.

## 填充工厂 / Filled Storage Factories

私有 `MultiArray.full(*, shape, value)` 与 `MutableMultiArray.full(*, shape, value)`
在 Rust 中为每个槽位建立同一 Python 对象的强引用，随后把唯一 Vec 按目标存储顺序
交给固定上游 builder 直接接管。Python 不构造重复 list，也不保存权威元素镜像。
这是强引用所有权传输，不实现新的坐标、广播或数值内核。

- `shape` 接受已有 Rust Shape 或内置公开形状的受检快照，布局与维度保持不变；
  scalar size=1。非法形状在创建元素引用前拒绝。
- `value` 是不透明叶对象，包括 None、Result、list/tuple、NumPy scalar 和用户对象。
  不调用 array/item/iter/len/copy 等协议，不推断 dtype，不广播，不 deepcopy。
  所有槽位共享叶对象的可变状态，但槽位本身独立；两个工厂调用产生独立容器。
- 在分配前检查 `size * sizeof(PyObject reference)` 不超过原生 isize 字节容量；
  超限返回 OVERFLOW。Vec 使用 `try_reserve_exact`，分配失败返回结构化
  APPLICATION_ERROR / RESOURCE，不发布部分容器或持久保留输入引用。
  此防护不承诺任意大请求可成功，或防护 OS 在实际触页时杀进程等外部资源行为。
- full 按已有 create 的 classmethod 规则构造 facade 子类。zeros/ones 为静态便捷工厂，
  分别以一个内置 float 0.0/1.0 调用基础类 full，返回基础数组类而非隐式特化子类。
  自定义数值域应显式 full(value=domain_zero)，不推断其零值/单位。
- 重复叶必须按实际槽位数被 GC 遍历；容器与叶构成的引用环可以回收。
  可变数组替换最后一个叶引用时仍遵守整批发布、解锁后析构的既有合同。

`tests/native/test_array_factories.py` 覆盖两布局、scalar/多维、精确引用计数、
不可调用叶协议、None/Result/sequence/NumPy scalar、独立槽位/共享叶、容量溢出、
子类、重复边 GC、并发释放和超时析构重入；真实 solver 合同以 full 建立精确 Rational
padding 矩阵与成本，再批量更新、冻结、归约并接入 SCIP/Gurobi10。

These private factories are not drop-in replacements for legacy NumPy broadcasting
or dtype inference. Public constructor/from_list sharing and serialization remain separate gates.

私有 `from_list` 的显式嵌套/不透明叶/逻辑布局与 dtype/广播边界现见
`nested-array-contract.md`。它由原生迭代式解析直接交固定 Rust builder，不调用 NumPy；
公共任意 Sequence 与旧物理展平的兼容适配尚未切换。

## 引用快照与对象图 / Reference Snapshots and Object Graphs

通用/可变数组的受检 to_snapshot/from_snapshot，以及 Shape/数组/矩形与惰性 view 的
copy/deepcopy/pickle 合同见 `array-state-contract.md`。原生两阶段恢复保留 memo、重复叶和环，
Python 仅处理标准对象状态与用户扩展协议，不重写坐标或数学内核。DTO 不等于 JSON 或对象图
重定位；私有格式也不等于旧公开 `_shape/_data` payload 已迁移。
