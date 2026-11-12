# ospf-python

[English](README.md)

OSPF 的 Python 接口，正从独立实现迁移为 Rust 绑定。

## Rust 绑定迁移

包已采用 Maturin/PyO3 混合构建，私有扩展 `ospf_python._native` 链接固定 revision 的
`ospf-rust`。当前公开建模和领域 API 仍使用原 Python 实现；扩展导入成功不代表内核
替换或真实 Rust 求解后端已经完成。

源码构建需要 Rustup、`rust-toolchain.toml` 指定的工具链、平台链接器，以及获取固定
Rust 源码和依赖的网络。不要求相邻的 `ospf-rust` checkout。基础安装不要求 solver SDK
或许可证。原生 Gurobi 支持以 Rust 的 10/11/12 feature 为准，不要求 13。
可选 Python SDK extras 仅服务尚未迁移的 Python adapter，不能启用已编译扩展的 Rust feature。

本地文档链接和示例位于源码仓库及源码包中，不随已安装的 wheel 分发。在包索引
页面可从[源码仓库](https://github.com/fuookami/ospf-python)进入文档。运行源码树
中的示例前，请先按原生开发指南构建该源码树的扩展。

迁移边界见[绑定决策](docs/migration/decisions/0001-binding-boundaries.md)和
[能力映射](docs/migration/api-map.toml)。

私有 BPP1D `PackingContext` 可在固定 Rust 候选搜索及有限候选整数求解中接收
Python 策略。策略读取独立组合快照并返回 `bool` 或 `Ok(bool)`；私有求解也可
接收声明式精确线性模型扩展，注册及指标回调只读取独立快照，失败保留为显式
Result。私有可重建列池可求解固定版本 LP 和捕获代次的独立最终整数模型，并分别
复核精确源方案；公共 FFD 入口尚未切换，完整列生成、可信对偶价格及全局最优
证明也尚未提供。见
[BPP1D 合同](docs/migration/bpp1d-contract.md)、
`examples/bpp1d_pattern_policy_example.py` 和
`examples/bpp1d_model_extension_example.py`、
`examples/bpp1d_column_pool_example.py`。

常规数学 `clamp` 已接通固定 Rust 排序候选并返回现有 Result，使用选中的原对象前
须先处理成功或失败；工具模块的同名函数不变。见[限制合同](docs/migration/clamp-contract.md)
和 `examples/clamp_binding_example.py`；性能与跨平台验收仍待完成。

常规数学 `min_of`、`max_of` 和 `min_max_of` 同样返回 Result，并委托固定 Rust
排序；当前候选慢于原内置算法，升级前请阅读[极值合同](docs/migration/ordinary-extrema-contract.md)。

公共数组默认迭代已将共享/live 槽位读取委托原生协议适配器，保留 Python generator 接口
和原 ndarray 共享。隐式 `.item()` 仅针对真正的 NumPy scalar，普通对象及 ndarray 叶
保持身份。这不是完整数组内核切换；兼容变更见[迭代迁移说明](docs/migration/public-iteration-cutover.md)。

公共数组另增返回现有 Result 的 `at(indices=...)`，可变数组另增
`set_at(indices=..., value=...)`，由固定 Rust 严格校验坐标并访问原共享 ndarray。
旧 `get/set` 签名不变，自定义形状必须显式确认标准布局；见[受检读写合同](docs/migration/public-array-access.md)。
另有 `at_many(indices=[...])` 先检查整批坐标再收集共享槽位，保留请求次序与重复坐标，
但不承诺并发原子快照。

两个公共数组类的 `to_list()` 已接通返回现有 Result 的原生源码候选，使用前须显式消费，
例如 `array.to_list().unwrap()`。标准逻辑嵌套布局由固定 Rust 规划，修复列布局误按 C-order
导出；NumPy 仅负责 dtype 序列化，自定义 hook 保留其外部协议。完整调用性能/发行及
权威存储仍待验收，见[嵌套导出合同](docs/migration/public-nested-export.md)。

公共 `fast_sum` 仍走原 NumPy 实现；[替换合同](docs/migration/fast-sum-contract.md)
记录 dtype、布局、错误边界及已知精度缺陷，兼容测试和纯 Rust 计时探针不代表归约内核已经切换。

`combinations(items, k)` / `permutations(items, k)` 及异步入口共用固定 Rust 选择内核，
显式返回现有 Result；先消费成功值再遍历，位置顺序、不透明叶身份及 live 自定义
索引协议保留。[调用方升级说明](docs/migration/selection-contract.md)
解释原始错误来源和 executor 取消边界。运行 `python -m examples.selection_example`
可体验四个入口与精确 `Quantity[Fraction]`；已有事件循环应直接 `await main_async()`。
Windows CPython3.13 的操作验证不代表 Linux、Gurobi11/12、其余数学/数组迁移或
全领域资源预算已经完成。

公共 `cross(*iterables)` 现在返回现有 Result，笛卡尔枚举委托固定 Rust 内核。
调用方需先消费成功列表，再进行遍历；任意 iterable、顺序、重复项和不透明叶身份保持不变。
升级说明见[合同](docs/migration/cross-contract.md)，精确物理量示例见
`examples/cartesian_product_example.py`，不会隐式转成 float。

公共 `MultiArray.reduce(f)` 与 `MutableMultiArray.reduce(f)` 现在返回现有 Result，
使用结果前须先消费成功/失败。原生边界由固定 Rust 索引驱动物理次序的 live 左折叠，
保留 Python 回调、精确物理量及不透明结果身份；不是 `fast_sum` 或完整数组存储迁移。
见[归约合同](docs/migration/public-reduction-cutover.md)与 `examples/array_reduction_example.py`。

两个公共数组类的 eager `map(f)` 和 `flat_map(f)` 也返回现有 Result。
原生物理遍历保留 live 读取和任意 Python 回调，输出 dtype/广播/array 协议仍由 NumPy
负责。扩展数据保持最终源 shape，包括历史尺寸不一致行为；不是 lazy view 映射或完整
存储迁移。见[映射合同](docs/migration/public-mapping-cutover.md)与
`examples/array_mapping_example.py`。

公共 `MappedMultiArrayView.materialize()` 返回现有 Result，默认采用原生 live 坐标采样
和固定 Rust 输出布局发布，修复列布局物化的坐标错位，保留 C-order 回调与 NumPy 输出
探测次序。普通 view 物化与 reshape/flatten 按各自合同独立验收；见
[物化合同](docs/migration/public-mapped-materialization.md)及
`examples/mapped_materialization_example.py`。

普通 `MultiArrayView.materialize()` 已接通原生源码候选并返回现有 Result，使用时显式
消费，例如 `view.materialize().unwrap()`。固定 Rust 校验 offset 后剩余区域并规划存储
索引，复制保留 dtype、不透明叶及附加存储轴；非零 offset 不再错误复制全源。
完整调用性能/发行及 view 的 shape/get 权威仍待验收，见
[普通视图合同](docs/migration/public-view-materialization.md)与
`examples/view_materialization_example.py`。
标准存储路径按固定 Rust 步长提供的受检描述符一次复制区域，不逐槽分配 BigInt/索引；
自定义存储和 ndarray 子类保留实际 copy/take 协议，NumPy 仍只承担 dtype 感知存储边界。
原生 view 与存储变换共用既有 Result 工厂发布，不保留调用 owner；全零 offset 仍校验
实时元数据，但不再构造不会用于索引的稠密形状。

公共 `MultiArray.transpose()` 与 `MutableMultiArray.transpose()` 也显式返回现有
Result：固定 Rust 坐标与标准布局索引替代旧 Python 坐标循环，同时保留不可变源逐槽
live、可变源预复制、NumPy dtype/赋值及自定义 shape/整数步长协议。这不代表完整共享
存储切换，见[转置合同](docs/migration/public-transpose-cutover.md)。

公共 `reshape/flatten` 已接通原生 shape/存储编排，显式返回现有 Result。
此前候选与完整旧版本对照时 reshape 通过本机性能门槛，flatten 超预算。
当前 shape.size 候选的 reshape 未稳定通过本机门槛，flatten 仍超预算；求解器与
隔离发行也须重新验收，不能沿用旧测量。
绑定保留当前 DynShape 的分配/初始化
及 Ok 构造 hook，包括绑定导入前的替换。NumPy 仍负责 dtype 感知复制；完整存储、
跨平台和长期资源另行验收，见[存储变换合同](docs/migration/storage-transform-contract.md)。

数组迭代、映射、归约和转置也读取变更后的 shape.size，旧版本本机验收须重新验证。

公共 Shape dataclass 的 size、strides 和宽松扁平索引现已接通原生计算候选，保留字段、
pickle 路径与稀疏整数元数据；包门面按需导出，消除 shape/绑定导入循环。机器整数元数据
避免预先转换 BigInt 及重复布局探测。完整调用预算、发行与公开存储权威仍须分别验收，
尚不能视为完整的形状或存储切换，见
[公共形状合同](docs/migration/public-shape-contract.md)。

公共 `Rational` 的源码计算候选已将规范化、算术与精确顺序比较委托固定 Rust
BigRational/OSPF traits，保留 frozen 双字段数据类、旧零值兼容及 Python copy/pickle
对象图协议；严格 Result 运算仍独立。子类构造器现在收到规范结果整数对，而非未约分
中间值。原生构造作用域以临时身份证明避免同一结果对象重复规范化，仍实际执行子类
构造与后处理，不持久缓存数值。完整调用性能与跨平台发行仍是验收门槛，不能用私有批量速度抵销；见
[公共有理数合同](docs/migration/public-rational-contract.md)。
四个公开整数类型也已接通固定 Rust 算术/比较的源码候选，使用临时任意精度整数，
分别保留无上限、钳制及负值拒绝政策，以及 Python 子类钩子、构造顺序和 dataclass/pickle
协议。外部数值仍使用自身 Python 数值槽，不提供旧整数 backend 或持久值镜像。
完整调用性能、领域/资源预算及发行仍待验收，见
[整数合同](docs/migration/public-integer-contract.md)和[示例](examples/integer_binding_example.py)。

公共 `Quantity.to(target, *, context=None, exact=True, numeric_adapter=None)` 已默认
接通返回现有 Result 的源码候选，使用时须显式消费成功/失败，不能直接把返回对象当
Quantity。普通内置单位使用固定 Rust 单位数学和量纲检查，支持精确整数/Fraction/
Rational/Decimal 及显式有限 Float64/Floating；整数非整结果提升 Fraction。Decimal
采用规范出口（不保留原 quantum、尾零及负零），仅 exact=False 允许舍入。开放单位
回调继续可扩展，公开 `NumericAdapter[V]` 显式连接自定义数值表示，不隐式转 float；
符号零遵循固定 Rust 运算次序。这不是完整 Quantity 切换：RG-008、helpers、温差、
小数维度、完整调用预算及全部领域/平台仍待验收。见
[数量合同](docs/migration/quantity-unit-contract.md)，可运行
`python -m examples.quantity_conversion_example` 体验无 solver 的自然入口。

数量 `min_quantity`/`max_quantity` 和 `QuantityValueRange.contains` 的默认源码候选也
显式返回 Result。极值保留首个平局的原输入对象；内置单位采用 Rust 精确 SI 比较及
量纲检查，不隐式转 float、不读取 Decimal 运算上下文。NumericAdapter 显式导入自定义
数值；开放单位保持 Python rich comparison，只有实际混合边界将原生精确 SI 键导出
规范 Fraction。contains 须消费 `.unwrap()` 后的布尔值，不能直接判断 Result 对象。
时长、checked 四则、RG-008、完整预算和领域/平台仍待验收，不能据此宣布完整 helper
切换。见[极值/范围合同](docs/migration/quantity-ordering-contract.md)，可运行
`python -m examples.quantity_ordering_example`。

`from_hours`、`from_minutes`、`to_timedelta` 的源码候选也显式返回 Result，例如
`to_timedelta(from_hours(1).unwrap()).unwrap()` 得到有符号 timedelta。内置换算复用
固定 Rust 单位通道；精确 SI 值不经 float 舍入到微秒，Float64 则保留 CPython timedelta
舍入。已知非时间量纲失败，开放数值/单位/工厂协议保留明确边界。这不代表完整时长或
Quantity 正式切换；见[时长合同](docs/migration/quantity-duration-contract.md)及
`python -m examples.quantity_duration_example`。完整预算、发行、checked 四则、RG-008、
全部领域和平台要求继续保留。

Windows solver 版 wheel 须在原生导入前注册 SDK DLL 搜索目录；`tests/conftest.py`
在收集任意测试前注册显式配置的 `OSPF_NATIVE_DLL_DIRS`，不依赖 native 测试先导入。

Linux solver 版 wheel 将 SCIP/Gurobi 运行库保留在外部，并使用原生 `linux`
wheel 标签；此类 wheel 有意不支持直接上传 PyPI。固定 revision 的 SCIP crate
还会把构建时 `SCIPOPTDIR/lib` 写入 RPATH，因此当前产物要求同路径存在匹配运行库，
否则须用部署环境的 `SCIPOPTDIR` 重新构建。solver 版 sdist 重建由
`scripts/verify_binding_distribution.py` 自动选择该策略。

## 概述

ospf-python 是一个综合优化建模框架，支持：
- 线性规划 (LP)
- 混合整数规划 (MILP)
- 二次规划 (QP)
- 领域框架：装箱、下料、调度
- 符号数学运算（含 LaTeX 渲染）
- 持久化插件（SQLite、Redis）

## 安装

```bash
# 克隆并安装
git clone <repo-url>
cd ospf-python
uv sync --extra dev

# 运行测试
uv run pytest -q

# 运行覆盖率
uv run pytest --cov=ospf_python --cov-report=term-missing
```

使用现有 Python SCIP adapter 时额外安装 `--extra scip`；这不启用 Rust SCIP 后端。
私有原型的源码构建、DLL 搜索及测试命令见[原生开发指南](docs/migration/native-development.md)，
这些命令不会切换公共核心。将原型用于完整求解前，请先核对[上游语义缺口](docs/migration/rust-gaps.md)。

## 模块结构

| 模块 | 说明 |
|------|------|
| `ospf_python.utils` | 错误处理（Result 模式）、函数式工具、协议 |
| `ospf_python.multiarray` | N 维数组（numpy 后端） |
| `ospf_python.math` | 代数、几何、组合、混沌映射、符号数学 |
| `ospf_python.quantities` | 物理量与单位系统 |
| `ospf_python.core` | 优化核心：变量、token、模型、求解器 |
| `ospf_python.framework` | 领域框架（见下表） |

## 领域框架

| 模块 | 说明 | 示例 |
|------|------|------|
| `framework.bpp1d` | 一维装箱 — 将物品装入箱中 | `examples/bpp1d_example.py` |
| `framework.bpp2d` | 二维装箱 — 放置矩形/圆形 | `examples/bpp2d_example.py` |
| `framework.bpp3d` | 三维装箱 — 列生成算法 | — |
| `framework.csp1d` | 一维下料 — 优化材料使用 | — |
| `framework.csp2d` | 二维下料 — 直切方案 | `examples/csp2d_example.py` |
| `framework.gantt_scheduling` | 甘特图调度 — 资源约束 | — |
| `framework.network_scheduling` | 网络排程 — 最短路径、最大流 | `examples/network_scheduling_example.py` |

## 数学符号运算

`math.symbol.operation` 模块提供符号数学能力：

```python
from ospf_python.math.symbol.operation.differentiate import Differentiator
from ospf_python.math.symbol.operation.evaluate import PolynomialEvaluator
from ospf_python.math.symbol.operation.latex import LatexRenderer
from ospf_python.math.symbol.operation.quick_dsl import QuickDsl
from ospf_python.math.symbol.polynomial.canonical_polynomial import CanonicalPolynomial

dsl = QuickDsl(factory=CanonicalPolynomial)
ev = PolynomialEvaluator(factory=CanonicalPolynomial)

x = dsl.var("x")
poly = dsl.sum(dsl.product(x, x), dsl.constant(1.0))  # x^2 + 1
val = ev.evaluate(poly, {"x": 3.0})  # 10.0
```

完整示例见 `examples/math_symbol_example.py`。

### 可用运算

| 运算 | 模块 | 说明 |
|------|------|------|
| 求导 | `operation.differentiate` | 符号求导 |
| 求值 | `operation.evaluate` | 在指定点求值 |
| LaTeX | `operation.latex` | 渲染为 LaTeX |
| 解析 | `operation.parse` | 解析字符串表达式 |
| 序列化 | `operation.serde` | 序列化/反序列化 |
| 规范化 | `operation.normalize` | 规范化多项式形式 |
| 转换 | `operation.convert` | 多项式类型转换 |
| 编译 | `operation.compile` | 编译为可调用函数 |
| 因式分解 | `operation.factorization` | 因式分解 |
| 快速 DSL | `operation.quick_dsl` | 流式 DSL 构建表达式 |
| FLT64 | `operation.flt64_quick_dsl` | Float64 优化 DSL |

## 持久化插件

| 后端 | 模块 | 状态 |
|------|------|------|
| SQLite | `framework.persistence.sqlite_repository` | 已实现 |
| Redis | `framework.persistence.redis_repository` | 已实现 |
| 基类 | `framework.persistence.repository` | 抽象基类 |

```python
from ospf_python.framework.persistence.sqlite_repository import SQLiteRepository
from ospf_python.framework.persistence.redis_repository import RedisRepository
```

## 求解器插件

| 求解器 | 状态 | 许可 | 说明 |
|--------|------|------|------|
| MockSolver | 内置 | N/A | 测试用 |
| Gurobi | 已实现 | 商业 | 通过 gurobipy |
| SCIP | 已实现 | 学术 | 通过 pyscipopt |
| COPT | 已实现 | 商业 | 通过 coptpy |
| MindOPT | 已实现 | 商业 | 通过 mindoptpy |

```python
from ospf_python.core.solver.mock_solver import MockSolver
from ospf_python.core.solver.gurobi.gurobi_solver import GurobiSolver
```

## Public API

### 核心建模

```python
from ospf_python.core.model.mechanism.meta_model import MetaModel
from ospf_python.core.solver.solver import Solver
from ospf_python.core.solver.mock_solver import MockSolver
```

### 物理量

```python
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.unit.length import METER, KILOMETER
from ospf_python.quantities.unit.mass import KILOGRAM
```

`ospf_python.quantities.Unit`（也可从 `ospf_python.quantities.unit.Unit` 导入）
公开现有单句柄 Rust 运行时单位门面。`Unit.create(...)`、直接 `to_si`/`from_si`
及 `Quantity.to(...)` 显式返回 `Result`，保留数值域与 `NumericAdapter` 政策，
不统一强制转换为浮点数。原生点减点实际生成的温差单位可以继续参与转换、极值、
范围和时长校验；已知 affine 点与线性差不能混用，零偏移的点也不例外。
详见[运行时单位合同](docs/migration/runtime-unit-contract.md)及
`examples/runtime_unit_example.py`。

自然 `Quantity.add/subtract/multiply/divide` 与默认运算符已接入同一受检 Rust 源码
候选，显式返回 `Result`。同量纲加减按实际单位换算，整数除法保持精确，点减点
生成真实温差单位，精确点差运算也保留 1/3 等循环比例；混合内置域按明确次序提升，精确域转浮点默认须无损，
`exact=False` 才显式放宽近似。开放数值协议和 `NumericAdapter` 仍是扩展点。
详见[四则合同](docs/migration/quantity-arithmetic-contract.md)及
`examples/quantity_arithmetic_example.py`。将结果用于数组回调或后续四则前，必须
先消费该层 `Result`，不要将控制值当作数量。

源码接通不代表整体切换验收完成。原生输出单位的完整 DTO/pickle/deepcopy、RG-008、
全部 223 预定义单位、性能预算和领域/平台验证
仍为必需；尚未实测的 Gurobi 11/12 与 Linux 组合不计为通过。

### 错误处理（Result 模式）

```python
from ospf_python.utils.functional import Result, Ok, Failed
from ospf_python.utils.error import ErrorCode
```

## 数量快照

`Quantity.to_dict()` / `.to_json()` 与 `Quantity.from_dict()` / `.from_json()`
以 Result 提供显式版本化纯数据 DTO，保留数值域、Float64 符号零、Decimal 表示、
登记家族字段及真实 native 输出单位 metadata；不隐式 float 化或执行 wire 指定类。
泛型 `SnapshotAdapter` 为开放值和单位分别提供显式策略。原生 Unit/Rational 已有
copy、deepcopy 和可信 pickle 源码候选，Unit 保留既有身份相等政策，不设隐蔽缓存。
`dataclasses.asdict` 仍是 Python 对象图，不冒充纯数据 DTO。原生精度缺口影响的
旧单位以 `native=null` 存档原字段，其后算术仍返回 DATA_LOSS，不走 Python fallback。
详见[快照合同](docs/migration/quantity-snapshot-contract.md)及
`examples/quantity_snapshot_example.py`。完整验收、性能缺口、RG-008 与平台/领域
迁移仍待完成。

## 扩展点

- **Extra Context**: 通过 `extra context` 模式添加自定义变量/约束
- **Extra Pipeline**: 通过 `pipeline` 模式添加自定义约束/目标
- **求解器适配器**: gurobi、scip、copt、mindopt（通过 `core.solver.<vendor>`）

## 泛型数值类型

- `RealNumber` — 泛型算法的抽象数值类型
- `Quantity[T]` — 带单位的物理量（`.rules §5`）
- 不同单位裸值不得混算

## 快速开始

```bash
uv sync
uv run pytest -q
```

## 许可证

MIT
