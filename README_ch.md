# ospf-python

ospf-kotlin 优化框架的 Python 实现。

[English](README.md)

## 概述

ospf-python 是一个综合性的优化建模框架，提供：

- **核心建模**：基于 MetaModel 的优化，支持变量/约束/目标注册
- **求解器抽象**：统一接口支持多种求解器（Gurobi、SCIP、COPT、MindOpt）
- **领域框架**：预构建的框架：
  - 三维装箱（BPP3D）
  - 一维下料（CSP1D）
  - 甘特调度
- **数学库**：代数、几何、符号计算和混沌理论
- **物理量系统**：类型安全的单位系统，支持量纲分析

## 安装

```bash
# 基本安装
uv pip install -e .

# 包含求解器支持
uv pip install -e ".[gurobi,scip]"

# 开发环境
uv pip install -e ".[dev]"
```

## 快速开始

```python
from ospf_python.core.model import MetaModel
from ospf_python.core.variable import LinearVariable

# 创建模型
model = MetaModel("my_model")

# 添加变量
x = model.add_variable("x", lower_bound=0)
y = model.add_variable("y", lower_bound=0)

# 设置目标
model.set_objective(x + y, minimize=True)

# 添加约束
model.add_constraint(x + 2 * y >= 10)

# 求解
result = model.solve()
print(f"最优值: {result.objective_value}")
```

## 项目结构

```
ospf_python/
├── utils/          # 错误处理、Result 模式、函数式工具
├── multiarray/     # 多维数组抽象（numpy 后端）
├── math/           # 代数、几何、符号计算、混沌
├── quantities/     # 物理量和单位系统
├── core/           # 核心建模框架
│   ├── variable/   # 变量类型
│   ├── token/      # Token 系统
│   ├── symbol/     # 符号函数
│   ├── model/      # MetaModel 及模型变体
│   ├── solver/     # 求解器抽象和 mock
│   └── plugin/     # 求解器适配器（gurobi、scip、copt、mindopt）
└── framework/      # 领域特定框架
    ├── bpp3d/      # 三维装箱
    ├── csp1d/      # 一维下料
    └── gantt_scheduling/  # 甘特调度
```

## 系统要求

- Python 3.13+
- NumPy 1.26+
- Pydantic 2.0+
- Returns 0.22+

## 许可证

MIT
