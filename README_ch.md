# ospf-python

[English](README.md)

ospf-kotlin 优化框架的 Python 实现。

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
uv sync

# 运行测试
uv run pytest -q

# 运行覆盖率
uv run pytest --cov=ospf_python --cov-report=term-missing
```

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

### 错误处理（Result 模式）

```python
from ospf_python.utils.functional import Result, Ok, Failed
from ospf_python.utils.error import ErrorCode
```

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
