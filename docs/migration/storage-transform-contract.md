# 存储重塑与展平候选 / Candidate Storage Reshape and Flatten

`reshape` 和 `flatten` 均为 **specified**，不是退回旧内核。当前源码已
接通原生存储编排并将
`reshape/flatten` 显式升级为现有 `BindingResult`，成功值仍是基本不可变
`MultiArray`。2026-10-30 的 checked 快速路径以固定 Rust `Shape<1>` 规划 exact
数组、exact `Shape2` 和内置正 `int` 的 flatten 计数，复制前统一执行检查；两轮
预注册 ABBA/BAAB 完整调用均为 **96/96、0 failed**，原 `1.15x` 门槛和
count >= 10,000 规则不变。历史旧版对照中 flatten 曾出现 8/12 项失败，失败记录
保留，不再作为当前源码的 pending 性能证据。Linux、Gurobi 11/12、固定 runner、
全领域和长期资源预算仍未认证。

## 原生职责 / Native Responsibility

固定 Rust `DynShape` 校验 ordinary ndarray + exact `DynShape` 重塑的正轴、实际存储
元素数和乘积容量，规划一维物理发布形状。依据实际 ndarray 的 `size` 而非源逻辑
shape，不截断、不填值、不跨布局重排。输出保持目标 Python shape 对象身份；目标的
storage_order 不参与物理重塑，也不额外探测它。

精确 ndarray 路径已删除原 `.reshape(...).flatten().copy()` 链。NumPy 仅提供一次
独立 C-order dtype-aware copy，随后按 Rust 已验证的相同元素数更新独立缓冲的头部。
通过 NumPy C API 的 `PyArray_NewCopy` 和 same-count `PyArray_Resize(refcheck=0)`
发布，不使用 NumPy 2.5 已弃用的 `.shape=`，也不在普通 ndarray 路径反复解析 Python
copy/resize 方法；已有一维副本无需再改头部。
此时缓冲是新建、独占、C-contiguous 的 exact ndarray，不是原共享输入或借用视图。
保持 `owndata=True`、`base is None`、原 dtype、结构化 object 引用和 C-order 值序列。
不对原始数据执行 resize，不会因 metadata 推断而增删 payload。

2026-10-28 源码复核发现：先前普通正整数 flatten 热路径在 Python 中直接构造
形状，原生路径只处理复制，没有执行上游一维形状规划；旧版关于该路径已经使用
`Shape<1>` 的说法不成立。当前 exact 快速路径改由
`flatten_value_result_checked` 在复制前调用固定 Rust `Shape<1>` 计数检查；
非标准 shape、动态计数、稀疏 BigInt 和扩展路径仍走完整 counted 入口。计数
不一致时明确返回 `DATA_LOSS`。超出 Python 可寻址范围的正 BigInt 仅保留
稀疏元数据，不构造虚假等长缓冲，不承诺任意精度上游索引。非内置整数元数据保留
原对象表示；外部整数协议失败进入现有错误上下文。该实现不因接通上游调用而自动
通过固定 runner、Linux 或 Gurobi 11/12 验收。
真实缓冲复制保留原 `_data.copy()` 的 rank、元素数量和 dtype：历史 `shape.size != data.size`
或底层二维 data 仍能存在，不无说明地替用户修复/展平。

普通 ndarray 的复制通过 `numpy = 0.30.0` 的动态 C API 表访问，仍由 NumPy 负责
任意 dtype 的内存、结构化 object 字段和引用计数；不读取裸 payload、不构造 Rust
数值切片。进入 C API 前独立验证实际 NumPy 类型，不能以调用方传入的 type 对象作为
裸指针安全依据。ndarray 子类和自定义存储始终调用原 Python copy hook。唯一修改
header 的内部 helper 只接收刚创建且未发布的独立副本，数量由 Rust 事先验证相同，
不持有任何 Rust payload 借用；C API 的新引用和失败均由 PyO3 正常接管。

The C API adapter removes Python dispatch, not NumPy's dtype authority. Its dynamic ABI,
minimum-runtime compatibility and source-distribution rebuild are covered by the current
wheel/sdist evidence; later artifacts must be revalidated separately.

绑定复用一个私有 `_StorageTransform` 协议配置，只持有 ndarray/shape 类型和现有
成功/失败工厂，不持有数组所有者、shape 实例、计数或载荷缓存。两个自然操作分别使用
低参数数量的入口，直接把 Rust 传输转换为现有 `Ok`/`Failed`，不构造中间 Python
传输 tuple；失败仍复用统一 `invoke` 映射，外部异常仍在 Python 边界原样保留。
配置对象向 GC 暴露全部三个引用边；不持锁调用外部协议，允许同一配置并发重入。

The reusable protocol configuration is not another array authority or a metadata cache.
Only factories are retained across calls, and GC traverses both result factories and the
type tuple. A zero-argument resolver captures the public constructor at the original
Python call-expression evaluation point, not after evaluating its copy argument.

Native code owns structural planning and operation orchestration. NumPy copying remains
the external storage-publication boundary, not a Rust numerical kernel. No dummy/ZST
payload is passed to upstream `reshape/flatten` to manufacture an algorithm cutover;
no full Python-leaf mirror or numeric dtype whitelist is introduced.

## 外部扩展与时序 / Extensions and Timing

- 可变 reshape 先以捕获的 `_shape` 和 `_data.copy()` 构造临时 immutable owner；
  两类 flatten 则不做额外输入预复制。未覆盖构造/操作时成功结果为 immutable base array。
- 临时 owner 构造完成后动态解析并调用它的 `reshape`，不能绕过用户在构造器返回
  类型上提供的重载。默认方法重新进入同一原生规划；覆盖方法应遵守已升级的 Result
  操作合同，其成功或失败的外层 Result 原样传播，不拆包或额外包一层 Ok。覆盖方法的
  普通异常保留原对象，BaseException 仍传播；不以省一次分派为理由跳过扩展。
- ndarray 子类或非 exact `DynShape` 保留完整外部 `reshape(dims).flatten().copy()`
  协议，包括任意 target dims、NumPy `-1` 推断和自定义返回对象。此路径是用户扩展
  协议，不是普通 ndarray 已删除算法的异常 fallback。
- 外部存储路径先解析源 reshape callable，再读取目标 dims；释放 bound method 和临时 shaped
  结果的时机保持在后续 flatten/copy/结果构造之前。原最后 flattened 局部对象仍保活
  至结果构造，不改变 ndarray 子类 copy hooks 的次数。
- flatten 仍以命名参数 `dims=` 调用当前公共 shape 构造器，不绕过自定义
  `__new__` 和 `__init__`；无论 hook 在绑定导入前还是导入后替换，当次调用均
  生效。动态 shape 工厂在其调用完成后及时释放，不能由原生参数引用延迟到存储
  copy 之后。成功 Result 正常调用绑定初始化时捕获的 `Ok` 类，故该类的
  `__new__`/`__init__` 动态替换仍生效；重绑定私有 `storage_transform.Ok`
  名称不会替换已配置的工厂，不承诺该私有模块名称是扩展入口。
- 构造器求值时序按原 Python 表达式保留：flatten 在 flat shape 构造后、缓冲 copy 前
  捕获公共构造器；不可变外部 reshape 在 `reshape(...).flatten()` 完成后、最终 copy
  前捕获；可变预复制则在读取 `_shape` 和执行输入 copy 前捕获临时对象构造器。
  copy hook 中替换模块的 `MultiArray` 不会追溯改变已捕获的 callable；下一次调用
  或后续临时对象的 reshape 仍会看见新的模块绑定。
- 可变预复制的构造调用完成后即释放捕获的 callable，再解析临时对象的 `reshape`；
  callable 的析构副作用因此对后续分派可见。flatten 的局部 flat shape 则保活至
  构造 callable 释放之后，即使自定义构造器未保存 shape。原表达式与原生入口使用
  同一生命周期对照测试，不用 GC 最终回收代替调用边界的确定性释放顺序。
- 构造 CALL 的临时参数不能在 callable 之前析构：flatten 和不可变 reshape 在
  callable 释放后才释放复制结果；可变预复制依次释放 callable、临时 shape 参数、
  临时复制参数，之后才解析临时 owner 的 reshape。flatten 的局部 shape 和不可变
  外部 reshape 的 flattened 局部数据仍按原局部变量生命周期保活。
- 不 `.item()`、转 Float64、解包叶 Result 或隐式换单位；Fraction/Quantity/None/
  opaque object 及结构化 object 字段仍按 dtype 复制并共享叶身份，槽位不共享输入。
- 普通外部 Exception 返回 `APPLICATION_ERROR / EXTERNAL_STORAGE_TRANSFORM`，保留
  原对象与 traceback，不格式化；直接 StopIteration 不作 PEP479 转换，BaseException
  传播。默认 Rust 数量/容量失败是结构化失败，不再人为制造 NumPy ValueError。

所有外部协议均无业务锁，允许线程重入；不保证共享并发写入的事务快照，不回滚已发生
的外部副作用。不建立持久原生 owner/cache；不能由局部资源探针证明任意用户协议长期
无泄漏。当前候选不代表整个数组存储、公共 Shape 或任意 dtype 数值计算已 Rust 化。

Callable destruction follows the original call expression: release the precopy constructor
before looking up the temporary owner's reshape. The flatten local shape remains alive
until after its constructor is released, even when the constructor does not retain it.
Temporary copy arguments are released after the callable, not when a native argument tuple
is destroyed. Precopy releases its temporary shape before its temporary copied data, while
flatten retains its local shape through the call cleanup.

## 验收入口与未完成项 / Gates

`test_transform_compatibility.py` 保存旧 dtype/rank/layout/历史错配及扩展合同，调用已
显式消费外层 Result。`test_public_storage_transform.py` 覆盖 native C-order 发布、
ownership、巨大稀疏元数据、外部失败、重入和容量。`test_storage_transform_hot_path.py`
包含两类/两布局/两方法/三档/四叶域的完整调用与独立物理 oracle。真实单位化 MILP
消费者使用 reshape/flatten 后再转置和 live 物化。

历史候选曾通过 Windows CPython 3.13 的默认/debug 回归、局部资源包络、真实
SCIP/Gurobi10 消费者、wheel 与同一 sdist 的仓库外隔离重建；历史旧版对照中
reshape 性能通过、flatten 未通过。当前 checked 源码的完整调用、资源、求解器
消费者和发行证据已在上方记录。`test_storage_publication_hooks.py` 覆盖两类
数组、shape/Result 的 new/init、绑定导入前后共 16 个独立进程合同。Linux、
Gurobi 11/12、固定 runner、全领域及长期资源预算仍须按实际证据记录，不能因本机
操作合同通过而登记为已认证。详细本地结果与待办只记录在被忽略的 logs 进度文档。

当前扩展已对不可变/可变数组和行/列布局重跑真实消费者：`flatten -> reshape ->
transpose -> live materialization` 后注册精确单位化配置 MILP，SCIP 与 Gurobi10 共
**8 passed / 8 skipped**。2026-10-30 的 checked 快速路径又把 exact
`MultiArray`/`MutableMultiArray`、exact `Shape2` 和内置正 `int` 接到
`flatten_value_result_checked`：复制前统一执行固定 Rust `Shape<1>` 计数检查，
不绕过 `pinned_flatten_length`，同时保留 shape 构造 hook 和 Result 发布时序。
定向合同 **700 passed**，快速路径合同 **576 passed**，96 项独立 oracle
**96 passed**。

以同一源码身份运行两轮预注册 ABBA/BAAB 完整调用，均 **96/96、0 failed**；
受门禁 flatten 最大比率为 `1.1068929443x`/`1.0565404647x`，reshape 为
`1.1142482710x`/`0.9831181489x`，仍按原 `1.15x` 门槛和 count >= 10,000
规则判定。八个独立资源进程全部通过，峰值增量最大 `2,469,888 B`，预热后增长
最大 `8,192 B`。基础与 `scip,gurobi10` wheel、同一 sdist 的仓库外 `--locked`
重建、隔离安装和完整 smoke 均通过。

因此四条合同删除已完成的
`current-source-complete-call-and-resource-revalidation` 与
`current-source-distribution-revalidation`；两个 flatten 也删除已由完整调用证据
覆盖的 `complete-old-baseline-performance`。只保留
`fixed-runner-full-domain-and-long-term-resource` 和
`linux-and-gurobi11-12-validation`。该结论仍是 Windows CPython 3.13 单机操作范围，
不认证固定 runner、Linux 或 Gurobi 11/12。

## 固定 Runner 门禁 / Fixed Runner Gate

`benchmarks/storage_transform_fixed_runner.py` 固化 seed `278177592`、96 组合
矩阵、9 轮 ABBA/BAAB、冻结旧实现、`1.15x` 门槛、两轮独立性能和 600 秒长稳。
长稳使用 8 个真实独立子进程，覆盖 native/legacy、不可变/可变及
`reshape/flatten`，要求峰值增量不超过 `24 MiB`、预热后增长不超过 `4 MiB`。
报告只有在声明 runner 身份与预注册扩展 SHA-256 同时匹配，且所有性能、矩阵和
资源条件通过时才会 `accepted=true`。

`.github/workflows/performance-acceptance.yml` 是仅手动触发的
`[self-hosted, Windows, X64, ospf-fixed]` 门禁，不能由普通托管 runner 冒充。
当前本机完整演练已验证两轮 192 行矩阵、8 个 600 秒独立资源进程及全部本地
门禁，但 runner 身份和预注册扩展哈希未匹配，报告仍为 `accepted=false`、
`fixed_runner=false`；因此不能据此关闭 pending。
