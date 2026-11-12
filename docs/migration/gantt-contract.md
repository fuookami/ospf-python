# 甘特调度（P6 / gantt）区域能力合同（210 个公开能力已完成名称与字段级盘点）

固定 Rust revision：`119854756a0aeb66d2998055f96fa7175c7bfb37`；本区域 api-map 声明的上游
crate：`ospf-rust-framework-gantt-scheduling`（该 revision 下有 **283** 个公开类型，
全工作区 3418 个）。Python 侧为 `ospf_python.framework.gantt_scheduling` 的 **210** 个顶层公开
能力（199 个 dataclass、5 个普通类、3 个枚举、3 个函数，分布在 138 个模块）。
**首轮盘点未改任何生产代码、未重建扩展、未删除任何 Python 实现**，只做盘点并登记
`inventoried` 合同。

## 方法（可重放）

```powershell
python logs/p6/gantt-inventory/inventory.py
python logs/p6/gantt-inventory/update_contracts.py          # 先 dry-run
python logs/p6/gantt-inventory/update_contracts.py --apply
```

`inventory.py` 逐能力做两件事：① 用 `dataclasses.fields`/`enum`/`inspect` 取 Python 侧形态
（字段名、枚举成员、方法名或函数签名）；② 解析固定 revision 的公开 `pub struct/enum/trait`
面（同名多处以本区域 crate 优先），取命名域字段或枚举变体名。判定只用名称与字段集合，
**不含任何语义、行为、数值域或求解器用法比较**，因此这是盘点而非平价证明。
上游只被读取，未被修改（其工作区另有 131 项与本任务无关的未提交改动）。

> **2026-10-30 修正**：首版与本文件一样只解析类型面，因此 3 个函数能力被记为"无同名对手"，
> 这是无证据的判定。现已用 `logs/p6/area-screening/fix_gantt_functions.py`（复用跨区域筛查工具
> 的固定 revision `pub fn` 面与可达性核对）重判这 3 项并就地重写它们的合同块：
> `build_triad_model` 与 `build_schedule` 在全工作区确实没有同名 `pub fn`（`fn-absent`）；
> `extract_shadow_prices` 在 `ospf-rust-framework-gantt-scheduling` 内**有同名 `pub fn`**
> （`task_column_generation.rs:215`，是 `TaskColumnGenerationAlgorithm` 的关联方法，签名为
> `(&mut self, lp_result: &LPResult, constraint_name_to_index: &HashMap<String, usize>)`，
> 模块链 `pub mod` 可达），但它是方法而非自由函数，绑定它需要先构造并持有该算法对象，
> 因此**不构成机械委托**，合同的 pending 保留 RG-024/RG-025 并新增
> `parameter-and-return-type-parity-verification`。类型侧的 207 项判定不受影响。

## 判定分布（210 个能力）

| 判定 | 数量 | 含义 |
| --- | --- | --- |
| `absent` | **175** | 本区域 crate 的 283 个公开类型里没有同名者 |
| `name-only-outside-area-crate` | **21** | 同名类型只存在于别的 crate（`ospf-rust-example` 9、`bpp3d`/`bpp2d` 的通用名 `Capacity`/`Load` 等），不能充当本区域的固定对手 |
| `name-match-fields-differ` | **10** | 本区域 crate 有同名 struct，但字段集合不同 |
| `name-match-shape-uncompared` | **4** | 同名存在但形态不可比（trait/单元结构体/Python 侧是服务类） |
| `name-match-fields-agree` | **0** | **没有任何一个能力在名称与字段集合上都对上** |

`absent` 的词表邻近度（CamelCase 词元 Jaccard，仅用于说明“上游叫什么”）：
15 个与任何公开类型**零词元重叠**、135 个 0.1–0.59、25 个 ≥0.6；这 25 个里 22 个邻近项是
struct、3 个是 trait，而其中**只有 1 个**共享 ≥50% 字段名，且那一个是 Python 侧只有一个
`name` 字段的退化匹配（此类“只有 `name` 字段”的 Python 能力共 **37** 个，字段比较对它们无
判别力）。

## 词表与数据形态鸿沟（证据样本）

上游用 `Activity*` 抽象建模同一领域（`Activity`、`ActivitySchedulingProblem`、
`ActivitySchedulingAggregation`、`ActivitySchedulingApplicationService` …），Python 侧按
子领域切分（`bunch_compilation`/`task_compilation`/`capacity_scheduling`/`produce`/`resource`）。
因此“名字近似”不等于“数据一致”：

- `TaskSolution` Python `[task_key, start_time, end_time, resource_key, cost]`（单任务一行）
  vs 上游 `TaskSolution` `[assigned_tasks, canceled_tasks]`（整解的索引集合）——同一名字、
  两个层次。
- `ResourceCapacity` Python `[resource_key, time_window_start, time_window_end, max_capacity,
  used_capacity]` vs 上游 `[time_range, lower_bound, upper_bound, less_slack_limit,
  over_slack_limit]`——上游是带松弛上下界的约束区间，Python 是用量快照。
- `ResourceAggregation` Python 6 个集合 vs 上游 `[execution_usages, storage_usages,
  connection_usages]`；`CapacitySchedulingAggregation` Python `[name, _assignments,
  _capacities, _loads]` vs 上游 `[compilation, order_compilation]`。
- 名称都不同但显然是同一概念的邻近对：`ResourceCapacityData`→`ResourceCapacity`、
  `TaskAggregation`→`TaskCompilationAggregation`、`ProduceOrderConstraint`→`OrderConstraint`、
  `BunchProblem`→`BunchPricingProblem`、`TaskColumn`→`TaskPricingColumn`（字段共享率 0.25，
  其余为 0.0）。

## 允许与不允许的处置

- 首轮盘点时 210 个能力一律登记为 `inventoried`，pending 挂 **RG-024**（本区域词表与数据形态鸿沟）、
  `gantt-native-binding-and-facade-implementation`、完整调用预算与平台矩阵；3 个函数另挂
  `natural-result-and-consumer-cutover`。在此之前不得声明任何绑定、切换或退役。
  修正后这 3 个函数的 compatibility 分别为 `pinned-rust-pub-fn-absent`（2 个）与
  `pinned-rust-reachable-pub-fn-name-match`（`extract_shadow_prices`，仍受 RG-024/RG-025 阻塞）。
- 不允许的做法：在绑定层另写一套等价的甘特领域模型（那会成为第二套内核）；把别的 crate
  （尤其 `ospf-rust-example` 示例代码）里的同名类型当作本区域的固定对手；只凭名称邻近
  就建立委托。
- 可选路径只有三条，且都需要明确授权：① 由上游提供与 Python 形状一致的公开 API
  （本任务禁止改动相邻 Rust 仓库）；② 用户确认把 Python 公开面**重构**到上游 `Activity*`
  模型上（属公开 API 变更）；③ 用户确认把这些能力登记为“合理保留的 Python 集成”
  （与本区域 `disposition = rust` 相冲突，需同时改 api-map 的 disposition）。

## 未覆盖

- 未做任何语义、算法、数值域或求解器调用比较；未测任何入口的成本与资源包络；
  未做 wheel/sdist 隔离构建与 Linux、Gurobi 11/12 矩阵。
- 名称解析靠正则读取上游源码，`pub(crate)`、别名导出、宏生成与 `where` 子句形态未覆盖；
  上游类型多于被匹配到的字段（trait 的方法、impl 块内的行为）不在此次比较范围内。
- Python 侧 199 个 dataclass 的字段**类型**只取了名字，未做类型级对账。
- 其余 13 个 `disposition = rust` 区域（bpp3d 102、csp1d 91、symbolic 91、models/solvers
  各 43、algebra 41 等）尚未做同类盘点。

## 2026-10-31 更新：真实任务对偶影子价格桥

`task_model_builder.extract_shadow_prices` 已从 `inventoried` 前移到
`specified`。新的原生路径不是对同名项的换名包装：

1. `_native._task_shadow_prices` 在 Rust 中构造固定 revision 的
   `TaskColumnGenerationAlgorithm` 和 `BasicTaskCompilationContext`。
2. Python 提供的真实 `task_compilation_*` 约束 dual 被装入
   `LinearDualSolution` / `LPResult`；算法内的 no-op solver 只满足类型构造，
   不参与计算。
3. 调用上游 `extract_shadow_prices` 后，只发布算法持有的非零任务价格；零值与
   超出任务范围的索引不发布。
4. `SolverOutput.dual_values` 和公开函数的 `dual_values` 是唯一真实 dual
   入口。省略 dual 时，现有 0/1 紧约束兼容行为保持不变，但不属于影子价格。

证据：`logs/p3/gantt-shadow-price-source-20261031/`。真实 solver dual 发布、
公共服务切换、列生成/定价生命周期、完整调用性能/资源及 Linux/Gurobi 11/12
仍是未完成门槛，因此不得登记 `verified` 或 `switched`。

## 2026-10-31 更新：Gurobi LP 对偶发布

`GurobiLinearSolver._build_output` 现在从 Gurobi LP 的唯一、非空约束名读取真实
`Pi` 并写入 `SolverOutput.dual_values`。MIP 没有可用的约束对偶，重复/空约束名
或 SDK 不提供属性时保持 `None`；不会发布部分映射或伪造零值。

已在隔离的 gurobipy 12.0.3 环境（Rust 固定版支持的 10/11/12 范围内）通过
LP/MILP 测试，证据见 `logs/p3/gurobi-dual-adapter-20261031/`。尚未验证 Gurobi
10/11，也未完成 Gurobi 原始对偶符号、等式拆分和约束行顺序到 Gantt/Rust
`LinearDualSolution` 的规范化，因此公共 Gantt 服务仍不切换。

## 2026-10-31 更新：`LinearTriadModel` 到 Gurobi 的 LP 物化桥

`GurobiLinearSolver.solve` 现接受两类输入：

- 原始 `gurobipy.Model`，保持直接求解和真实 LP `Pi` 发布；
- `LinearTriadModel`，按“显式变量、目标键、边界键、约束系数键”的稳定顺序
  补全变量并物化为 Gurobi 模型；未携带类型的旧模型仍按连续变量处理。

物化规则：

1. 未声明的变量下界为 `0.0`、上界为正无穷；二元变量默认边界为 `[0, 1]`；
2. 目标按最小化构建，目标系数、约束系数和 RHS 必须是有限值；
3. 变量边界允许无穷，但拒绝 NaN 和下界大于上界；
4. 约束方向接受 `<`/`<=`/`=<`、`>`/`>=`/`=>`、`=`/`==`；
5. 空变量集、空约束名、重复显式变量名和未知模型类型返回 `ERROR`；
6. 新模型只有在完整构建成功后才替换旧模型；构建失败会销毁临时模型并保留
   上一模型。

真实 Gurobi 12.0.3 探针：

```text
min 2x + 3y
s.t. x + y  >= 4
     x + 2y >= 6
     x, y   >= 0
```

得到唯一最优点 `x=2, y=2`、目标值 `10`、约束对偶 `c1=1, c2=1`。

回归：

```text
Gurobi + SolverOutput default/debug: 70 passed
Gantt 全目录 + 9 个原生 Gantt 文件 + solver output/value + Gurobi:
  default/debug: 1131 passed, 612 skipped
迁移合同: 49 passed
```

612 个跳过项仍为当前固定扩展未编译的 SCIP/Gurobi10/Gurobi11/Gurobi12，
各 153 个，不计为真实后端通过。证据：
`logs/p3/gurobi-triad-bridge-20261031/`。

### 2026-10-31 变量类型与 relaxation 语义（P3-AD）

`LinearTriadModel` 新增 `variable_types` 元数据。公共 Gantt
`build_triad_model` 的规则是：

1. `relaxation=True` 时全部变量输出为 `continuous`，但二元变量仍保留
   `[0, 1]` 边界；
2. `relaxation=False` 时保留 `MetaModel` 字典变量声明的类型，支持
   `VariableType` 枚举值；未声明类型的列对象按 `binary` 处理；
3. 空类型或未知类型不会被静默降级，最终由 Gurobi 物化边界返回 `ERROR`。

`GurobiLinearSolver` 只接受并能证明 `continuous`、`integer`、`binary` 到
Gurobi `C`、`I`、`B` 的映射；`semi_continuous`、`semi_integer` 和未知类型
返回 `ERROR`，不冒充已支持。二元变量要求有限边界且满足
`0 <= lb <= ub <= 1`。真实 Gurobi 12.0.3 测试已覆盖同一约束下连续解
`0.5`、二元解 `1.0`、整数解 `2.0` 的分歧，并确认最终任务模型包含连续
`start_*` 与二元 `assign_*`。

定向测试为 `37 passed`；Gurobi 12 + Gantt Gurobi E2E 为 `73 passed`；
Gantt 全目录组合默认/debug 各为 `1140 passed, 612 skipped`。证据：
`logs/p3/gurobi-variable-types-20261031/`。

## 2026-10-31 更新：公共 Gantt 任务模型闭环（P3-AE）

`TaskApplicationService` 的 Python 任务模型现在把列作为唯一可执行调度决策。
每个任务建立 `task_compilation_{index} == 1`，活跃列的覆盖系数为 `1`；因此
初始列集必须覆盖全部任务，否则最终 MIP 明确不可行。`start_*`、`assign_*`
不再是与列选择脱节的独立决策，而是由下列等式派生：

```text
start_link_{task}: start_{task} - sum(start_col * col) = 0
assign_link_{task,resource}:
  assign_{task,resource} - sum(col covering task/resource) = 0
```

其余领域语义为：

1. 容量行 `cap_{resource}_{start}_{end}` 的左端使用任务的资源需求量，不再固定为
   `1`；窗口边界取自任务最早/最晚开始、最早结束、截止时间和时间域。
2. 优先关系 `prec_{pred}_{succ}` 为
   `start_succ - start_pred >= duration_pred + min_gap`。
3. 连续变量 `makespan` 满足 `makespan - start_task >= duration_task`；最终目标为
   `makespan + 所选列成本`。
4. `add_columns` 对整批输入先校验后写入。重复/空列键、非有限成本或开始时间、
   空列、未知任务、重复 `(task, resource)`、同一任务在列内开始时间不一致、
   早于最早开始或晚于截止时间均返回失败，不会留下半批注册状态。
5. `build_triad_model` 读取 `MetaModel.objectives` 的 `variable/coefficient`，
   因此 makespan 与列成本进入同一个 Gurobi 目标；LP 松弛仍保留二元变量的
   `[0, 1]` 边界。

真实 Gurobi 12.0.3 非退化探针使用两个均需 `r1` 两单位、容量为三的任务，
并给出一个容量冲突列、一个优先关系冲突列和一个串行可行列。结果只选择
`serial_ok`，得到 `t1=[0,3)`、`t2=[3,5)`、`makespan=5`、目标值 `6`；
容量行对冲突列和可行列的系数分别为 `4` 和 `2`，优先行为
`-start_t1 + start_t2 >= 3`。

验证边界：

```text
Gantt 宽回归 default/debug: 1147 passed, 612 skipped
迁移合同:                    49 passed
```

612 个跳过项来自当前固定扩展未编译的 SCIP/Gurobi10/Gurobi11/Gurobi12，
各 153 个，不计为真实后端通过。证据：
`logs/p3/gantt-closed-task-model-20261031/`。

### 仍未切换的原因

- 这是 Python 公共任务模型与 Gurobi 物化闭环，不是固定 Rust 公共 Gantt
  绑定的切换。`TaskApplicationService`、`build_triad_model`、`build_schedule`
  仍是 `inventoried`，不能登记 `verified` 或 `switched`。
- 容量由有限事件点窗口离散化，不是任意连续时间剖面的完整容量语义；列仍携带
  显式开始时间，未实现连续时间容量日历或资源可用区间图。
- 当前模型没有取消语义，也不自动生成初始列或执行定价子问题。达到
  `max_iterations` 会标记收敛，`finalize` 只切换最终状态；这不构成完整列生成/
  定价生命周期或全局最优证书。
- 任务影子价格只在 `SolverOutput.dual_values` 提供真实 LP 对偶时进入固定 Rust
  `extract_shadow_prices`；无对偶的 0/1 紧约束兼容路径不是影子价格。
- Gurobi 原始对偶符号、等式拆分、行顺序到 Rust `LinearDualSolution` 的规范化，
  以及 Gurobi 10/11、SCIP/MindOpt/COPT、Linux、完整性能/资源与 wheel/sdist
  矩阵仍未验收。

## 2026-10-31 更新：任务模型权威迁入 Rust（P3-AF）

`TaskApplicationService` 的唯一可变模型状态已从 Python `MetaModel` 改为
`MetaModelFloat64`。任务变量、任务覆盖行、容量行、优先关系、makespan 行、
开始/分配桥和目标都先写入新的 Rust 模型；Python 只保留调度问题、活跃列和
结果提取所需的数据。

线性求解仍沿用现有 `LinearTriadModel` 边界，但三元组改为如下单向投影：

```text
Rust MetaModelFloat64
  -> to_linear_triad() 独立结构快照
  -> _build_triad_from_export()
  -> 现有 Solver / Gurobi adapter
```

投影规则：

1. 只接受 `minimize` 和零目标常数；目标由 `makespan + Σ column.cost` 构成。
2. 原生变量必须是 continuous、integer 或 binary；变量名和约束名必须唯一。
3. `None` 下界按现有任务模型语义映射为 `0.0`；二元空上界映射为 `1.0`，
   其他空上界映射为 `+inf`。
4. `relaxation=True` 只取消整数性，仍保留二元 `[0, 1]` 边界。
5. 原生导出、三元组物化和 Gurobi 模型构建均不会发布半成品；失败时保留
   上一个已发布模型。

列生成生命周期也已改为候选集重建：

- `register` 从空列集构建原生模型。
- `add_columns` 整批校验后，以“旧活跃列 + 新列”重建，成功后原子替换。
- `remove_columns` 以候选活跃列重建，成功后关闭旧原生模型。
- `refresh_shadow_price` / `extract_solution` 都从当前原生模型导出只读快照。

验证边界：

```text
Gantt 全目录 + 原生导出/影子价格合同 default/debug: 999 passed
迁移合同:                                               35 passed
真实 Gurobi 12.0.3:                                     serial_ok, starts 0/3,
                                                          makespan 5, objective 6
```

`build_triad_model` 作为旧 Python `MetaModel` 参考构建器仍存在，但已不是
`TaskApplicationService` 的默认权威路径。Bunch 服务、完整定价/取消、连续
容量日历、公开 Rust Gantt facade、Gurobi 10/11、SCIP/MindOpt/COPT、Linux、
性能/资源预算和 wheel/sdist 矩阵仍未完成，因此相关入口继续保持
`inventoried`。

## 2026-10-31 更新：束编组模型权威迁入 Rust（P3-AG）

`BunchApplicationService` 的唯一可变模型状态也已从 Python `MetaModel` 改为
`MetaModelFloat64`。`register`、`add_columns` 和 `remove_columns` 都从候选
活跃列构建一个新的 Rust 模型，完整成功后才替换当前模型并关闭旧模型；Python
侧只保留问题、活跃列和结果提取所需数据。

当前原生模型结构为：

1. 每个任务一个连续 `start_*` 变量，边界来自最早开始和最晚开始；每个活跃束列
   一个二元 `bunch_*` 变量。
2. `demand_{task}: sum(covering bunches) >= 1`，保留既有“每任务至少覆盖一次”
   语义，允许同一任务被多个带成本列覆盖。
3. `cap_{resource}_{start}_{end}: sum(capacity coefficients) <= resource.capacity`。
   同一列内多个成员在同一事件窗口重叠时系数累加，不覆盖；当前公共束模型仍按
   每个重叠成员一个资源单位计算，不是任务的联合资源需求量。
4. 目标为 `minimize sum(selected bunch.cost)`。束列成本必须有限，列键不能为空
   或重复，资源必须存在，成员任务必须存在，开始时间必须有限并落在任务窗口内。
5. `add_columns` 在写入前整批校验；失败批次保持原模型身份和活跃列集合不变。
   `remove_columns` 同样通过候选集重建发布，成功后才关闭旧模型。
6. 求解与 LP 松弛仍通过 `LinearTriadModel` adapter，但三元组来自
   `MetaModel.to_linear_triad()` 的独立快照。真实 dual 可用时，
   `refresh_shadow_price` 返回后端提供的约束价格；没有 dual 时才保留明确的
   0/1 紧约束兼容标记，不将其当作影子价格。

真实 Gurobi 12.0.3 探针使用两个单位资源任务、容量为 1 的资源、四个束列：
一个窗口重叠冲突列、一个串行可行列和两个拆分列。结果选择 `serial_ok`，
得到 `t1=[0,3)`、`t2=[3,5)`、`makespan=5`、目标值 `1`；冲突列在
`cap_r1_0_2` 的累计系数为 `2`，串行列系数为 `1`。

验证边界：

```text
Gantt 全目录 + 原生导出/影子价格合同 default/debug: 1012 passed
迁移合同:                                               35 passed
```

这次迁移只关闭束服务的 Python 模型权威，不关闭束领域语义。优先关系行仍保留
旧 Python 束桥接的可观察形式，尚未像任务模型一样建立开始变量与列选择的等式桥，
因此不能据此宣称跨列优先关系已闭环。有限事件窗口、自动定价、取消、完整列生成
生命周期、公开 Rust Gantt facade、其他后端/平台、性能资源与 wheel/sdist 矩阵
仍是未完成门槛；`BunchApplicationService` 继续登记为 `inventoried`。

上述优先关系/开始桥限制已由 P3-AH 关闭；本小节保留 P3-AG 当时证据，不回写为
更大范围的验收结论。

## 2026-10-31 更新：束编组优先关系与开始选择桥（P3-AH）

束编组原生模型现在按任务把覆盖列分为二元 `cover_mode_{task}_{mode}`，每个模式
对应一个 `(start, resource)`。同一任务的不同模式互斥，同一模式可包含多个开始与
资源一致的列；因此既有“每任务至少覆盖一次、可被多个带成本列覆盖”的合同仍保留，
同时不会把任务开始错误绑定到第一个覆盖列。

当前原生结构在 P3-AG 基础上增加：

```text
bunch_{column} - cover_mode_{task,mode} <= 0
cover_mode_{task,mode} - sum(bunches in mode) <= 0
covered_{task} - sum(cover_mode_{task,*}) == 0
sum(cover_mode_{task,*}) <= 1
start_{task} - sum(mode_start * cover_mode_{task,*}) == 0
start_{successor} - start_{predecessor} >= predecessor.duration + min_gap
```

`demand_{task}: sum(covering bunches) >= 1` 保持不变；容量仍按有限事件窗口累计，
每个重叠成员一个资源单位。同一束列内同一任务重复出现时，重复项的开始时间必须
一致，否则整批校验返回 `ILLEGAL_ARGUMENT`，候选模型不发布。

真实 Gurobi 12.0.3 探针在两个单位资源任务、容量 1、`t1 -> t2` 优先关系下加入
一个重叠冲突列、一个串行可行列、一个优先关系倒置列和两个拆分列。结果只选择
`serial_ok`：`covered_t1=covered_t2=1`、`start_t1=0`、`start_t2=3`、
`t1=[0,3)`、`t2=[3,5)`、`makespan=5`、目标 `1`；冲突列容量系数为 `2`，
串行列系数为 `1`，优先关系倒置列选择值为 `0`。

Gantt 全目录 + 原生导出/影子价格合同在默认与
`PYTHONMALLOC=debug -X dev` 下均为 `1016 passed`，迁移合同为 `35 passed`。
证据见 `logs/p3/gantt-bunch-precedence-start-bridge-20261031/`，14 项
`SHA256SUMS` 复核 `mismatches=0`，其文件自身 SHA-256 为
`060d5642537abd366ae45f49c64ad88ab99ad7df178daee55d7a6d564f032927`。

这仍不是公共 Gantt 切换。自动定价、取消、完整列生成生命周期、真实 LP 对偶的
最优性证书、任意连续容量日历、公开 Rust Gantt facade、其他后端/平台、性能资源
与 wheel/sdist 矩阵仍未完成；三个公共入口继续保持 `inventoried`。

上述 P3-AH 小节“每个重叠成员一个资源单位”的容量限制已由 P3-AI 关闭；该小节
保留当时的验证记录，不回写为更大范围的验收结论。

## 2026-10-31 更新：束编组容量按真实资源需求（P3-AI）

束容量系数现在使用任务对当前列资源的真实汇总需求量，而不是固定 `1.0`：

```text
capacity_coeff(column, task, window) =
    task.resource_demand(column.resource_key)
    when [task.start, task.start + task.duration)
         overlaps [window.start, window.end)
```

同一列内多个成员落在同一有限事件窗口时逐成员累加；同一任务重复出现仍按重复
成员累计，并继续要求重复项开始时间一致。这样容量行的左端与任务输入中的资源
需求一致，不会把“需要两单位”的任务静默建模成一单位。

`GanttProblem.validate()` 在原生模型发布前检查资源需求：

1. 每一项必须有限且非负；
2. 同一资源重复条目的汇总值也必须有限；
3. 零需求合法，未知资源仍按 `NOT_FOUND` 拒绝；
4. 非法问题返回 `ILLEGAL_ARGUMENT`，任务与束编组服务都不会发布候选模型。

真实 Gurobi 12.0.3 使用两个任务、二者均需 `r1` 两单位、资源容量三和
`t1 -> t2` 优先关系。重叠列在 `cap_r1_0_2` 的系数为 `4`，超过容量而被排除；
串行列在同一窗口的系数为 `2`，是唯一低成本可行列。结果为
`t1=[0,3)`、`t2=[3,5)`、`makespan=5`、目标 `1`，负需求问题在模型发布前
被拒绝。

Gantt 全目录 + 原生导出/影子价格合同在默认与
`PYTHONMALLOC=debug -X dev` 下均为 `1024 passed`，迁移合同为 `35 passed`。
证据见 `logs/p3/gantt-bunch-demand-capacity-20261031/`，14 项
`SHA256SUMS` 复核 `mismatches=0`，其文件自身 SHA-256 为
`662bfa570c7b31b194fac0da20d1d3bc5d26d9cae64074c42bda8ce1545bb2dc`。

这仍不是公共 Gantt 切换。容量继续按有限事件点窗口离散化，不支持任意连续
容量日历；自动定价、取消、完整列生成生命周期、真实 LP 对偶的最优性证书、
公开 Rust Gantt facade、其他后端/平台、性能资源与 wheel/sdist 矩阵仍未完成，
三个公共入口继续保持 `inventoried`。

## 2026-10-31 更新：容量窗口纳入候选列事件（P3-AJ）

P3-AI 的有限事件窗口此前只使用任务的最早/最晚开始、结束和截止时间。候选列
允许的开始时间不一定落在这些任务事件上，导致列与旧窗口部分重叠时仍按整个
窗口计入容量，可能把实际不重叠的列误判为资源冲突。

P3-AJ 为每个资源同时收集：

1. 使用该资源的任务边界；
2. 活跃任务列中 `(task, resource, start)` 的 `start` 与
   `start + task.duration`；
3. 活跃束列中 `(task, start)` 的同类边界；
4. 有限时间域终点。

束编组容量窗口改为按资源生成，并跳过不使用该资源的任务和列。全部事件点按
12 位小数规范化，避免 duration 加法产生 `0.8999999999999999` 一类亚纳秒
窗口。公开服务签名和列校验不变；该变化只影响候选原生模型的窗口划分。

真实 Gurobi 12.0.3 使用两个时长 `0.2`、资源需求 `1`、容量 `1` 的任务，
候选列开始分别为 `0.3` 和 `0.7`。旧任务事件窗口包含 `[0.2,0.8)`，会同时
计入两个实际不重叠的列；新窗口拆为 `[0.3,0.5)`、`[0.7,0.8)` 和
`[0.8,0.9)`，任一容量行都不同时包含两列。任务服务得到
`start_t1=0.3`、`start_t2=0.7`、`makespan≈0.9`、目标 `2.9`；束服务得到
同一调度、`makespan≈0.9`、目标 `2.0`，两任务覆盖值均为 `1`。

Gantt 全目录 + 原生导出/影子价格合同在默认与
`PYTHONMALLOC=debug -X dev` 下均为 `1029 passed`，迁移合同为 `35 passed`。
证据见 `logs/p3/gantt-candidate-window-events-20261031/`，14 项
`SHA256SUMS` 复核 `mismatches=0`，其文件自身 SHA-256 为
`559b311fa2780b7e90f7cceef69b35794ad418f17bf552f6f6dc57314c5092e8`。

这仍不是任意连续时间容量日历：窗口只覆盖当前活跃候选列可能产生的开始/结束
事件。自动定价、取消、完整列生成生命周期、真实 LP 对偶的最优性证书、公开
Rust Gantt facade、其他后端/平台、性能资源与 wheel/sdist 矩阵仍未完成，
三个公共入口继续保持 `inventoried`。

## 2026-10-31 更新：原生 LP 松弛与证书价格桥（P3-AK）

固定 Rust revision 的 `MetaModelFloat64` 新增私有
`solve_relaxed_compiled`。该方法在 Rust 所有者线程中克隆当前线性快照，对每个
变量调用固定 revision 的 `LinearVariableState::relaxed()`，再对同一松弛快照
调用 `compile_flt64()`、真实后端求解和 `issue` 证书。二元变量继续保留
`[0,1]` 的隐式边界；整数性只在本次求解快照中取消。普通 `solve` 与
`solve_compiled` 的模型、报告和证书路径不变。

`TaskApplicationService` 新增 keyword-only `native_solver`：

1. 省略该参数时，仍走既有的 `Solver` / fixture 路径，默认公共行为不变。
2. 显式设置时，`refresh_shadow_price` 调用同一原生模型的松弛证书求解；
   `constraint_handles()` 与 `source_price()` 按源约束名发布真实价格，再交给
   固定 Rust 任务影子价格算法。
3. 原生报告的解向量按 `to_linear_triad()` 的变量顺序校验长度后 zip，避免用
   名称或猜测索引重建价格输入。
4. 证书继续绑定原生模型所有者、修改代次和来源行；模型修改或关闭后不能再用
   旧证书查询价格。

定向合同使用二元和整数模型验证：约束 `x >= 0.5` 下，MIP 解为 `1.0`，LP
松弛解为 `0.5`，源约束证书价格为 `1.0`。Gantt 单任务、列成本 `2.5` 的
原生路径返回 `task_compilation_0=2.5`，且传入的 fixture solver 从未被调用。

真实 C API 原生求解使用 Gurobi 10.0.1 NODE 许可证；它属于固定 Rust revision
支持的 `gurobi10/11/12` 范围。Gurobi 12.0.3 wheel 的 PIP 许可证仅允许
`gurobipy` 接口；直接调用其 C API `GRBstartenv` 返回 `10009`
（`PIP license can only be used from gurobipy interface`）。因此 Gurobi 12
本轮只作为 Python adapter 测试环境，不是原生 C API 求解通过证据；Gurobi 11
仍未验证。

验证结果：

```text
Gantt 全目录 + 原生导出/对偶合同 default: 1050 passed, 57 skipped
同上 PYTHONMALLOC=debug -X dev:             1050 passed, 57 skipped
迁移合同:                                   35 passed
```

57 个跳过项来自当前扩展未编译的 SCIP/Gurobi11/Gurobi12 参数化，不计为真实
后端通过。证据冻结在
`logs/p3/gantt-native-lp-dual-20261031/`；Gurobi 10 原生扩展 SHA-256 为
`b09a19eb73f52652693881e887a06839f6b459ca00765cd2692111b2e4f3c4c9`，
18 项 `SHA256SUMS` 复核 `mismatches=0`，其文件自身 SHA-256 为
`41ccdeecad4825a6b1d321cbf5908c023923a51dc45728548bf2ea8b7726c39f`。

本更新只登记为 `specified`，不是公共 Gantt 切换。自动定价、取消、完整列
生成生命周期、Gurobi 11/12 C API 原生验证、公开 Rust Gantt facade、
SCIP/MindOpt/COPT、Linux、性能资源预算和 wheel/sdist 矩阵仍未完成；三个
公共入口继续保持 `inventoried`。

## 2026-10-31 更新：显式原生最终 MIP 提取（P3-AL）

`TaskApplicationService.extract_solution` 在显式设置 `native_solver` 时不再
调用 Python solver。它从同一原生模型调用 `solve_compiled`，使用编译报告中的
最终 MIP 解构造调度表；省略 `native_solver` 时继续使用原 solver 路径。

编译快照与 `to_linear_triad()` 导出保持相同变量顺序。服务在发布前校验报告解
向量长度，再用 `zip(..., strict=True)` 建立变量名到值的映射，不按名称或猜测
索引重建解向量。`solution_presence=NONE`、不可行、缺少目标值或长度不一致均
显式失败，不把空解补零成调度结果；只有 `solution_presence=OPTIMAL` 才标记
`is_optimal=True`，可行 incumbent 保持非最优标记。

最终模型含二元列，因此 `solve_compiled` 的普通 MILP 证书预期失败；本路径只
消费报告解，不宣称 MILP 最优性证书。LP 对偶证书仍只由 P3-AK 的
`solve_relaxed_compiled` 路径发布。

真实 Gurobi 10.0.1 NODE 使用三任务完整列得到开始时间 `0/3/5`、
`makespan=9`、目标 `19`、`is_optimal=True`，传入的 fixture solver 调用数为
`0`。验证结果：

```text
Gantt 全目录 + 原生导出/对偶合同 default: 1051 passed, 57 skipped
同上 PYTHONMALLOC=debug -X dev:             1051 passed, 57 skipped
迁移合同:                                   35 passed
```

57 个跳过项仍来自未编译的 SCIP/Gurobi11/Gurobi12 参数化，不计为真实后端
通过。证据冻结在 `logs/p3/gantt-native-mip-extraction-20261031/`；Gurobi 10
原生扩展 SHA-256 为
`9a5b18873e760bbf13640712c3e5b4088a4d05683d7c0838b3f3f7ceff21aa1f`，
12 项 `SHA256SUMS` 复核 `mismatches=0`，其文件自身 SHA-256 为
`1eafb50efb578eebb070f25ef79f4359dc93cd3ac876ffdd051e03a41544db9a`。
证据冻结后已恢复默认 editable，`native_solvers=""` 且固定 Rust revision
不变。

本更新仍不是公共 Gantt 切换。自动列生成、完整列生成生命周期、连续时间容量
日历、Gurobi 11/12 C API、公开 Rust Gantt facade、SCIP/MindOpt/COPT、
Linux、性能资源预算和 wheel/sdist 矩阵仍未完成；三个公共入口继续保持
`inventoried`。

## 2026-10-31 更新：有限候选池精确 reduced cost 与自动加列（P3-AM）

固定 Rust revision
`119854756a0aeb66d2998055f96fa7175c7bfb37` 上新增私有
`_native._task_improving_columns`。每个候选列输入成本和非零源行系数，Rust 将
Float64 转为精确有理数后计算：

```text
reduced_cost = cost - sum(row_coefficient * source_row_dual)
```

只有 `reduced_cost < -tolerance` 才标记为严格改善。缺失对偶行、空或重复候选
键、非有限或负容差都返回结构化失败，不使用浮点近似边界。Python 适配层为
`ospf_python._binding.gantt_task.improving_columns`，当前只登记为 `specified`。

`TaskApplicationService` 新增 keyword-only `run_column_generation`：

1. 必须显式设置 `native_solver` 且已有至少一个初始活跃列；不会回落到 Python
   solver 或自动猜测初始列。
2. 先整批校验候选池。未知资源、任务已声明资源但列引用其他资源、重复键、
   非有限值、未知任务和非法开始时间均在发布前失败；任务未声明
   `resource_requirements` 时保留历史通配兼容，可接受现有资源。
3. 容量窗口固定为活跃列与完整候选池的事件并集。加列不会改变行结构，因此
   同一轮对偶与候选系数的行身份一致。
4. 每轮从当前原生模型执行松弛证书求解，使用完整源行对偶和精确 reduced cost
   选择所有严格改善列；整批重建并原子替换原生模型。
5. 没有严格改善列时设置 `finite_pool_exhausted=True` 并结束。达到
   `max_iterations` 时只标记本次运行停止，不宣称有限池耗尽。

真实 Gurobi 10.0.1 NODE 探针使用一个时长 `3.0` 的任务、初始列成本 `2.5`、
改善列成本 `1.5` 和边界列成本 `2.5`。结果是只加入 `cheap`，活动列为
`seed, cheap`，`finite_pool_exhausted=True`、迭代数 `2`、fixture solver
调用数 `0`；最终 MIP 为 `is_optimal=True`、`makespan=3.0`、目标 `4.5`。

验证结果：

```text
定向定价与任务服务:                         48 passed
Gantt 全目录 + 原生导出/对偶/定价合同 default: 1061 passed, 57 skipped
同上 PYTHONMALLOC=debug -X dev:               1061 passed, 57 skipped
迁移合同:                                     35 passed
```

57 个跳过项仍来自未编译的 SCIP/Gurobi11/Gurobi12 参数化，不计为真实后端
通过。证据目录为
`logs/p3/gantt-finite-pool-column-generation-20261031/`。

该入口只证明调用方给定有限候选池在固定行结构和容差下没有进一步改善列，
不证明上游完整 `TaskColumnGenerationAlgorithm` 定价域、全局定价完成、取消
语义、任意连续时间容量日历或整数最优性证书。公共 `TaskApplicationService`、
`build_triad_model`、`build_schedule` 和 `extract_shadow_prices` 仍未登记为
`verified` 或 `switched`；Gurobi 11/12 C API、SCIP/MindOpt/COPT、Linux、
性能资源预算和 wheel/sdist 矩阵继续打开。

## 2026-10-31 更新：有限候选池列生成停止语义（P3-AN）

`TaskApplicationService.run_column_generation` 新增三个 keyword-only 参数：
`time_limit`、`cancellation` 和 `on_progress`。`time_limit` 是整轮列生成的总
时限，从进入运行范围时用单调时钟建立 deadline；每个 LP attempt 只获得当前剩余
秒数。非法、非有限或非正的时限在发布模型前返回 `ILLEGAL_ARGUMENT`，已过期时限
返回 `TIMEOUT`。

固定 Rust `SolveHandle` 只能服务一次求解，因此新增私有
`_binding.control.CancellationScope`：

1. 每个 attempt 通过 `new_handle()` 获得新的单次原生句柄。
2. 预取消作用域会立即取消之后创建的句柄；运行中的 `cancel()` 同时传播到当前及
   后续 attempt。
3. 取消来源和原因在 Python 边界校验，非法值返回结构化失败；Rust 仍保有首次
   不可变取消记录和完成先后关系。
4. 原生 attempt 同时返回失败且作用域已取消时，服务优先发布 `CANCELLED`，不把
   协作式停止误报为一般 `SOLVE_FAILED`。

停止结果映射为 `CANCELLED -> ErrorCode.CANCELLED`、
`TIME_LIMIT -> ErrorCode.TIMEOUT`，其他非完成终态仍为 `SOLVE_FAILED`。取消或
超时不会设置 `finite_pool_exhausted`；停止发生时已经成功提交的模型和列继续
保留，尚未完成的候选批次不发布，不回滚已提交结果。达到 `max_iterations` 的
既有停止语义不变，也不宣称有限池耗尽。

真实 Gurobi 10.0.1 NODE 探针结果：

```text
pre-cancel:          CANCELLED, active=["seed"], finite_pool_exhausted=false
second-attempt:      CANCELLED, active=["seed","cheap"], iteration=1
small time_limit:    TIMEOUT,   active=["seed"], finite_pool_exhausted=false
1000-task timeout:   TIMEOUT,   active=["all"], elapsed≈0.14s
fixture solver calls: 0
```

其中第二次 attempt 取消发生在首个改善列成功发布之后，证明停止不会回滚已提交列；
1000 任务探针证明整轮原生时限在大模型上返回结构化停止而不是空解或有限池完成。

验证结果：

```text
TestTaskRunColumnGeneration:                 18 passed
任务服务 + 原生控制:                          85 passed, 54 skipped
Gantt 全目录 + 原生导出/对偶/定价合同 default: 1074 passed, 57 skipped
同上 PYTHONMALLOC=debug -X dev:               1074 passed, 57 skipped
迁移合同:                                     35 passed
Rust gantt_task 单元测试:                     4 passed
```

57 个跳过项来自未编译的 SCIP/Gurobi11/Gurobi12 参数化，不计为通过。证据冻结在
`logs/p3/gantt-column-generation-stop-semantics-20261031/`；Gurobi 10 扩展
SHA-256 为
`207a7db730c4a8d3c1e9d3da608e3479477608967859751c77e6b4f6384dc9ba`。
证据冻结后已恢复默认 editable，`native_solvers=""`，默认扩展 SHA-256 为
`a9235ba74bbbdd1fcaa7087f3112d4a59d1631718fe652a93c9d00df2b12908d`。

本更新只关闭有限候选池 `run_column_generation` 的整轮时限、取消和进度回调，
以及停止时已发布列的原状态语义。它不关闭 `finalize` / `extract_solution`
停止控制、完整列生成生命周期取消、上游完整定价域、任意连续时间容量日历、
整数最优性证书、Gurobi 11/12 C API、SCIP/MindOpt/COPT、Linux、性能资源预算
或 wheel/sdist 矩阵。公共 `TaskApplicationService`、`build_triad_model`、
`build_schedule` 和 `extract_shadow_prices` 仍未登记为 `verified` 或
`switched`。

## 2026-10-31 更新：最终 MIP 停止控制（P3-AO）

`finalize` 保持 O(1) 状态切换，不接收求解控制参数；实际最终 MIP 求解发生在
`extract_solution`。因此 `TaskApplicationService.extract_solution` 新增三个
keyword-only 参数：`time_limit`、`cancellation` 和 `on_progress`。

不传停止参数时，现有默认 solver 路径和显式 `native_solver` 路径行为不变。默认
solver 路径收到任一停止参数时返回 `NOT_SUPPORTED`，不会静默忽略限制；最终 MIP
停止控制只对显式原生后端生效。时限必须有限且为正，整数必须位于 Float64 精确
边界内；`cancellation` 必须是 `CancellationScope`，`on_progress` 必须可调用，
非法输入在导出模型前返回 `ILLEGAL_ARGUMENT`。

每次最终 MIP attempt 都从作用域创建新的单次 `SolveHandle`。预取消在导出
`to_linear_triad()` 前停止，不改变原生模型、活跃列或收敛状态；原生 attempt
返回失败但作用域已经取消时优先返回 `CANCELLED`。

终态映射如下：

1. `CANCELLED` 始终映射为 `ErrorCode.CANCELLED`，即使后端报告已有 incumbent，
   也不发布部分方案。
2. `TIME_LIMIT` 且 `solution_presence=NONE` 映射为 `ErrorCode.TIMEOUT`。
3. `TIME_LIMIT` 且已有 `FEASIBLE` / `OPTIMAL` incumbent 时保留方案，但
   `is_optimal` 只在 `solution_presence=OPTIMAL` 时为真，不伪造最优性证书。
4. `INFEASIBLE` 映射为 `NO_SOLUTION`；其他非完成终态映射为 `SOLVE_FAILED`。

真实 Gurobi 10.0.1 NODE 探针在 1000 任务最终 MIP 上以 `time_limit=1e-5`
观测到 `TIME_LIMIT + FEASIBLE`：服务保留 `makespan=1.0` 的 incumbent，并报告
`is_optimal=False`；若后端在时限内尚未形成 incumbent，则同一合同返回
`TIMEOUT`，不把两种终态混为一谈。回调取消返回 `CANCELLED`。默认 fixture
solver 在两条原生路径上的调用数均为 `0`。

本更新只关闭显式原生最终 MIP 提取的单次 `time_limit`、`cancellation` 和
`on_progress` 语义。它不关闭完整列生成生命周期取消、上游完整定价域、任意连续
时间容量日历、整数最优性证书、Gurobi 11/12 C API、SCIP/MindOpt/COPT、Linux、
性能资源预算或 wheel/sdist 矩阵。公共 `TaskApplicationService`、
`build_triad_model`、`build_schedule` 和 `extract_shadow_prices` 仍未登记为
`verified` 或 `switched`。

## 2026-10-31 更新：列生成生命周期停止与取消（P3-AP）

`TaskApplicationService.refresh_shadow_price` 新增 keyword-only `time_limit`、
`cancellation` 和 `on_progress`。不传参数时默认 solver 与显式原生路径保持原行为；
默认 solver 路径收到任一停止参数时返回 `NOT_SUPPORTED`。显式原生路径复用
`_refresh_native_shadow_price` 的同一 LP 快照、证书价格和单次句柄逻辑，不在公共
入口复制求解流程。非法时限、取消类型或回调在导出模型前返回
`ILLEGAL_ARGUMENT`；预取消在导出前返回 `CANCELLED`，不改变模型、活跃列、
影子价格或迭代数。

`register`、`add_columns` 和 `remove_columns` 新增 keyword-only
`cancellation`。批量列校验在每列及每个任务资源分配前观察取消；候选原生模型
构建前后也观察取消。构建完成后才发现取消时，候选模型立即关闭，不替换当前模型，
也不发布活跃列、容量窗口、价格、收敛或有限池状态。`run_column_generation` 的
批量校验复用同一检查点；`finalize` 仍是 O(1) 状态切换，因此不接收无意义的求解
停止参数。

该取消是协作式边界语义，不是异步强制中断。单次原生候选模型构建不可中途打断；
`register` / `add_columns` / `remove_columns` 不提供伪造的时限或进度事件。取消在
检查点之后、发布之前发生仍可能完成一次发布，因此不宣称线性化原子取消。

真实 Gurobi 10.0.1 NODE 探针覆盖公共影子价格刷新的正常停止控制、预取消和回调
取消。正常刷新返回认证的 `task_compilation_0=2.5`；预取消和回调取消返回
`CANCELLED`，模型身份、迭代数和影子价格保持不变；fixture solver 调用数为 `0`。

验证结果：

```text
任务服务文件 Gurobi 10:                       96 passed
任务服务 + 原生控制:                          124 passed, 54 skipped
Gantt 全目录 + 原生导出/对偶/定价合同 default: 1113 passed, 57 skipped
同上 PYTHONMALLOC=debug -X dev:               1113 passed, 57 skipped
迁移合同:                                     35 passed
Rust gantt_task 单元测试:                     4 passed
迁移盘点:                                     explicit_contracts=1446,
                                               unresolved_exports=0, issues=[]
```

57 个跳过项来自当前 Gurobi 10 扩展未编译的 SCIP/Gurobi11/Gurobi12 参数化，
不计为通过。证据冻结在
`logs/p3/gantt-column-generation-lifecycle-stop-20261031/`。

本更新关闭 Python 列生成编排在协作检查点上的取消，以及显式原生 LP 刷新的停止
控制；它不关闭上游完整 `TaskColumnGenerationAlgorithm` 定价域、任意连续时间
容量日历、整数最优性证书、Gurobi 11/12 C API、SCIP/MindOpt/COPT、Linux、
性能资源预算或 wheel/sdist 矩阵。公共 `TaskApplicationService`、
`build_triad_model`、`build_schedule` 和 `extract_shadow_prices` 仍未登记为
`verified` 或 `switched`。

## 2026-10-31 更新：完整任务定价域桥（P3-AQ）

新增私有 `_binding.gantt_task.TaskPricingAlgorithm`，直接持有固定 revision 的
`TaskColumnGenerationAlgorithm`。主问题从上游注册的任务-执行器列重建：

```text
task_compilation_{task} == 1
executor_compilation_{executor} <= 1
```

变量仍是上游注册的二进制任务-执行器列，目标由当前未删除列的成本写入。Python
定价策略收到完整无时隙域，包括任务、执行器槽、认证行对偶、任务影子价格、
`global` 与 `verified_duals`，以及固定列、保留列和迭代信息。策略返回共享
`ColumnGenerationBatch`，不另写一套 Python 定价模型。

下界发布规则如下：

1. 只有 `completion=EXHAUSTED`、`no_improving_columns=True` 且 LP 证书仍与
   当前主问题一致时，`certified_lower_bound()` 才返回 LP 下界。
2. `BUDGET_LIMIT`、`INTERRUPTED`、`HEURISTIC` 或缺少“无改善列”证据时返回
   `None`，不把停止或启发式状态冒充证明。
3. 新增初始列或已定价列会使旧下界与完成状态失效；非法整批列在写入前失败。
4. 策略返回未知完成状态、非法列或抛出异常时返回结构化 `Result`，不发布部分
   批次状态。

首次冻结证据时，全量 `tests/native` 暴露了两个旧 Bunch 测试仍读取已删除的
`_meta_model`/旧重复成员语义，以及原子质量单位超过固定上游 64 位十进制比例尺的
既有 `DATA_LOSS` 边界。旧 Bunch 测试已改读 `_native_triad()` 的完整变量、类型和
边界快照，并按变量名读取解；原子质量单位测试明确断言既有 `Failed + DATA_LOSS`
政策，不以放宽生产校验掩盖边界。

修正后固定 Gurobi 10.0.1 扩展的定向 7 文件为 **182 passed, 96 skipped**，完整
`tests/native` 为 **7161 passed, 1312 skipped**；迁移合同为 **35 passed**，
默认 feature Rust 单测为 **202 passed**。迁移盘点为
`explicit_contracts=1449`、`unresolved_exports=0`、`issues=[]`。

`TaskPricingAlgorithm` 是 GIL-affine 的 unsendable 对象，不承诺跨线程并发调用。
该更新只证明上游无时隙任务-执行器完整定价域及 LP 下界语义，不证明多资源连续
时间 Gantt 列生成、公共 `TaskApplicationService` 切换、Gurobi 11/12、SCIP、
MindOpt、COPT、Linux、完整性能/资源预算或 wheel/sdist 矩阵。证据目录为
`logs/p3/gantt-task-pricing-domain-followup-20261031/`；Gurobi 10 扩展
SHA-256 为
`b70969711cd45657b8669b4d19bf6d42ac223c1803c472e868c8a8720b2aab24`，
恢复默认 editable 后 `native_solvers=""`，扩展 SHA-256 为
`5f9486650d09c6d7b1670256044f3936945825f1f67f05bbbc2df54acad64d0b`。

## 2026-10-31 更新：公共任务列生成门面（P3-AR）

新增公共
`ospf_python.framework.gantt_scheduling.application.service.task.task_column_generation_algorithm`
模块，公开 `TaskColumnGenerationAlgorithm`、`TaskPricingBatch`、
`TaskPricingLpReport`、`TaskPricingColumn` 和 `TaskPricingPolicy`。公共类直接继承
P3-AQ 的私有 PyO3 适配器，不复制 `TaskColumnGenerationAlgorithm`、主问题或证书
状态；因此公共入口仍只有一个 Rust 权威对象。

调用方可以从公共包导入并创建完整无时隙任务-执行器定价域：

```python
from ospf_python.framework.gantt_scheduling.application.service.task import (
    TaskColumnGenerationAlgorithm,
)

algorithm = TaskColumnGenerationAlgorithm.create(
    task_count=2,
    executor_count=2,
).unwrap()
algorithm.add_columns([(0, 0, 1.0), (1, 1, 2.0)]).unwrap()
report = algorithm.solve_lp(solver="gurobi10").unwrap()
```

公共门面保留 P3-AQ 的完整域、策略回调、认证行对偶、`global` /
`verified_duals`、批次快照和 LP 下界失效规则。它仍是 GIL-affine unsendable
对象；`TaskApplicationService` 的现有有限候选池/显式开始时间路径没有切换，
因此不能把本工作登记为 `verified` 或 `switched`。多资源连续时间 Gantt、
公共服务消费者切换、Gurobi 11/12、SCIP/MindOpt/COPT、Linux、性能资源预算和
发行矩阵继续打开。证据目录为
`logs/p3/gantt-task-column-generation-facade-20261031/`。

## 2026-10-31 更新：显式任务定价服务消费者（P3-AS）

`TaskApplicationService` 新增 `run_task_pricing`，作为公共
`TaskColumnGenerationAlgorithm` 的显式消费者：

```python
result = service.run_task_pricing(
    columns=((0, 0, 1.0), (1, 1, 2.0)),
    policy=pricing_policy,
).unwrap()
```

该方法要求先 `register` 一个 `GanttProblem`，并按问题中任务与资源的声明顺序映射
上游任务索引和执行器索引。它创建公共门面、注册初始无时隙任务-执行器列、求解
一次 LP、调用定价策略，并返回 `TaskPricingResult`：

```text
task_keys
resource_keys
lp_report
batch
certified_lower_bound
```

`run_task_pricing` 支持服务配置的显式原生后端、单个 LP 时限、
`CancellationScope` 和只读进度回调。输入、取消和后端检查都在创建算法前完成；
`INFEASIBLE`、`TIME_LIMIT`、非最优完成和策略失败均映射为结构化 `Result`。

该入口只编排无时隙任务-执行器定价子域，不替换或修改现有 Gantt 原生模型、活跃
列、容量窗口、影子价格、迭代次数或收敛状态。因此它是显式服务消费者，不是现有
有限候选池/显式开始时间路径的切换，也不能登记为 `verified` 或 `switched`。

Gurobi 10.0.1 下新增服务入口定向测试 **7 passed**，任务服务文件
**103 passed**；默认扩展下新增入口为 **5 passed, 2 skipped**。证据目录为
`logs/p3/gantt-task-pricing-service-consumer-20261031/`。多资源连续时间 Gantt、
现有服务路径切换、整数最优性证书、Gurobi 11/12、SCIP/MindOpt/COPT、Linux、
性能资源预算和最终发行矩阵继续打开。

## 2026-10-31 更新：Gantt 有限任务列提取切换到 Rust activity 权威桥（P3-AT）

`TaskApplicationService.extract_solution` 在同时满足以下条件时，改为消费
`_binding.gantt_task.solve_task_columns(objective="makespan_cost")`：

1. 服务显式配置了 `native_solver`；
2. 当前 `_active_columns` 非空；
3. 求解仍处于有限、显式开始时间列模型。

该路径直接构造固定 revision 的 activity 模型，不经过旧 Python 列系数装配。
目标保持公共语义 `makespan + selected column costs`，层级前缀成本按真实结束
时间差计算；默认 `rank` 模式仍保留私有桥原有的 makespan 次序目标。

同一列中同一任务的多个资源分配在 `makespan_cost` 模式下合并为一个覆盖活动：

- 同一任务的开始/结束时间必须一致；
- 无显式资源需求时，各分配的资源用量和可用区间联合进入容量语义；
- 有显式资源需求时，重复分配视为重复 `(task, resource)` 并结构化拒绝；
- 列成本只附加到合并后组的第一个活动，覆盖行只计一次。

服务从选中列按 `problem.tasks` 顺序重建调度，重复分配必须保持同一开始时间，
并保留首次出现的资源键。不可行、无解、超时、取消和可行 incumbent 均映射为
结构化 `Result`；可行超时解不宣称最优，目标值从选中列精确重算。

兼容边界：

- 显式原生后端但活跃列为空时，继续走原有编译最终 MIP 路径；
- 未显式配置原生后端时，公共默认求解器路径不变；
- `run_column_generation` 仍使用有限候选池和 LP 对偶定价，尚未切换到上游完整
  定价域；
- 任意连续时间容量日历、整数最优性证书、Gurobi 11/12、SCIP/MindOpt/COPT、
  Linux、完整性能/资源预算和最终发行矩阵继续打开。

Gurobi 10.0.1 下 Gantt 全目录与原生 Gantt 文件为
**1335 passed, 468 skipped**，完整 `tests/native` 为
**7166 passed, 1321 skipped**，迁移合同 **49 passed**，packaging
**56 passed**。跳过项来自未编译的其他后端，不计为通过。证据目录为
`logs/p3/gantt-finite-task-column-activity-cutover-20261031/`。

## 2026-10-31 更新：Gantt 束列最终解提取切换到 Rust activity 权威桥（P3-AU）

`BunchApplicationService` 新增可选 `native_solver` 构造参数。仅当它被显式
配置且 `_active_columns` 非空时，`extract_solution` 改为消费
`_binding.gantt_bunch.solve_bunch_columns`，由固定 Rust revision 的有限
activity 模型求解当前束列，再从选中列重建调度表：

- 选中列按输入顺序保留，任务开始时间与指定资源来自选中列；
- 目标值取源域复核后的选中列精确成本 `(分子, 分母)`，不把原始后端浮点目标
  当作精确证书；
- 同一任务若被不同束列覆盖为不同开始时间或资源，返回结构化
  `APPLICATION_ERROR`，不静默采用第一个；
- 选中列未覆盖全部任务时同样结构化失败；
- `problem_status=INFEASIBLE`、无解或未完成终止映射为既有服务错误码。

兼容边界：

- 显式原生后端但活跃列为空时，保留原有编译最终 MIP 路径；
- 未显式配置原生后端时，默认 solver 路径不变；
- `extract_bunch_solutions`、`run_column_generation` 与定价生命周期未切换；
- 任意连续时间容量日历、整数最优性证书、Gurobi 11/12、SCIP/MindOpt/COPT、
  Linux、完整性能/资源预算和最终发行矩阵继续打开。

Gurobi 10.0.1 下 Gantt 全目录与原生 Gantt 文件为
**1339 passed, 468 skipped**，完整 `tests/native` 为
**7166 passed, 1321 skipped**，迁移合同 **49 passed**，packaging
**56 passed**。证据目录为
`logs/p3/gantt-bunch-activity-cutover-20261031/`。

## 2026-10-31 更新：Gantt 束编组方案提取切换到 Rust activity 权威桥（P3-AV）

`BunchApplicationService.extract_bunch_solutions` 与 P3-AU 的
`extract_solution` 复用同一条有限束列求解路径。仅当显式配置
`native_solver` 且 `_active_columns` 非空时，才消费
`_binding.gantt_bunch.solve_bunch_columns`，并按选中列输入顺序构造
`BunchSolution`：

- `bunch_key`、`resource_key`、任务开始时间和精确列成本均来自源域复核后的
  选中列，不从后端浮点目标反推；
- 不可行、无解、未完成终止和源域复核失败映射为既有结构化错误码；
- 空活跃列与未配置原生后端保留原编译最终 MIP / 默认 solver 路径；
- `extract_bunch_solutions` 不发布 `GanttSolution`、活跃列、影子价格、
  迭代次数或收敛状态，也不新增自动定价或完整列生成生命周期。
- 有限桥的覆盖复核只要求每个任务至少被一个选中活动覆盖；同一任务可以由
  多个开始时间和资源相同的兼容列同时选中。桥按每个选中列返回独立
  `BunchSolution` 快照，不执行唯一调度映射。
- 只有 `extract_solution` 在调用 `_schedule_from_bunch_columns` 时拒绝同一
  任务被不同开始时间或资源模式覆盖，并返回结构化 `APPLICATION_ERROR`。

Gurobi 10.0.1 下束服务定向 **37 passed**；Gantt 全目录与原生 Gantt 文件为
**1341 passed, 468 skipped**；完整 `tests/native` 为
**7166 passed, 1321 skipped**。证据目录为
`logs/p3/gantt-bunch-solution-activity-cutover-20261031/`。跳过项来自未编译的
其他后端，不计为通过。

覆盖边界修正后，同一兼容重复覆盖的桥测试、唯一调度冲突拒绝测试和逐列快照
测试将上述定向扩为 **94 passed, 102 skipped**；Gantt 全目录与原生 Gantt 文件
为 **1344 passed, 471 skipped**，完整 `tests/native` 为
**7167 passed, 1324 skipped**。修正证据目录为
`logs/p3/gantt-bunch-coverage-boundary-20261031/`。
