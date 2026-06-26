# Demo 2: 3D Bin Packing (Aviation)

[English](#overview) | [中文](#概述)

## Overview

Extended 3D bin packing for aviation business. Demonstrates framework extension points for aircraft/stowage/airworthiness contexts.

### Business Description

- **Domain**: 3D bin packing with aviation constraints
- **Contexts**: 11 domain contexts (aircraft, stowage, airworthiness, loading effectiveness, MAC, etc.)
- **Applications**: 4 applications (FullLoad, LoadingOrder, Predistribution, WeightRecommendation)
- **Solver**: Gurobi/SCIP via framework (importorskip for unavailable solvers)

### Usage

```python
from examples.framework_demo.demo2.application.full_load_application import (
    FullLoadApplication,
)
# Create application with framework solver
# Solve 3D bin packing with aviation constraints
```

### File Structure

```
demo2/
├── domain/
│   ├── aircraft/           # Aircraft model (16 files)
│   ├── stowage/            # Stowage planning (33 files)
│   ├── airworthiness_security/  # Airworthiness constraints (25 files)
│   ├── loading_effectiveness/   # Loading optimization (21 files)
│   ├── mac/                # Mean Aerodynamic Chord (6 files)
│   └── ...                 # 5 more contexts
├── application/            # 4 application services
└── infrastructure/         # DTOs and adapters
```

---

## 概述

扩展 3D 装箱用于航空业务。演示框架扩展点在飞机/船舱/适航上下文中的应用。

### 业务说明

- **领域**: 航空约束的 3D 装箱
- **上下文**: 11 个领域上下文（飞机、船舱、适航、配载有效性、MAC 等）
- **应用**: 4 个应用（满载、装载顺序、预分配、重量建议）
- **求解器**: 通过框架使用 Gurobi/SCIP（不可用时 importorskip）

### 文件结构

参见上方英文部分。
