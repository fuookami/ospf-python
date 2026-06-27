# ospf-python 迁移清单 / Migration Matrix

**基线:** ospf-kotlin (main baseline), ospf-rust (reference)
**目标:** Python 3.13+
**生成时间:** 2026-06-26

## 状态说明

| 状态 | 含义 |
|------|------|
| done | 功能、API、测试都对齐 |
| partial | 有实现但行为缺失 |
| stub | 只有空类、空返回、TODO、NotImplementedError |
| missing | Python 无对应包/模块 |
| excluded | 明确决定不迁移，并写原因 |

## 模块总览

| 模块 | Kotlin 文件数 | Python 文件数 | 实际实现 | Stub | 状态 |
|------|--------------|--------------|---------|------|------|
| utils | 47 | 47 | 45 | 2 | partial |
| multiarray | 9 | 9 | 9 | 0 | done |
| math | 278 | 278 | 277 | 1 | partial |
| quantities | 43 | 43 | 43 | 0 | done |
| core | 178 | 178 | 178 | 0 | done |
| framework | 374 | 374 | 374 | 0 | done |
| **总计** | **929** | **929** | **926** | **3** | **partial** |

## Stub 文件清单

| 文件 | 行数 | 问题 | 优先级 |
|------|------|------|--------|
| `utils/concept/move.py` | 2 | 空类 | P2 |
| `utils/concept/swap.py` | 5 | 空类 | P2 |
| `math/collection_aliases.py` | 6 | 类型别名，import 路径问题 | P1 |

## TODO/NotImplementedError 清单

| 类型 | 数量 | 优先级 |
|------|------|--------|
| TODO | 74 | P2 |
| NotImplementedError | 14 | P1 |

## 框架模块状态

| 框架 | 状态 | 说明 |
|------|------|------|
| bpp3d | done | 103 文件，真实实现 |
| csp1d | done | 84 文件，列生成生命周期 |
| gantt_scheduling | done | 134 文件，BranchAndPrice |

## 求解器状态

| 求解器 | 状态 | 说明 |
|--------|------|------|
| MockSolver | done | 测试用 |
| GurobiSolver | done | gurobipy 集成 |
| ScipSolver | done | pyscipopt 集成 |
| CoptSolver | partial | 需许可证 |
| MindOptSolver | partial | 需许可证 |

## 测试状态

| 指标 | 值 |
|------|-----|
| 测试文件 | 298 |
| 测试通过 | 5007 |
| 覆盖率 | 91% |
| ruff | clean |
| mypy | clean (strict) |

## 下一步

1. **阶段 1:** 修测试策略（stub 测试改为失败驱动）
2. **阶段 2:** 补齐 P0 正确性缺口（math.symbol.operation/parse/serde）
3. **阶段 3:** 补齐缺失 framework 模块（bpp1d/bpp2d/csp2d/network_scheduling）
4. **阶段 4:** 补齐插件体系
5. **阶段 5:** 统一 public API
6. **阶段 6:** 验收标准
