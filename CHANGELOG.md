# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- GitHub Actions CI workflow (lint, typecheck, test, solver-integration)
- CHANGELOG.md
- PyO3/Maturin 原生绑定包 `ospf_python._native`，随 wheel 分发；
  `py.typed` 标记与 `.pyi` 存根随包发布 / PyO3/Maturin native bindings shipped
  as `ospf_python._native` with `py.typed` and a `.pyi` stub.
- 求解器构建特性 `scip`、`gurobi10`（另预留 11/12）/ Build features `scip`,
  `gurobi10` (11/12 reserved).
- Windows wheel 自带 `gurobi100.dll`，无需外部 PATH 配置即可 import /
  Windows wheels bundle `gurobi100.dll`, so `import` works without PATH setup.
- 5 个脚本式可运行示例 / Five runnable script-style examples under `examples/`.
- `CHANGELOG.md` 纳入 Keep a Changelog 1.1.0 结构 / CHANGELOG follows
  Keep a Changelog 1.1.0.

### Changed
- `Requires-Python` 提升至 `>=3.13` / `Requires-Python` raised to `>=3.13`.
- 移除未使用的运行时依赖 `pydantic>=2.0` 与 `returns>=0.22`：产品代码与测试均无真实导入，
  `pydantic` 仅出现在一篇未实现的持久化插件提案文档里。基础依赖现为 `numpy>=1.26` /
  Removed unused runtime dependencies `pydantic>=2.0` and `returns>=0.22`; base
  dependencies are now `numpy>=1.26`.
- 数组/数量/求解器的热路径逐步改由原生扩展承载；**迁移尚未完成**，
  部分公共能力仍为 Python 实现，详见 `docs/migration/api-map.toml` /
  Hot paths are progressively served by the native extension. **The migration is
  not complete**: some public capabilities are still implemented in Python; see
  `docs/migration/api-map.toml`.

### Fixed
- Gurobi 线性求解器：模型已构建但未被调用方传入时，`solve()` 现在回退到
  已构建的 `self._model`，不再直接返回 `ERROR` /
  Gurobi linear solver: `solve()` now falls back to the already-built model
  instead of returning `ERROR` when the caller omits it.
- `MultiArray.transpose()` 此前只改写 `shape` 而不置换数据（`(2,3)`、数据
  `[0,1,2,3,4,5]` 被标成 `(3,2)` 却仍按 `[[0,1],[2,3],[4,5]]` 返回），现在返回真实
  转置 `[[0,3],[1,4],[2,5]]` / `transpose()` previously relabelled `shape` without
  permuting data; it now returns a real transpose.
- `reshape()` 与 `to_list()` 此前忽略 `StorageOrder`，`COLUMN_MAJOR` 数组被按行主序
  解释；现在按声明的存储顺序处理 / `reshape()` and `to_list()` ignored
  `StorageOrder` and treated column-major arrays as row-major; both now honour
  the declared order.
- `MultiArrayView.materialize()` 此前忽略视图偏移，恒返回整个底层数组；现在返回视图
  对应的子区域（`(2,3)` 源、偏移 `(1,0)` → 数据 `[3,4,5]`、形状 `(1,3)`) /
  `materialize()` ignored view offsets and returned the whole backing array; it
  now returns the view's region.
- `pow_int()` 对负数指数此前**静默返回 0**（`2**-1` 得 `0`）；现在返回
  `ILLEGAL_ARGUMENT` 失败，指数必须非负 / `pow_int()` silently returned `0` for
  negative exponents, which is wrong; it now fails with `ILLEGAL_ARGUMENT`.

### Known issues
- 带非零偏移的 `MappedMultiArrayView.materialize()` 抛 `IndexError`
  （`index 6 is out of bounds for axis 0 with size 6`）：坐标计划按源形状生成坐标，
  未计入视图有效区域。该缺陷在迁移前已存在（旧实现抛同一个 `IndexError`），
  且无自动化测试覆盖 / Mapped view materialisation with non-zero offsets raises
  `IndexError`; pre-existing before the migration and currently untested.
  Reproduction: `logs/p3/b125-mapped-offset-defect-20261110/`.

## [0.1.0] - 2026-06-25

### Added
- Complete 1:1 migration from ospf-kotlin (902 source files)
- **utils** (47 files): Result/Error 三参 sealed, Either/Variant, Eq/Ord Protocol, Context, parallel primitives, serialization
- **multiarray** (9 files): numpy backend, Shape1-4/DynShape, MultiArray/MutableMultiArray, einsum
- **math** (278 files): algebra(33), chaotic(88), combinatorics(4), fractal(2), geometry(26), operator(16), ordinary(12), symbol(77)
- **quantities** (43 files): Quantity[T] generic, PhysicalUnit Protocol, 33 physical units
- **core** (178 files): error(1), variable(6), token(7), symbol(43), model(44), solver(77) with MockSolver + gurobi/scip/copt/mindopt adapters
- **framework** (370 files): bpp3d(103), csp1d(84), gantt_scheduling(134), shared(49) with DDD structure and column generation lifecycle
- **examples** (5 files): core_demo, bpp3d, csp1d, gantt demos
- README.md (English) + README_ch.md (Chinese) with cross-links
- 4482 tests passing, 88% code coverage
- Type system: Result[T,C,E] 三参 sealed, MetaModel axis, RealNumber Protocol, Quantity/PhysicalUnit, Solver interfaces
- Column generation lifecycle: register → add_columns → remove_columns → refresh_shadow_price → finalize → extract_solution
- End-to-end verification: bpp3d + csp1d + gantt via framework MetaModel/context/solver
- 4 solver adapters: gurobi, scip, copt, mindopt (with importorskip for unavailable libraries)

### Changed
- gantt_scheduling application services: 16-line stubs → 788+1066 lines real BranchAndPrice column generation
- mypy strict mode: removed ignore_errors=true, fixed all 272 hidden type errors
- pyproject.toml: added classifiers, keywords, urls, license-files

### Fixed
- 28 assert True placeholder tests replaced with real behavior tests
- mypy ignore_errors=true hiding 272 type errors across csp1d/gantt/copt/mindopt
- Various type annotation issues across all modules

[Unreleased]: https://github.com/fuookami/ospf-python/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/fuookami/ospf-python/releases/tag/v0.1.0
