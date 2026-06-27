# ospf-python 迁移清单 / Migration Matrix

**基线:** ospf-kotlin (main baseline), ospf-rust (reference)
**目标:** Python 3.13+
**更新时间:** 2026-06-26

## 状态说明

| 状态 | 含义 |
|------|------|
| done | 功能、API、测试都对齐 |
| partial | 有实现但行为缺失 |
| stub | 只有空类、空返回、TODO、NotImplementedError |
| missing | Python 无对应包/模块 |
| excluded | 明确决定不迁移，并写原因 |

## 模块总览

| 模块 | Python 文件数 | 实际实现 | Stub | 测试 | 状态 |
|------|--------------|---------|------|------|------|
| utils | 47 | 45 | 2 | 13 | partial |
| multiarray | 9 | 9 | 0 | 21 | done |
| math | 278 | 277 | 1 | 79 | partial |
| quantities | 43 | 43 | 0 | 23 | done |
| core | 178 | 178 | 0 | 73 | done |
| framework (bpp3d) | 103 | 103 | 0 | 4 | done |
| framework (csp1d) | 84 | 84 | 0 | 6 | partial |
| framework (gantt) | 134 | 134 | 0 | 30 | done |
| framework (bpp1d) | 28 | 28 | 0 | 0 | partial |
| framework (bpp2d) | 20 | 20 | 0 | 0 | partial |
| framework (csp2d) | 20 | 20 | 0 | 0 | partial |
| framework (network_scheduling) | 20 | 20 | 0 | 0 | partial |
| framework (shared) | 22 | 22 | 0 | 9 | done |
| persistence | 3 | 3 | 0 | 0 | partial |
| **总计** | **1,010+** | **1,008+** | **3** | **320+** | **partial** |

## Stub 文件清单（仅原代码库）

| 文件 | 行数 | 问题 | 优先级 |
|------|------|------|--------|
| `utils/concept/move.py` | 2 | 空类 | P2 |
| `utils/concept/swap.py` | 5 | 空类 | P2 |
| `math/collection_aliases.py` | 6 | 类型别名 | P2 |

## TODO/NotImplementedError 清单（仅 math/symbol）

| 类型 | 数量 | 模块 | 说明 |
|------|------|------|------|
| TODO | 64 | math/symbol | 原代码库遗留 |
| NotImplementedError | 14 | math/symbol | QuickDsl.var/constant/sum/product, PolynomialEvaluator.evaluate 等 |

## 已知正确性缺口

| 模块 | 问题 | 优先级 |
|------|------|--------|
| math/symbol/operation | QuickDsl、PolynomialEvaluator 未实现 | P0 |
| csp1d 空服务 | CostarFiller、generation caches 等仍为空 | P1 |
| 新增 framework | bpp1d/bpp2d/csp2d/network_scheduling 无独立测试 | P1 |
| stub 测试 | test_csp1d_stubs.py、test_operation_stubs.py 仍验证占位行为 | P1 |

## 测试状态

| 指标 | 值 |
|------|-----|
| 测试文件 | 320+ |
| 测试通过 | 5,329 |
| 覆盖率 | 92% |
| ruff | clean |
| mypy | clean (strict) |

## CI 硬门禁状态

| 门禁 | 状态 | 说明 |
|------|------|------|
| ruff check | ✅ | 自动化 |
| mypy strict | ✅ | 自动化 |
| pytest | ✅ | 自动化 |
| TODO/NotImplementedError 检测 | ❌ | 仅注释，未接入 CI |
| stub/placeholder 检测 | ❌ | 仅注释，未接入 CI |
