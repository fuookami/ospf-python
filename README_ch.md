# ospf-python

[English](README.md)

ospf-kotlin 优化框架的 Python 实现。

## 概述

ospf-python 是一个综合优化建模框架，支持：
- 线性规划 (LP)
- 混合整数规划 (MILP)
- 二次规划 (QP)
- 领域框架：三维装箱、一维下料、甘特调度

## 模块结构

| 模块 | 说明 |
|------|------|
| `ospf_python.utils` | 错误处理（Result 模式）、函数式工具、协议 |
| `ospf_python.multiarray` | N 维数组（numpy 后端） |
| `ospf_python.math` | 代数、几何、组合、混沌映射、符号数学 |
| `ospf_python.quantities` | 物理量与单位系统 |
| `ospf_python.core` | 优化核心：变量、token、模型、求解器 |
| `ospf_python.framework` | 领域框架：bpp3d、csp1d、gantt_scheduling |

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

## 求解器

| 求解器 | 状态 |
|--------|------|
| MockSolver | 内置，测试用 |
| gurobi | 通过 gurobipy |
| scip | 通过 pyscipopt |
| copt | 通过 coptpy |
| mindopt | 通过 mindoptpy |

## 快速开始

```bash
uv sync
uv run pytest -q
```

## 许可证

MIT
