# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- GitHub Actions CI workflow (lint, typecheck, test, solver-integration)
- CHANGELOG.md

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
