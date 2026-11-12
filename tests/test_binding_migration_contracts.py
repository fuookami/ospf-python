"""迁移范围门禁测试 / Migration scope gate tests."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

import pytest

from scripts.check_binding_migration import (
    _check,
    _module_name,
    _scan_source,
    _select_area,
)

_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def manifest(tmp_path: Path) -> dict[str, Any]:
    """创建最小范围合同 / Create a minimal scope contract."""
    (tmp_path / "acceptance.py").write_text("", encoding="utf-8")
    return {
        "schema_version": 1,
        "area": [
            {
                "id": "sample",
                "namespace": "sample",
                "phase": "P3",
                "disposition": "rust",
                "rust_crates": ["ospf-rust-math"],
                "tests": ["acceptance.py"],
            }
        ],
    }


@pytest.mark.parametrize(
    ("path", "expected"),
    [("sample/__init__.py", "sample"), ("sample/numbers.py", "sample.numbers")],
)
def test_module_names(path: str, expected: str) -> None:
    """包入口不追加 __init__ / Package entry points omit __init__."""
    assert _module_name(Path(path)) == expected


def test_surface_includes_protocols_fields_magic_and_exports() -> None:
    """覆盖动态语言合同候选 / Include protocol contract candidates."""
    module = _scan_source(
        file="sample/__init__.py",
        source="""
from sample.other import Original as Alias
__all__ = ['Alias', 'Value']
class Value:
    amount: int
    def __add__(self, other): ...
    def _private(self): ...
    def visible(self, *, count: int = 1) -> int: ...
""",
    )
    names = {symbol.name for symbol in module.symbols}
    assert {
        "sample.Alias",
        "sample.Value",
        "sample.Value.amount",
        "sample.Value.__add__",
        "sample.Value.visible",
    } <= names
    assert "sample.Value._private" not in names
    assert not module.unresolved


def test_conditional_definitions_are_inventory_candidates() -> None:
    """条件定义不遗漏 / Do not omit conditional definitions."""
    module = _scan_source(
        file="sample/conditional.py",
        source="""
if condition:
    class OptionalType:
        def method(self): ...
try:
    def optional_function(): ...
except ImportError:
    pass
""",
    )
    assert {symbol.name for symbol in module.symbols} >= {
        "sample.conditional.OptionalType",
        "sample.conditional.OptionalType.method",
        "sample.conditional.optional_function",
    }


def test_computed_exports_are_not_executed() -> None:
    """不执行动态导出表达式 / Never execute computed export expressions."""
    module = _scan_source(
        file="sample/dynamic.py",
        source="__all__ = unknown_callable()",
    )
    assert len(module.unresolved) == 1


def test_wildcard_without_explicit_exports_requires_review() -> None:
    """通配符导出必须复核 / Wildcard exports require review."""
    module = _scan_source(
        file="sample/wildcard.py", source="from sample.other import *"
    )
    assert len(module.unresolved) == 1


def test_most_specific_namespace_wins() -> None:
    """按命名空间边界选择 / Match namespace boundaries, most specific first."""
    areas = [
        {"namespace": "sample", "id": "general"},
        {"namespace": "sample.number", "id": "numbers"},
    ]
    assert _select_area("sample.number.integer", areas) == areas[1]
    assert _select_area("sample.numbering", areas) == areas[0]
    assert _select_area("sampled", areas) is None
    assert (
        _select_area("sample.child", [{"namespace": "sample", "recursive": False}])
        is None
    )


def test_mapped_symbols_are_not_marked_binding_verified(
    tmp_path: Path,
    manifest: dict[str, Any],
) -> None:
    """范围覆盖不能冒充绑定验证 / Scope coverage is not binding verification."""
    module = _scan_source(file="sample/value.py", source="class Value: pass")
    report = _check(root=tmp_path, manifest=manifest, modules=[module])
    assert not report["summary"]["issues"]
    assert report["scope_only_not_binding_parity"] is True
    assert report["modules"][0]["symbols"][0]["status"] == "inventoried"


def test_unmapped_module_fails(tmp_path: Path, manifest: dict[str, Any]) -> None:
    """新范围未登记时失败 / Reject unregistered scopes."""
    module = _scan_source(file="unknown/module.py", source="")
    report = _check(root=tmp_path, manifest=manifest, modules=[module])
    assert "Unmapped module: unknown.module" in report["summary"]["issues"]


def test_duplicate_namespaces_fail(tmp_path: Path, manifest: dict[str, Any]) -> None:
    """拒绝歧义范围 / Reject ambiguous scopes."""
    manifest["area"].append({**manifest["area"][0], "id": "duplicate"})
    module = _scan_source(file="sample/value.py", source="")
    report = _check(root=tmp_path, manifest=manifest, modules=[module])
    assert "Duplicate area namespace: sample" in report["summary"]["issues"]


def test_missing_contract_symbol_fails(
    tmp_path: Path, manifest: dict[str, Any]
) -> None:
    """合同引用不存在符号时失败 / Reject nonexistent contract symbols."""
    manifest["contract"] = [
        {
            "symbol": "sample.Missing",
            "status": "specified",
            "compatibility": "preserve",
            "acceptance": ["acceptance.py"],
        }
    ]
    report = _check(
        root=tmp_path,
        manifest=manifest,
        modules=[_scan_source(file="sample/__init__.py", source="")],
    )
    assert "Contract symbol not found: sample.Missing" in report["summary"]["issues"]


def test_outside_acceptance_path_fails(
    tmp_path: Path, manifest: dict[str, Any]
) -> None:
    """验收引用不得逃逸根目录 / Acceptance paths stay inside the root."""
    manifest["area"][0]["tests"] = ["../outside.py"]
    report = _check(
        root=tmp_path,
        manifest=manifest,
        modules=[_scan_source(file="sample/__init__.py", source="")],
    )
    assert any(
        "outside-root acceptance" in issue for issue in report["summary"]["issues"]
    )


def test_repository_api_map_covers_sources() -> None:
    """所有现有模块均有迁移归属 / Every existing module has a migration owner."""
    root = _ROOT
    manifest = tomllib.loads(
        (root / "docs/migration/api-map.toml").read_text(encoding="utf-8")
    )
    modules = [
        _scan_source(
            file=path.relative_to(root).as_posix(),
            source=path.read_text(encoding="utf-8-sig"),
        )
        for path in (root / "ospf_python").rglob("*.py")
    ]
    report = _check(root=root, manifest=manifest, modules=modules)
    assert not report["summary"]["issues"]
    assert report["summary"]["modules"] > 0


@pytest.mark.parametrize(
    ("source", "symbol"),
    [
        (
            "ospf_python/framework/bpp1d/application/bpp1d_application_service.py",
            "ospf_python.framework.bpp1d.application.bpp1d_application_service."
            "Bpp1dApplicationService.execute",
        ),
        (
            "ospf_python/framework/bpp1d/infrastructure/bpp1d_solver_adapter.py",
            "ospf_python.framework.bpp1d.infrastructure.bpp1d_solver_adapter."
            "Bpp1dSolverAdapter.solve",
        ),
    ],
)
@pytest.mark.parametrize("status", ["verified", "switched", "legacy_removed"])
def test_bpp1d_cutover_requires_safe_optimality_evidence(
    *, source: str, symbol: str, status: str
) -> None:
    """领域切换不能忽略已证实缺口 / Domain cutover cannot ignore the proven gap."""
    manifest = tomllib.loads(
        (_ROOT / "docs/migration/api-map.toml").read_text(encoding="utf-8")
    )
    contract = next(item for item in manifest["contract"] if item["symbol"] == symbol)
    assert "RG-014-safe-domain-optimality-evidence" in contract["pending_acceptance"]
    assert (
        "RG-015-sound-float-candidates-and-feasibility"
        in contract["pending_acceptance"]
    )
    area = next(item for item in manifest["area"] if item["id"] == "bpp1d")
    module = _scan_source(file=source, source=(_ROOT / source).read_text("utf-8"))
    report = _check(
        root=_ROOT,
        manifest={
            "schema_version": 1,
            "area": [area],
            "contract": [{**contract, "status": status}],
        },
        modules=[module],
    )
    assert report["summary"]["issues"] == [
        f"Accepted contract has pending acceptance: {symbol}"
    ]


@pytest.mark.parametrize(
    "status", ["specified", "bound", "verified", "switched", "legacy_removed"]
)
@pytest.mark.parametrize("pending", [[], ["FS-001", "RG-005"]])
def test_declared_pending_acceptance_prevents_premature_certification(
    *, tmp_path: Path, manifest: dict[str, Any], status: str, pending: list[str]
) -> None:
    """未完成合同不得宣称验收 / Pending contracts cannot claim acceptance."""
    manifest["contract"] = [
        {
            "symbol": "sample.operation",
            "status": status,
            "compatibility": "explicit-upgrade",
            "acceptance": ["acceptance.py"],
            "pending_acceptance": pending,
        }
    ]
    report = _check(
        root=tmp_path,
        manifest=manifest,
        modules=[
            _scan_source(file="sample/__init__.py", source="def operation(): ...")
        ],
    )
    blocked = bool(pending) and status in {"verified", "switched", "legacy_removed"}
    assert bool(report["summary"]["issues"]) is blocked
    if blocked:
        assert report["summary"]["issues"] == [
            "Accepted contract has pending acceptance: sample.operation"
        ]


@pytest.mark.parametrize("pending", [None, "FS-001", {}, [""], [" "], [1]])
def test_invalid_pending_acceptance_fails(
    *, tmp_path: Path, manifest: dict[str, Any], pending: Any
) -> None:
    """拒绝含糊的前置字段 / Reject ambiguous pending fields."""
    manifest["contract"] = [
        {
            "symbol": "sample.operation",
            "status": "specified",
            "compatibility": "explicit-upgrade",
            "acceptance": ["acceptance.py"],
            "pending_acceptance": pending,
        }
    ]
    report = _check(
        root=tmp_path,
        manifest=manifest,
        modules=[
            _scan_source(file="sample/__init__.py", source="def operation(): ...")
        ],
    )
    assert report["summary"]["issues"] == [
        "Invalid pending acceptance: sample.operation"
    ]
