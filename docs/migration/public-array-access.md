# 公共数组受检读写 / Public Checked Array Access

## 范围与兼容 / Scope and Compatibility

公共 `MultiArray` / `MutableMultiArray` 新增 `at(*, indices, standard_layout=False)`，
公共 `MutableMultiArray` 新增 `set_at(*, indices, value, standard_layout=False)`。
这些入口返回项目现有三参数 sealed `Result`，不会改变 Result、数组或形状类的身份。
旧 `get/set`、方括号协议及其调用方尚未切换；不更改旧返回类型、不新增业务异常，
也不把旧宽松坐标混叠当成正确语义。`AbstractMultiArray` 不增加抽象方法，避免破坏第三方实现。

These additive public operations provide checked migration entry points, not a replacement
of existing get/set signatures or a completed public storage cutover. Existing subclasses
inherit them without acquiring a new abstract-method requirement.

```python
import numpy as np
from ospf_python.multiarray import MultiArray, MutableMultiArray, Shape2, StorageOrder

data = np.arange(6, dtype=np.int16)
shape = Shape2(2, 3, StorageOrder.COLUMN_MAJOR)
array = MutableMultiArray(shape, data)
alias = MultiArray(shape, data)
assert array.set_at(indices=(1, 1), value=17).is_ok()
assert data[3] == alias.at(indices=(1, 1)).unwrap() == 17
assert array.at(indices=(0, 3)).is_failed()  # 不混叠 / No coordinate aliasing.
```

## 权威与计算 / Authority and Computation

- 每次读取当前 `_shape` 的 dims/order，通过一次
  `_native._SharedAccess.read/write` 调用完成固定 revision 的 `Shape.create`、严格坐标
  `checked_index`、存储检查和 Result 发布。绑定的协议对象只持有类型/常量/Result
  工厂；原生侧逐元素要求内置 `int`，拒绝 bool、NumPy 整数、浮点和少轴/多轴坐标。
  不调用旧 `flat_index/strides/size` 算法，没有失败后 fallback，也不缓存形状、owner、
  叶或 buffer。
- 每次定位成功后取得当前 `_data`；必须是真正 ndarray（允许子类）、一维且数量与形状一致。
  保留原对象、dtype、正负 stride、共享与外部写入。没有持久形状缓存、元素镜像或 Rust 数据副本。
- 当前仍为外部 ndarray 权威存储；Rust 负责严格坐标计算，Python 只适配外部 ndarray 协议。
  不宣称 ospf-rust 接管共享存储或 NumPy dtype 算法。
- 严格坐标必须为完整非负整数 tuple，不接受 bool、NumPy 整数、浮点、少轴/多轴或负索引。
  维数/类型错误返回 ILLEGAL_ARGUMENT，越界返回 OUT_OF_RANGE；保留已有 Rust 错误来源和原始码。
- 零维 `DynShape(())` 的唯一坐标是 `()`；正维必须满足既有稠密机器范围。
  任意精度公开稀疏形状仍可构造，仅进入本稠密边界时失败。

The existing pinned native shape machinery is reused; there is no new indexing kernel.
The original ndarray remains the only storage authority, including strided buffers.

## 自定义形状与扩展 / Custom Shapes and Extensions

精确内置 Shape1–4/DynShape 自动接受；所有子类和自定义形状默认返回 Failed，且不读取其属性。
传入 `standard_layout=True` 表示调用方明确要求按当前 dims/order 的标准行列布局定位，
**不表示保留任意自定义 flat_index 映射**。只读取 dims/order，不要求或调用旧 Protocol 的
其他属性和方法。确认参数必须是内置 bool。

数组子类可以覆盖新入口；旧自定义映射调用方暂时仍使用原入口，必须独立审查后迁移。
不静默 reinterpret 自定义映射，不在标准 Rust 索引失败后调用旧算法。

Custom shapes and subclasses require explicit standard-layout consent; this is not an
adapter for arbitrary mappings. Arbitrary mappings remain a separate migration gate.

## 值、失败与副作用 / Values, Failures and Side Effects

读取只转换真实 `np.generic` 及其子类的 item；普通 object、ndarray、None 和 Result 叶
作为数据保留身份，不访问伪装的 `__class__` 或普通 item，不执行 Result 的业务解包。
这是与已验收公共迭代一致的标量规则。

写入保留 ndarray dtype 的赋值语义，包括显式数值截断、object 身份和用户转换协议；
不承诺精确数值转换。如需精确 solver 系数，必须另行经过 Rational/受检 Float64 边界。
只读、dtype 转换、ndarray 子类、用户形状属性及 scalar.item 的普通外部异常转换为
APPLICATION_ERROR / EXTERNAL_ARRAY，原始异常对象及 traceback 放在
`FailureContext.callback_exception`，不格式化用户异常。KeyboardInterrupt/SystemExit
等非 Exception 的 BaseException 按原对象传播。

没有数组锁跨越用户代码，允许 dtype 转换重入。一次操作持有局部 shape/data 快照，
不保证并发修改 `_shape/_data` 的跨属性事务；多次操作也不是一个快照事务。
失败前的用户回调副作用、复杂 dtype 的部分赋值及外部线程写入不回滚。
异常 traceback 可能保活源，释放失败 Result 后才可回收；成功结果不额外缓存 owner/buffer。
既有 object ndarray 非 GC 引用边缺口没有被此入口修复。

External protocols retain their original assignment/conversion behavior and side effects.
Failures retain exception identity; no transaction, callback rollback, storage-GC fix,
zero-copy native ownership or performance improvement is implied.

## 批量读取与实际导入消费者 / Batch Reads and the Existing Import Consumer

两个公共数组类提供 `at_many(*, indices, standard_layout=False)`。`indices` 必须为内置
list，元素沿用单点严格坐标 tuple 合同，允许重复，结果按请求顺序返回独立 list。
一次操作只建立一个 Rust 形状、调用一次批量坐标检查，再调用一次原生引用收集器；
不执行逐点 Python at/unwrap，也不调用旧 get/flat_index/strides。

```python
values = array.at_many(indices=[(1, 1), (0, 2), (1, 1)]).unwrap()
assert values == [17, 4, 17]
assert array.at_many(indices=[(0, 0), (0, 3)]).is_failed()
```

整个坐标批次通过后才读取 `_data`，因此尾部非法坐标不会执行前部槽位或 scalar.item。
空批次仍检查 shape、标准布局确认和 data 的一维/数量合同，成功返回空 list。
本次操作只取得一个 data 引用；scalar.item 若替换 owner._data，不会重定位本次未读槽位，
但对已取得 buffer 的槽位写入会被后续读取观察到。重复坐标也逐次读取并执行真实 scalar
转换，不缓存叶或转换结果。只读与正/负/零 stride 输入均可读取。

原生收集器在不持锁的情况下逐项执行外部 ndarray 索引和可选真实 scalar.item，
完整成功才发布结果 list；普通异常保留原对象/traceback，BaseException 传播。
失败会释放未发布的列表，但外部异常自身的 traceback 或用户代码可能继续保活叶/源。
不回滚用户副作用，不提供“先快照全部原始槽位再转换”的保证，也不是并发原子快照。
成功列表仅持有返回叶，不额外缓存 owner/buffer；叶本身的回边仍然有效。
形状、ndim、dtype、长度及缓冲 resize 的外部修改必须由调用方同步（包含回调中的修改）；
本入口只在开始收集前校验元数据，不承诺检测所有中途失效，更不能把该路径作为共享
存储完整失效政策已验收的证据。坐标传输占 O(batch × rank)，偏移与结果 DTO 占 O(batch)，
并非 O(rank) 游标或零分配读取。

同一收集器的 raw 模式已接入既有 `_binding.MultiArray/MutableMultiArray.from_legacy_state`：
旧物理序列验证后直接原生收集，保留 NumPy scalar 类型而不调用 item；不再走
`_numpy_snapshot` 的 ravel/list 或重复的一维形状创建。源必须仍是精确内置 ndarray，
dtype/数量/显式 copy=True/自定义形状政策不变，随后由固定 Rust builder 发布独立槽位。
完整 raw 路径通过 CPython 内置 list 构造收集原序列，避免逐槽重新索引的性能回归；
收集前后均检查数量。这是外部序列协议适配，不是在原生 crate 中重写 NumPy 数学。
这项改进是现有 Result 消费者的实际默认路径，不是只添加一个无人调用的私有接口。
通用多维 `from_numpy` 的既有转换路径不因此宣称已替换。

Batch reads amortize checked shape/index/result overhead while retaining external storage
authority. Ordered observations of one captured buffer are not a concurrent atomic snapshot.
The existing explicit legacy import now reuses the raw collector and still detaches slots;
it does not become a shared import or invoke scalar conversion.

## 验证与后续 / Verification and Remaining Gates

`tests/multiarray/test_public_array_access.py` 覆盖严格索引、原生委托、两布局、共享/动态源、
正负 stride、dtype/只读、自定义映射显式确认、不透明叶/Result、原始异常/进程控制、
scalar 子类、重入及成功路径无缓存。真实 solver 合同位于
`tests/native/test_solver_boundary.py`：`test_public_batch_checked_reads_feed_real_solver_without_scalar_ffi`
在行/列布局上把 `at_many` 收集的精确系数送入真实 SCIP/Gurobi10 模型并复核最优解。
当前扩展实测 SCIP/Gurobi10 各两布局通过，Gurobi11/12 因未编译跳过；证据见
`logs/p3/at-many-real-consumer/`。发行 smoke 同时验证受检读写和共享行为。

`test_public_checked_shared_access_registers_real_solver_coefficients` 进一步在行/列布局上
通过 `MutableMultiArray.set_at` 写入共享 ndarray，并分别用可变数组与不可变别名的 `at`
读取，再把系数送入真实 SCIP/Gurobi10 模型复核最优解。当前扩展同为
SCIP/Gurobi10 各两布局通过、Gurobi11/12 跳过；证据见
`logs/p3/at-set-at-real-consumer/`。

`tests/multiarray/test_public_array_batch.py` 另外验证批量原生委托、全批先验、重复/空批次、
捕获 buffer 后的重入、失败输出释放、成功无 owner/buffer 缓存及旧字段默认消费者的
raw 委托。当前源码合同默认与 `PYTHONMALLOC=debug` + `-X dev` 均为 **54 passed**。

`at_many` 的当前 Windows CPython 3.13 本地操作门槛最近重新审计了四轮。批量读取
每轮 8 个 `count >= 10000` 受门禁组合均通过，四轮最大比率为
`0.9005627161886319x–0.925991306227106x`。但真实旧字段导入的 16 个
stride/layout 组合中，round1 有一个 `object`/列布局/100,000 槽组合达到
`1.2015098108624036x`；后三轮最大分别为 `1.0131082197411792x`、
`1.0181524068476926x`、`1.012615433417101x`。严格原 `1.15x` 门槛下不能忽略或
选择性采用该失败，原始证据继续保留。随后使用预注册、未缩小矩阵的 16 场景
ABBA/BAAB 抗漂移复验：每场景 15 轮、每实现两次采样取中位数，两个独立进程的
最大场景比率分别为 `1.0093328994679276x` 和 `1.0118874196527579x`，两轮均
16/16 通过。以该更强复验和原 `1.15x` 门槛，两个 `at_many` 只在 Windows
CPython 3.13 局部操作范围登记 `switched`；旧顺序失败没有被删除或改写。

同一当前源码的 8 个独立资源进程覆盖两类数组、两布局及 int64/object，全部满足
`32 MiB` 峰值增量 / `4 MiB` 预热后增长包络，最大峰值增量 `20,054,016 B`、最大
增长 `376,832 B`。这些是本机操作证据，不推广成固定 runner、全领域或长期资源结论。

固定 revision `119854756a0aeb66d2998055f96fa7175c7bfb37` 的当前源码已重建
基础 wheel、`scip,gurobi10` wheel 和同源 sdist。两个 wheel 均在仓库外隔离站点
安装；同源 sdist 分别以 `--locked` 重建基础与双后端 wheel、重新安装并通过发行
smoke。基础站点批量合同 **54 passed**；solver 站点批量合同 **54 passed**，真实
SCIP/Gurobi10 批量消费者 **4 passed / 4 skipped**，skip 仅为未编译的
Gurobi11/12。两站点均断言产品模块和扩展来自站点；solver 扩展与 wheel 内
SHA-256 `3f1b45450e5fc8bebf6242a1e33491c8579a245066e9f98152449d96eb2e0ec7`
一致。完整哈希与证据见 `logs/p3/at-many-switch-current-20261031/FINDINGS.md`。

### 固定形状快路径

逐点 `_SharedAccess.read/write` 仍是唯一公共调用路径，但精确内置 `Shape1`–`Shape4`
现在使用固定上游形状算法，不在每次访问中构造多个 `BigInt` 和 `DynShape`。快路径每次
调用重新读取当前 `d0`–`d3`、存储顺序和完整索引，随后仍执行固定 revision 的
`fixed_shape` 稠密校验、维度容量检查、坐标长度/范围和上游 `index_of`；没有跨调用
缓存 owner、shape、data、offset 或叶。`DynShape`、自定义形状、shape 子类和显式
`standard_layout=True` 继续走原严格路径。

错误观察时序保持不变：先校验维度整数类型与坐标整数类型，再读取存储顺序，随后执行
维度容量、坐标长度/范围和索引检查。快路径没有第二套公开索引算法，也没有失败后
回退到旧 `flat_index/strides`。

### 当前验收

两轮完整调用基准均遍历 100/10,000/100,000 个坐标，覆盖行/列布局和 int64/object，
并计入 Result 构造与 `unwrap`。在未调整 oracle、样本或原 `1.15x` 门槛的情况下：

| 操作 | 第 1 轮 | 第 2 轮 | 通过数 |
| --- | --- | --- | --- |
| `at` | 最差 `0.8328596048463607x` | 最差 `0.9086908077994429x` | 两轮各 12/12 |
| `set_at` | 最差 `0.7242256489661619x` | 最差 `0.744265217130002x` | 两轮各 12/12 |

当前访问/批量合同默认 **145 passed**，`PYTHONMALLOC=debug` + `-X dev` 再次
**145 passed**。8 个真实独立资源子进程覆盖两类数组、两布局和 int64/object，可变
场景同时执行 `at`/`set_at`，结果 **8/8 passed**；最大预热后增长 `1,601,536 B`、
最大峰值增量 `4,853,760 B`，限制仍为 `4 MiB` / `32 MiB`。报告明确保留
`fixed_runner=false`、`full_resource_budget_verified=false`，不能据此关闭固定
runner、全领域或长期资源门槛。

固定 revision `scip,gurobi10` 扩展上的真实消费者为 **4 passed / 4 skipped**，
skip 仅为未编译的 Gurobi11/12。基础与 solver wheel 均在仓库外隔离站点安装并运行
**145 passed**；solver 站点另跑真实消费者 **4 passed / 4 skipped**。两站点均断言
产品模块、`multi_array.py` 和 `_native` 来自站点，模块泄漏为 `{}`。同源 sdist
分别以 `--locked` 重建基础和双后端 wheel，仓库外发行 smoke 均通过。

默认 editable 已恢复为 `native_solvers=""`。迁移盘点为
`explicit_contracts=1444`、`unresolved_exports=0`、`issues=[]`；迁移门禁和生产
质量门禁 PASS，迁移合同 **35 passed**，定向 mypy、Ruff、Rust `rustfmt --check`
与 `cargo check --release --locked` 通过。严格 `cargo clippy -- -D warnings`
仍被既有 `native/src/shared_nested.rs` 的 `clippy::let-and-return` 阻断；
仅允许该既有 lint 后，当前改动通过 `-D warnings`。

### 状态与剩余门禁

三个逐点入口 `MultiArray.at`、`MutableMultiArray.at` 和
`MutableMultiArray.set_at` 按 `at_many` 先例，只在 **Windows CPython 3.13 局部
操作范围**登记 `switched`。这不是完整数组、旧协议或跨平台切换。

旧 `get/set`、方括号协议、任意自定义映射、共享批量写事务、共享存储 GC、调用方/
领域迁移、固定 runner、全领域、长期资源、Linux 与 Gurobi11/12 仍需独立验收。
这些限制不得因本轮局部状态变化而从迁移范围移除。
