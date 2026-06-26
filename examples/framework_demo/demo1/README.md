# Demo 1: SSP Network Routing

[English](#overview) | [中文](#概述)

## Overview

Shortest Service Path (SSP) network routing with bandwidth allocation. Demonstrates framework extension points for network routing business.

### Business Description

- **Domain**: Network routing with bandwidth constraints
- **Contexts**: Bandwidth context (12 files) + Route context (9 files)
- **Application**: SSP solver (184 lines) using Dijkstra algorithm
- **Solver**: Python built-in (no external solver required)

### Usage

```python
from examples.framework_demo.demo1.interface import Demo1Interface

iface = Demo1Interface()
result = iface.create_and_solve(
    nodes=["A", "B", "C", "D"],
    edges=[
        ("e1", "A", "B", 10.0),
        ("e2", "B", "D", 10.0),
        ("e3", "A", "C", 10.0),
        ("e4", "C", "D", 10.0),
    ],
    services=[
        ("s1", "A", "D", 3.0),
        ("s2", "A", "D", 2.0),
    ],
)
print(f"Feasible: {result.feasible}")
print(f"Routes: {result.routes}")
print(f"Total cost: {result.total_cost}")
```

### File Structure

```
demo1/
├── bandwidth_context/     # Bandwidth allocation context
│   ├── model/            # EdgeBandwidth, NodeBandwidth, ServiceBandwidth
│   ├── limits/           # Demand, edge, service constraints
│   └── service/          # Pipeline generators
├── route_context/        # Network routing context
│   ├── model/            # Assignment, Graph, Service
│   └── limits/           # Node, service assignment constraints
├── application.py        # SSP solver orchestration
├── interface.py          # Public API
└── infrastructure/       # DTO definitions
```

---

## 概述

最短服务路径（SSP）网络路由与带宽分配。演示框架扩展点在网络路由业务中的应用。

### 业务说明

- **领域**: 带宽约束的网络路由
- **上下文**: 带宽上下文（12 文件）+ 路由上下文（9 文件）
- **应用**: SSP 求解器（184 行）使用 Dijkstra 算法
- **求解器**: Python 内置（无需外部求解器）

### 文件结构

参见上方英文部分。
