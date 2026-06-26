# Demo 3: CSP Column Generation

[English](#overview) | [中文](#概述)

## Overview

1D Cutting Stock Problem (CSP) with column generation. Demonstrates CSP1D framework with real solver integration.

### Business Description

- **Domain**: 1D cutting stock with column generation
- **Parameters**: rawLength=1000, 4 product demands (450/97, 360/610, 310/395, 140/211)
- **Solver**: Gurobi/SCIP via CSP1D framework column generation lifecycle

### Usage

```python
from examples.framework_demo.demo3.main import run_demo

result = run_demo()
print(f"Iterations: {result['iterations']}")
print(f"Converged: {result['converged']}")
print(f"Columns: {result['columns']}")
```

### File Structure

```
demo3/
└── main.py    # CSP column generation with 4-product demand instance
```

---

## 概述

一维切割库存问题（CSP）与列生成。演示 CSP1D 框架与真实求解器集成。

### 业务说明

- **领域**: 列生成的一维切割库存
- **参数**: rawLength=1000，4 个产品需求（450/97, 360/610, 310/395, 140/211）
- **求解器**: 通过 CSP1D 框架列生成生命周期使用 Gurobi/SCIP

### 文件结构

参见上方英文部分。
