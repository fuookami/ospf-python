# 各区域 Python 公开能力与固定上游公开面的对应度筛查（名称、字段与函数级）

固定 Rust revision：`119854756a0aeb66d2998055f96fa7175c7bfb37`。筛查对象：所有
`disposition = rust` 的 27 个 api-map 区域中的 740 个顶层公开能力（首轮筛查时它们尚无合同）。
两轮都未改生产代码、未重建扩展、未删除任何 Python 实现；只做筛查并登记 `inventoried` 合同。

> **v2 修正（2026-10-30）**：首版有两处缺陷——① 上游面是用 `rg` 扫**工作区**得到的，而该工作区
> 带着与本项目无关的 131 项 wasm 改动；② 只解析 `pub struct/enum/trait`，**根本没解析 `pub fn`**，
> 于是 51 个函数形状的能力全被判成 `absent`（无任何函数面证据）。现改为 `git grep`/`git show` 直接读
> 固定 revision，并加上函数面与可达性核对。重跑后**逐能力对比只有 51 项判定变化，全部是函数**，
> 非函数的 689 项在固定 revision 与工作区上判定完全一致（`diff-v1-v2.json`），说明首版的类型面结论
> 没有被 wasm 改动污染。首版输出完整保留在 `v1-working-tree/` 以便复核。

## 方法（可重放）

```powershell
python logs/p6/area-screening/screen_areas.py --self-test          # 解析逻辑自检
python logs/p6/area-screening/screen_areas.py --replay             # 全部区域（固定 revision）
python logs/p6/area-screening/diff_v1_v2.py                        # 逐能力对比 v1/v2
python logs/p6/area-screening/check_fn_reachability.py             # 同名 pub fn 可达性
python logs/p6/area-screening/update_contracts.py --rewrite        # 先 dry-run
python logs/p6/area-screening/update_contracts.py --rewrite --apply
```

`--replay` 是必须的：这 740 个能力在首轮已登记合同，若仍按“未建合同”筛选会得到空集，
两轮就不可比；`--replay` 从 `v1-working-tree/mapping-*.json` 取同一批符号复放。
`--rewrite` 就地重写这些符号的合同块（而不是追加），因此合同总数保持 1189 不变。

`screen_areas.py` 对每个能力取 Python 形态（dataclass 字段名 / 枚举成员 / 类公开方法 /
函数签名，嵌套类按属性链解析），再解析该区域 api-map 里 `rust_crates` 声明的上游 crate 在
**固定 revision 上**的公开 `pub struct/enum/trait` 面（含命名域字段或枚举变体名）与
`pub fn` 面（自由函数优先于同名 impl 方法，并记录签名摘要），只比较**名称、字段名集合与
函数名**；另有全工作区名称索引用来区分"完全不存在"与"同名只存在于别的 crate"。
类型判定五档：`name-match-fields-agree` / `name-match-fields-differ` /
`name-match-shape-uncompared` / `name-only-outside-declared-crates` / `absent`（+ 零词元重叠）。
函数判定三档：`fn-name-match-in-declared-crate` / `fn-name-only-outside-declared-crates` /
`fn-absent`。函数命中再由 `check_fn_reachability.py` 核对**能否从 crate 根访问**：整条模块链
`pub mod`，或存在解析到同一模块的 `pub use`（显式列名或该模块的 `*` glob），并记录门控属性。
**不含语义、行为、字段类型、参数类型、数值域、求解器用法或成本比较。**

## 总体结果（740 个能力）

| 判定 | 数量 |
| --- | --- |
| `absent`（声明 crate 无同名公开类型） | **391** |
| `name-match-shape-uncompared` | 139 |
| `name-match-fields-differ` | 109 |
| `name-only-outside-declared-crates` | 43 |
| `fn-absent`（全工作区无同名 `pub fn`） | 42 |
| `name-match-fields-agree` | **7** |
| `fn-name-match-in-declared-crate` | **6** |
| `fn-name-only-outside-declared-crates` | 3 |

合计仍为 740。与首版的差异全部来自函数面：51 个函数能力原被误判 `absent`，现在
42 个确实无同名 `pub fn`、6 个在声明 crate 内有同名可达 `pub fn`、3 个只在别的 crate 有。

按区域（caps＝未建合同能力数，types＝该区域声明 crate 的公开类型数；
列为 agree/differ/uncompared/other-crate/absent）：

按区域（caps＝能力数，types/fns＝该区域声明 crate 在固定 revision 上的公开类型数/`pub fn` 数；
列为 agree/differ/uncompared/other-crate/absent 与 fn match/other/absent）：

| area | phase | caps | types | fns | agree | differ | uncompared | other crate | absent | fn match | fn other | fn absent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bpp3d | P6 | 102 | 296 | 347 | 0 | 17 | 36 | 8 | 41 | 0 | 0 | 0 |
| csp1d | P6 | 91 | 170 | 213 | 0 | 36 | 13 | 4 | 38 | 0 | 0 | 0 |
| symbolic-math | P3 | 91 | 1188 | 2230 | 2 | 11 | 7 | 2 | 60 | 2 | 2 | 5 |
| model-symbols | P4 | 43 | 905 | 1544 | 0 | 0 | 4 | 2 | 37 | 0 | 0 | 0 |
| models | P4 | 43 | 905 | 1544 | 0 | 8 | 7 | 3 | 25 | 0 | 0 | 0 |
| solvers | P4 | 43 | 905 | 1544 | 0 | 6 | 10 | 0 | 27 | 0 | 0 | 0 |
| algebra | P3 | 41 | 294 | 744 | 0 | 2 | 18 | 0 | 21 | 0 | 0 | 0 |
| math-basics | P3 | 40 | 294 | 744 | 1 | 0 | 0 | 2 | 13 | 1 | 1 | 22 |
| quantities | P3 | 38 | 88 | 73 | 0 | 1 | 9 | 2 | 26 | 0 | 0 | 0 |
| multiarray | P3 | 35 | 81 | 108 | 0 | 2 | 9 | 2 | 16 | 0 | 0 | 6 |
| geometry | P3 | 26 | 304 | 812 | 4 | 14 | 2 | 1 | 4 | 0 | 0 | 1 |
| remote | P7 | 26 | 336 | 571 | 0 | 1 | 8 | 1 | 16 | 0 | 0 | 0 |
| bpp1d | P6 | 24 | 66 | 46 | 0 | 2 | 0 | 4 | 18 | 0 | 0 | 0 |
| csp2d | P6 | 16 | 61 | 213 | 0 | 0 | 0 | 6 | 10 | 0 | 0 | 0 |
| bpp2d | P6 | 14 | 156 | 297 | 0 | 1 | 0 | 1 | 12 | 0 | 0 | 0 |
| framework-solver | P5 | 12 | 336 | 571 | 0 | 2 | 7 | 0 | 1 | 0 | 0 | 2 |
| math-multiarray | P3 | 12 | 374 | 843 | 0 | 0 | 3 | 0 | 0 | 3 | 0 | 6 |
| network-scheduling | P6 | 11 | 212 | 216 | 0 | 2 | 0 | 2 | 7 | 0 | 0 | 0 |
| gurobi | P4 | 9 | 905 | 1544 | 0 | 1 | 0 | 2 | 6 | 0 | 0 | 0 |
| scip | P4 | 8 | 905 | 1544 | 0 | 0 | 0 | 1 | 7 | 0 | 0 | 0 |
| tokens | P4 | 7 | 905 | 1544 | 0 | 0 | 4 | 0 | 3 | 0 | 0 | 0 |
| variables | P4 | 6 | 905 | 1544 | 0 | 2 | 1 | 0 | 3 | 0 | 0 | 0 |
| framework-model | P5 | 2 | 336 | 571 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 |

注：`model-symbols`/`models`/`solvers`/`tokens`/`variables`/`scip`/`gurobi` 共享
`ospf-rust-core`（905 个公开类型、1544 个 `pub fn`），因此它们的 absent 率反映的是"Python 核心
建模面与 core crate 的名称不对应"，不是 crate 太小。

## 六个"声明 crate 内确有同名可达 `pub fn`"的函数候选（v2 新增）

这是全部筛查里唯一**不需要用户授权就能继续推进**的一组：上游在 Python 侧声明的 crate 里
确实存在同名、可从 crate 根访问的公开函数，因此它们不属于 RG-025 所说的"词汇分裂"。

| Python 入口 | 上游 `pub fn` | 模块路径 | 可达方式 |
| --- | --- | --- | --- |
| `math.ordinary.prime.is_prime` | `pub fn is_prime(num: usize) -> bool` @ ospf-rust-math/src/ordinary/prime.rs:199 | `ospf_rust_math::ordinary::prime::is_prime` | pub-mod |
| `math.multiarray.einsum.operations.trace` | `pub fn trace<T, S>(a: &MultiArray<T, S>) -> Result<T, EinsumError>` @ ospf-rust-multiarray/src/einsum/operations.rs:202 | `ospf_rust_multiarray::einsum::operations::trace` | pub-use |
| `math.multiarray.multi_array_extensions.dot` | `pub fn dot<T, S1, S2>(a: &MultiArray<T, S1>, b: &MultiArray<T, S2>) -> Result<T, EinsumError>` @ ospf-rust-multiarray/src/einsum/operations.rs:149 | `ospf_rust_multiarray::einsum::operations::dot` | pub-use |
| `math.multiarray.multi_array_extensions.matmul` | `pub fn matmul<T, S1, S2>( a: &MultiArray<T, S1>, b: &MultiArray<T, S2>, ) -> Result<MultiArray<T, DynShape>, EinsumError>` @ ospf-rust-multiarray/src/einsum/operations.rs:35 | `ospf_rust_multiarray::einsum::operations::matmul` | pub-use |
| `math.symbol.expression.operation.evaluate_boolean.evaluate_boolean` | `pub fn evaluate_boolean( expression: &ParsedBooleanExpression, context: &impl EvaluationContext, ) -> EvaluationResult` @ ospf-rust-math/src/symbol/expression/evaluation.rs:97 | `ospf_rust_math::symbol::expression::evaluation::evaluate_boolean` | pub-use |
| `math.symbol.expression.operation.normalize.normalize` | `pub fn normalize<N: Normalize>(mut value: N) -> N` @ ospf-rust-math/src/symbol/operation/normalize.rs:41 | `ospf_rust_math::symbol::operation::normalize::normalize` | pub-use |

读法与限制：

- `matmul` / `dot` / `trace`（`ospf-rust-multiarray::einsum`，经
  `pub use operations::{contract, dot, matmul, outer, trace, transpose}` 抬升）返回
  `Result<_, EinsumError>`，与 Python 侧"公开 API 返回 Result"的合同同向。**v3 实测
  （2026-10-30）把这三条从"候选"降级为"不可委托"**并登记 RG-026：上游秩域窄于出厂入口
  （`matmul` 只收 2D×2D、`dot` 只收等长 1D、`trace` 只收方阵，而出厂入口分别还接受
  1D×1D/2D×1D、2D×2D/1D×2D、矩形）；上游位模式是朴素左结合累加（与同输入的 Python 朴素循环
  逐位相同），与 NumPy/BLAS 差 1–25 ULP；完整调用预算在 11 个自然规模里只有 `dot` 16384
  达标，而它只能靠已被否决的按尺寸分支使用。证据见 `logs/p3/einsum-parity-audit/`。
- `is_prime(num: usize) -> bool` 的 v4 平价审计已完成：出厂入口对任意精度整数做精确比较和取模，
  实测 `-5 -> False`、`2**64+1 -> False`；上游 `is_prime_u64` 也只扩到 64 位，仍不能覆盖
  负数或更宽整数。它是 RG-009 已登记的机器字宽缺口，**不是新出口**。意外输入 `5.0 -> True`
  仅记录为现状，不登记为承诺整数域。
- `evaluate_boolean` 与 `normalize` 的 v4 平价审计也已完成。前者两端分别是
  `Expression + dict[str, Any] -> bool` 与 `ParsedBooleanExpression + EvaluationContext -> Trivalent`：
  缺绑定在 Python 抛 `KeyError`，上游返回 `Unknown`，且上游值域仅为 Null/Boolean/f64/String。
  后者是通用 Python 表达式树的常量折叠，而上游自由函数是
  `normalize<N: Normalize>(N) -> N`，只覆盖 Linear/Quadratic/Canonical 及其不等式；
  上游布尔树规范化也不是同一入口。两者登记为 RG-027，不能直接委托。
- 6 条同名自由函数合同已完成 `parameter-and-return-type-parity-verification` 并移除该项：
  3 条 einsum 改挂 RG-026 与两项授权项，`is_prime` 改挂 RG-009，`normalize` 与
  `evaluate_boolean` 改挂 RG-027。它们的 `status` 仍为 `inventoried`，未宣布任何绑定或过关。
  证据见 `logs/p3/free-fn-parity-20261031/`。

## 七个"名称+字段一致"的能力

`ospf_python.math.operator.tolerance.Tolerance`（`epsilon`）、
`math.geometry.axis2.Axis2` / `axis3.Axis3` / `axis_plane3.AxisPlane3`（枚举变体
`X/Y/Z`、`XY/XZ/YZ`）、`math.geometry.circle.Circle`（`center`、`radius`）、
`math.symbol.monomial.canonical_monomial.CanonicalMonomial`（`coefficient`、`powers`）、
`math.symbol.monomial.linear_monomial.LinearMonomial`（`coefficient`、`symbol`）。

它们**全部是叶子类型**：字段名一致不等于字段类型一致，也不等于行为一致。**v3 实测
（2026-10-30，`logs/p3/fields-agree-audit/leaf-costs.json`）**把上一版的推断换成了逐入口数字：
出厂自然调用成本只有 12.1–74.3 ns（枚举成员访问 12.1–12.4 ns、`Tolerance` 48.2 ns、
`Circle` 70.8 ns、`CanonicalMonomial` 70.4–74.3 ns、`LinearMonomial` 68.4 ns），而扩展里
**最便宜的一次 PyO3 往返**（`_native._checked_nonnegative(3)`，floor2 实测 196.8 ns）已经是它们的
2.65–16.3 倍，且这个下界还不含结果对象分配与参数解析。所以 7 个一致项**全部**判为
`leaf-construction-cost-proven-unreachable`，不构成可直接委托的结论，只说明"上游确实存在同名
同形的那一小部分是可核对的"。

## 结论：按当前 revision 与当前口径，剩余能力没有"机械委托"这条路

- 740 个能力里 391 个在声明的上游 crate 中没有同名公开类型，42 个在全工作区没有同名 `pub fn`，
  另有 43 + 3 个同名只出现在别的 crate（多为通用名或示例 crate）。
- 类型侧名称对上的 156 个里 109 个字段集合不同、139 个形态不可比、只有 7 个字段名集合一致，
  而这 7 个是叶子类型且按审计判据过不了预算门槛。
- 函数侧 51 个里有 6 个在声明 crate 内确有可达同名 `pub fn`（见上一节）；其中
  `matmul`/`dot`/`trace` 经 v3 实测在秩域、舍入与预算三项上都不满足，已降级为 RG-026；
  其余 3 个经 v4 签名与语义审计也不可直接委托，分别登记为 RG-009 与 RG-027。
- 已单独深查过的 gantt 区域给出同一结论的更强版本（RG-024）：连"同一名字"都是不同层次的建模
  （`TaskSolution` Python 是单任务一行、上游是整解索引集合）。
- 因此 §11 要求的"所有仍承诺的核心能力均由 Rust 实现"在固定 revision 上不是实现工作量问题，
  而是**上游公开 API 与 Python 公开 API 的形状不一致**问题。可选路径只有三条，全部需要授权：
  ① 上游按 Python 形状提供（或映射表）；② Python 公开面重构到上游形状（公开 API 变更，
  需同步真实调用方、类型注解与全部下游）；③ 用户确认把这些能力登记为"合理保留的 Python
  集成"并同步把区域 disposition 从 `rust` 改掉。在此之前禁止在绑定层另写等价模型。

## P7 扩展：`facade` / `integration` / `review` 的 255 项

同一套筛查已推广到 18 个非 `rust` disposition 区域，共 255 个当时尚无合同的顶层能力：
facade 118、integration 44、review 93。结果仍只有名称、字段名和函数名级证据：

| 判定 | 数量 |
| --- | ---: |
| `absent` | 127 |
| `fn-absent` | 81 |
| `fn-name-only-outside-declared-crates` | 18 |
| `name-match-shape-uncompared` | 11 |
| `name-match-fields-differ` | 8 |
| `fn-name-match-in-declared-crate` | 7 |
| `name-only-outside-declared-crates` | 3 |
| `name-match-fields-agree` | 0 |

7 个函数同名项经可达性核对后**没有一个是可从 crate 根调用的模块级函数**：5 个是
`TrajectoryFiles`、`ConflictExtractionTier` 或 `IntegerDomain` 的关联方法；2 个
`quantity_snapshot.encode/decode` 位于私有内联模块 `snapshot_codec`，crate 根仅公开 CP 快照的
`to_canonical_json`/`from_canonical_json` 包装与 artifact 解码。2026-10-31 的后续审计同时检查参数、
返回、生命周期和载荷，并实际执行 Python 探针，确认它们与 Python 的数组槽访问、数量选择、数量快照
和组合/排列选择语义无关。证据见 `logs/p3/non-module-callable-parity-20261031/`，缺口登记为 RG-028。

P6 甘特的 `task_model_builder.extract_shadow_prices` 也在同一轮完成核对。Python 自由函数接收
`MetaModel`、约束系数和 `SolveValue`，返回启发式影子价格字典；固定 Rust 同名项是
`TaskColumnGenerationAlgorithm::extract_shadow_prices(&mut self, &LPResult, &HashMap<String, usize>)`，
修改算法实例并依赖 LP 对偶解。它不是模块级函数，状态所有权、输入和返回协议均不同，因此也不能按
名称机械委托。至此全局 `parameter-and-return-type-parity-verification` 待办由 8 降为 0。随后，
`public_array_access.read/write` 已确认真正使用 `_native._SharedAccess` 且有公开消费者，故前移到
`specified` 并摘除 RG-028；其余 6 条仍保持 `inventoried` 且挂 RG-028，不表示绑定、切换或验收完成。

### P7 源码接通复核：13 个共享数组适配器从 `inventoried` 前移到 `specified`

P7 的“未实现”判定是名称/字段筛查结论，不应当作实现状态。2026-10-31 对
`public_array_access`、`shared_mapping`、`shared_nested`、`shared_reduction`、
`shared_transpose`、`shared_view`、`storage_transform` 和 `coordinate_materialization`
做了逐入口源码核对：其中 12 个直接构造或调用 `_native._SharedAccess`、
`_read_shared_array`、`_map_shared_array`、`_nested_shared_array`、`_reduce_shared_array`、
坐标计划、`_SharedView` 或 `_StorageTransform`；`shared_view.external_failure` 是原生视图发布
路径上的纯 Python 异常边界。13 个入口均有实际消费者。证据见
`logs/p3/shared-array-adapter-source-20261031/`。

对应合同状态由 `inventoried` 改为 `specified`，移除
`binding-adapters-native-binding-and-facade-implementation`、
`non-rust-disposition-screening-review` 和不再适用的直接委托 pending；保留
`complete-call-performance-and-resource-budgets` 与
`linux-and-gurobi11-12-validation`。这不是 `verified`/`switched`，也不改变公共 view
materialize、reshape/flatten 等入口各自的预算结论。

### P3-T：20 个标量和三值适配器从 `inventoried` 前移到 `specified`

2026-10-31 继续核对另外 20 个 `_binding` 入口的实际源码接线：12 个初等运算符、
`integer_power.pow_int`、`logarithm.log_base`、`prime_sieve.primes_up_to`、
2 个分形迭代入口、`fractal.julia_contains_pair` 以及
`trivalent.logic/optional_bool`。前 19 个入口通过共享适配器或直接调用固定 PyO3
扩展；`julia_contains_pair` 是唯一特例，它是纯 Python 输入边界，构造 `c` 后构造
`z` 并返回 pair，不读取 `max_iterations`、不调用扩展，随后由公开 Julia contains
路径把 pair 交给 `JuliaSet.iterate`。因此该行不能冒充原生分形算法或“已原生消费
迭代上限”的证据。

所有入口均已定位到实际公开消费者；12 个初等运算符共用
`_native._elementary_operator`，整数幂、对数、素数筛和分形迭代分别使用
`_native._pow_int`、`_log_base`、`_primes_up_to`、`_fractal_escape_time`，
三值逻辑只编码 True/False/None 标签后调用 `_native._trivalent` 并恢复原枚举单例。
对应 20 条合同由 `inventoried` 前移到 `specified`，移除已完成的
`binding-adapters-native-binding-and-facade-implementation`、
`non-rust-disposition-screening-review` 与 `natural-result-and-consumer-cutover`；
保留完整调用性能/资源及 Linux/Gurobi 11/12 门槛。证据见
`logs/p3/scalar-trivalent-adapter-source-20261031/`。

全局状态变为 `inventoried=1230 / specified=196 / switched=13 / bound=5`，
`_binding` 状态为 `inventoried=71 / specified=67`；RG-028 仍为 6，
`parameter-and-return-type-parity-verification` 仍为 0。`specified` 只表示源码已接通
候选，不是 `verified`/`switched`。

### P3-U：18 个运行时、Result 与 multiarray 句柄适配器前移到 `specified`

2026-10-31 继续复核 3 个数组回调控制面、Quantity 四则/时长/单位转换、
4 个共享 Result 边界、5 个单位家族登记入口，以及 `MultiArrayIterator` 和
`MutableMultiArrayView`。3 个回调入口、4 个 Result 入口和 5 个单位登记入口是
纯 Python 控制面，不承载数组遍历、结果体系或单位算法：

- `array_callback` 的注入 operation 才拥有原生批量遍历；适配器只处理用户函数链、
  iterable 物化、Result-as-data、原异常/失败与回调序号。
- `result.invoke/invalid/unsupported` 把 PyO3 `(value, Failure)` 或边界条件映射到
  现有 sealed Result；`FailureContext` 保存原始异常、回调 Result 和位置。
- `unit_registry` 在定义时记录原类、十维指数、affine 身份、原方法/code 与句柄
  descriptor，只做静态身份门禁，不读取或缓存实例数值。

Quantity 四则、时长构造/导出和 `convert_unit_value` 分别直接进入
`_native._quantity_arithmetic`、`_quantity_duration_from`、
`_quantity_to_timedelta` 与共享的 `_convert_quantity_dispatched`。
`MultiArrayIterator` 的 next/advance/close 委托原生游标；
`MutableMultiArrayView.set_many` 委托源句柄的 `region_set_many`。这些入口均定位到
实际消费者，但不改变公共数组权威或完整 Quantity 切换状态。

18 条合同由 `inventoried` 前移到 `specified`，移除已完成的
`binding-adapters-native-binding-and-facade-implementation`、
`exact-multiarray-binding-native-binding-and-facade-implementation`、
`non-rust-disposition-screening-review` 和不再适用的直接委托 pending；保留完整调用
性能/资源及 Linux/Gurobi 11/12 门槛。状态变为
`inventoried=1212 / specified=214 / switched=13 / bound=5`，`_binding` 为
`inventoried=53 / specified=85`；RG-028 仍为 6，parity pending 仍为 0。
证据见 `logs/p3/adapter-runtime-source-20261031/`。

### P3-V：17 个 BPP1D DTO、wire 与原生列池门面前移到 `specified`

2026-10-31 继续核对 `_binding.bpp1d` 剩余的 DTO 和原生门面。16 个入口不是
Rust 同名类型，而是 Python 本地输入、注册/提取快照、编译列、列池快照、
LP/final/bounded solve 包络或回调协议：

- `_wire_reference` 与 `_wire_spec` 将 `VariableRef`、辅助变量、线性约束和
  扩展目标编码为固定原生 tuple；`_reference`、`_compiled_columns` 与
  `_pool_snapshot` 再从原生快照恢复独立 Python DTO。
- `PatternRegistration`、`PatternExtraction` 只交给用户注册/提取回调，
  不持有或修改原生模型；`PatternExtension` 的回调对通过
  `_extension_callbacks` 转换成 `_native._Bpp1dExtension`。
- `ItemSpec` 与 `BinSpec` 由 `PackingContext.create` 严格校验后，将精确
  rational handle、材料和库存编码进 `_native._create_bpp1d_context`。
- `PackingLpSolve`、`PackingFinalSolve` 与 `PackingSolve` 分别包装原始报告、
  编译列和独立复核 Result；候选完整标记不被提升为最优性证明。

`PatternPool` 是这批唯一真实原生句柄门面：`snapshot`、`add_columns`、
`remove_columns`、`solve_lp`、`solve_final_milp` 和 `close` 均委托固定版
`_native.Bpp1dPool`，Python 不实现第二套列池。它仍不等于完整列生成：可信影子
价格、定价完成、扩展生命周期、取消/时限和资源包络继续打开。

17 条合同由 `inventoried` 前移到 `specified`，移除已完成的 binding/facade 与
`non-rust-disposition-screening-review` pending；求解相关合同保留 RG-014 与
RG-015，以及完整调用性能/资源、Linux/Gurobi 11/12 门槛。全局状态变为
`inventoried=1195 / specified=231 / switched=13 / bound=5`，`_binding` 为
`inventoried=36 / specified=102`；RG-028 仍为 6，parity pending 仍为 0。
BPP1D 原生及 framework 定向测试默认和 debug 均为 **177 passed, 180 skipped**；
跳过项要求 `native_solvers` 中已编译的真实后端，本机扩展
`native_solvers=""`，因此不认证实际求解路径。迁移合同 **35 passed**，
盘点 `explicit_contracts=1444`、`unresolved_exports=0`、`issues=[]`。
证据见 `logs/p3/bpp1d-dto-source-20261031/`。

### P3-W：14 个 model DTO、求解包络与原生投影门面前移到 `specified`

2026-10-31 继续复核 `_binding.model` 的 14 个剩余入口。4 个是输入 DTO，
9 个是来自原生报告的 Python 快照或求解/定价包络，1 个是原生投影句柄门面：

- `VariableSpec`、`ConstraintSpec`、`ColumnDecisionSpec` 和 `ColumnSpec`
  分别编码到 `MetaModel.add_variables`、`add_constraints`、
  `create_projection` 和 `ColumnProjection.columns/add_columns` 的原生 tuple。
- `ProjectionMasterInfo`、`PricingInfo`、`PricingCandidate` 与
  `PricingBoundInfo` 是脱离原生句柄的历史快照；
  `CompiledSolveReport`、`ProjectionMasterSolve`、`ProjectionPricingSolve`
  和 `ProjectionIntegerSolve` 保留原始报告摘要与独立证书/候选/解 Result。
- `SolveReport` 是从固定原生 raw JSON 解析的 Python 摘要，不再是完整 Rust
  `SolveReport` 的字段平价：proof、mapping、diagnostics、provenance、statistics
  与 trace 仍保存在 `raw_json`。报告或候选通过不会被提升为全局最优或定价完成。
- `ColumnProjectionFloat64` 的列、主问题、定价请求/信息/界、LP/整数/定价求解
  和关闭全部委托 `_native.ColumnProjection`；Python 只校验 Float64 DTO 边界并
  映射 Result。

14 条合同由 `inventoried` 前移到 `specified`，移除已完成的 binding/facade 与
`non-rust-disposition-screening-review` pending；求解/定价相关合同保留
RG-014、RG-015、完整调用性能/资源和 Linux/Gurobi 11/12 门槛，
`ColumnProjectionFloat64` 另保留列生成生命周期与取消/时限门槛。全局状态变为
`inventoried=1181 / specified=245 / switched=13 / bound=5`，`_binding` 为
`inventoried=22 / specified=116`；RG-028 仍为 6，parity pending 仍为 0。
13 个 model/投影定向测试默认和 debug 均为 **86 passed, 464 skipped**；
跳过项仍由 `native_solvers=""` 的真实后端 fixture 决定。迁移合同
**35 passed**，盘点 `explicit_contracts=1444`、`unresolved_exports=0`、
`issues=[]`。证据见 `logs/p3/model-dto-source-20261031/`。

### P3-X：混沌单步与 `SolveHandle` 三个运行时门面前移到 `specified`

2026-10-31 继续处理 `_binding` 剩余的运行时入口：

- `chaotic_system.chaotic_system_step` 是固定
  `_native._chaotic_system_step` 的 Result 门面。它只接受 20 个已冻结系统名，
  参数与状态保持公共类字段顺序，并把原生 float64 单步向量恢复成 tuple。
- `chaotic_system.array_step_or_none` 是同一原生单步的窄域公开派发边界。
  只有 float64 数组或全部由有限内置 `float` 构成的 list/tuple 才进入 Rust；
  float32、整数、布尔、object、非有限值、二维容器和其他协议返回 `None`。
  当前五个公开混沌类实际消费该路径，另外十五个类仍保留 Python 分支，不能把
  这五条窄域切换写成 20 个类的完整切换。
- `control.SolveHandle` 是固定 `_native.SolveHandle` 的薄句柄门面。阶段、首次
  取消记录的不可变事实、取消/完成先后和单次 attempt 状态都由 Rust 持有；
  Python 只提供只读属性和既有 Result 映射。该句柄已进入 model、BPP1D 与
  Gantt 的求解请求。

3 条合同由 `inventoried` 前移到 `specified`，移除已完成的
`binding-adapters-native-binding-and-facade-implementation`、
`non-rust-disposition-screening-review` 和不再适用的
`natural-result-and-consumer-cutover`；混沌门面保留宽数值域和其余公开类切换
门槛，`SolveHandle` 保留真实后端取消与时限门槛，并继续保留完整调用性能/资源及
Linux/Gurobi 11/12。全局状态变为
`inventoried=1178 / specified=248 / switched=13 / bound=5`，`_binding` 为
`inventoried=19 / specified=119`；RG-028 仍为 6，parity pending 仍为 0。
5 个定向测试默认和 debug 均为 **158 passed, 168 skipped**；跳过项来自
`native_solvers=""` 的真实后端 fixture。迁移合同 **35 passed**，盘点
`explicit_contracts=1444`、`unresolved_exports=0`、`issues=[]`。
证据见 `logs/p3/runtime-chaotic-control-source-20261031/`。

### P3-Y：Gantt 14 个 DTO、求解包络与有限列桥前移到 `specified`

2026-10-31 继续处理 `_binding` 中剩余的 Gantt 合同。逐入口源码复核结果：

- `gantt_activity` 的 `Resource`、`Mode`、`Activity`、`Precedence`、`Row`
  是冻结 Python 输入 wire DTO，分别编码到固定原生活动的资源、模式、活动、
  依赖和业务行 tuple；原生边界继续负责身份、存在性和行语义校验。
- `Placement`、`Schedule` 是从原生 transport tuple 恢复的结果快照；
  `ActivitySolve` 保留原始报告摘要和独立源域复核 Result。整数纳秒端点、
  placement 顺序与原生精确分子/分母成本跨边界保留。
- `gantt_bunch` 的 `BunchSelection`、`BunchSolve`、`TaskSelection`、
  `TaskSolve` 是有限结果/求解包络，不是 Rust 同名 DTO 平价。
  `TaskSelection` 的 makespan 是源域值，报告 objective 仍是内部 ordinal rank，
  不能当作公共秒制目标。
- `solve_bunch_columns` 与 `solve_task_columns` 只处理传入的有限 legacy 列：
  快照后经 `gantt_bunch._solve_columns`、`gantt_activity.solve_activity` 进入
  `_native._solve_activity`，再独立复核覆盖、任务资源、可用窗口、优先级、
  容量和精确成本。它们不执行列生成或定价。

14 条合同由 `inventoried` 前移到 `specified`，全局状态变为
`inventoried=1164 / specified=262 / switched=13 / bound=5`，`_binding` 为
`inventoried=5 / specified=133`；RG-028 仍为 6，parity pending 仍为 0。
9 个 Gantt 定向测试文件默认和 debug 均为 **74 passed, 612 skipped**，612 个
跳过项全部是未编译的 SCIP/Gurobi10/11/12 fixture，不能计作真实后端验收；
迁移合同 **35 passed**，盘点 `explicit_contracts=1444`、
`unresolved_exports=0`、`issues=[]`。证据见
`logs/p3/gantt-dto-source-20261031/`。

公共 Gantt 服务、列生成/定价生命周期、连续时间调度、全局最优、
RG-014/RG-015、完整调用性能/资源、Linux/Gurobi 11/12 和 wheel/sdist 仍未
验收，因此 14 条都不登记 `verified` 或 `switched`。

### P3-Z：5 个 RG-028 适配器按独立合同前移到 `specified`

2026-10-31 复核最后 5 个 `_binding` `inventoried`。它们不是缺失实现，也不再
需要按同名 Rust 入口委托：

- `quantity_ordering.select` / `contains` 分别调用
  `_native._quantity_extreme` / `_native._quantity_contains`。原生边界持有
  单次流式遍历、精确 SI 与开放 key 比较、已知量纲检查、首次原对象平局和
  结构化失败传输；和上游冲突层级选择、整数域成员判断无关。
- `quantity_snapshot.encode` / `decode` 是 `ospf.quantity` schema v1 的 Python
  兼容 wire。编码先冻结单位再调用数值 adapter，使用原生 Unit/Rational
  元数据；解码拒绝重复 JSON 字段、只使用显式 adapter 并交给调用方 factory。
  它不是私有 `ConstraintProgrammingSnapshot` codec。
- `selection.select` 调用 `_native._selection`。组合/排列计划、位置深度优先
  顺序、live indexed 读取、原始叶身份、容量检查和外部异常都由固定原生层
  处理；它不是 `ConflictExtractionTier::select`。

5 条由 `inventoried` 前移到 `specified`，从这 5 条摘除 RG-028，全局状态变为
`inventoried=1159 / specified=267 / switched=13 / bound=5`；`_binding` 达到
`inventoried=0 / specified=138`，RG-028 从 6 降至 **1**，parity pending
仍为 0。7 个定向测试文件默认和 debug 均为 **3313 passed, 64 skipped**，
其中 64 个跳过项是未编译的 SCIP/Gurobi10/11/12 fixture；迁移合同
**35 passed**，盘点 `unresolved_exports=0`、`issues=[]`。证据见
`logs/p3/rg028-adapter-source-20261031/`。

这 5 条仍保留完整性能/资源、数量全单位/完整切换及 Linux/Gurobi 11/12 门槛，
不能据源码接通登记 `verified`/`switched`。当时 RG-028 只剩 Gantt
`extract_shadow_prices`，由下一工作包建立算法实例、`LPResult` 与约束索引的
所有权/生命周期桥。

### P3-AA：Gantt 真实对偶影子价格桥前移到 `specified`

2026-10-31 完成 RG-028 最后一个入口。新增 `_native._task_shadow_prices`
直接构造固定 revision 的
`TaskColumnGenerationAlgorithm<BasicTaskCompilationContext, ShadowPriceOnlySolver>`，
把真实约束对偶装入 `LPResult::new`，再调用上游
`TaskColumnGenerationAlgorithm::extract_shadow_prices`。算法内部无操作 solver
只满足类型构造，影子价格路径不会调用它；结果是从
`task_compilation_{i}` 行按 upstream `f64::EPSILON` 规则筛出的非零对偶。

Python 公开入口新增 `dual_values` 与可选 `task_count`：提供对偶时只返回真实
任务行价格；`SolverOutput.dual_values` 已接入任务应用服务，便于 solver 适配器
后续发布真实 dual。未提供对偶时仍返回旧的 0/1 紧约束标记，但文档明确它不是影子
价格，也不能用于 `verified`/`switched` 证据。

合同由 `inventoried` 前移到 `specified` 并摘除 RG-028；全局状态变为
`inventoried=1158 / specified=268 / switched=13 / bound=5`，`_binding` 仍为
`inventoried=0 / specified=138`，RG-028 与 parity pending 均为 **0**。Gantt
定向、原生桥、solver output 与迁移合同测试在默认和 debug 下均通过；证据见
`logs/p3/gantt-shadow-price-source-20261031/`。

真实 Gurobi/SCIP 对偶发布、完整消费者切换、列生成/定价生命周期、公共 Gantt
服务、完整性能/资源、Linux/Gurobi 11/12 和发行矩阵仍未完成，因此该入口不是
`verified`/`switched`。

8 个字段差异项包括 `SolveReport`（扁平快照对完整报告）、`RunningHeartBeat`（时间戳对运行时/计数）、
`Response`（HTTP 响应对成功/失败包络）、`SortBy`（单字段对排序项集合）以及
`UnsupportedPredicatePolicy`（`IGNORE/WARN/ERROR` 对 `AlwaysFalse/FailFast/ClientFilter`）等，
字段名与语义均未对齐，不能委托。逐项字段、函数签名、来源行和合同处置见
`logs/p7/nonrust-screening/FINDINGS.md` 与 `results.json`。

筛查同时修正了文档污染：crate pathspec 现在只接受 `*.rs`，`README.md` 中的示例类型不再进入
Rust 源码面。`ExResult` 的证据已从 `ospf-rust-base/README.md:53` 改为真实定义
`ospf-rust-base/src/error.rs:345`；255 项判定类别不变。初次登记时 255 条合同均为
`inventoried` 并挂 `non-rust-disposition-screening-review`；当前 138 条 `_binding`
合同均为 `specified`，各自仍保留语义、类型、成本、资源或平台验收。

## 未覆盖

- 除本页已记录的 138 个 `_binding` `specified` 合同外，未比较字段类型、语义、行为、异常与协议；
  未测任何成本或资源包络；未做 wheel/sdist、Linux 与 Gurobi 11/12。
- 上游解析仍是固定 revision 上的正则源码级：`pub(crate)`、宏生成类型、`where` 子句形态与
  trait 方法未覆盖；同名的多个类型定义取声明 crate 中先出现者。函数面已覆盖 `pub fn` 与
  `pub use`（含 `*` glob）再导出，但 `impl` 方法只标注宿主类型、未参与函数形状的判定。
- Python 侧只取顶层 `def`/`class`（含嵌套类链），未展开方法级能力清单。
- `disposition` 为 `facade`/`integration`/`review` 的 255 项已做名称级筛查，但上述语义、类型、
  行为、成本和平台项仍未覆盖。
