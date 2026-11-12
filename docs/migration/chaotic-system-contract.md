# 混沌高维系统与吸引子家族合同（20 个私有原生候选已实现，5 个公开类已在窄域派发）

固定 Rust revision：`119854756a0aeb66d2998055f96fa7175c7bfb37`。当前扩展
`3469a86853febbaf207a9f6edeeac8cf39c9303f6688e376166da3d3d66153f0`
（`native_solvers=scip,gurobi10`；上一轮的
`ddfdbd74817a9cb3dc2d0cc57c5429b744a5b69827c99865c3e216c7f986e2b8` 自本轮起重建后作废）。

范围：`ospf_python.math.chaotic` 的 88 个公共类。其中 13 个一维标量映射由
`docs/migration/chaotic-scalar-contract.md` 单独约定（仍 `specified`，等待 RG-011）；
本文件覆盖其余 **75 个二维/高维映射、吸引子与系统类**，当前分布为
**5 个 `bound`（窄域内公开类已派发）+ 15 个 `specified`（已实现私有原生候选但未派发）
+ 55 个 `inventoried`（等待 RG-022 处置）**。
派发只在可证明逐位且同形的窄域内发生，域外仍走原实现；**没有删除任何 Python 内核**。

## 方法（可重放）

1. `logs/p3/chaotic-attractor-parity/map.py`：解析两侧源码，建立类名↔Rust 结构体、
   参数名列表、参数默认值、`step` 状态维度的映射（Python 88 类 / 上游 82 系统，
   同名匹配 79）。
2. `gen_probe.py` + `probe/`：生成单 crate 刷入（`--offline --locked`，release），
   对每个同名且参数个数相同且默认值为数类的系统，用 **Python 出厂默认参数向量**
   构造上游系统，在两个非退化状态上各执行一次 `step`，按 f64 位模式打印。
   映射变体含：位置映射、步长固定在末位时的前 n−1 参数全置换（n ≤ 7）、
   以及名称别名（`dt→h`、`x0→xr`、`sigma/rho/beta→a/c/b`）推出的置换。
3. `compare.py`：用同一默认参数构造出厂 Python 类，自动适配其调用形状
   （`__call__(ndarray)` / `__call__(tuple)` / `__call__(x, y, z)` / `step(...)`），
   与上游逐位比较，并记录最大绝对/相对误差。
4. 证据：`parity.json`（逐类结论）、`map.json`、`probe-plan.json`、
   `dispositions.log`（分组清单）、`probe-build{2,3,4}.log`。
5. `logs/tmp/diff_parity_profiles.py`：同一探针按 debug（`opt-level=0`，57 秒）重新刷入后，
   逐类比对 `verdict`、三类逐位标志、最大绝对/相对误差、两侧 f64 位模式、调用形状、
   变体总数与两个 `summary`，结果 `debug_release_agree=true`（`diffs=[]`），故下表不依赖
   release 的浮点代码生成（`parity-debug.json`、`parity-release-vs-debug.json`）。
6. `logs/p3/chaotic-system-binding/`：把“默认点逐位一致”变成可绑定证据的三步——
   `disambiguate.py` 在**互不相同**的参数向量（2 组 × 4 状态）上重跑刷入，为 25 个候选
   各自解出**唯一**成立的映射（`pos`/`perm`/`alias` 的下标串相同视为同一条，
   结果无 ambiguous、无 unresolved）；`sweep.py` 用 seed 20261030 的 2000 组随机参数与
   随机状态逐位扫描；`binding_table.py` + `gen_binding.py` 只把扫描后仍干净的 20 个类
   固化为 Rust 源码。证据：`mapping.json`、`sweep.json`、`binding-report.json`、
   `generated-table.{json,txt}`。

## 判定

| disposition | 类数 | `compatibility` | 含义 |
| --- | --- | --- | --- |
| 位置映射逐位一致且随机扫描通过 | 15 | `pinned-rust-model-bit-exact-positional-candidate` | 已实现为私有原生候选，按位置绑定 |
| 显式置换后逐位一致且随机扫描通过 | 5 | `pinned-rust-model-bit-exact-permuted-candidate` | 已实现，必须固化参数置换，位置映射会得到错误模型 |
| 名称别名映射逐位一致且随机扫描通过 | 0 | `pinned-rust-model-bit-exact-alias-mapped-candidate` | 唯一的别名候选 `HindmarshRoseModel` 已被随机扫描证伪 |
| 默认点逐位一致、随机扫描证伪 | 5 | 沿用原判（未改） | 舍入级分歧 1–512 ULP，不能保证逐位一致，回 RG-022 |
| 任何映射都不一致 | 13 | `pinned-rust-model-diverges-needs-disposition` | 上游公式与出厂模型不同，需处置决定 |
| 参数个数不同 | 19 | `pinned-rust-parameter-set-differs-needs-disposition` | 两侧系数集合基数不同，不存在重命名空间 |
| 上游状态形状不可表达 | 7 | `pinned-rust-state-shape-unrepresentable` | 上游 `step` 入参不是 `Point2/3/4`（向量或其他形状） |
| 默认值非数值对象 | 3 | `pinned-rust-parity-unprobed-defaults` | 无法构造可比较实例，平价未测 |
| 上游无同名系统 | 8 | `no-pinned-rust-counterpart-needs-disposition` | 固定 crate 无同名系统可委托 |

上表的 `*-candidate` 描述固定 revision 的模型映射判定；已实现公开派发的 5 个
`bound` 合同统一使用 `public-narrow-finite-float64-dispatch-bit-exact-ndarray-shape`，
其中 `ChuaCircuit` 的 `perm01324` 继续作为实现细节记录在合同 `notes` 中。

逐位置换明细（20 个已实现候选的固化映射，见 `generated-table.txt`）：
`RucklidgeAttractor` = `perm102`、`ChuaCircuit` 与 `LorenzStenfloAttractor` = `perm01324`、
`DuffingEquation` = `perm120345`、`DequanLiAttractor` = `perm0415326`，其余 15 个为恒等位置
映射。原判里 `LorenzSystem` = `perm0213`、`GenesioTesiAttractor` = `perm2103`、
`HindmarshRoseModel` = `alias012354678`（`r↔s` 互换、`x0→xr`、`I→i`、`dt→h`）**均未进入实现**，
原因是随机扫描证伪。注意 `RosslerAttractor` 同时存在 `perm1023`，但其位置映射已逐位一致，
故归入第一类。

“任何映射都不一致”的 13 个类：`AizawaAttractor`、`CoulletAttractor`、
`DadrasAttractor`、`KickedRotator`、`LorenzMod1Attractor`、`LorenzMod2Attractor`、
`LoziMap`、`LuChenAttractor`、`SymplecticMap`、`ThomasAttractor`、
`ThomasCyclicallySymmetricAttractor`、`VanDerPolSystem`、`WimolBanlueAttractor`。
其中 `KickedRotator`、`SymplecticMap` 只有 1 个参数、`LoziMap`/`Thomas*`/`VanDerPol`/
`WimolBanlue` 只有 2 个且已穷举置换，因此它们的差异不可能由参数顺序解释；
`AizawaAttractor` 另可逐式核对：上游把 `dz` 写进第二分量、`dy` 写进第三分量，
且 `dx` 定义与出厂实现不同，属于模型级差异而不是记号差异。
最大相对误差介于 8.5e-4（`CoulletAttractor`）与 0.98（`KickedRotator`），
全部远离“只是浮点结合顺序不同”的 last-bit 级别（判定阈值 1e-13，
`last-bit-rounding-only` 计数为 0），因此这些差异是模型级而非舍入级。

## 私有原生候选（本轮已实现）

上表前 3 类里通过随机扫描的 **20 个类**已落地为**私有**通道，公开 API 一字未改：

- `native/src/chaotic_system.rs`（由 `gen_binding.py` 生成）导出
  `_native._chaotic_system_step(*, system, params, state)`，按固化映射委托固定 revision 的
  上游系统；只接受 `list`/`tuple` 里的**内置 `float`**，超过 `MAX_INPUTS = 9` 的长度或元数、
  维度不符、未知名一律返回结构化 `ILLEGAL_ARGUMENT`，不抛异常；执行前后各一次
  `py.check_signals()`，计算本身在 `py.detach()` 内。
- `ospf_python/_binding/chaotic_system.py`：`SUPPORTED_SYSTEMS`（20 个名字）与
  `chaotic_system_step(...) -> BindingResult[tuple[float, ...]]`，未知名走 `invalid()`。
- `ospf_python/_native.pyi` 增补存根；`tests/native/test_chaotic_system_binding.py` 对 20 个类
  按 seed 20261030 抽 1000 组随机参数/状态与出厂 Python 内核逐位差分（跳过两侧非有限的分量，
  每类实际比较至少 250 个分量），另测名单一致性、
  **公开类不派发**、类型域拒绝（`int`/`bool`/`np.float64`/`complex`/任意对象、`ndarray` 容器）、
  元数与未知名拒绝，以及 5 个被证伪类必须 `Failed`。
- Rust 侧 `cargo test --release` 通过 2 项（含把出厂默认参数的 f64 位模式冻结为断言）。

这 20 个类的合同状态因此从 `inventoried` 升为 `specified`，门槛
`native-binding-and-facade-implementation` 已由证据满足并换成
**`public-chaotic-class-dispatch-and-call-shapes`**：把公开类改为委托原生入口，需要同时
定下出厂的 ndarray/tuple/三标量调用形状、返回类型与 in-place 语义、开放数值协议，以及
完整调用预算——其中调用形状可原样保留（见下节探测），只有**宽数值域的收窄**仍需决策。

## 公开派发前提（参数域与返回形态探测）

`logs/p3/chaotic-public-dispatch/probe_domains.py` 把**同一批数值**以 7 种输入域分别喂给出厂
Python 类与私有原生入口（原生侧永远收到等值的内置 `float`），逐位比较并记录出厂侧的返回类型、
dtype、shape 与元素类型；另测全 NaN / 全 Inf / 全零状态与 8 种 ndarray 形状。
证据：`domain-probe.json`、`FINDINGS.md`。

| 输入域 | 逐位一致（20 个类） | 关键事实 |
| --- | --- | --- |
| `float` | 20 | 既有合同 |
| `numpy.float64` | 20 | numpy 走同一套 double 运算 |
| `int` | 20（仅位模式） | 但 16 个类的返回元素含整数（13 个全整数、3 个混合），委托后一律变 float/float64，且 >2^53 时整数算术精确、float64 会舍入 |
| `bool` | 10 | 9 个 ndarray 类 `TypeError`（numpy 布尔不支持 `-`/取负）、`FinanceAttractor` `ZeroDivisionError`；委托会静默成功，等于删掉既有报错 |
| `numpy.float32` | 0 | 出厂保持 float32 运算，尾数低位被清零 |
| `Decimal` | 0 | 十进制精确算术，7 个类直接报错 |
| `Fraction` | 0 | 有理精确算术 |

特殊状态：全零 20/20；全 NaN 16/20，4 个类只差在 **NaN 符号位**（`ChenCelikovskyAttractor`、
`Lorenz84Model`、`LorenzStenfloAttractor`、`NewtonLeipnikAttractor`）；全 Inf 19/20，
`DuffingEquation` 出厂 `ValueError: math domain error` 而原生返回 Inf/NaN。非有限输入下出厂
numpy 路径还会发 `RuntimeWarning`，原生路径不发，这本身是可观察差异。

返回形态（`float` 域）：5 个类返回 `ndarray` float64（`BurkeShawAttractor`、
`ChenCelikovskyAttractor`、`ChenLeeAttractor`、`ChenSystem`、`ChuaCircuit`）、11 个返回
`tuple<float>`、4 个返回 `tuple<float64>`（元素是 numpy 标量）。9 个 ndarray 入参类对
`(3,)`、`(3,1)` 列向量、`list`、非连续切片都能同形委托，**返回 shape 跟随输入 shape**；
`(1,3)` 行向量与多一分量的数组在 9 个类上一律报错。

因此存在一条**不需要决策**的窄派发：仅当每个分量类型恰为 `float` 或 `numpy.float64`、
且全部有限时委托原生，并按类回封装成上述公开形态，其余输入原样走现有 Python 路径。
### 已采纳的宽域政策（2026-11-11 用户裁决 A）

| 问题 | 裁决 |
| --- | --- |
| `int`/`bool`/`float32`/`Decimal`/`Fraction` 是否继续作为公开支持域 | **是，保留全宽域** |
| NaN 符号位是否必须保留 | **保留** |
| `DuffingEquation` 的 `math domain error` 是否必须保留 | **保留** |

**因此「删除 Python 内核」在本能力上不是待办项，而是被明确否决的动作。**
窄派发仍只在「每分量类型恰为 `float`/`numpy.float64` 且全部有限」时委托原生；
其余宽域输入由**保留的 Python 内核**计算——这是**声明的政策路径**，不是
`policy.implicit_legacy_fallback = False` 所禁止的隐式回退：域外输入不会「原生失败后
偷偷回落」，而是在入口处按类型判定后直接走既有实现，且该行为已由 45 项回归与 58 项
接线合同覆盖。

保留全宽域的代价（实测，见 `logs/p3/chaotic-narrow-dispatch/`）：

| 输入域 | 20 类逐位一致 | 若收窄会失去 |
| --- | --- | --- |
| `float` / `float64` | 20 / 20 | — |
| `int` | 20（仅位模式） | 16 个类返回整数元素 |
| `bool` | **10** | 9 个 ndarray 类从 `TypeError` 变成静默成功（等于删掉既有报错） |
| `float32` | **0** | 出厂保持 float32 运算，尾数低位被清零 |
| `Decimal` / `Fraction` | 0 / 0 | 精确算术 |

**「旧内核删除」这一全局清单项在本能力上因此保持开放**，且是**用户已确认的永久状态**，
不得再作为「未做的工作」计入迁移进度。

## 窄派发实现（5 个 ndarray 类已切换到原生入口）

`ospf_python/_binding/chaotic_system.py` 新增两个私有 helper，公开签名一字未改：

- `_finite_floats(values)`：`dtype` 存在且不是 `float64` 直接拒绝；用一次 `tolist()` 把容器下沉成
  内置值（**不逐元素 `float()` 转换**）；要求每个元素 `type(item) is float` 且 `math.isfinite`；
  非标量容器（列向量）在元素类型检查处被拒。
- `array_step_or_none(*, system, params, state)`：窄域内直连 `_native._chaotic_system_step`
  （**跳过 `BindingResult` 门面**，原生返回 `(values, failure)` 二元组），失败或超域返回 `None`，
  成功返回新的 `float64 (dimension,)` 数组。

`BurkeShawAttractor`、`ChenCelikovskyAttractor`、`ChenLeeAttractor`、`ChenSystem`、`ChuaCircuit`
的 `__call__` 开头接这条快路，返回 `None` 时原样继续执行既有 numpy 实现；`iterate` 逐步复用
`__call__`，因此中途溢出成 Inf/NaN 后自动回到 Python 内核。回归见
`tests/native/test_chaotic_public_dispatch.py`（45 项：3 种风味 × 300 组随机向量逐位/同 dtype/
同 shape/同容器、多步 `iterate`、宽域与超量分量回落、参数域外回落、不就地改写调用方数组），
接线合同见 `tests/native/test_chaotic_system_binding.py`（58 项）。

**预算口径教训**（`logs/p3/chaotic-narrow-dispatch/`，权威结论在 `fair-budget-v2.json`）：
`measure_dispatch_cost.py` 量的是旧胶水，`measure_dispatch_budget.py` 两侧风味不同（before 收
ndarray、candidate 收 list），`measure_fair_budget.py` 虽同输入但用逐元素 `float()` 下沉，导致
数组风味全线 1.48–2.06 失败。只有 `measure_fair_budget_v2.py`（同一输入对象、`tolist()` 一次性
下沉、不走 Result 门面）给出可信比值：**5 个类在三种风味下均为 0.704–0.810**。
其余 15 个类在同一口径下是**回归**：11 个标量形状 2.4–7.1×，4 个序列入参但返回 `tuple` 的类
1.145–4.5×，因此一律不切。代价结构（`layer-cost.json`）：3 分量标量步的 python 内核只要 624 ns，
而 guard 1353 ns + PyO3 裸调 1190 ns + Result 门面 3133 ns = 单步原生入口的固定开销远超内核本身。

### 5 个 `bound` 类的隔离发行与资源复测

`logs/p3/chaotic-bound-distribution/` 在仓库外全新 venv 中分别安装 locked wheel 和由
同一 sdist 重建的 wheel，各跑 35 个测量：5 个类的单步 1e4/1e5/1e6 次，以及
`iterate(0/1e3/1e4)`。两种安装形态共 70 行的原生结果与 Python 回落逐位一致；
wheel 扩展 SHA-256 与源码树相同
`3469a86853febbaf207a9f6edeeac8cf39c9303f6688e376166da3d3d66153f0`，sdist 重建扩展
得到独立构建哈希但行为哈希逐项相同。

固定状态重复单步的 `PrivateUsage` 增量最大为 wheel 20 480 B、sdist 36 864 B，
1e6 次调用没有随次数增长；`iterate(10 000)` 的私有增量分别为 wheel 0.29–2.13 MiB、
sdist 1.32–1.98 MiB，并返回 10 001 个状态数组，符合公开的列表返回合同而非常量内存。
`tests/native/test_chaotic_system_binding.py`、`tests/native/test_chaotic_public_dispatch.py`
和 `tests/math/chaotic` 合跑 **602 passed**；5 个热路径基准 **5 passed**。外部 SCIP/Gurobi
DLL 仍未随 wheel 打包，隔离运行依赖 `OSPF_NATIVE_DLL_DIRS`；Linux/Gurobi 11/12 未验证。

## 允许与不允许的处置

- 20 个已实现候选里，5 个 ndarray 类已在窄域切到原生入口并标 `bound`；其余 15 个的下一步也只有
  一条路：在**不改变公开签名**的前提下把公开类切到原生入口，并在同一夹具下补完整调用预算。
  在此之前它们停在 `specified`，不得标 `verified/switched`，也不得删除 Python 内核。
  `bound` 不等于可退役：宽数值域、NaN 符号位与 `DuffingEquation` 定义域报错仍待决策，
  Linux、Gurobi 11/12 矩阵也未做。
- 5 个随机扫描证伪的类**没有**登记原生候选：在绑定层重写等价模型等于第二套内核，禁止；
  保持 Python 实现并登记为“合理保留”需用户确认；把公开数值合同从“逐位一致”收窄为
  “容许 ULP 级分歧”属公开行为变更，同样需用户确认。
- 其余 50 个类的处置选项与上一节相同，仍只有改上游（本任务禁止）、用户确认的保留/退役、
  用户确认收窄公开数值合同三种。
- 本轮改了生产代码，但只改**新增**的私有原生模块与门面；未改任何公开 API、未删除 Python
  内核、未把任何类标记为 `bound/verified/switched`。

## 未覆盖

- 平价只在两个非退化状态、f64、默认参数、单步上测得；不含参数域、NaN/Inf、signed
  zero、长轨道收敛、多步 `iterate`/生成器语义、异常与协议合同。
- 5 个 `bound` 类的完整调用预算、隔离 wheel/sdist 和资源包络已补测；Linux 与
  Gurobi 11/12 矩阵仍未验证。
- 参数个数不同与状态形状不同的类，其上游 `step` 的完整签名只做了单数判定，
  逐分量语义映射仍需人工确认。
- 20 个候选的逐位证据只覆盖“内置 `float` 输入 + 单步 + 定长 list/tuple 容器”这一条通道；
  出厂公开类的 ndarray/tuple/三标量形状、数组步长与非连续内存、`np.float64` 输入、
  in-place 写回与返回值类型**均未经原生路径实现或测量**。
- 证伪样本只存在于 `sweep.json`（seed 20261030）与探针 crate，仓库内测试无法重现上游侧的
  那一半数值，因此 5 个类的 ULP 分歧是**离线证据**，不是 CI 断言。
- 派发探测每域只测 8 组随机值，未测数组写回/in-place 语义、多步 `iterate`/生成器、异常消息
  文本逐字合同，也未给出 >2^53 整数的实际分歧样本；窄派发自身的类型守卫与封装成本尚未计入
  完整调用预算。
  其中窄派发的类型守卫与封装成本**已计入**完整调用预算（`fair-budget-v2.json`，三风味
  0.704–0.810），仓库内也补了多步 `iterate` 与不就地写回的回归；仍未测的是 >2^53 整数的实际
  分歧样本、异常消息文本逐字合同、生成器语义，以及 Linux 与 Gurobi 11/12 矩阵。
