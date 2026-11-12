# Rust 上游缺口

本文件维护人工审查的语义合同与修复要求，不记录阶段完成率。当前绑定固定 revision 为 `119854756a0aeb66d2998055f96fa7175c7bfb37`。

## RG-029：SCIP 带进度回调的求解每次泄漏约 2.55 MiB

状态：**已在 `ospf-rust` 修复（根因为 `Rc<ScipPtr>` 引用环），尚未生效——pin 仍是
`119854756a0aeb66d2998055f96fa7175c7bfb37`，需改 pin 后重跑全部证据。**

### 根因与修复（2026-11-11，`D:/workspace/ospf/ospf-rust`）

`russcip 0.9.1` 的 `Variable` 内含 `Rc<ScipPtr>`（强引用）。插件的 `SCIPTelemetryRuntime`
把 `Vec<Variable>` 存进自己，而 runtime 又被放进 `SCIPTelemetryEventHandler`，
handler 的 `Box` 由 **SCIP 实例自己持有**：

```
SCIP 实例 → 事件处理器 → runtime → scip_vars: Vec<Variable> → Rc<ScipPtr> → 同一实例
```

`Rc` 永不归零 → `ScipPtr::drop` 不执行 → **`SCIPfree` 从不被调用** → 整个实例（约 2.6 MiB）泄漏。
这解释了「只在有回调时泄漏」「与模型规模无关」「三条路径量级一致」。

修复：`scip_vars` 改存 `*mut russcip::ffi::SCIP_VAR`（`Variable::inner()` 是公开方法），
取值改用 `SCIPgetSolVal(scip, SCIPgetBestSol(scip), var)`。**实测 52,015,104 B / 20 轮 →
0–1.5 MB（噪声级）**；新增 4 条上游回归测试（含 incumbent 值仍为 1.0 的正确性验证），
`ospf-rust-core-plugin-scip` 47 个测试全过。

### 修复前的原始记录
`native/src/solve.rs` 的 scip 与 gurobi 两条分支结构完全对称（都是 `bridge.map(...)` →
`Arc::new(move |snapshot| bridge.emit(...))` → 放进 config → `with_config`），
所以差异不在绑定层，而在 `crates/core-plugin/scip`（`russcip 0.9.1`）或 SCIP 自身。

实测（Windows CPython 3.13、scip 变体、同一进程）：

| 实验 | 每轮增长（SCIP） | 每轮增长（gurobi10，对照） |
| --- | --- | --- |
| 完整 5 段（**不传回调**） | **−4,301 B**（无泄漏） | +15,360 B |
| **完整 5 段 + `on_progress`** | **+2,543,616 B** | **−1,843 B**（无泄漏） |
| 跳过 `solve` | +614 B | +205 B |
| 只 `create` + `close` | **0 B** | +614 B |

泄漏与模型规模无关（同一 15 轮：1 变量 **+2,551,808 B/轮**、10 变量 **+2,556,177**、
100 变量 **+2,853,274**，100 倍变量只放大 12%）。三条独立探针互相吻合：
单轮 20 轮实验 2,543,616 B/轮、15 轮实验 2,551,808 / 2,556,177 B/轮、
`_solve_batch`（每批 4 模型）9.87–10.53 MiB/批 ≈ 4 × 2.55 MiB。

已排除：逐变量收集（`lib.rs:160-165` 的 `needs_values` 路径，若成立应随变量数线性增长）；
message handler（`russcip 0.9.1` 与插件里都没有 `SCIPsetMessagehdlr`）；
「event handler 的 `Box` 从不释放」（`scip.rs:786` 的 `into_raw` 与 `:780` 的
`eventhdlrfree` 里的 `from_raw` 是对配的）。

量级提示：~2.55 MiB 比「收集 1 个或 100 个变量的 `Vec<f64>`」（8 B / 800 B）大五个数量级，
且与规模无关，因此泄漏的是**某个与实例等量的结构**；而不传回调时不泄漏，
说明实例本身在无回调时是正常释放的——**是回调路径额外保留了约一个实例量的状态**。

影响面（2026-11-11 实测扩到真实领域流程）：`native/src/bpp1d.rs:829` 的 `solve` 同样接受
`on_progress`。同一进程 12 轮装箱求解：**无回调 +9,899 B/轮**（走平）、
**有回调 +2,533,035 B/轮（2.42 MiB）**，12 轮共涨 29 MiB。
与 `model.solve` 的 2,543,616 / 2,551,808 B/轮同一量级，说明是**同一个每实例泄漏**，
不是 bpp1d 特有。因此「用 SCIP 跑装箱/调度并开进度回调」的生产用法会持续涨内存。

第三条路径（甘特 `gantt_task.solve_lp`）**已实测，且速率更高**：
`TaskApplicationService(native_solver="scip")` 重复 `refresh_shadow_price` 12 轮，
**无 `on_progress` +250,880 B/轮**（走平）、**有 `on_progress` +5,498,197 B/轮（5.24 MiB）**，
12 轮共涨 62.9 MiB。**是 `model.solve`（2.5 MiB）的 2.16 倍**，
与「列生成每轮解约 2 个 LP、每个 LP 各泄漏约 2.5 MiB」一致——
即**甘特迭代越多泄漏越快，长时间排程场景最严重**。
另注：`tests/framework/gantt_scheduling` 里凡出现 `on_progress` 的用例都把 native 层 mock 掉了
（`test_task_application_service.py:854/872/924`），**所以现有测试不会发现这条路径**；
建议补一条「甘特 + scip + 回调」的资源用例。

最小复现：同一进程内重复 N 次「建 1 变量模型 → `set_objective` →
`solve(solver="scip", on_progress=<任意回调>)` → `close`」，`PrivateUsage` 每轮约 +2.5 MiB；
去掉 `on_progress` 后归零。装箱路径的等价复现见
`logs/p3/b394-rg029-domain-impact-20261111/probe-bpp1d-leak.py`。

处置要求：定位需在 C 侧打点（`SCIPsetMemoryhdlr` 或 `SCIPfree` 前后），属上游改动；
修复落在 `ospf-rust` 的 scip 插件或 `russcip`，须单独立项并重跑全部证据（改 pin）。
回归应覆盖：`tests/native/test_model_lifecycle_stress.py` 的
`test_repeated_solver_sessions_reclaim_threads_memory_and_callbacks[scip]`
（该用例在 base 构建上 skip，只有 scip 变体才会执行）。

证据：`logs/p3/b388-scip-memory-growth-20261111/`、`logs/p3/b389-scip-stage-probe-20261111/`、
`logs/p3/b390-scip-leak-localized-20261111/`、`logs/p3/b391-scip-varscale-20261111/`、
`logs/p3/b392-russcip-source-read-20261111/`。

## RG-026：固定 revision 的 `einsum` 内核秩域窄于 NumPy、且按朴素左结合累加

状态：未解决；阻止把 `matmul`/`dot`/`trace` 三个出厂入口委托固定上游内核
（`ospf_rust_multiarray::einsum::{matmul,dot,trace}`，源码
`ospf-rust-multiarray/src/einsum/operations.rs` 的 35/149/202 行）。两侧都在固定 revision 上
**实际执行**后测到两类分歧，任一类都足以否掉“机械委托”。

**秩域**（`logs/p3/einsum-parity-audit/semantics-divergence.json`，同一形状网格两侧各跑一遍）：
上游 `matmul` 只接受 2D×2D；出厂 Python 的 `matmul` 还接受 1D×1D（返回 1 元素数组）与
2D×1D（返回 4 元素数组），上游对这两例返回 `DimensionMismatch`。上游 `dot` 只接受等长 1D；
出厂 `dot` 还接受 2D×2D（6 元素）与 1D×2D（2 元素）。上游 `trace` 只接受 2D 方阵；出厂
`trace` 对 3×5 矩形返回标量（`np.trace` 取主对角），上游返回 `UnsupportedOperation`。
两侧都拒绝的组合里异常类型也不同（`EinsumError::*` 对 `ValueError`/`TypeError`），
所以“都报错”也不等于可直接替换的协议。

**舍入**（`bit-exactness.json`）：上游内核是朴素三重循环加逐元素 `clone()`，每次累加都是左结合；
出厂路径走 NumPy/BLAS。实测上游位模式与“同一 LCG 输入 + Python 朴素左结合循环”逐位相同
（matmul 8×8 64/64 个元素、dot 64 与 16384、trace 64×64 全部 `matches_naive_left_assoc=true`），
但与出厂 NumPy 结果不同：matmul 8×8 有 14/64 个元素不同、最大 2 ULP；dot 64 为 1 ULP、
dot 16384 为 25 ULP（最大相对差 2.8e-15）；trace 64×64 为 1 ULP。按
[混沌系统合同](chaotic-system-contract.md)的既有政策，“把公开数值合同从逐位一致收窄为容许
ULP 级分歧”属于公开行为变更，需要用户确认，不能在绑定里默认接受。

**预算**（`budget-projection.json`）：完整调用比值
`(copy + 196.8 ns PyO3 往返 + 437.0 ns 结果发布 + 实测上游内核) / 出厂 oracle` 在 11 个自然规模里
只有 1 个不超过 1.15：`dot` 16384（0.380）。其余从 matmul 8³ 的 1.633 一直到 matmul 256³ 的
276.0、trace 1024² 的 455.6 全部超预算；即使把拷贝记成 0（`ratio_without_any_copy`），
matmul 8³ 仍是 1.464、dot 64 是 1.966、trace 1024² 是 3.016。`trace` 的结构性原因是出厂 oracle
只读对角（O(n)），而绑定必须整体搬运缓冲（O(n²)）。唯一达标的 `dot` 16384 只能靠“按尺寸分支”
（大尺寸走原生、小尺寸走 NumPy）使用，而该做法已按
[标量混沌合同](chaotic-scalar-contract.md)明确否决为第二套算法。

要求：若要这三个入口可委托，上游需同时提供 ① 与 Python 秩域一致的入口（1D×1D、2D×1D 的
`matmul`，2D×2D、1D×2D 的 `dot`，矩形与 offset 的 `trace`）；② 与 NumPy 一致的累加顺序，或
明确声明并获授权的 ULP 容差；③ 不拥有缓冲的数组交换，或显著更快的收缩内核，以满足 1.15。
在任一条落地前，这三条合同停在 `inventoried`，`pending_acceptance` 挂本缺口与两项授权
（秩域收窄、ULP 容差扩大），绑定层不得另写等价 einsum 内核、不得按尺寸分支、不得用 NumPy
门面换名。

证据由独立探针 crate `logs/p3/einsum-parity-audit/kernel-probe/`（同一 pin、同一离线缓存、
不含 PyO3 与 Python 门面）与 `check_bit_exactness.py`、`budget-arithmetic.py` 产出；
`probe.log` 的裸内核耗时与 `oracle-costs.json` 的出厂成本出自同一夹具。本包未改生产代码、
未改 Rust、未重建扩展。

## RG-027：符号表达式的同名 `normalize` / `evaluate_boolean` 与 Python 自由函数不共享输入 AST、结果类型或缺失值语义

状态：未解决；阻止 `ospf_python.math.symbol.expression.operation.normalize.normalize` 与
`ospf_python.math.symbol.expression.operation.evaluate_boolean.evaluate_boolean` 直接委托固定 revision。
2026-10-31 的 v4 审计同时读取固定 revision 源码并实际调用出厂 Python 入口；证据见
`logs/p3/free-fn-parity-20261031/`。两侧名称相同，但公开类型、失败协议和语义均不同。

### `normalize`

| 维度 | 出厂 Python | 固定 Rust |
| --- | --- | --- |
| 输入 | `Expression` 对象树，节点可为 Constant/Path/PropertyPath/Binary/Unary/BooleanAdapter | `normalize<N: Normalize>(N) -> N` 的泛型值 |
| 已实现类型 | 任意 Python `Expression` 子类；未识别节点原样返回 | 仅 `Linear`、`Quadratic`、`Canonical` 及三种不等式实现 `Normalize` |
| 操作 | 递归常量折叠；常量子树用 Python 运算符求值 | 多项式合并同类项；不等式把右端常量并入左端并置零 |
| 值域 | 常量值是 `Any`，可容纳字符串、Decimal、自定义对象等 | 泛型系数 `T` 需满足各 impl 的 Clone/Zero/PartialEq/Add/Sub/Hash 等约束 |
| 返回 | 新的表达式树，或原样返回 Path/PropertyPath/不支持节点 | 消耗并返回同一 `N` 类型 |

实测 Python 侧：`"left" + "right"` 的二元常量表达式规范化为
`ConstantExpression("leftright")`，`(2 + 3) * x` 部分折叠为 `5 * x`，
`BooleanExpressionAdapter` 包装的 `True && False` 折叠为 `Constant(False)`，`PathSymbol`
保持对象身份。上游自由函数没有接收 ScalarExpression/BooleanExpression/Python Expression
的桥，也没有上述任意值常量折叠入口。

上游另有 `normalize_boolean_expression` / `normalize_with_config`，但它们是布尔树的结构
规范化（扁平化、`Trivalent` 常量折叠、去重、双重否定等），不是 Python 的通用标量表达式
常量折叠，也不是那个同名自由函数。不能把“同名可达”或“另有 normalize 名称”当作平价证明。

### `evaluate_boolean`

| 维度 | 出厂 Python | 固定 Rust |
| --- | --- | --- |
| 输入 | 任意 `Expression` + `dict[str, Any]` | `&ParsedBooleanExpression` + `&impl EvaluationContext` |
| AST 值域 | Python 任意对象和自定义 Expression | `ExpressionValue::{Null, Boolean, Number(f64), String}` |
| 查找失败 | `PathSymbol` 抛 `KeyError`；PropertyPath 可抛 KeyError/AttributeError/IndexError/TypeError | 缺引用返回 `Trivalent::Unknown` |
| 自定义节点 | Python 子类可提供任意 `evaluate` | `Custom` 本地求值为 `Unknown` |
| 返回 | `bool(expr.evaluate(bindings))` | `EvaluationResult = Trivalent` |

实测 Python 侧：缺绑定为 `KeyError('missing')`，`None -> False`，非空字符串 `-> True`，
嵌套字典路径 `{"obj": {"flag": 0}} -> False`。若直接改调上游，缺绑定会从异常变成
`Unknown`，返回类型会从内建 `bool` 变成三值枚举；再把 `Unknown` 映射为 `False` 虽可保持
返回类型，却会改变现有缺绑定行为。当前 revision 没有把 Python Expression 递归转换成
`ParsedBooleanExpression`、把 `dict[str, Any]` 转成 `EvaluationContext` 的通用桥。

### 处置要求

要让两个入口无公开行为变化地委托，上游需提供 ① 与 Python Expression 节点和任意值一致的
AST/值交换，或等价的表达式树常量折叠与求值入口；② 明确的缺绑定、Custom 节点、非有限数和
任意 Python 运算符传播协议；③ `Trivalent` 到现有返回协议的确定映射。另一条路径是由用户
明确授权修改 Python 公开类型/异常/缺值语义，或将对应能力登记为合理保留的 Python 集成。
在此之前两条合同保持 `inventoried`，绑定层不得另写表达式内核、不得静默把 Unknown 当作
False、不得用布尔专用规范化冒充通用标量 `normalize`。

本审计只改 Python 仓库的合同、文档和证据，不修改相邻 Rust/WASM、固定 revision、Cargo/lock
或生产实现，也没有把任何入口标成 `bound`/`switched`。

## RG-028：同名命中不可直接委托；已按独立原生合同闭环

状态：已解决；8 个同名命中均已按独立合同接通，不能按名称机械委托的结论继续有效。
2026-10-31 的审计只读固定 revision，并实际执行两侧能够直接调用的 Python 入口；证据见
`logs/p3/non-module-callable-parity-20261031/`。

初始盘点覆盖 8 条，它们曾挂着 `parameter-and-return-type-parity-verification`。全部核完后，
该 pending 已从这 8 条合同移除，全局 parity 引用归零；但“待核对项清零”不等于“可以直接
委托”。以下保留初始同名比较与不可机械委托结论：

| Python 入口 | 固定 Rust 同名项 | 不可委托原因 |
| --- | --- | --- |
| Gantt `task_model_builder.extract_shadow_prices` | `TaskColumnGenerationAlgorithm::extract_shadow_prices(&mut self, &LPResult, &HashMap<String, usize>) -> ()` | Python 旧自由函数读取 `MetaModel`、约束系数和 `SolveValue`，按松弛启发式返回 `dict[str, float]`；Rust 是算法实例方法，修改自身 `shadow_prices`，输入为 LP 对偶解和约束名索引。二者不能按名称委托，现由显式 `LPResult` 原生桥处理真实对偶。 |
| `_binding.public_array_access.read/write` | `TrajectoryFiles::{read,write}` | Python 对共享 ndarray 槽位做受检读写并保留别名；Rust 做 JSONL 轨迹文件 I/O。业务对象和载荷无关。 |
| `_binding.quantity_ordering.select`、`_binding.selection.select` | `ConflictExtractionTier::select(&CapabilityMatrix) -> Self` | Python 分别做单位数量的流式极值选择和 Python 序列的组合/排列；Rust 从能力矩阵选择冲突提取层级。两者只是共享通用词 `select`。 |
| `_binding.quantity_ordering.contains` | `IntegerDomain::contains(i64) -> bool` | Python 对带单位数量做闭区间判断并保持 SI/affine 语义；Rust 判断 `i64` 是否属于整数域。值域、单位和返回对象不同。 |
| `_binding.quantity_snapshot.encode/decode` | 私有 `snapshot_codec::{encode,decode}` | Python 读写 `ospf.quantity` schema v1 的数值/单位 DTO，支持 adapter 和工厂恢复；Rust 读写 `ConstraintProgrammingSnapshot` 的 canonical JSON artifact。自由函数位于 `mod snapshot_codec`，crate 根只公开 CP 快照的 `to_canonical_json`/`from_canonical_json` 包装和 artifact 解码，不可按该函数名调用。 |

运行时探针进一步确认 Python 侧合同：共享数组 `(1,0)` 读为 `3`，写入后底层槽位为 `9`；数量
极小值返回原输入对象，`1.5 m` 落在 `1 m..2 m`；数量快照为
`{"schema":"ospf.quantity","version":1,...}` 且能无损往返；位置选择分别返回
`[[1,2]]` 与 `[[1,2],[2,1]]`；甘特旧助手在同一输入下返回紧约束 `1.0`、
松约束 `0.0`。这些行为都不是固定 Rust 同名方法的自然结果。P3-AA 新增的真实对偶路径
在相同任务行输入下返回实际值 `-2.5`，并省略零对偶，旧 0/1 仅保留为无对偶兼容路径。

处置要求：7 个绑定适配器继续按各自已有的原生 PyO3 合同实现，不得借这些同名 Rust
方法换名；甘特已建立算法实例、`LPResult`、约束索引和真实 dual 的显式桥。旧启发式返回
只作为无对偶输入的兼容路径，不得作为影子价格或迁移验收证据。本缺口关闭的是源码接通，
不关闭完整 solver dual 发布、消费者切换、性能、平台或发行验收。

后续进展：

- P3-S 已确认 `public_array_access.read/write` 直接使用
  `_native._SharedAccess`、存在公开 `at/set_at` 消费者并通过共享数组定向测试；
  两条已前移到 `specified` 并摘除 RG-028。
- P3-Z 已确认 `quantity_ordering.select/contains` 分别使用独立原生
  `_quantity_extreme/_quantity_contains`；`selection.select` 使用原生
  `_selection`；`quantity_snapshot.encode/decode` 是版本化 `ospf.quantity`
  schema v1 的 Python 兼容 wire，使用原生 Unit/Rational 状态而非私有 CP codec。
  这 5 条已前移到 `specified` 并摘除 RG-028，证据见
  `logs/p3/rg028-adapter-source-20261031/`。
- P3-AA 已把甘特 `task_model_builder.extract_shadow_prices` 前移到
  `specified`。`_native._task_shadow_prices` 构造固定
  `TaskColumnGenerationAlgorithm<BasicTaskCompilationContext, _>`，将显式
  `SolverOutput.dual_values` 装入 `LPResult` 后调用上游真实方法；返回只含非零
  `task_compilation_*` 对偶。无对偶输入仍走已标注的旧 0/1 兼容路径。证据见
  `logs/p3/gantt-shadow-price-source-20261031/`。
- RG-028 pending 现为 **0**；全局参数/返回类型 parity pending 仍为 **0**。

上述前移只表示源码接通，不代表 `verified`/`switched`、完整预算、数量全单位
切换或 Linux/Gurobi 11/12 已通过。甘特真实原生日志的 public service 切换、真实
solver 对偶发布、列生成/定价生命周期及完整预算仍打开。

## RG-022：混沌高维族的上游模型与出厂 Python 模型在 55/75 个公共类上不等价

状态：未解决；阻止 `ospf_python.math.chaotic` 的 55 个二维/高维公共类委托固定上游实现
而不改变公开数值行为。同名匹配到的 79 个类里，38 个可用出厂默认参数直接对比，
其中 25 个在默认参数向量上逐位一致（17 个位置映射、7 个需显式参数置换、1 个需名称
别名映射），13 个在任何已搜索映射下都不一致；另外 19 个两侧参数个数不同（不存在
重命名空间）、7 个上游 `step` 入参不是 `Point2/3/4`（状态形状无法表达）、3 个因出厂
默认值为非数值对象而未能测得平价，还有 8 个公共类在固定 crate 中没有同名系统。
25 个默认点一致的类随后被随机扫描再证伪 5 个（`BoualiAttractor`、
`GenesioTesiAttractor`、`HindmarshRoseModel`、`LorenzSystem`、
`ShimizuMoriokaAttractor`），故可委托的候选只有 20 个，需处置的类由 50 个升为 **55 个**。

证据：`logs/p3/chaotic-attractor-parity/`（`map.json`、`probe-plan.json`、
`parity.json`、`dispositions.log`、release 探针构建日志）。差异是模型级而非舍入级：
13 个不一致类的最大相对误差为 8.5e-4 到 0.98，而“仅浮点结合顺序不同”应在 1e-13 量级，
实测该类计数为 0。可逐式复核的例子：`AizawaAttractor` 上游把 `dz` 加到第二分量、
`dy` 加到第三分量，且 `dx` 的定义与出厂实现不同；`KickedRotator` 与 `SymplecticMap`
只有 1 个参数、`LoziMap`/`ThomasAttractor`/`VanDerPolSystem`/`WimolBanlueAttractor`
只有 2 个参数且已穷举置换，故其差异不可能来自参数顺序。
新增的 5 个证伪属于另一类证据缺口：`logs/p3/chaotic-system-binding/sweep.json` 在
每个系统 2000 组随机参数与随机状态（seed 20261030）上逐位对比，这 5 个类出现
1 到 512 ULP 的分歧（例：`LorenzSystem` 某样本上游给出 `0x1.2741f86b60200p-7`，
出厂内核为 `0x1.2741f86b60000p-7`），既非模型级错位，也不能保证逐位一致。默认参数点的逐位
一致**不可外推**，因此不登记为绑定候选；debug（`opt-level=0`）与 release 两种优化
等级的结论逐类一致（`debug_release_agree=true`），故该分歧不是 release 代码生成造成。

允许的处置只有三种，且都需明确授权：由上游提供与出厂模型一致的系统（本任务禁止改动
相邻 Rust/WASM 仓库）、把保持 Python 实现的类登记为用户确认的“合理保留/退役”，
或在用户确认下收窄公开数值合同（属于公开行为变更）。在绑定层另写等价模型等于
第二套内核，不允许。逐类的 disposition、置换表与门槛见
`docs/migration/chaotic-system-contract.md`。做该盘点的那一轮未改公共 API、未实现任何
绑定、未删除任何 Python 内核，75 个类当时全部停留在 `inventoried`。

后续进展（2026-10-30，工作包 G）：其余 20 个候选已实现为**私有**原生入口
`_native._chaotic_system_step` 与门面 `ospf_python._binding.chaotic_system.chaotic_system_step`
（扩展 sha256 `3469a86853febbaf207a9f6edeeac8cf39c9303f6688e376166da3d3d66153f0`），
这 20 个类当时全部为 `specified`；55 个待处置类
仍挂本缺口，`inventoried` 共 58 个（55 个本缺口 + 其余家族的 3 个）。

后续进展（2026-10-30，工作包 I）：其中 5 个 ndarray 形状的公开类已在“有限 `float64` 窄域”内
改为委托原生实现，合同状态前移到 `bound`（`BurkeShawAttractor`、`ChenCelikovskyAttractor`、
`ChenLeeAttractor`、`ChenSystem`、`ChuaCircuit`），完整调用预算比值 0.704–0.810；其余 15 个类
停在 `specified`，因为单步原生入口对标量/tuple 形状是 2.4–7.1× 的回归（见 RG-023）。
本缺口的 55 个待处置类与 `inventoried` 计数不变；窄域之外的宽数值域、NaN 符号位与
`DuffingEquation` 定义域报错仍是未决公开行为问题，因此这 5 个类不能退役 Python 内核。

后续进展（2026-10-30，工作包 J）：这 5 个 `bound` 类已在仓库外全新 venv 中分别安装
locked wheel 与由同一 sdist 重建的 wheel，各跑 35 个单步/`iterate` 测量，共 70 行；
原生与 Python 回落逐位一致。固定状态单步 1e6 次的 `PrivateUsage` 增量最大为
wheel 20 480 B、sdist 36 864 B；`iterate(10 000)` 私有增量为 0.29–2.13 MiB，
返回 10 001 个数组。合同已移除 `complete-call-performance-and-resource-budgets`，
但宽数值域、NaN 符号位、`DuffingEquation` 定义域和 Linux/Gurobi 11/12 仍未关闭；
证据见 `logs/p3/chaotic-bound-distribution/`。

## RG-025：27 个 `disposition = rust` 区域的公开面筛查显示 740 个能力中只有 7 个字段名一致、6 个函数有同名可达 `pub fn`

状态：未解决；阻止 P3–P7 其余区域（bpp3d 102、symbolic-math 91、csp1d 91、model-symbols 43、
models 43、solvers 43、algebra 41、math-basics 40、quantities 38、multiarray 35、geometry 26、
remote 26、bpp1d 24、csp2d 16、bpp2d 14、math-multiarray 12、framework-solver 12、
network-scheduling 11、gurobi 9、scip 8、tokens 7、variables 6、framework-model 2）在不改变
公开 API 的前提下委托固定 revision。范围、逐区域分布与方法见
[各区域公开面对应度筛查](area-correspondence-screening.md)。

实测（固定 revision `119854756a0aeb66d2998055f96fa7175c7bfb37`，上游面用 `git grep`/`git show`
在该 revision 上解析、绝不读工作区；`logs/p6/area-screening/area-summary.json` 与逐区域
`mapping-<area>.json`）：740 个能力里**391 个在该区域 api-map 声明的上游 crate 中没有同名公开类型**，
42 个函数在全工作区没有同名 `pub fn`（两者合计 433，其中 75 个连一个 CamelCase 词元都不共享），
43 + 3 个同名只出现在别的 crate（`ospf-rust-core` 的通用名或 `ospf-rust-example` 示例代码），
139 个同名但形态不可比（trait/单元结构体/Python 服务类），109 个同名但字段集合不同，
**只有 7 个字段名集合一致**：
`Tolerance{epsilon}`、`Axis2{X,Y}`、`Axis3{X,Y,Z}`、`AxisPlane3{XY,XZ,YZ}`、
`Circle{center,radius}`、`CanonicalMonomial{coefficient,powers}`、
`LinearMonomial{coefficient,symbol}`。
函数面另判：**6 个在声明 crate 内确有同名 `pub fn` 且可从 crate 根访问**
（`ospf-rust-multiarray` 的 `matmul`/`dot`/`trace`，`ospf-rust-math` 的 `is_prime`/`normalize`/
`evaluate_boolean`，逐条证据见 `logs/p6/area-screening/fn-reachability.json`）。

这 7 个一致项全是叶子类型，且按 `logs/p3/budget-reachability-audit/AUDIT.md` 的判据
（出厂完整调用成本需 ≥ 约 1 µs 才可能过 1.15），构造一个叶子 dataclass/枚举的成本远低于该线，
因此“名称+字段一致”并不构成可委托结论。字段差异样本：`Bound` Python
`[value, bound_type]` vs 上游 `[value, interval]`；`Constraint` 的同名类型只在
`ospf-rust-core`（不是 bpp1d 声明的上游）。已单独深查的 gantt 区域给出更强版本（RG-024）：
同名也是不同层次的建模。

这 6 个函数候选是 RG-025 里唯一**不需要授权**就能继续核对的部分。2026-10-31 已把
`parameter-and-return-type-parity-verification` 从这 6 条合同全部移除，审计结论不是“可机械委托”：
`matmul`/`dot`/`trace` 在秩域、舍入和预算上不满足，转 RG-026；`is_prime` 的任意精度域与
`usize`/`u64` 入口不一致，转 RG-009；`normalize` 是多项式/不等式 `Normalize` trait 而非 Python
表达式树常量折叠，`evaluate_boolean` 是三值 AST 求值而非任意 Python `Expression` + 字典的
`bool()` 协议，两者转 RG-027。后续单独审计的甘特 1 条和绑定适配器 7 条也已完成调用形态、
参数、返回、生命周期和载荷核对，结论转 RG-028；全局
`parameter-and-return-type-parity-verification` 待办归零，但这 8 条仍不是可机械委托或已切换。

除此之外，要求的处置只有三条，且全部需要明确授权：① 上游按 Python 公开形状提供 API，或给出可核对的
名称/字段映射表；② 用户确认把 Python 公开面重构到上游形状（公开 API 变更，必须同步真实调用方、
类型注解与全部下游）；③ 用户确认把这些能力登记为“合理保留的 Python 集成”并把相应区域的
disposition 从 `rust` 改掉。禁止在绑定层另写等价模型（第二套内核），也禁止把别的 crate 的
同名类型当作固定对手建立委托。

除上述 6 个函数的后续审计外，本缺口只做名称、字段名集合与函数名级核对：未比较其余能力的字段类型、
参数/返回类型、语义、行为、异常与协议，未测成本或资源包络，未做 wheel/sdist 与 Linux、Gurobi 11/12；
上游解析仍是该 revision 上的正则源码级，
未覆盖 `pub(crate)`、宏生成类型、`where` 子句形态与 trait 方法；函数面已覆盖 `pub fn`（自由函数优先）
与 `pub use`（含 `*` glob）可达性，但 impl 方法只标注宿主类型。首版（用 `rg` 扫工作区且未解析函数面，
导致 51 个函数被误判 `absent`）的完整输出保留在 `logs/p6/area-screening/v1-working-tree/`，逐能力对比
见 `diff-v1-v2.json`：只有这 51 项判定变化，其余 689 项在工作区与固定 revision 上完全一致。

## RG-024：甘特调度（P6）上游公开面的词表与数据形态与本区域 210 个 Python 能力不一致

状态：未解决；阻止 `ospf_python.framework.gantt_scheduling` 的 **210** 个顶层公开能力
（199 dataclass、5 普通类、3 枚举、3 函数，分布在 138 个模块）委托固定 revision 的上游实现。
范围与逐能力证据见 [甘特区域能力合同](gantt-contract.md)。

实测分布（`logs/p6/gantt-inventory/mapping.json`，固定 revision
`119854756a0aeb66d2998055f96fa7175c7bfb37` 的 `ospf-rust-framework-gantt-scheduling`，
该 crate 有 283 个公开类型、全工作区 3418 个）：

- `absent` **175**：本区域 crate 无同名公开类型；其中 15 个与任何公开类型零词元重叠，
  135 个词元重叠 0.1–0.59，25 个 ≥0.6（22 struct、3 trait），而这 25 个里只有 1 个共享
  ≥50% 字段名，且那个是 Python 侧只有 `name` 一个字段的退化匹配。
- `name-only-outside-area-crate` **21**：同名类型只出现在别的 crate（`ospf-rust-example` 9 个，
  以及 `bpp3d`/`bpp2d`/`csp2d`/`base`/`framework` 里的 `Capacity`/`Load`/`Assignment`/`Task`
  等通用名），不是本区域声明的上游。
- `name-match-fields-differ` **10**、`name-match-shape-uncompared` **4**、
  `name-match-fields-agree` **0**：**没有任何一个能力在名称与字段集合上对上**。

形态差异是层次性的，不是命名偏好：`TaskSolution` Python 是单任务一行
`[task_key, start_time, end_time, resource_key, cost]`，上游同名 struct 是整解的
`[assigned_tasks, canceled_tasks]`；`ResourceCapacity` Python 是用量快照
`[resource_key, time_window_start, time_window_end, max_capacity, used_capacity]`，上游是带松弛
上下界的约束区间 `[time_range, lower_bound, upper_bound, less_slack_limit, over_slack_limit]`；
`ResourceAggregation` Python 6 个集合对上游 `[execution_usages, storage_usages,
connection_usages]`。上游整体以 `Activity*` 抽象建模（`ActivitySchedulingProblem`、
`ActivitySchedulingAggregation`、`ActivitySchedulingApplicationService` …），Python 按
`bunch_compilation`/`task_compilation`/`capacity_scheduling`/`produce`/`resource` 子领域切分。

要求的上游能力（三条路径都要明确授权，本任务不得改相邻 Rust 仓库）：① 上游提供与 Python
公开形状一致的 API，或至少给出可核对的名称/字段映射表；② 用户确认把 Python 公开面重构到
`Activity*` 模型（公开 API 变更，需同步真实调用方与类型注解）；③ 用户确认把本区域
disposition 从 `rust` 改为保留的 Python 集成并同步 api-map。在任一条落地前，禁止在绑定层
另写等价甘特领域模型（那会成为第二套内核），也禁止把示例 crate 的同名类型当固定对手建立委托。

本缺口只做名称与字段集合级核对，**不含语义、行为、数值域或求解器用法比较**，也未测成本与
资源包络；正则解析未覆盖 `pub(crate)`、别名导出、宏生成与 `where` 子句形态。

## RG-023：固定上游只提供单步混沌入口，标量/tuple 形状的多步演化必须走批量入口才可能达标

状态：未解决；阻止 `ospf_python.math.chaotic` 其余 15 个已有原生候选的公开类
（11 个三标量/二标量形状 + 4 个序列入参但返回 `tuple` 的形状）在不改变公开调用形状的前提下
委托固定上游。单步入口本身正确且逐位一致，问题只在成本结构：3 分量标量步的出厂 Python 内核
只要 624 ns，而一次 PyO3 裸调 1190 ns、加窄域守卫 1353 ns、再加 `BindingResult` 门面 3133 ns，
固定开销已数倍于内核本身。

证据：`logs/p3/chaotic-narrow-dispatch/`（`layer-cost.json` 给出各层成本，`fair-budget-v2.json`
给出同一输入对象、同一下沉方式下的完整调用比值）。权威口径为 `measure_fair_budget_v2.py`：
`BurkeShawAttractor` 等 5 个 ndarray 类在 float64 数组/list/tuple 三种风味下均为 0.704–0.810；
11 个标量形状类为 2.4–7.1×，`Lorenz84Model`（ndarray 风味 0.945，list/tuple 风味 2.6–4.5）、
`LorenzStenfloAttractor`（1.145，最差 1.789）、`LotkaVolterraSystem`（1.293）、
`NewtonLeipnikAttractor`（1.173）也全部超标。前两个版本
（`measure_dispatch_budget.py`、`measure_fair_budget.py`）因两侧输入风味不同或逐元素 `float()`
转换而给出过错误结论，不得引用。

要求的上游能力：一个**批量/多步**混沌入口，按系统名与参数一次接受初始状态与步数
（或分量拆散的标量重载），返回整条轨道，使单次 PyO3 往返摊销到 N 步上；同时保持与出厂
Python 内核逐位一致的浮点顺序。只有步数在一侧被折叠，标量与 tuple 形状才可能进入预算。
上游 Rust/WASM 仓库不在本任务可改动范围内，因此该缺口需上游排期；在此之前这 15 个类
必须留在 Python 内核，不得为了“看起来已迁移”而接受 >1 的完整调用比值。

## RG-021：固定上游筛法在进程内首次调用付与上界无关的一次性初始化成本

状态：未解决；阻止 `primes_up_to` 在最小上界档（`limit=100`）的“冷启动完整调用”达到
1.15 预算。同一入口的稳态与所有 `limit ≥ 10000` 冷启动档均已实测远快于冻结的旧 Python
筛法，因此这不是内核慢，也不是适配层开销，而是上游首次进入的一次性成本。

在排除 import 的全新进程中重复两轮（每档 5 个全新进程、逐次单独计时），当前扩展
`3469a86853febbaf207a9f6edeeac8cf39c9303f6688e376166da3d3d66153f0` 的结果：
`primes_up_to(100)` 首调用 56.55–59.5 µs，第 3–6 次稳态中位 2.9–4.6 µs；
冻结旧筛法同条件首调用 21.8–22.65 µs、稳态 8.2–9.4 µs。首调用比率 2.497–2.729，
独立 gate 为 2.807；稳态比率 0.354，`limit=10000` 首调用比率 0.103，`1e6` 为 0.052–0.056。

归因证据（`logs/p3/primes-current-revalidation/gate.json` 的 `cross_first_call_ns`
与 `target_after_cheap_primer_ns`）：

- 成本在原生侧：当前 `_native._primes_up_to` 裸首调用 59.4 µs，与公开路径首调用
  56.55–59.5 µs 同量级，Python facade 只占很小部分。
- 与请求上界无关：任何先行筛法调用——包括连素数表都不产生的退化入参 `limit=1`——
  都把目标 `100` 的首调用从 56.55–59.5 µs 降到 12.2 µs；primer 取 2 或 10000 时
  降幅相同，说明是一次性初始化而非按上界累积的工作。
- 与其他原生入口无关：先调用 `build_info` 与 `_trivalent` 之后，筛法首调用仍是 50.5 µs；
  反向也不会互相吸收。
  因此该成本特定于固定上游 `ospf_rust_math::ordinary::get_primes` 的进程级缓存路径。

允许的处置只有两种：上游提供可显式初始化/可查询的一次性成本入口（或让首次进入
不付全量分配），或经授权把冷启动预算改成“每进程一次性成本 + 稳态比率”的两段式口径。
当前按用户要求不修改相邻 Rust/WASM 仓库、不更改 revision，也不在绑定内另写第二套筛法、
不在导入期偷偷预热（那会把成本移到不可见处并改变 import 合同）。
同一缓存的 3 个独立生命周期进程还显示：2e6 后私有内存保持约 33–34 MiB，
之后 1000 次小调用不再增长且 GC 后增量为 0；但紧跟大调用的小查询中位为
10.15–19.45 µs，连续小调用稳态为 2.50–2.60 µs。该交互延迟与首次初始化分开保留，
不能据此宣称缓存生命周期已全部通过。
证据覆盖 Windows 本机、当前扩展
`3469a86853febbaf207a9f6edeeac8cf39c9303f6688e376166da3d3d66153f0`，
见 `logs/p3/primes-current-revalidation/`。

## RG-020：几何距离度量在上游被限定为 f32/f64

状态：未解决；阻止用固定版 `Point.distance_squared`、`Edge.length_squared` 或
`Manhattan.distance` 替换现有 Python 平方/曼哈顿距离的完整公开域。此项与
[RG-019](#rg-019) 无关：那两个入口的 Float64 数值语义
已实测一致，缺的是可表达性，不是精度。

固定 revision 的 `Distance` trait 声明为 `pub trait Distance<S: Field + Float>: Clone`，
`Point::distance_squared` 也位于 `impl<const D: usize, S: Field + Float>`。用只依赖
`ospf-rust-math`、`num-rational` 的编译探针（同一 pin、同一 lock、`--features typegap`）
请求 `Manhattan: Distance<BigRational>` 与 `Point2<BigRational>::distance_squared`
时，rustc 报 E0277/E0599，并明确 `Float` 仅由 `f32`/`f64` 实现、该 trait 是 sealed trait。
因此任意宽整数、`Decimal`（受上下文舍入与 Overflow 信号约束）、`Fraction`、复数、
NumPy 整数回绕/数组 dtype/shape 以及用户 `__sub__`/`__mul__`/`__abs__`/`__add__`
槽位都无法传入上游度量，只能在绑定外另写一套算法——那是本合同禁止的做法。

同一探针的 Float64 位模式对照（10 组：普通、大有限数、反向大数、极小、次正规、
负零、`inf`+`nan`、`nan`+`inf`、`inf-inf`、常规小数；debug 与 release 一致）显示
`Point.distance_squared` 等于 Python `distance_squared`、`Manhattan.distance` 等于
Python `manhattan_distance`，逐位相同，`Edge.length_squared` 也确认委托给
`Point.distance_squared`。证据、位模式与编译失败日志位于
`logs/p3/geometry-squared-manhattan-contract/`，仅覆盖 Windows 本机。

所需处置是上游提供可对开放数值协议单态化（或显式域分派并结构化拒绝）的距离度量，
使平方/曼哈顿在保持逐项回调顺序、Decimal 上下文、精确有理/整数和数组语义的同时
由 Rust 计算；或经授权把公开数值域收窄到 Float64 并同步修改合同、类型注解、调用方
与文档。当前按用户要求不修改相邻 Rust/WASM 仓库、不更改 revision，也不在绑定内
复制平方和/绝对值累加算法或静默保留旧 Python 内核作为 fallback。

## RG-019：几何欧氏距离的数值域差异

状态：未解决；阻止将固定版几何 `Euclidean`、`Point.distance`、`Edge.length`
或 `Vector.norm` 直接作为现有 Python 欧氏距离、二维边长或向量长度的完整替代。
这不意味着平方距离、曼哈顿距离或其他几何能力已被全面判定为不可迁移。

固定版 `Euclidean.distance` 将坐标差平方后累加再开方；`Point.distance` 和
`Edge.length` 调用该路径，`Vector.norm` 也先平方累加。独立 Rust 程序使用与
生产相同的固定 Git revision 和锁文件共有依赖，在 debug/release 中直接运行；
再以相同的 Float64 位模式调用当前 Python 自然入口。两个构建结果一致：

| 二维差值 / 2D difference | Python `hypot` | 固定 Rust 上述路径 |
| --- | --- | --- |
| `(3.0, 4.0)` | `5.0` | `5.0` |
| `(1e308, 1e308)` | 有限约 `1.4142e308` | `inf` |
| `(1e-200, 1e-200)` | 非零约 `1.4142e-200` | `0.0` |
| `(5e-324, 0.0)` | `5e-324` | `0.0` |
| `(inf, nan)` | `inf` | `nan` |

三维 `distance3` 对上述大值、极小值及 `inf/nan` 同样与固定上游
`Euclidean`/`Point.distance` 分类不同。证据、输入/输出位模式、lock 对照和
实际日志位于 `logs/p3/geometry-distance-contract/`。这是 Windows CPython 3.13
和本机 Rust 的有限反例，不是对跨平台逐位相等的承诺。

所需处置是提供有明确误差及非有限值政策、避免不必要中间溢出/下溢的上游距离
与范数能力，并验证点、边、向量消费者；还须处理现有 Python 开放数值协议和
二维先减、三维先转换的区别。不能将 Float64 子集、宽松容差、直接复用 Python
旧计算或绑定内自写算法作为完整替代。当前按用户要求不修改相邻 Rust/WASM
仓库、不更改 revision；此缺口不阻止其他无关迁移工作。

## RG-018：Gantt 任务列生命周期不能直接映射到模型事务

状态：未解决；阻止把固定版 `IterativeTaskCompilation` 的原始可变操作直接
暴露为安全的 Python 加删列生命周期。下述是固定版直接 Rust 见证，不涉及邻近
Rust/WASM 工作区的未提交改动，也不代表所有 Gantt 路径都有同样行为。

- `remove_columns` 只标记任务列并删除累计项，不接收或修改模型。对已注册
  的 `x == 1, min 5x`，删除后活跃列数为 0、`extract_kept` 为空，但原模型
  指纹和 `x` 的 `[0,1]` 范围均未改变；重建中间符号后，原有直接约束及目标
  仍包含 `x`。SCIP 9.2.4 和 Gurobi 10.0.1 均仍求得 `x=1`、目标 5。该见证
  使用外部直接注册的行和目标；单独重建符号并不自动重写所有已注册消费者。
- 删除未知索引会将其加入已删除集合。空上下文删除 `999` 后读取活跃列数，
  debug 发生可捕获的算术 panic，release 得到 `usize::MAX`。这不是安全的
  `Result` 边界，也不能用 release 中的数值作为真实列数。另一见证先删除尚未
  存在的索引 `0`，再正常添加首列：该列和累计项已注册，却立即被视为已删除，
  活跃数为 0、`extract_kept` 不返回该列。
- 任务编译对象注册在模型 A 后，仍可向模型 B 加列；若 A 的取消变量索引与 B
  的无关变量索引相同，累计项会把 B 的无关变量当作取消变量。不能用整数索引
  单独认证跨模型所有权。
- 无效任务索引的批次会先整批预检；但这不代表所有失败均原子。探针有意预置
  一个与后续生成 ID 冲突的符号，使加列在注册变量和第一个符号后失败；返回
  错误时活动列、变量及前一个符号仍保留，再重试同列返回空新增。该反例刻意
  制造 ID 冲突，不宣称常规输入必然触发；它证明仅检查批次输入不足以保证
  事务回滚。

相同探针对启用标准主问题的 `IterativeBunchCompilation` 做对照：注册、加列、
删列和重加后，两个后端的目标依次为 `300, 205, 9, 205, 9`；删除将旧变量
固定为零，新列取得不同变量索引。人为造成主问题行名冲突时，束的加列和删列
均回滚模型及上下文。这是有限实例，不证明全部自定义管道、扩展行、异常、
模型恢复或长期资源均已安全。探针及实际构建/运行日志位于
`logs/p2/gantt-lifecycle-probe/`。

上游或绑定所需的完整合同包括：模型所有权、未知/已退休身份检查、不可复用
的列句柄、模型和上下文的原子提交与回滚，以及变量界、受影响约束、目标、
缓存和定价证据的同步。仅在 Python 过滤未知索引、隐藏结果列或重建符号不能
证明模型已同步。绑定不得把本次束对照外推为任务路径安全；必要修复应先在
固定 Rust 能力边界落实并经授权审查 revision，或单独验证使用现有事务接口的
完整桥接。还须遵守 [RG-016](#rg-016lp) 和
[RG-017](#rg-017)。

## RG-017：重复线性项在展开时丢失系数

状态：私有 Float64 输入桥已防护；固定 Rust 的直接调用及其他建模入口尚未修复。

固定版 `linear_model_snapshot()` 按输入顺序用 Float64 合并同一变量的系数。
例如 `[1e16, 1.0, -1e16]` 的三个实际 Float64 值的精确和为 1，但展开结果为
零并移除该项。纯 Rust 原生单测直接构造上游模型复现了约束和目标两种情况。
以这些系数构造 `x <= 0`、`x <= 1`、`maximize x` 的连续模型，旧绑定下
SCIP 和 Gurobi 10 均返回 `x=1`；`solve_compiled()` 还对错误展开后的模型
签发了证书。按原始系数的精确二进制有理数计算，该解不满足原约束。这一
证书只证明已展开的错误模型，不能证明输入模型。实际运行及独立 `Fraction`
复核见 `logs/p2/duplicate-linear-terms/`。

当前 `MetaModelFloat64.add_constraints()` 和 `set_objective()` 共用的原生
输入桥在确认句柄和有限性后，用固定 `ospf-rust-math` 的有理数运算将同一
变量的项精确合并，再用现有精确 Float64 出口验证；成功时每个变量仅注册一项。
最终和可表示时即使中间 Float64 求和会溢出或舍入，也保留准确结果；严格出口
转换得到有限值但不能精确往返时返回 `DATA_LOSS`，无法得到有限值时返回
`OVERFLOW`。例如 `Float64::MAX + 1` 的精确和大于最大有限值，但转换结果仍为
有限的 `Float64::MAX`，因此返回 `DATA_LOSS`，不是 `OVERFLOW`。失败不提交批量
约束或目标，不推进代次，不使既有句柄和证书失效。单项仍原样传入；重复项的
精确零按正零发布。这是明确的私有输入合同变化，并非以浮点近似替代原式。

此保护只覆盖上述共享入口，不覆盖绕过该入口直接组装的 Rust/领域模型，也不
保证其他展开、定价、求解器容差、内存分配或长期性能安全。上游应在原始线性
项与所有展开/后端路径之间定义一致的精确求和或明确拒绝策略，测试可表示的
消去、不可表示与溢出、真实 LP 的原始可行性和证书；验证修复后再按授权审查
revision 更新，不能只修改 Python 报告或证书字段。

## RG-016：LP 对偶门禁的非零容差

状态：部分防护，尚未解决精确定价和完成证明。固定 revision 的
`require_optimal_lp_certificate_for_linear_model` 使用 `1e-7` 检查 primal
行/界、报告目标与 primal-dual 目标间隙；来源身份和模型指纹不能将此容差
门禁提升为精确零间隙证明。Python 仓库的通用证书与投影主 LP 现额外以精确
二进制有理数验证实际编译 LP 的可行性、边界支持、零间隙与拆行价格；投影
还保守检查源快照到主问题的列行/目标贡献及块定价系数。检验数精确累加后
舍入为有限 Float64，并拒绝非零结果下溢为零。不能因这些检查通过就推断
所有投影结构、列可行性或定价最优界没有误差，也不证明列生成完成。

独立探针对 `0 <= x <= 1, x >= 1, min x` 构造 `x=1` 的精确可行伪报告，
其对偶 `-(1-2^-25)` 以 `2^-25` 的非零间隙通过固定 Rust 门禁。新增成本
`1-2^-26` 的同需求列，按该对偶得到正检验数 `2^-26`，而精确最优对偶下
检验数为负 `-2^-26`，新列提供严格更优的可行目标。Python `Fraction` 独立
复核及 Rust 探针见 `logs/p2/bpp1d-pool-final-milp/`。此为合成报告反例，
不声称实际 SCIP/Gurobi 必然给出该对偶。绑定现拒绝该报告并保留原报告，
不会修改固定 Rust revision 或仅叠加 primal 复核。

进一步的固定版本投影探针使用零目标、精确零间隙的主 LP 合成报告，源行价格
和系数均为 `-(1+2^-52)`，原目标系数为 `1+2^-51`。定价的 Float64 乘减
实际返回零，而独立 `Fraction.from_float` 计算的真实系数和该列检验数均为
`-2^-104`。绑定现在拒绝发布不等于精确值的块系数；此报告同样是合成反例，
不声称真实后端必然给出该对偶。探针和见证见 `logs/p2/exact-dual-gate/`。
上述保护只处理已展开 Float64 快照上已检查的运算，后续仍需审查其余投影
结构、源列可行性、求解器定价界和性能资源，再决定可安全发布的能力范围。

局部列校验的进一步审查表明，当前私有绑定的初始加列、主问题重建和定价批次
使用固定上游的零容差选项；上游按展开快照的精确二进制值复核局部行和变量界，
并以零容差检查整数性。新增测试覆盖消去、边界、整数性、源模型修改和批次失败，跨块行
则由主问题处理。这些有限案例不证明所有投影结构。定价求解报告的候选复核
另有默认 `1e-7` 的可配置容差，不与零容差的列池校验等同。

## RG-015：BPP1D Float64 候选完整性与可行性

状态：未解决；阻止直接将固定版 BPP1D 的 `candidate_complete`、
`globally_optimal` 或浮点装箱复核提升为 Python 领域证明。此项与 RG-014
的 Gurobi 默认 gap 独立，不能靠更换求解器或仅设置零 gap 解决。

独立纯 Rust 探针直接使用固定 revision 的 `PackingContext`、默认候选策略、
`Bpp1dMilp::solve` 和 `Bpp1dColumnGeneration::solve`，不经过 Python
绑定；箱长 0.33、最大重量 0、间距 0、箱数目标、无限库存，三件不同身份且
各需求 1。输入顺序为 `a=0.1, c=0.2, b=0.03`。候选生成声称完整，却只有
6 个非空组合，遗漏 `a,b,c`；同一个组合经上游 `validate_pattern` 和
`pack` 单独验证均成功。独立地把每个实际 Float64 值转换为精确有理数后，
可以在一个箱子内放置 `a@0, b@0.1, c@0.13`，三个端点首尾精确相接，
最终端点恰好等于 Float64 的 0.33。因此一箱是严格可行且显然最优。

两条求解入口分别使用本机 SCIP 9.2.4 和 Gurobi 10.0.1，均返回两箱、
`candidate_complete=true`、`globally_optimal=true`；求解报告的最优值和界
均为 2、gap 为 0。该报告是**实际遗漏候选的模型**的报告，本例不将其归责为
求解器解错模型。仅将同一输入按 `a,b,c` 重排后，完整候选有 7 个，两后端、
两入口均返回一箱。两次正式 release 运行逐项用 Python `Fraction.from_float`
独立枚举候选并复核实际放置、物品身份与端点；日志和精确见证在
`logs/p2/bpp1d-float-contract/`。这是单机有限反例，不代表全部平台、输入或
扩展策略均有同样表现。

同一探针还发现上游严格比较不能可靠地证明输入 Float64 的精确容量：
长度容量 `1e16`、两件长度 `1e16` 和 `1` 时，候选与最终放置都被上游接受，
但把原始二进制 Float64 作为精确值复核，第二件终点超出容量整整 1。把相同
数值用于重量容量和重量时亦超重 1。两后端、两入口均返回该一箱结果。普通
小数 `0.4,0.1,0.1`、容量 `0.6` 也产生精确二进制意义下
`1/2**55` 的放置重叠与终点超出；其量级很小，是否容许必须由明确的领域容差
合同决定，不能把本例当作所有业务容差下均不可接受。精确算术只作独立事实与
反例，不自行规定最终用户的物理测量误差口径。

固定版的同一 `PackingContext` 和 `PatternAssignmentContext` 也支持
`BigRational`。独立 Rust 探针将上述 Float64 输入按其**精确二进制值**转成
有理数：六个小案例的有界候选集、精确需求行、箱数目标及实际有理数坐标均与
独立 `Fraction` 复核一致。这是值得继续研究的复用路径，而不是对任意输入、
近似测量合同、时间或资源的证明。它也不能直接替换当前完整求解入口：对于
身份顺序 `a=0.1,b=0.2,c=0.03`，精确候选含一箱组合，但固定版
`PatternAssignmentContext<f64>` 将该有效组合拒绝；其精确第三件起点
`10808639105689191/36028797018963968` 不能无损表示为 Float64。
固定版 `Bpp1dMilp`/列生成应用入口及 `compile_flt64()` 仍要求 f64，故不能
仅将精确候选塞回 Float64 主问题或静默舍入坐标。

另一个直接 Rust 探针通过上游通用 `SolverExt` 在严格转换策略下求解上述
精确主模型，不经过 Float64 BPP1D context。六个小案例分别在本机 SCIP 和
Gurobi10 执行两次；独立脚本按精确算术检查候选、实际后端矩阵、变量边界与
类型、目标、求解向量、身份、坐标、重量和需求。这个可复用方向没有设置显式
时限，没有执行 BPP1D 应用入口或列生成，也不提供一般最优性证明；默认 Gurobi
报告仍受 RG-014 限制。现已按此方向接入私有 Python 同单位有限候选整数
主模型和后端，并以 `SafeRational` 复核，保留原始报告及独立方案结果；
具体边界见 [BPP1D 合同](bpp1d-contract.md)。这不解决固定上游 Float64
入口、RG-006 的其他路径、扩展、列生成或公共领域入口。

严格转换也不意味着后端运算在有理数域内执行。另一个直接 Rust 探针使用三个
长度为 1 的同身份物品、一种长度为 1 的无限库存箱型和成本目标；成本取 Float64
`0.1` 的精确二进制值。唯一候选变量的值为 3，严格转换后的成本系数无损，但
本机 SCIP 与 Gurobi10 的报告目标均比按原始有理数重算的箱成本大 `1/2**55`。
两次 release 运行独立复核了需求行、后端矩阵、变量边界与解；该差异不是本例
可行性或最优解错误的证明。若改用精确十进制 `1/10` 的有理数成本，两个严格
转换入口均在求解前返回 `PrecisionLoss`。后续边界须区分输入转换、浮点后端
报告和原域重算结果，明确不可转换值的错误及目标/界的容差，不能把严格转换或
返回的有理数类型本身当作精确目标、界或全局最优证明。

所需处置：为长度、重量、间距及坐标定义输入单位、精确/近似和绝对/相对误差
合同；用可靠舍入界或明确受限的精确数值域保证候选搜索不遗漏合同允许的组合，
并对实际放置、需求、库存和约束进行独立复核。应直接覆盖输入重排、极端量级、
一般小数、重复件数、间距、不同单位、无解及截断；在证明成立前不能信任原始
`candidate_complete` 或包装后的 `globally_optimal`，也不能把上游 Float64
验证单独称为可靠的可行证据。当前私有精确边界只按所声明的同一单位和默认
领域规则验证方案，不覆盖混合单位或业务扩展；原始报告可保留供审计但不是
证明。当前不修改相邻 Rust/WASM 仓库或固定 pin。

## RG-014：Gurobi 默认 MIP gap 与最优性声明

状态：未解决；阻止将 Gurobi 10 的 `OPTIMAL`、`VERIFIED/EXACT` 或非负
incumbent 直接作为定价完成或源 MILP 最优的证明。该缺口也不因其他后端的
有限测试而关闭。

本机 Gurobi 10.0.1 的原生默认 `MIPGap` 为 `0.0001`；绑定使用固定 Rust
revision 的默认 `GurobiConfig`，报告中该配置为 `None`。上游的
`refine_status_with_mip_gap` 只在显式配置正 gap 且报告相对 gap 大于阈值时
降级，因此默认值没有触发这一分支。对含一个固定为 1 的连续变量和 120 个二元
变量、8 行容量约束的最大化模型，默认 Gurobi 给出目标 `1000004092`、界
`1000012696`、绝对 gap `8604`，但报告 `OPTIMAL` 和 `VERIFIED/EXACT`。
相同模型的 SCIP 9.2.4 返回 `1000006640`；两个向量均独立用原始整数系数验证
二元性、8 行约束及目标，后者是更优可行解，而不仅是非零界差的推测。

不经 Python 的固定 revision 独立 Rust release 探针用同一数据重现默认报告；
显式设置 `mip_gap=0` 的 Gurobi 运行返回 `1000006640` 和零报告 gap。探针
与生产 lock 的共有依赖版本、来源及 checksum 一致。单个零 gap 实例并不能证明
所有数值容差、绝对 gap 或其他模型的精确性，不能靠全局改默认配置宣称修复。

在同一私有列投影中，先把 Gurobi 定价得到的向量加入主问题并重求 LP，再对
同一当前请求分别定价：Gurobi 返回检验数 `0` 且报告 `OPTIMAL`、
`VERIFIED/EXACT`，SCIP 返回独立复核可行、检验数 `-2548` 的列。主问题凸性
价格为 `-1000004092`；Gurobi 报告的 `c*x` 下界为 `-1000012696`，并非可以
由该候选推导无负检验数。证据和初次假设失败均保留在
`logs/p2/column-phase-one-binding/`。这是该 Windows、本机许可证和版本下的
实测，不推广为 Gurobi 11/12 或 Linux 的结果。

当前私有界观察在同一模型上返回 Gurobi 下界 `-1000012696`、凸性价格
`-1000004092`，两者比较为 false，因此不会把该次报告看成非负；SCIP 的
独立可行候选仍为 `-2548`。这只验证此次报告界和价格的接线，比较为 false
本身不证明存在负检验数，比较为 true 也不排除后端数值误差或其他块的负列。

固定 revision 的 BPP 分区服务也有直接 Rust 复现：一个空货物、单舱位的
合法领域模型，通过分区扩展决策加入上述 120 个二元变量及容量行。相同实际
定价模型的默认 Gurobi 候选目标为 `-1000004092`、报告下界为 `-1000012696`，
SCIP 给出目标 `-1000006640` 的更优候选；两个候选均按原始整数数据、完整
源模型和领域提取规则复核。服务对这两轮定价的 trace 均给出
`pricing_proven=true`，但候选实际不是最优。此实例的 `lp_converged=false`，
源报告是 `Incumbent` 而非 `Optimal`；**没有**在该实例证明错误的收敛声明或
源最优声明。这是有意构造的领域扩展压力模型，不代表真实货运闭环，也不推广
到其他 Gurobi 版本、平台或 BPP 实例。独立探针与输出位于
`logs/p2/bpp-pricing-proof/`。

固定 revision 的 BPP1D 默认领域规则也能直接复现**错误全局最优声明**，
不使用扩展规则或 Python：12 件不同身份物品，长度依次为
`[32,32,22,29,25,43,38,42,44,22,27,47]`、每件重量 1、需求各 1；
另一件长度 101、重量 0、需求 1。廉价箱长 100、重量容量 12、成本 1、
库存不限；昂贵箱长 101、重量容量 0、成本 `1000000000`、库存 1；间距 0，
目标为成本。独立枚举全部子集，与上游生成的 191 个候选逐项一致，且上游
报告候选完整。两条实际入口 `Bpp1dMilp::solve` 和
`Bpp1dColumnGeneration::solve` 分别使用默认 Gurobi 10 三次均报告
`Optimal/Verified/Exact` 及 `globally_optimal=true`，但返回 7 个廉价箱，
目标 `1000000007`、报告下界 `1000000001`。同一最终模型的 SCIP 方案
只需 5 个廉价箱，目标 `1000000005`；两者均复核编译矩阵、完整源模型、
物品身份及件数、坐标、长度、重量、库存和整数成本。

该更优结论还可独立于 solver 状态证明：昂贵箱的重量容量为 0，只能装特殊
物品；其余 12 件总长 403，至少需要 5 个长 100 的廉价箱。一个五箱方案按
上述列表的零基序号分组为 `(0,1,10)`、`(2,3,4,9)`、`(5,6)`、`(7,8)`、
`(11)`。因此真实最优成本为 `1000000005`。同机对照显式设置 Gurobi
`mip_gap=0` 时两入口均得到该成本；这一实例不证明零 gap 消除所有数值或
绝对 gap 风险。列生成入口的 `pricing_converged=true` 是有限池 LP 的声明，
此处实证的是最终整数结果的错误 `globally_optimal`，不据此断言 LP 对偶
或所有其他领域也错误。探针、候选完整性检查、方案和退出码位于
`logs/p2/bpp1d-global-proof/`；这是合成高成本偏置实例，不是实际业务负载
或 Gurobi 11/12、Linux 的验收结果。

当前绑定保留上游完整报告、独立复核候选可行性，并明确候选与报告都不单独
认证定价完成；不篡改 `proof`、不伪造降级状态，也不将错误标签当成功门禁。
上游应区分后端真实生效的默认、显式相对及绝对 gap，保证终止原因、最佳界、
最优状态和证明可靠性一致，并覆盖偏置目标、欠精确 incumbent、取消及无界等
直接 Rust 回归；BPP 分区调用方还须避免将有 gap 的报告提升为可靠局部定价证明。
迁移 BPP1D 时不得把上游 `globally_optimal` 直接当成可信的 Python 全局最优
结论；若没有可靠证据，应保持结论范围保守，并保留原始报告供审计。定价完成
门禁还须单独解决编译目标常数、对偶/投影代次、数值容差、每个块与重复向量，
不得仅依赖状态或用一个模型的结果替代一般证明。
当前不修改相邻 Rust/WASM 仓库或固定 revision。

## RG-013：SCIP 编译 LP 的极小时限尚不能作为可靠门禁

状态：未解决。Windows 本机 SCIP 9.2.4 对 80 个连续变量、约 1200 行的固定
LP，同时在 `SCIPConfig` 和 `SolveOptions` 设置 `1 ns` 后，实际返回
`COMPLETED`、最优解和可通过的对偶证书；报告配置记为 `Some(1e-9)`，Rust
报告时间约 36 ms。独立纯 Rust release 程序使用固定 revision、相同输入与
相同时限复现；相同模型的 Gurobi 10.0.1 返回 `TIME_LIMIT`。构模、时钟分辨率
和对偶回退均可能影响这一观察，现有证据尚不足以判定根因或推广到其他时限、
平台及全部 SCIP 求解路径，也不把报告时间等同纯 backend 时间。

为避免承诺未经验证的限时行为，私有 `solve_compiled()` 对 SCIP 的所有显式
`time_limit` 暂返回 `NOT_SUPPORTED`，在拒绝之前不消耗取消句柄；不更改普通
`solve()` 的行为、不伪造超时报告。Gurobi 编译路径仍传入相同时限配置及单次
选项，1 ns 测例保留真实 `TIME_LIMIT` 报告且不产生证书；这也不是硬实时保证。
待独立区分 SCIP 的时钟精度、建模耗时、native 参数和显式对偶回退的限制与取消
传播，并覆盖多个时限/模型/平台后，才能重新开放对应入口。当前不修改 Rust
仓库或更新固定 revision。复现及真实退出码位于 `logs/p2/compiled-dual/`。

## RG-012：单次求解时限未进入后端报告配置

状态：Rust 通用合同未解决。固定 revision 的 SCIP 和 Gurobi10 单次 `time_limit`
可以传给后端，但后端报告的配置摘要和指纹来自 solver 配置，不包含仅设在
`SolveOptions` 的时限。相同模型分别设置无限制、10.25 秒和 20.5 秒时，报告的
requested/effective `time_limit` 均为 `None`，配置指纹相同。改变求解限制却得到
同一审计指纹，不能作为完整求解配置记录。独立纯 Rust release 探针不经过 PyO3
也在本机两个真实后端复现；探针与绑定的 11 个相关锁定依赖的版本、来源和
checksum 一致。节点和解数量限制是否有同样问题仍须独立复现；本项不以源码相似性
代替实测。

当前 Python 私有绑定将 `Duration` 转换后的同一时限同时传给后端配置与单次
选项，让后端执行和报告使用一致输入，不修改报告或计算自造指纹。默认无限制、
不同限制、纳秒舍入、预取消、可复用的非法输入和真实后端均有专项测试。预取消
可能只产生配置摘要而无配置指纹，该摘要不证明后端已启动。本局部接线不修复
直接使用 Rust `SolveOptions` 的调用，也不处理所有其他单次选项。

上游应为持久配置与单次覆盖定义完整的请求/实际配置语义，在最终报告、审计
指纹及取消前置路径一致记录真实限制；覆盖默认、覆盖、相同值、不同值、节点和
解数量限制及两个后端的直接 Rust 回归。修复经验证并获授权后再审查 revision
升级；当前不修改相邻 Rust/WASM 仓库或固定 pin。

## RG-011：标量混沌映射的模型与调用合同差异

状态：未解决；仅阻止相关映射未经适配地直接切换，不阻塞其他模块。固定上游
公开的同名 `GaussMap`、`ExponentialMap`、`SingerMap` 与 Python 对应类的
数学表达式不同。它们可以是合理的不同数学变体，这不是认定上游算法错误；目前
尚未找到并验证能完整表达这三个 Python 模型的其他公开标量映射。不能依据名称
直接替换、复制公式到绑定充当上游内核，或删除旧能力。

其他类也不能仅按名称转换：Python `CircleMap` 当前不取模，Rust 同名类取模，
Rust `ArnoldTongue` 的显式参数是待验证候选；Python `SinusMap` 对应正弦形式，
Rust 同名类是幂形式，`SineMap::new(1.0)` 是待验证候选。现有 Python
`ChebyshevMap` 的域外异常及 NaN 与 Rust 的零值分支不同；Python 正弦/指数
运算的异常也与 Rust `f64` 的 NaN/无穷不同。Python 的开放数值协议、子类
重写及两种迭代返回形式不能通过强制转换为 `f64` 保留。

Logistic 已增加未接入公共入口的固定上游 `f64` 候选，并明确拒绝非内置 float；
公共入口仍执行原 Python 公式。上游 `Field + Float` 接口的同类型、无错误返回
算术不直接表达 Python 的异构数值槽及其异常和引用生命周期。曾评估在原生层重演
这些槽的迁移期分支，但这仍是另一套算法，未用于候选或公共入口。开放协议、
公共 Result 转换和无旧内核切换仍需独立解决，候选不关闭本缺口。

所需处置：按 [标量合同](chaotic-scalar-contract.md) 逐类验证真实公式和参数，
明确非有限值、Result 映射、开放数值协议、默认值及迭代合同。无法由当前固定
revision 表达的模型应继续记录独立上游能力需求，必要时在获得授权后审查通用
上游支持和 revision 更新；当前仅改 Python 仓库，不改相邻 Rust/WASM 工作树
或固定 pin。有限样本对照、私有探针与同名导出都不是公共能力切换的证明。

## RG-010：动态形状分配失败的进程级风险

状态：未解决；阻止宣称公开 Shape 的完整资源与错误合同已通过。固定上游
`DynShape.len()` 首次计算长度时同时构造 offsets，动态向量分配没有可恢复失败
接口；Python 绑定的部分维度收集和稀疏 BigInt 兼容路径也有不可恢复分配。

Windows 隔离诊断中，100 万个正轴的旧扩展返回 1，而直接调用完整上游动态形状
的候选因内存分配失败终止解释器；同一受限环境的 Python 大分配能收到 `MemoryError`。
100000 轴的零、负及超机器范围稀疏元数据，旧候选和直接动态形状候选均可终止。
两类现象不能归为同一个新增回归，也不能以低内存探针证明其他平台安全。

当前源码对正的机器范围动态 `size` 完整校验后组合固定上游形状的长度，避免按
rank 分配，并保留无持久缓存；这是组合适配，不宣称完整 `DynShape.len()` 已直接
绑定。非稠密内置整数的动态 `size` 暂时复用既有的 CPython 原地乘法协议，不再
转换整个 tuple 为 Rust BigInt 向量；这是显式的迁移期兼容路径，**不是 Rust 整数
内核，也不能作为完整 Rust 切换**。Windows 受限内存测试覆盖 10 万轴的零、负数、
大整数，以及实际要求大结果分配的 `MemoryError`；只证明所测路径，不保证任意
资源条件或其他平台安全。

固定形状稀疏算术、动态 offsets/索引及其他调用仍可能进行不可恢复分配。继续审查
这些路径的可恢复分配或不增加向量的正确实现，为动态稀疏 `size` 提供可恢复的 Rust
精确整数实现后才能移除 CPython 过渡路径，并补充跨平台与长期资源验证。必要的
上游修改单独跟踪，不修改相邻 Rust/WASM 工作树或变更当前固定 revision。

公开稠密 `strides()` 现先校验全部维度，再组合固定上游 `Shape<4>.offsets()`，
不再创建随 rank 增长的 Rust 维度和 offsets 向量。Windows 低内存合同覆盖行/列
布局的结果 tuple 分配失败，以及先能分配同大小 tuple 后构造大量大整数步长的受限
场景；这些局部结果不覆盖稀疏步长、宽松索引或原生数组形状。固定的 PyO3 0.30.1
中 `PyTuple::new` 和内置整数 `into_pyobject` 在底层分配返回空指针时使用
`assume_owned`，会先报告 unraisable 错误再 panic；本次稠密步长发布显式使用可
返回错误的 C API，但不能据此宣称绑定其他路径不存在同类风险。

稠密标准索引的上一候选在 Windows Job Object 限额下复现过进程终止：预构造的
10 万轴元数据及 100 万轴公开 `flat_index` 在所测两布局都能触发。当前候选先
校验维度，按四轴调用固定上游 `Shape<4>.index_of()` 并组合结果，不再为有效标准
稠密索引创建按 rank 增长的 Rust 向量；结果整数使用可返回分配异常的 Python C
API。对应受限测试现在成功返回或产生 `MemoryError`。宽松坐标、非标准步长、
稀疏元数据及原生动态形状仍有其他不可恢复分配路径，此局部修复不关闭 RG-010。

宽松整数点积现先用受检 `i128` 逐对计算，避免对每轴创建 BigInt 向量；七个
Windows 低内存合同覆盖负坐标、越界、截短/额外坐标、非标准步长、零轴及
`2**80` 结果。超出 `i128` 或中间运算溢出时，逐对转换并执行 Rust BigInt 点积，
不再收集按 rank 增长的两条 BigInt 向量。Windows 受限合同另覆盖 10 万轴及
200/4096 位操作数、乘积溢出、累计溢出和抵消。BigInt 输入转换、算术及结果
发布仍可能因分配失败终止，且 `i128` 结果才使用可传播分配失败的 Python C API。
Windows 隔离诊断中，预构造的 8000 万位操作数在有限内存下的 BigInt 输入转换
仍会因约 10 MB 分配失败终止进程；此结果不能概括其他平台。上述合同不能关闭
RG-010 或声称任意精度点积的 OOM 安全。

锁定依赖的源码复核进一步说明了限制：CPython 3.13 非 limited-API 下，PyO3
0.30.1 的 BigInt 输入转换使用 `Vec::reserve_exact`，输出转换先生成字节向量；
num-bigint 0.4.8 的完整乘法也会分配向量。其 `BigInt::checked_add` 和
`checked_mul` 分别直接返回 `Some(self + v)` 和 `Some(self * v)`，并不检查
分配失败。仅把这两个方法替换到点积中，或只让输入缓冲使用 `try_reserve`，
都不能使整个输入、运算和输出链可恢复；具体源码摘录和哈希保存在
`logs/p3/unbounded-index-stream/bigint-allocation-source-review.txt`。

## RG-008：运行时 Scale 与 mixed-affine 精确域的十进制舍入

状态：未解决；阻止完整精确物理量切换，不表示整个迁移无后续工作可做。

两条独立纯 Rust 复现，不经过 PyO3 或 Python 门面：

1. 将 Python 原子质量单位系数 `1.6605390666e-27` 的精确 IEEE 值通过
   `BigDecimal::from_f64` 接入，再调用 `Scale::from_big_decimal(...).value()`，
   得到的 BigDecimal 不等于输入。一般的 150 位有限十进制系数也可复现。
2. 创建 affine 点单位（scale=3、offset=1）及同量纲线性差单位（scale=1），
   用 `Quantity<BigRational, Unit>::checked_add` 将 0 个点单位加 1 个差单位，
   返回的点值不等于精确 1/3。结果是先将 scale 比值在 BigDecimal 域舍入，
   再转为 BigRational，不能因最后返回有理数而称为无损。

源码定位：ScaleFactor::value 调用 ospf-rust-math ordinary::pow，整数指数 1
   路径进入已锁定 bigdecimal 0.4.11 的默认精度 powi；mixed-affine 的
`convert_linear_difference_value` 在转目标 V 之前做 BigDecimal 比例相除。
普通 `to_unit` 的逐阶段 BigRational 换算与这个 mixed-affine 分支不同，
不能把本缺口推广成所有有理数单位换算都错误。

当前 Python 仓库原生底座仍在构造 Scale 后逐值核对原系数，失真返回 DATA_LOSS。
精确 mixed-affine 绑定先用固定 Rust 的 `to_unit` 将线性差转换到与点同一比例的
临时线性单位，再调用原有 checked 加减，避免原分支对不同十进制比例求商；输出
仍是上游产生的点单位，不复制单位数学或回退 Python 算术。该组合不修复上游直接
调用 `checked_add/sub` 的缺陷，也不改变 Float64 路径的运算次序。构造防护仍意味着
不支持相应高精度系数，并不是完成完整数值域的替代方案。
全部 223 预定义单位的切换门禁包含原子质量单位，相关失败不得 skip/xfail
或通过仅测试 222 个单位消除。

2026-10-28 补充边界实证：在当前基础扩展上，以不经 Decimal 上下文舍入的
重复数字 1 构造 99/100/101/115/150 位系数，分别取十进制指数
`-30/-27/0/5`。20 项中 99/100 位输入完整保留，101/115/150 位输入均被
绑定的 `DATA_LOSS` 防护拒绝。这是注册探针的结果，不表示任意超过 100 位的
十进制表示必然失真（例如尾零可不改变数值）。重新扫描全部 33 家族、223
常量，仅 `Mass.ATOMIC_MASS_UNIT` 构造失败。原 float 的精确十进制值有
115 位有效数字；改传较短 `Decimal("1.66053906660e-27")` 虽可构造，但不等于
原 float 的确切值，不能作为兼容修复。可重跑脚本及逐项输出保存于
`logs/p3/quantity-scale-precision-boundary/`，原有 223 常量转换门禁保持不变。

已复核锁定依赖 `bigdecimal 0.4.11` 的 `pow_u64_with_context`：即使指数为
1，也调用 `ctx.round_decimal_ref`；`BigDecimal::powi` 使用默认 Context。
固定上游 `Scale::from_big_decimal` 的指数 1 经 `ScaleFactor::value` 进入
此路径。`Scale` 的因子及 OnceLock 缓存均为私有字段；公开十进制/有理数
底数构造最终仍经 `ordinary::pow`，不能仅换构造器就视为无损。当前不引入
绑定本地系数分解算法或私有字段注入来规避上游合同。

2026-10-31 对固定 revision 的公开 API 审计补充：`Scale::from_base_exponent`
只把输入写成单元素私有 `scales`；`from_int`、`from_f64`、
`from_big_decimal` 都汇入该构造器。`ScaleFactor::value` 对 `Float` 调用
`ordinary::pow`，对 `Rational` 先把分子/分母分别转为 BigDecimal 相除再调用
同一幂函数。锁定 `bigdecimal 0.4.11` 的 `powi` 使用默认 100 位 Context，
且 `pow_u64_with_context` 在指数为 1 时仍执行
`round_decimal_ref`。`Scale::pow(1)` 又从 `value()` 经
`from_big_decimal` 重建单因子 Scale；JSON 十进制值恢复同样无法保留原因子分解。
因此固定 revision 不存在可由绑定层使用的公开无损 Scale 构造路径，“预先拆成
两个可精确表示因子”“换用 `Scale::pow(1)`”或“恢复原十进制文本”都不是有效修复。
证据和逐行源码/blobs 见
`logs/p3/quantity-scale-precision-boundary/public-api-audit-20261031.md`。

2026-10-29 隔离探针进一步发现：特定原子质量二进制系数可以拆成两个均可精确
表示的上游 Scale 因子，乘积值虽正确，但对该组合执行上游 `Scale::pow(1)` 后
再次失真；对最小正 Float64 次正规数，同样形式的因子自身已超过该精度限制。
单位 JSON 只保存十进制值并在恢复时重新构造 Scale，因此该特例也不足以保证
常规运算或快照往返。探针不改变构造代码、八项原子质量红灯或上游修复要求。

上游修复要求：单位比例的指数 1 身份保持全部有效位；其他幂的精度策略应明确，
不使用隐式固定精度破坏精确单位规则；mixed-affine 的系数比应在目标数值域内
计算，精确域不提前作十进制舍入。加入原子质量/高精度系数/精确 1/3 的纯 Rust
回归，验证后再按用户授权审查 revision 更新。当前不修改相邻 Rust/WASM 仓库，
不改 pin、不设置全局 BigDecimal 精度或引入私有字段绕过来假装修复。

## RG-001：线性目标常数丢失

状态：未解决；阻止完整目标语义切换。不得把拒绝非零常数当作最终兼容方案。

最小合同：创建连续变量 `0 <= x <= 2`，设置 `maximize x + 5`，统一报告应给出解 `x=2`、目标值 7，并使目标界、gap、指纹、审计和序列化口径一致。

当前源码与真实 SCIP 行为：

- `MetaModel::set_linear_objective_input` 接受有 `constant_term` 的输入。
- `LinearTriadModel` 只保存 `c` 和方向，不包含目标常数。
- Rust SCIP 统一报告给出目标值 2，typed objective 和 objectiveValue 均未保留常数，bestBound 也是 2。
- 原型中的两变量 LP（常数 5）与 MILP（常数 7）同样漏掉常数，不能仅修正 Python 便捷字段。

当前绑定防护：`set_objective` 对非零常数返回 `NOT_SUPPORTED`，保持先前目标不变；默认 0 不受影响。Python 不维护常数副本、不补算报告、不静默丢弃。

上游修复要求：在 Rust 模型展平、backend 目标 offset、SolveReport、best bound/gap、审计/指纹、模型变换和序列化之间定义一致的常数合同，增加 Rust 回归；验证后更新绑定固定 revision，重新启用非零常数并以 Python 真实后端测试验收。禁止只调整报告单个字段。

## RG-002：SCIP 遥测/取消事件处理器在求解后仍被保留

状态：未解决；阻止宣称 SCIP 回调的底层资源生命周期全部验收。绑定已解除 Python 回调引用，但未修复底层观察者保留。

最小合同：遥测回调捕获一个 `Arc<()>`，只保留对应 `Weak` 用于观测；创建 solver 和模型、真实求解，然后销毁 solver 与模型。所有使用该回调的求解对象释放后，`Weak::strong_count()` 应为 0。

固定 revision 在 Windows SCIP 9.2.4 的纯 Rust 探针中得到 1；相同流程 Gurobi 10 得到 0。不经过 PyO3 或 Python 门面也可复现，因此不能归因于 Python GC。此证据只定位到 Rust/SCIP 集成及其依赖路径，尚未确定具体负责释放的组件。

2026-11-01 的跨进程定量对照进一步收窄了触发条件。每个 solver/mode 在独立
Windows 子进程中执行 4 次预热和 16 批 × 8 次真实 solve；SCIP 无回调时两轮私有
内存增长分别为 `0 B` 和 `192,512 B`，启用回调时分别为
`325,210,112 B` 和 `324,403,200 B`，线程数均保持 4，Python callback weakref
均在每次 solve 后释放。Gurobi 10 的有/无回调两轮均在既有 `4 MiB` 门槛内。
最终全模式运行中，仅传取消句柄、不传 Python 回调的 SCIP 增长
`324,214,784 B`；回调与取消同时启用的增长为 `324,464,640 B`，没有叠加。
因此固定 revision 在任一
telemetry/取消运行时安装的上游 SCIP 事件处理器都会被保留，不能归因于模型创建、
Python callable 引用或某个单独 Python 回调路径。证据见
`logs/p2/cross-process-sustained-20261101/FINDINGS.md`；该证据仍只覆盖
Windows/CPython 3.13、本机后端和 132 次串行子进程运行。

当前绑定防护：每次求解的 `CallbackLease` 在成功或失败退出时，持 GIL 显式取出并释放 Python 回调；后端保留的观察者不再持有用户 Python callable。弱引用合同测试验证求解后 callable 可回收。此措施不证明桥接结构、底层事件处理器或 SCIP 原生资源均已释放。

上游修复要求：定位 SCIP 事件处理器 userdata/遥测闭包的分配与释放路径，在正常终态、取消及回调失败路径均释放捕获资源；增加纯 Rust 弱引用回归与重复求解压力验证。修复必要时涉及依赖库；验证通用修复并更新绑定固定 revision 后，重新执行 Python 生命周期与发行物验收。

## RG-003：精确有理数点积的原生计算成本

状态：性能缺口未解决；不表示数值结果错误。当前不能将批量归约的正确性通过等同于公共精确数值替换的性能验收。

复现合同：使用固定 seed 20261029，三档 `(元素数, 整数位宽)` 为 `(32,32)`、`(256,128)`、`(2048,256)`；左右分母分别为 17/19，分子为确定性有符号/正整数。分别测已有值点积及包含创建的完整流程，以 Fraction 核对精确结果，不把输入准备时间混入已有值点积。

在同机两轮基准中，批量路径优于逐项 Python/FFI 调用，但中大点积和包含创建的流程仍慢于迁移前冻结的公共 Python Rational，而非后续接通的源码候选。使用完全相同整数数据、不经过 PyO3 的 release Rust 探针重现同量级点积成本，乘法与加法阶段均有贡献；将累加改为 owned `AddAssign` 未带来实质改善，因此未把这种无效改写作为优化提交。

此证据将问题范围缩至固定 Rust 数值类型/运算路径及其依赖，不单独证明某条 OSPF trait 或某个依赖函数是缺陷。不能在绑定中复制 Python 数学算法来获得表面上的性能通过，也不能回退 Python 内核、缩窄整数精度或跳过规范化。

后续以公共完整调用同 seed/规模/整数对的阶段探针区分了整数对复制、规范化、直接 gcd、整数乘积和 OSPF 运算。计时二进制不链接分配计数器；独立插桩程序只报告分配请求，结果由 Fraction/math.gcd 核对。六个关键数值依赖的版本、Git 来源和 feature 与生产构建逐项匹配。注册的大小分子与小分母数据上，主要成本已定位到 BigInt gcd 调用（包含其内部复制、位操作与分配），不能继续仅用 Python/FFI 或分配次数解释。此为阶段计时及请求计数，不是独占 CPU 火焰图、峰值内存验收或任意数据域的性能结论。

固定依赖的 BigInt gcd 委托 BigUint 的 Stein 路径；Ratio 的乘法先做交叉 gcd，再经 Ratio::new 规范化，创建/加法/除法等也会进入相应规范化路径。优化应审查不均衡整数位宽下的 gcd、约分与临时分配，而不是在 Python 仓库复制一套替代算法。规范结果再次求 gcd 的诊断输出为 1，不构成任意 raw ratio 都已规范的证明；历史字段或显式 new_raw 输入仍可能未约分，不可仅凭正分母删除结果校验或发布虚假构造证明。

比较与取负须分开处理：无 FFI 的比较与旧完整调用接近，并不表示当前公共比较已满足预算。当前公共取负序列仍含 DTO 原始字段的规范复验；已证实规范的常驻 Rust 值只做 NegRef 是另一条更便宜的诊断路径，不能把复验成本全部归因于 NegRef 或将该诊断直接重导为公共实现。完整 Rust 权威值/字段恢复/继承与构造合同若调整，须单独原子设计和验收，不增加持久数值镜像或私有 batch 来抵销单项失败。当前调用序列的纯 Rust 耗时也不是所有可能绑定设计的普遍下界。

后续要求：针对上述路径做更精细的 CPU 定位与不同分母/位宽的通用验证；必要的通用优化先在上游/依赖中验证后再审查固定 revision 的升级。目前按用户要求不修改相邻 Rust 仓库、不切换到其 WASM 工作树。任何优化须保持任意精度、规范化、精确序列化和错误合同；按原数据、多个规模复测单项/批量/完整流程，再审查公共替换预算。局部微基准不能代替真实领域端到端预算，注册数据的阶段定位也不表示整个迁移被阻塞。

## RG-004：mapped view 的占位符轴重排未用于元素遍历

状态：未解决；阻止直接把固定上游 mapped view 作为任意轴排列/完整公开映射视图的实现。

最小合同：行存储 `(2,3)` 数组 `[1,2,3,4,5,6]`，使用
`MultiArrayView::new_by_map` 交换两轴后，shape 应为 `(3,2)`，行访问序列应为
`[1,4,2,5,3,6]`。独立纯 Rust release 探针得到正确 shape，但实际序列仍为
`[1,2,3,4,5,6]`，不经过 Python/PyO3 也能复现。

源码检查：`calculate_view_shape` 处理 PlaceHolder 的轴位置，但
`map_to_iterator_vector` 把各 Map 转成原轴完整范围，未把占位符排列用于
`DummyAccessIterator` 的推进。现有 `test_view_map_transpose` 仅检查 shape，
没有检查元素或坐标。证据定位到该固定 revision 的映射迭代路径，不表示矩形 dummy view
或所有访问顺序都有同一缺陷。

当前绑定边界：私有 `transpose()` 只支持反转全部轴；反转维度同时翻转 storage order，
由上游 Shape/builder 接管不变的物理槽位序列，避免使用有缺陷的 mapped-view iterator。
此操作创建独立容器，保持对象身份，不是任意 permutation 或共享转置视图。
矩形 view 先按自身 storage order 通过已验收的 dummy view 取得快照再执行同样操作。
Python 不实现坐标重排引擎，不以错误遍历结果建立兼容合同。

上游修复要求：统一 mapped shape、坐标寻址和迭代的占位符排列，覆盖非对称轴、
行列布局/访问顺序、固定/范围/重排组合与嵌套视图；增加逐元素 Rust 回归。
当前只登记外部前置，不修改相邻 Rust 仓库、不更新固定 revision。

## RG-005：固定版 FastSum 轴归约成本

状态：本地性能前置未解决；不是数值结果错误，也不是整个迁移目标被阻塞。
完整公共合同见 [fast_sum 替换合同](fast-sum-contract.md)。

复现合同：Float64 物理输入 `((index * 17 % 101) - 50) / 8`，二维形状
`(8,8)`、`(100,100)`、`(1000,1000)`，行/列存储，分别全量和轴 0/1 求和。
该二进制分数数据可精确对照，不用浮点容差掩盖轴/布局错误。
独立逻辑布局的 NumPy sum 为 oracle，不能用已知忽略列布局的旧公共输出作 oracle。

纯 Rust release 探针使用固定 Git revision，分别实例化 DynShape、Shape<2> 和
Shape<2,RowMajor/ColumnMajor>，所有归约均调用上游 FastSum，不自写求和循环。
已有数组归约与 clone 后归约分开计时；后者也不包含 Python 校验/FFI/输出转换，
不是真实绑定的端到端性能。测试另验证物理次序舍入、Wrapping 整数和空/标量边界。

本地九轮交替测量中，中大输入轴归约的原生计算已明显慢于旧行布局 NumPy 操作；
静态 rank/布局特化没有消除差距。此证据足以拒绝“直接绑定即已通过性能验收”的结论，
但不能据此断言完整领域流程必然超过 15% 预算；还没有完整候选绑定或固定 runner 证据。
不把小输入优势、solver 占比或私有接口正确性当作公共切换预算通过。

后续要求：对固定版的坐标解码、投影寻址、除法、边界检查和布局特化进行原生 profiling，
先定位而非假定某一依赖有缺陷。任何通用优化应在上游独立验证后审查 revision 升级；
按用户要求当前不修改相邻 Rust 工作区、不更新 pin。若现有 revision 的合法边界优化
能改善，也必须复测完整绑定和领域预算，不在绑定另建第二套数学算法。
精度/累加顺序、object 零元和全部数值域是独立门槛，性能优化不能以降级这些合同换取。

## RG-006：num-rational 递归顺序比较可耗尽进程栈

状态：Python 绑定现有精确比较入口已加入原生非递归适配，并为 owner 线程显式
指定栈大小；固定依赖的通用 Ratio Ord 未修改，已测见证以外的上游比较不能据此
视为已经防护。

固定 Cargo.lock 的 num-rational 0.4.2 为 Ratio Ord 递归比较连分数余项。
取相邻 Fibonacci 数 F(n)、F(n+1)、F(n+2)，比较
`F(n)/F(n+1)` 与 `F(n+1)/F(n+2)`，可产生任意长的合法比较链。
Windows CPython3.13 原始公共候选的独立进程在n=8192构造成功后比较时退出
0xC00000FD（栈溢出），128/1024/4096正常；不能以 Python 异常或 panic 捕获恢复，
也不能通过缩窄任意精度域或跳过输入宣称解决。

绑定防护只在 Python 仓库 native/ 实施：已知正分母的 BigRational 输入，共享一个
常栈深比较适配，调用固定 OSPF BigInt MulRef 形成精确交叉乘积，再用 BigInt Ord。
不修改上游 checkout、Cargo revision/依赖、不添加 Python 比较 fallback。
公共顺序、私有 Rational.compare/相等和精确 float 往返检查都使用这一适配。
乘积可能分配与输入位数相应的内存，不等于常内存或资源沙箱。

回归必须在独立解释器检查真实退出码，覆盖8192/8193/16384深度、正负与相等、
公共全部顺序、私有比较和float精度政策；父/子扩展路径一致，Fraction独立差分。
Rust单测直接覆盖16384深度的共享适配。纯上游通用比较的后续修复须单独验证，
当前按用户要求不修改相邻Rust/WASM工作区或更新pin。

上游证书门禁会调用递归 Ord，因此绑定把 owner 线程栈显式固定为 8 MiB
（`native/src/owner.rs`）：未指定栈大小时 Rust 采用宿主
`RUST_MIN_STACK`，宿主把它设小会让整个进程在本绑定可达的输入上中止而不是返回
`Failed`。两个 Float64 精确值相乘的分母可达 `2^2148`；以
`floor(phi*2^2148)` 的奇数分子构造的见证达到 1547 帧，实测 release 需
>512 KiB、debug 需 >1 MiB，默认 2 MiB 在 4608 帧存活、5120 帧溢出。该见证
不是已证明的最深递归，见证、退出码与阈值扫描见 `logs/p2/recursive-ord-probe/`。

当前绑定对映射、报告、指纹和维度通过后、精确间隙非零且其余固定上游容差
检查会通过的报告，使用非递归预筛提前拒绝。相同 1547 帧见证在隔离子进程的
512 KiB 线程栈上，修改前于绑定真实门禁中溢出，修改后返回精确间隙失败；
见 `logs/p2/exact-gate-order/`。预筛不为任何报告签发证书：零间隙、预筛不
适用或其他错误仍走完整上游门禁，投影和求解器内部也可能再次调用上游检查。
因此该改动不证明这些路径或所有 Float64 输入的栈安全，固定上游仍需修复。

上游最优对偶证书的边界项 `residual * bound` 可以包含三个 Float64 因子；
`native/src/dual.rs` 的合成报告用三个最小次正规数得到 `2^-3222` 的非零
间隙，上游容差门禁接受而绑定精确门禁拒绝。因此 2148 不是整个证书路径的
分母位宽上界。8 MiB 覆盖了上述已测见证，但尚未证明覆盖所有 Float64 输入；
也不防护任意精度用户有理数被上游 Ord 比较，不声称上游通用比较、投影完备性
或定价界已获修复或证明。此合成报告不是实际后端必然返回的报告。

## RG-007：固定版 FastSum 浮点累加政策缺口

状态：fast_sum 默认切换的数值前置未解决；不阻塞其他独立能力的固定revision迁移。
完整边界见 [累加域可行性合同](fast-sum-contract.md#accumulator-feasibility-and-unmet-gate)。

固定revision的FastSum通过T::zero和AddAssign引用按物理次序累加，没有在该trait
接口中提供NumPy式pairwise或受检补偿累加策略。Float64输入
`[1e16,1,1,1,1,1,1,-1e16]` 的原生门槛仍真实失败：0而非已测NumPy的4。
自然候选在float16/32/64及complex64/128、行/列布局和多个轴形式均出现取消失配；
不能将问题只归因于旧float出口或输入捕获。该缺口不同于RG-005的投影寻址成本。

现有固定泛型BigRational对有限浮点的精确二进制值可得到数学精确和6，分子/分母
独立对照通过；这不意味着保持NumPy的4，亦不能恢复NaN/infinity/signed-zero及
中间溢出/FPE政策。有限`[max,max,-max,-max]` 已证明普通浮点与精确累加的结果和
错误标记不同。float32加宽为float64只改善局部示例，不解决完整浮点域。两种方案
都不获准作为隐藏fallback或默认政策；精确域诊断计时不是完整绑定预算。

后续要求：将精度、dtype提升、复数/扩展精度、IEEE特殊值、错误发布与重现性合成
一个明确的完整政策，再验证所需通用Rust能力及全部自然合同/性能/发行。不能放宽
已有取消误差断言、另写绑定pairwise/Kahan内核、隐式拒绝有效域或回退NumPy求和。
按用户要求，本工作区保持固定revision和相邻Rust/WASM不变；必要的上游能力仍是
独立前置，不在本次迁移中擅自升级pin。该门槛未解决时fast_sum继续specified，
其他无此依赖的Python绑定工作继续推进。

## RG-009：普通数论函数的固定整数宽度与边界溢出

状态：未解决；阻止将普通模块的 gcd/extended_gcd/lcm/factorize 与 prime.is_prime
直接当作现有 Python 任意精度入口的完整实现。范围和有效域见
[整数数论合同](number-theory-contract.md)。这不是整个 P3 或迁移的统一阻塞。

固定 revision 的 ordinary 导出签名只接收 usize/u64/i64；extended_gcd 仅为
i64。`is_prime` 为 `fn(usize) -> bool`，另有 `is_prime_u64(u64) -> bool`；后者把
输入扩到 64 位，但仍不表示负数和任意精度整数。大整数在 num-rational 内部已使用
不代表普通扩展 GCD、素性判断或分解具有相同域。
现有 Python 能精确计算 256 位 gcd/lcm/扩展 GCD，并分解 4097 位的光滑整数；
不能通过只绑定机器字、返回 NOT_SUPPORTED 或保留旧 Python fallback 宣称替换。

独立 Rust 程序使用与生产相同的依赖、lock、固定 Git revision 和六个数学依赖
版本/feature，不加载 PyO3 模块或 Python 门面；debug 与 release 均实际执行。
以下错误即使输入仍在所选函数签名范围内也可发生：

| 输入 / Input | 数学要求 / Required | debug | release |
| --- | --- | --- | --- |
| gcd_i64(i64::MIN,0) | 2^63 | panic | -2^63 |
| extended_gcd(i64::MIN,0) | 非负 g 且满足 Bézout | panic | (-2^63,-1,0)，恒等式不成立 |
| extended_gcd(i64::MIN,-1) | g=1 且满足 Bézout | panic | panic |
| lcm_i64(i64::MAX,2) | 2^64-2 | panic | -2 |
| lcm_u64(u64::MAX,2) | 2^65-2 | panic | 2^64-2 |
| factorize_i64(i64::MIN) | 按该函数 abs 政策分解 2^63 | panic | 空列表 |

64 组有界有符号 gcd/LCM/Bézout 与 9 组零/单位/素数/光滑分解同时由独立 Python
整数核对，避免将边界缺口泛化成全部普通数论都错误。factorize_i64 的负数问题是
上游自身 abs 政策的错误，不等于批准 Python 正整数 API 接受负数的最终政策。

2026-10-31 的 `is_prime` 平价审计补充：出厂入口以 Python 精确整数比较和取模执行，
实测负数 `-5 -> False`、超出 u64 的合数 `2**64+1 -> False`；同名 Rust 入口在
`usize`/`u64` 之外没有可表达这些输入的签名。冷门路径中 `is_prime_u64` 也不能代替
任意精度实现。意外浮点 `5.0 -> True` 只记录为当前实现细节，不进入承诺整数域。

上游要求：提供受检任意精度能力或明确可审查的通用实现，零/符号/最小负数与
超机器字输出保持数学正确；扩展 gcd 规范非负 g 并验证 Bézout，LCM 不先乘溢出，
素性判断接受现有任意精度整数域，分解保留完整整数和资源合同。需要纯 Rust 回归
覆盖上述边界、大光滑值及超出 u64 的素性输入，再经
授权审查 revision。当前不修改相邻 Rust/WASM、生产 Cargo/lock 或固定 pin。
绑定不复制 Euclid/试除、不用 catch_unwind 修补生产数学、不饱和/回绕/窄化结果，
不复制素性算法，也不把拒绝全部大整数当作原任意精度能力已经有替代。

## RG-030：相对 NumPy 的对比对含 Python 回调的操作无意义

状态：口径说明，不是待修缺口。本节的用途是界定 `complete-call-performance-and-resource-budgets`
这个标签在哪些契约上**不适用**。

### 结论

对**含 Python 回调**的操作（`array_callback.map_callback`、`array_callback.reduce_callback`、
`MultiArray.map` 的单回调路径等），「相对 NumPy 的比值」不构成可用的预算判据。
理由有三层，每层都有实测：

1. **两侧都要跨越 Python 边界**。NumPy 的 `np.sum` 在 `dtype=object` 上会逐个元素调用
   Python 的 `__add__`；本项目的绑定同样要回调 Python。**两侧的 Python 边界成本是同一个量级，
   比值趋近 1 不说明任何一方的实现好坏。**

2. **回调本身的成本淹没了被测操作**。B451 的逐行追踪（`logs/p3/b451-row-trace-20261111/`）实测：
   同样一次 `reshape`，`int16` 域 5,265 ns，`quantity` 域 **112,180 ns**——**差 21 倍，
   差额全在 Python 对象上**。在这种量级差下，比值的变化反映的是「回调里做了什么」，
   而不是「绑定写得好不好」。

3. **比值对 Python 侧的进程状态敏感**。B451 实测：在 `object`/`quantity` 域之后测 `int16`，
   每次调用会多出约 2 µs 的固定开销（`int16` +1,850 ns、`float64` +1,540、`object` +2,300、
   `quantity` −700）——**增量恒定、与操作成本无关**。**这个开销是 Python 分配器的状态，
   不是 Rust 实现的属性。**

### 因此的判据

| 情形 | 是否用「相对 NumPy 的比值」 |
| --- | --- |
| 纯数值路径（`int16`/`float64`/`int64` 上的 `reshape`/`flatten`/`sum`/`transpose`） | **适用**——两侧都不跨 Python 边界 |
| **含 Python 回调**（`map`/`reduce`/自定义 `__array_function__`） | **不适用**——见上三层理由 |
| **boxed 域**（`object`/`quantity`） | **不适用**——回调成本淹没被测操作 |

### 这不等于「含回调的操作没有预算」

**它们的预算应当是绝对成本**（每次调用的纳秒数、每次调用的分配字节数），
而不是与 NumPy 的比值。`benchmarks/absolute_budget.py` 已经采用这个口径。

### 与 `threshold = 1.15` 的关系

**`family_ratio_policy.json` 的 `threshold` 保持 1.15 不变。**

**理由**：B444 实测表明，把每侧每轮的样本数从 2 提到 8 之后，76 例门禁
**全部通过、最差 1.1026**——**1.15 这个阈值本身是对的，此前的不稳定来自样本数不足
（100 ns 量级的量化误差随机落在 native 或 legacy 一侧），不是阈值定错。**

**改阈值会掩盖一个已经修好的测量问题。所以本项不改 threshold，只界定它的适用范围。**
