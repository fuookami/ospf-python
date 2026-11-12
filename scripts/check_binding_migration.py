"""检查绑定迁移范围并生成只读盘点 / Check binding scope and inventory statically."""

from __future__ import annotations

import argparse
import ast
import json
import sys
import tomllib
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class _Symbol:
    name: str
    kind: str
    signature: str
    file: str
    line: int


@dataclass(frozen=True)
class _Module:
    name: str
    file: str
    symbols: tuple[_Symbol, ...]
    unresolved: tuple[str, ...]


def _module_name(path: Path) -> str:
    parts = path.with_suffix("").parts
    return ".".join(parts[:-1] if parts[-1] == "__init__" else parts)


def _statements(nodes: list[ast.stmt]) -> list[ast.stmt]:
    result: list[ast.stmt] = []
    for node in nodes:
        result.append(node)
        if isinstance(node, (ast.If, ast.Try, ast.TryStar, ast.With)):
            result.extend(_statements(node.body))
            result.extend(_statements(getattr(node, "orelse", [])))
            result.extend(_statements(getattr(node, "finalbody", [])))
            for handler in getattr(node, "handlers", []):
                result.extend(_statements(handler.body))
        elif isinstance(node, ast.Match):
            for case in node.cases:
                result.extend(_statements(case.body))
    return result


def _targets(node: ast.stmt) -> list[str]:
    if isinstance(node, ast.Assign):
        targets = node.targets
    elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
        targets = [node.target]
    else:
        return []
    return [target.id for target in targets if isinstance(target, ast.Name)]


def _scan_source(*, file: str, source: str) -> _Module:
    module = _module_name(Path(file))
    tree = ast.parse(source, filename=file)
    symbols: list[_Symbol] = []
    unresolved: list[str] = []
    nodes = _statements(tree.body)
    exports: set[str] = set()
    has_all = False
    for node in nodes:
        if isinstance(
            node, (ast.Assign, ast.AnnAssign, ast.AugAssign)
        ) and "__all__" in _targets(node):
            has_all = True
            if node.value is None:
                unresolved.append(f"{file}:{node.lineno}: unassigned __all__")
                continue
            try:
                values = ast.literal_eval(node.value)
            except (ValueError, TypeError, SyntaxError):
                unresolved.append(f"{file}:{node.lineno}: computed __all__")
                continue
            if isinstance(values, (list, tuple)) and all(
                isinstance(value, str) for value in values
            ):
                exports.update(values)
            else:
                unresolved.append(f"{file}:{node.lineno}: invalid __all__")

    def visit(*, body: list[ast.stmt], prefix: str, in_class: bool) -> None:
        for node in _statements(body):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_") and not (
                    in_class and node.name.startswith("__") and node.name.endswith("__")
                ):
                    continue
                signature = ast.unparse(node.args)
                if node.returns:
                    signature += " -> " + ast.unparse(node.returns)
                symbols.append(
                    _Symbol(
                        f"{prefix}.{node.name}",
                        "method" if in_class else "function",
                        signature,
                        file,
                        node.lineno,
                    )
                )
            elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                name = f"{prefix}.{node.name}"
                symbols.append(
                    _Symbol(
                        name,
                        "class",
                        ", ".join(map(ast.unparse, node.bases)),
                        file,
                        node.lineno,
                    )
                )
                visit(body=node.body, prefix=name, in_class=True)
            else:
                for name in _targets(node):
                    if not name.startswith("_"):
                        annotation = getattr(node, "annotation", None)
                        symbols.append(
                            _Symbol(
                                f"{prefix}.{name}",
                                "attribute" if in_class else "alias",
                                ast.unparse(annotation) if annotation else "",
                                file,
                                node.lineno,
                            )
                        )

    visit(body=tree.body, prefix=module, in_class=False)
    imported: dict[str, int] = {}
    for node in nodes:
        if isinstance(node, ast.ImportFrom) and node.module != "__future__":
            for alias in node.names:
                if alias.name == "*":
                    if not has_all:
                        unresolved.append(
                            f"{file}:{node.lineno}: wildcard without __all__"
                        )
                elif (
                    alias.name in exports
                    or (
                        Path(file).name == "__init__.py"
                        and not (alias.asname or alias.name).startswith("_")
                        and (node.module or "").startswith("ospf_python")
                    )
                    or alias.asname == alias.name
                ):
                    imported[alias.asname or alias.name] = node.lineno
    declared = {symbol.name for symbol in symbols}
    for name in sorted(exports | imported.keys()):
        qualified = f"{module}.{name}"
        if qualified not in declared:
            symbols.append(
                _Symbol(qualified, "export", "", file, imported.get(name, 1))
            )
    return _Module(module, file, tuple(symbols), tuple(unresolved))


def _select_area(module: str, areas: list[dict[str, Any]]) -> dict[str, Any] | None:
    matches = [
        area
        for area in areas
        if module == area["namespace"]
        or (area.get("recursive", True) and module.startswith(area["namespace"] + "."))
    ]
    return max(matches, key=lambda area: len(area["namespace"]), default=None)


def _check(
    *, root: Path, manifest: dict[str, Any], modules: list[_Module]
) -> dict[str, Any]:
    issues: list[str] = []
    areas = manifest.get("area", [])
    seen_ids: set[str] = set()
    seen_namespaces: set[str] = set()
    if manifest.get("schema_version") != _SCHEMA_VERSION:
        issues.append("Unsupported or missing schema_version")
    for area in areas:
        if not all(
            key in area
            for key in (
                "id",
                "namespace",
                "phase",
                "disposition",
                "tests",
                "rust_crates",
            )
        ):
            issues.append(f"Incomplete area: {area.get('id', '<missing>')}")
            continue
        for key, seen in (("id", seen_ids), ("namespace", seen_namespaces)):
            if area[key] in seen:
                issues.append(f"Duplicate area {key}: {area[key]}")
            seen.add(area[key])
        if area["phase"] not in {f"P{index}" for index in range(10)}:
            issues.append(f"Invalid phase: {area['id']}")
        if area["disposition"] not in {"rust", "facade", "integration", "review"}:
            issues.append(f"Invalid disposition: {area['id']}")
        if not area["tests"]:
            issues.append(f"Missing acceptance references: {area['id']}")
        for reference in area["tests"]:
            path = (root / reference).resolve()
            if not path.is_relative_to(root.resolve()) or not path.exists():
                issues.append(f"Missing or outside-root acceptance path: {reference}")
    valid_areas = [area for area in areas if "namespace" in area and "id" in area]
    all_symbols = {symbol.name for module in modules for symbol in module.symbols}
    contracts: dict[str, dict[str, Any]] = {}
    for contract in manifest.get("contract", []):
        name = contract.get("symbol", "")
        if name in contracts:
            issues.append(f"Duplicate contract: {name}")
        contracts[name] = contract
        if name not in all_symbols:
            issues.append(f"Contract symbol not found: {name}")
        if contract.get("status") not in {
            "inventoried",
            "specified",
            "bound",
            "verified",
            "switched",
            "legacy_removed",
        }:
            issues.append(f"Invalid contract status: {name}")
        pending = contract.get("pending_acceptance", [])
        if not isinstance(pending, list) or any(
            not isinstance(item, str) or not item.strip() for item in pending
        ):
            issues.append(f"Invalid pending acceptance: {name}")
        elif pending and contract.get("status") in {
            "verified",
            "switched",
            "legacy_removed",
        }:
            issues.append(f"Accepted contract has pending acceptance: {name}")
        if not contract.get("compatibility") or not contract.get("acceptance"):
            issues.append(f"Missing compatibility/acceptance: {name}")
        for reference in contract.get("acceptance", []):
            path = (root / reference).resolve()
            if not path.is_relative_to(root.resolve()) or not path.exists():
                issues.append(
                    f"Missing or outside-root contract acceptance: {reference}"
                )
    counts: Counter[str] = Counter()
    mapped: list[dict[str, Any]] = []
    for module in modules:
        area = _select_area(module.name, valid_areas)
        if area is None:
            issues.append(f"Unmapped module: {module.name}")
            continue
        counts[area["id"]] += 1
        mapped.append(
            {
                "module": module.name,
                "file": module.file,
                "area": area["id"],
                "phase": area["phase"],
                "symbols": [
                    {
                        **asdict(symbol),
                        "status": contracts.get(symbol.name, {}).get(
                            "status", "inventoried"
                        ),
                    }
                    for symbol in module.symbols
                ],
                "unresolved_exports": list(module.unresolved),
            }
        )
    for area in valid_areas:
        if not counts[area["id"]]:
            issues.append(f"Area has no modules: {area['id']}")
    return {
        "scope_only_not_binding_parity": True,
        "summary": {
            "modules": len(modules),
            "areas": len(areas),
            "symbol_candidates": len(all_symbols),
            "explicit_contracts": len(contracts),
            "unresolved_exports": sum(len(module.unresolved) for module in modules),
            "area_module_counts": dict(sorted(counts.items())),
            "issues": issues,
        },
        "modules": mapped,
    }


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--report", type=Path)
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    try:
        manifest = tomllib.loads(
            (root / "docs/migration/api-map.toml").read_text(encoding="utf-8")
        )
        modules = [
            _scan_source(
                file=path.relative_to(root).as_posix(),
                source=path.read_text(encoding="utf-8-sig"),
            )
            for path in sorted((root / "ospf_python").rglob("*.py"))
        ]
        report = _check(root=root, manifest=manifest, modules=modules)
        if not modules:
            report["summary"]["issues"].append("No ospf_python modules found")
        if arguments.report:
            arguments.report.parent.mkdir(parents=True, exist_ok=True)
            arguments.report.write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
    except (OSError, SyntaxError, ValueError, KeyError, TypeError) as error:
        print(f"Migration inventory failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    print("Scope inventory only; this does not verify Python/Rust binding parity.")
    return int(bool(report["summary"]["issues"]))


if __name__ == "__main__":
    raise SystemExit(_main())
