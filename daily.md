# OSPF Python 迁移改进计划

## 目标

以 Python 3.13 为基准，将 `ospf-kotlin` 的可迁移功能完整、正确地迁移到
`ospf-python`。对 Kotlin 语言内部 DSL 绑定较深的能力，允许改造成更符合
Python 风格的接口，但需要保证外部功能能力、求解流程、错误处理语义和文档声明
一致。

本轮改进的直接目标：

1. 建立可信的迁移完成度清单，区分已完成、部分完成、Python 风格替代、明确不迁移。
2. 消除当前“Complete 1:1 migration”与实际 partial 状态之间的冲突。
3. 补齐 solver/plugin、framework-plugin、CSP1D pricing 等已确认缺口。
4. 将 partial framework 模块逐步纳入严格类型检查和跨语言行为等价测试。

## 工作原则

1. 不以文件数量、目录存在或 import 成功作为完成依据。每个功能点必须有实现、测试和
   文档状态支撑。
2. Python 风格替代设计可以不复刻 Kotlin 内部 DSL 写法，但必须保留等价的外部能力。
3. 所有可能失败的业务流程优先返回 Result，不把异常作为常规控制流。
4. framework 建模能力应以 `MetaModel`、context、aggregation、pipeline、application
   编排层分工为主，不把约束和目标全部堆在 application service 中。
5. 对外 public API 应稳定、可测试、可文档化；迁移期命名不应泄漏到最终接口。
6. 明确不迁移的功能必须写清楚原因，例如 Python 生态缺失、商业 SDK 不可用、
   JVM/KSP 专属机制不可直接对应等。
7. 每个 partial 模块都需要有退出条件，不能长期停留在“已知 partial 但文档声称完成”的状态。

## 当前状态

已验证通过：

- Python 版本：`Python 3.13.14`
- 迁移门禁：`python scripts/check_migration_gates.py`
- 静态检查：`python -m ruff check .`
- 类型检查：`python -m mypy ospf_python`
- 测试：`python -m pytest`，当前结果为 `6609 passed, 7 skipped`

需要注意：

- `pyproject.toml` 仍对多个 framework 模块启用了 `ignore_errors = true`。
- `scripts/check_migration_gates.py` 中存在硬编码 partial 模块清单。
- 根目录缺少脚本注释中提到的 `migration-matrix.md`。
- `CHANGELOG.md` 中“Complete 1:1 migration”和“removed ignore_errors=true”的描述
  与当前仓库状态不一致。

## 初始差距清单

| 类型 | Kotlin 侧能力 | Python 当前状态 | 处理策略 | 优先级 |
|------|---------------|-----------------|----------|--------|
| Solver plugin | CPLEX、Hexaly、Lingo、Mosek、OptVerse、Gurobi11 等 | optional solvers 只有 Gurobi、SCIP、COPT、MindOPT | 逐个评估 Python SDK 可用性；可迁移则补 adapter，不迁移则写入排除说明 | P0 |
| Framework plugin | Kafka、MongoDB、MySQL、SQLite、Redis、Ktorm、MyBatis、expression-ksp | 已实现 SQLite、Redis、Base；其余多为 candidate | 补齐可迁移后端或定义 Python 替代方案 | P0 |
| CSP1D pricing | `ReducedCostPricingGenerator`、pricing report、canonical key、candidate filters | 有 reduced-cost 评分和目标计算，但缺对等 pricing generator 入口 | 补齐功能或提供等价 Python API，并加 parity tests | P0 |
| Partial modules | 多个模块在门禁中列为 partial | `math/symbol/operation`、CSP1D 子模块、BPP1D/BPP2D/CSP2D/network/persistence 等仍 partial | 逐模块功能对齐、测试补齐、移出 partial 清单 | P0 |
| 类型检查 | Kotlin 编译期覆盖完整模块 | Python mypy 对多个 framework 子树 `ignore_errors = true` | 按模块移除 ignore，修复真实类型问题 | P0 |
| 文档声明 | 应反映真实完成度 | CHANGELOG/README/docs 与实际状态不一致 | 用迁移矩阵驱动文档状态 | P1 |
| 迁移测试 | Kotlin 行为需要可复核 | `test_migration_consistency.py` 偏 smoke | 引入 fixture 和行为等价断言 | P1 |
| 错误处理 | Result 风格 | math symbol operation 有较多直接 raise | 区分协议/不变量和业务入口，业务入口 Result 化 | P1 |

## 优先级定义

- P0：影响“是否能宣称完整迁移”的阻断项。没有处理前不能发布完整迁移结论。
- P1：影响正确性证明、文档可信度或长期维护质量的重要项。
- P2：不阻断迁移完成声明，但影响体验、示例、可观测性或工程整洁度。

## 迁移矩阵字段

`migration-matrix.md` 建议使用表格维护，至少包含以下字段：

| 字段 | 说明 |
|------|------|
| Kotlin module | Kotlin Maven 模块或源码目录 |
| Kotlin feature | 具体功能点，不只写模块名 |
| Python package | Python 对应包、模块或类 |
| Status | `complete`、`partial`、`pythonic-replacement`、`excluded` |
| Public API parity | 外部 API 是否等价，允许说明 Python 风格差异 |
| Behavior parity | 是否有行为等价测试或 fixture |
| Type coverage | 是否纳入 mypy strict，不允许业务模块整体 ignore |
| Error handling | 是否遵循 Result 风格，例外原因是什么 |
| Tests | 对应测试文件或测试类别 |
| Docs | 对应 README/docs/API 文档 |
| Owner/Notes | 决策说明、剩余工作、排除理由 |

推荐状态定义：

- `complete`：实现、测试、类型检查、文档均完成，且无已知 parity 缺口。
- `partial`：已有可用实现，但功能、测试、类型或文档至少一项未满足完成标准。
- `pythonic-replacement`：不复刻 Kotlin DSL 或 JVM 机制，但 Python 对外能力等价。
- `excluded`：明确不迁移，必须说明原因和影响范围。

## 事项

### 1. 迁移矩阵与声明修正

- 新增 `migration-matrix.md`，作为迁移完成度的唯一事实来源。
- 将每个 Kotlin 模块映射到 Python 包、测试、文档和验收状态。
- 对 Kotlin 特有 DSL 或 JVM 生态绑定能力，标注 Python 替代设计或明确不迁移原因。
- 调整 `CHANGELOG.md`、`README.md`、`README_ch.md` 和相关 docs，避免 partial 模块被
  误描述为完整迁移。
- 修改 `scripts/check_migration_gates.py`，从 `migration-matrix.md` 读取 partial 与
  excluded 清单，避免硬编码。

细化任务：

- 收集 Kotlin 根模块、core-plugin 子模块、framework-plugin 子模块。
- 收集 Python `ospf_python` 包、examples、docs、tests 对应关系。
- 给每个模块至少拆到功能族级别，不只停留在目录级别。
- 将当前 `PARTIAL_MODULES` 迁入矩阵。
- 将当前缺失的 solver 和 plugin 标成 `partial` 或 `excluded`，避免隐性缺口。
- 为矩阵增加检查脚本，确保文档声明不能与矩阵状态冲突。

### 2. Solver 插件补齐或排除

- 对照 Kotlin core-plugin 清单评估以下 solver：
  - CPLEX
  - Hexaly
  - Lingo
  - Mosek
  - OptVerse
  - Gurobi11 独立兼容入口
- 为可迁移 solver 增加 Python adapter、optional dependency、importorskip 测试和文档。
- 对 Python 生态不可用或当前不计划支持的 solver，在迁移矩阵中标注明确排除原因。

每个 solver 的最小交付物：

- `ospf_python.core.solver.<solver>` adapter 或明确排除记录。
- `pyproject.toml` optional dependency。
- importorskip 单元测试。
- 状态映射测试：optimal、infeasible、unbounded、timeout、error。
- 基础 LP/MILP smoke test。
- 文档说明安装方式、许可证或商业 SDK 限制。

### 3. Framework Plugin 补齐或排除

- 对照 Kotlin framework-plugin 清单评估以下后端：
  - Kafka
  - MongoDB
  - MySQL
  - SQLite
  - Redis
  - Ktorm/MyBatis 对应的 Python SQLAlchemy/SQLModel 方案
  - persistence expression KSP 对应的 Python 表达式方案
- 保留 SQLite/Redis 现有实现，并补齐 Result 风格错误边界。
- 为新增后端提供最小 repository 契约测试和文档。
- 对不迁移项写入迁移矩阵，并在 docs 中标注候选或排除状态。

每个后端的最小交付物：

- repository 或 message adapter 的 public API。
- Result 风格连接、读写、序列化、查询失败处理。
- fake 或 mock 测试，不要求 CI 依赖真实外部服务。
- 可选真实集成测试，默认跳过或通过环境变量启用。
- README/docs 中标明 implemented、candidate 或 excluded。

### 4. CSP1D 完整性整改

- 补齐或等价替代 Kotlin `ReducedCostPricingGenerator`。
- 检查 `SimplePricingGenerator`、initial generator、pricing generator、top-k 方案选择
  与 Python 当前实现之间的行为差异。
- 补充 reduced-cost pricing、canonical key、candidate filter、shadow price、
  final MILP、recovery、partial solution 的 parity 测试。
- 复查 `framework/csp1d/domain/material` 与 `framework/csp1d/domain/cutting_plan_generation`
  的 partial 状态，逐项移除。

CSP1D 需要重点对齐的能力：

- initial cutting plan generation。
- simple pricing generation。
- reduced-cost pricing generation。
- cutting plan canonical key 和重复方案去重。
- candidate filters 和 width feasibility check。
- costar filler。
- shadow price extraction 和转换。
- column generation iteration trace。
- final MILP solve。
- recovery 和 warm start。
- partial solution 生成、KPI、render 数据。

对应测试应覆盖：

- 小规模确定性用例，输出方案可精确断言。
- reduced cost 排序和过滤逻辑。
- shadow price 为空、缺项、负值、重复产品时的行为。
- final MILP 失败但允许 partial solution 的路径。
- recovery fallback 开启和关闭两类路径。

### 5. Partial Framework 模块收敛

- 逐个收敛以下 partial 模块：
  - `math/symbol/operation`
  - `framework/csp1d/domain/cutting_plan_generation`
  - `framework/csp1d/domain/material`
  - `framework/bpp1d`
  - `framework/bpp2d`
  - `framework/csp2d`
  - `framework/network_scheduling`
  - `framework/persistence`
- 每个模块需要完成：
  - 功能矩阵对齐
  - public API 文档
  - 单元测试和关键行为测试
  - Result 风格错误处理复核
  - 从 `PARTIAL_MODULES` 或迁移矩阵 partial 状态中移除

模块退出 partial 的统一条件：

- 迁移矩阵中该模块所有功能点均为 `complete`、`pythonic-replacement` 或 `excluded`。
- 不存在未说明的 stub、placeholder、TODO、bare pass。
- public API 有文档和示例，至少覆盖主要调用路径。
- mypy 不再对该模块整体 ignore。
- 测试覆盖正常路径、失败路径和边界路径。
- 如果存在 Python 风格替代设计，必须有文档解释替代关系和行为差异。

### 6. 类型检查与错误处理

- 分阶段移除 `pyproject.toml` 中 framework 模块的 `ignore_errors = true`。
- 对外部库边界保留 `ignore_missing_imports`，但业务代码不得整体忽略类型错误。
- 复查 `math/symbol/operation` 中直接 `raise ValueError` 和 `raise TypeError` 的公共 DSL
  边界，能返回 Result 的入口应改成 Result 风格。
- 保留 Python 协议边界、值对象不变量和测试代码中允许的异常用法。

处理顺序建议：

1. 先移除类型最简单的模块 ignore，例如 `persistence` 或 `network_scheduling`。
2. 再处理 `bpp1d`、`bpp2d`、`csp2d`。
3. 最后处理复杂的 `csp1d` 和 `gantt_scheduling`。
4. 每次只移除一个模块的 ignore，修完后跑 mypy 和相关测试。

### 7. 跨语言行为等价测试

- 扩展 `tests/test_migration_consistency.py`，不再只覆盖基础 smoke。
- 增加 Kotlin fixture 或等价输入输出数据集。
- 覆盖以下关键场景：
  - core solver 状态映射
  - symbol operation 序列化、解析、化简、微分、积分
  - CSP1D cutting plan generation 和 pricing
  - BPP3D column generation 生命周期
  - Gantt task/bunch branch-and-price 核心路径
  - persistence repository 契约

测试数据建议：

- `tests/fixtures/kotlin_parity/` 保存跨语言输入输出。
- 使用 JSON 或 CSV 保存确定性 fixture，避免依赖 Kotlin 运行时。
- 对 solver 相关测试使用 mock solver 或可重复的小模型，真实 solver 集成测试单独标记。
- 每个 parity fixture 需要说明来源：Kotlin 单测、示例、人工构造或业务样例。

## 决策点

以下问题需要在执行前做出明确决策：

1. CPLEX、Hexaly、Lingo、Mosek、OptVerse 是否纳入 Python 支持范围。
2. Gurobi11 是否作为独立 adapter，还是统一由 Gurobi adapter 兼容。
3. Kafka 是否归入 persistence/plugin 范畴，还是单独建立 message plugin 包。
4. Ktorm/MyBatis 的迁移目标是 SQLAlchemy、SQLModel，还是仅迁移 repository expression 能力。
5. `math/symbol/operation` 的公共 DSL 是否同时提供异常版和 Result 版，还是统一 Result 版。
6. Kotlin 中仅因内部 DSL 存在的 builder API，在 Python 中是否保留同名入口或改为 dataclass/factory。

## 风险

| 风险 | 影响 | 缓解方式 |
|------|------|----------|
| 商业 solver SDK 不可安装或 CI 不可用 | adapter 难以做真实集成测试 | 使用 optional dependency、importorskip、mock solver contract test |
| 文档先行声称完成 | 用户误以为 partial 模块可生产使用 | 用迁移矩阵驱动 README/docs 状态 |
| mypy ignore 隐藏 framework 类型错误 | 静态正确性证明不足 | 按模块逐步移除 ignore |
| Kotlin DSL 与 Python 风格差异过大 | API parity 难判定 | 以外部功能和 fixture 输出为验收依据 |
| solver 数值差异 | 跨语言输出不完全一致 | 对目标值、方案可行性、KPI 使用容差和结构性断言 |
| 迁移矩阵失效 | 清单再次与代码脱节 | 将矩阵接入门禁脚本和文档检查 |

## 计划

### 第 1 阶段：建立事实来源

1. 新增 `migration-matrix.md`。
2. 将 Kotlin 根模块、core-plugin、framework-plugin、framework 领域模块全部映射到 Python。
3. 标注每项状态：`complete`、`partial`、`pythonic-replacement`、`excluded`。
4. 让迁移门禁脚本读取矩阵文件。
5. 修正文档中与当前状态冲突的完成度描述。

交付物：

- `migration-matrix.md`
- 更新后的 `scripts/check_migration_gates.py`
- 修正后的 `CHANGELOG.md`
- README/docs 中 partial 状态说明

完成标志：

- 门禁脚本不再依赖硬编码 partial 清单。
- 矩阵中没有未分类 Kotlin 模块。
- 文档中没有未经矩阵支撑的完整迁移声明。

### 第 2 阶段：处理高优先级缺口

1. 先处理 solver/plugin 明确缺口。
2. 再处理 framework-plugin 后端缺口。
3. 同步补齐 optional dependency、导入测试、文档示例和 CI 跳过策略。

交付物：

- solver 支持决策记录。
- framework-plugin 支持决策记录。
- 新增或排除的 solver/plugin 均体现在迁移矩阵中。

完成标志：

- Python 支持的 solver 与 optional dependencies 一致。
- 不支持的 Kotlin plugin 有明确排除说明。
- docs 中 candidate、implemented、excluded 状态与矩阵一致。

### 第 3 阶段：收敛 CSP1D

1. 对齐 Kotlin pricing lifecycle。
2. 补齐 reduced-cost pricing 等价能力。
3. 补足 shadow price、final MILP、recovery、partial solution 测试。
4. 将 CSP1D partial 子模块从 partial 清单移除。

交付物：

- reduced-cost pricing Python 入口或替代 API。
- CSP1D pricing parity tests。
- CSP1D final MILP/recovery tests。
- 更新后的 CSP1D 文档。

完成标志：

- CSP1D cutting plan generation 和 material 子模块不再 partial。
- CSP1D 关键生命周期测试覆盖成功、失败和 partial solution。

### 第 4 阶段：逐模块移除 partial 与 mypy ignore

1. 按风险顺序处理 `persistence`、`network_scheduling`、`csp2d`、`bpp1d`、`bpp2d`。
2. 再处理 `math/symbol/operation` 的 Result 化和 DSL 边界。
3. 每完成一个模块，移除对应 mypy ignore 或 partial 标记。

交付物：

- 每个模块的功能矩阵、测试和文档。
- 移除或缩小后的 mypy overrides。
- Result 风格错误处理复核记录。

完成标志：

- `pyproject.toml` 不再整体 ignore 业务 framework 模块。
- partial 模块清单清空或仅剩明确 excluded 项。

### 第 5 阶段：最终验收

1. 全量运行测试、ruff、mypy 和迁移门禁。
2. 检查 docs、README、CHANGELOG 与迁移矩阵一致。
3. 对明确不迁移项给出可审计的排除理由。
4. 发布前生成最终迁移报告。

交付物：

- 最终迁移完成度报告。
- 全量命令输出摘要。
- 已知限制和排除项列表。

完成标志：

- 可以基于矩阵和测试结果明确说明“哪些已完成，哪些明确不支持”。
- 不再使用泛化的“Complete 1:1 migration”描述掩盖排除项或 Python 风格替代项。

## 清单

### 阶段 1：事实来源与文档一致性

- [ ] 新增 `migration-matrix.md`。
- [ ] 改造 `scripts/check_migration_gates.py`，从迁移矩阵读取 partial/excluded。
- [ ] 修正 `CHANGELOG.md` 中不准确的完整迁移声明。
- [ ] 修正 README/docs 中 partial 模块的状态说明。
- [ ] 将当前 `PARTIAL_MODULES` 迁入迁移矩阵。
- [ ] 为 `excluded` 状态定义统一格式和必填说明。
- [ ] 增加文档状态检查，避免 docs 声称 complete 但矩阵仍 partial。

### 阶段 2：Solver 与 Plugin

- [ ] 评估并处理 CPLEX solver adapter。
- [ ] 评估并处理 Hexaly solver adapter。
- [ ] 评估并处理 Lingo solver adapter。
- [ ] 评估并处理 Mosek solver adapter。
- [ ] 评估并处理 OptVerse solver adapter。
- [ ] 评估 Gurobi11 是否需要独立兼容入口。
- [ ] 为新增 solver 补 optional dependency。
- [ ] 为新增 solver 补 importorskip 测试。
- [ ] 为排除 solver 写明排除原因。
- [ ] 评估并处理 Kafka framework plugin。
- [ ] 评估并处理 MongoDB persistence plugin。
- [ ] 评估并处理 MySQL persistence plugin。
- [ ] 评估 Ktorm/MyBatis 的 Python 替代方案。
- [ ] 评估 persistence expression KSP 的 Python 替代方案。
- [ ] 为新增 framework plugin 补 repository/message contract tests。
- [ ] 更新 persistence/plugin 文档状态。

### 阶段 3：CSP1D

- [ ] 补齐 CSP1D reduced-cost pricing 等价入口。
- [ ] 补齐 CSP1D pricing parity 测试。
- [ ] 补齐 CSP1D final MILP 和 recovery parity 测试。
- [ ] 补齐 CSP1D canonical key 和 candidate filter 测试。
- [ ] 补齐 CSP1D shadow price 缺项和异常路径测试。
- [ ] 补齐 CSP1D partial solution 测试。
- [ ] 收敛 `framework/csp1d/domain/cutting_plan_generation` partial 状态。
- [ ] 收敛 `framework/csp1d/domain/material` partial 状态。

### 阶段 4：Partial 模块收敛

- [ ] 收敛 `framework/persistence` partial 状态。
- [ ] 收敛 `framework/network_scheduling` partial 状态。
- [ ] 收敛 `framework/csp2d` partial 状态。
- [ ] 收敛 `framework/bpp1d` partial 状态。
- [ ] 收敛 `framework/bpp2d` partial 状态。
- [ ] 收敛 `math/symbol/operation` partial 状态。
- [ ] 移除 framework 模块的 `ignore_errors = true`。

### 阶段 5：Parity Tests 与最终报告

- [ ] 扩展 `tests/test_migration_consistency.py` 为真实行为等价测试。
- [ ] 补充跨语言 fixture 或等价输入输出样例。
- [ ] 生成最终迁移完成度报告。
- [ ] 全量执行 pytest、ruff、mypy、迁移门禁。
- [ ] 整理发布前已知限制。

## 验收标准

### 全局质量门禁

以下命令必须全部通过：

```powershell
.venv\Scripts\python.exe --version
.venv\Scripts\python.exe scripts/check_migration_gates.py
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m mypy ospf_python
.venv\Scripts\python.exe -m pytest
```

命令输出要求：

- Python 版本必须为 3.13.x。
- 迁移门禁无 TODO、NotImplementedError、stub/placeholder、非法 bare pass。
- ruff 无 lint 失败。
- mypy 不依赖业务 framework 模块整体 ignore。
- pytest 全量通过，允许的 skipped 必须有明确原因。

### 完整性验收

- `migration-matrix.md` 覆盖 Kotlin 根模块、core-plugin、framework-plugin 和所有 framework
  领域模块。
- 每个 Kotlin 功能点都有 Python 对应实现、Python 风格替代说明或明确排除说明。
- partial 模块清单为空，或仅包含有明确验收期限和排除说明的条目。
- README、README_ch、docs、CHANGELOG 与迁移矩阵状态一致。
- solver optional dependencies 与已支持 solver adapter 一一对应。
- persistence/plugin 文档中的 implemented 状态必须有实际模块和测试支撑。

### 正确性验收

- `pyproject.toml` 不再对业务 framework 模块使用整体 `ignore_errors = true`。
- 业务失败路径优先返回 Result，不直接抛出异常。
- 所有新增或迁移的 public API 有针对性单元测试。
- CSP1D、BPP3D、Gantt 的列生成或分支定价核心生命周期至少覆盖：
  - register
  - add columns
  - remove columns
  - refresh or extract shadow price
  - final MILP or final solve
  - extract solution
  - failure or partial solution path
- 跨语言一致性测试不只验证 smoke，而是覆盖关键输入输出和边界场景。

### 模块级验收模板

每个模块完成时需要记录：

| 项目 | 验收问题 |
|------|----------|
| 功能 | Kotlin 对应功能是否都有 Python 实现、替代或排除说明 |
| API | public API 是否稳定，是否避免迁移期命名 |
| 类型 | 是否通过 mypy，是否仍依赖局部或整体 ignore |
| 错误处理 | 失败路径是否返回 Result，异常是否属于允许例外 |
| 测试 | 是否覆盖正常、边界、失败和关键集成路径 |
| 文档 | README/docs 是否说明用法、限制和状态 |
| 示例 | 是否有最小可运行示例或 doc smoke |
| 兼容 | 与 Kotlin fixture 或预期行为是否一致 |

### 发布前验收

- 迁移矩阵中不存在状态不明的条目。
- 所有 `partial` 条目都有 issue、负责人或明确后续计划。
- 所有 `excluded` 条目都有原因、替代方案和影响说明。
- `CHANGELOG.md` 不再使用无法证明的完整迁移措辞。
- 最终报告能回答：
  - 已完整迁移哪些能力。
  - 哪些能力采用 Python 风格替代。
  - 哪些能力明确不支持。
  - 还剩哪些风险和限制。

## 近期行动建议

建议按以下顺序启动：

1. 先写 `migration-matrix.md`，把当前 partial、缺失 solver、缺失 plugin 全部显性化。
2. 修改 `check_migration_gates.py`，让门禁脚本读取矩阵。
3. 修正 CHANGELOG/README/docs 的完成度描述。
4. 处理 CSP1D `ReducedCostPricingGenerator` 等价能力，因为这是当前最明确的功能差距。
5. 选择一个较小 partial 模块试点移除 mypy ignore，例如 `persistence`。
6. 将试点流程固化后，再推广到 `network_scheduling`、`csp2d`、`bpp1d`、`bpp2d`。
