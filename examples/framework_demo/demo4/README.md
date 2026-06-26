# Demo 4: Gantt Scheduling

[English](#overview) | [中文](#概述)

## Overview

Full gantt scheduling business with task/crew/passenger/bunch/cargo/rule contexts. Demonstrates gantt framework with real solver integration.

### Business Description

- **Domain**: Gantt scheduling with multiple resource types
- **Contexts**: 8 domain contexts (task, crew, passenger, bunch_compilation, bunch_generation, bunch_selection, cargo, rule)
- **Application**: SchedulingApplication (269 lines) with BranchAndPrice column generation
- **Solver**: Gurobi/SCIP via framework (importorskip for unavailable solvers)

### Usage

```python
from examples.framework_demo.demo4.application.scheduling_application import (
    SchedulingApplication,
)
# Create application with framework solver
# Solve gantt scheduling instance
```

### File Structure

```
demo4/
├── domain/
│   ├── task/               # Flight task management (17 files)
│   ├── crew/               # Crew management (9 files)
│   ├── passenger/          # Passenger management (13 files)
│   ├── bunch_compilation/  # Bunch compilation (12 files)
│   ├── bunch_generation/   # Bunch generation (10 files)
│   ├── bunch_selection/    # Bunch selection (2 files)
│   ├── cargo/              # Cargo management (2 files)
│   └── rule/               # Business rules (10 files)
└── application/
    └── scheduling_application.py  # Main orchestration
```

---

## 概述

完整的甘特调度业务，包含任务/机组/乘客/束编组/货物/规则上下文。演示 gantt 框架与真实求解器集成。

### 业务说明

- **领域**: 多资源类型的甘特调度
- **上下文**: 8 个领域上下文（任务、机组、乘客、束编组、束生成、束选择、货物、规则）
- **应用**: 调度应用（269 行）使用 BranchAndPrice 列生成
- **求解器**: 通过框架使用 Gurobi/SCIP（不可用时 importorskip）

### 文件结构

参见上方英文部分。
