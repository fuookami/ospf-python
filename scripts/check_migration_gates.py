#!/usr/bin/env python3
"""迁移门禁检查脚本 / Migration gates check script.

扫描 ospf_python/ 检测：
- 未豁免的 TODO
- 非协议/抽象边界的 NotImplementedError
- stub/placeholder 标识符出现在 production 业务类
- bare pass 在 production 业务类方法体 (not in __init__.py, not Protocol/ABC, not exception handler, not conditional import, not sentinel class)
- stub returns 在 PARTIAL 模块: return (), return True, return 0.0, return None without justification

读取 migration-matrix.md 中的 excluded 白名单和 partial 模块列表。
Exit code 0 = clean, 1 = violations found.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

# Patterns to detect in ALL production code
PATTERNS = {
    "TODO": re.compile(r"\bTODO\b"),
    "NotImplementedError": re.compile(r"\braise NotImplementedError\b"),
    "stub/placeholder": re.compile(r"\bstub\b|\bplaceholder\b", re.IGNORECASE),
}

# Bare pass pattern: a line that is just "pass" (with optional whitespace)
BARE_PASS_PATTERN = re.compile(r"^\s*pass\s*$")

# Stub return patterns: only flagged in PARTIAL modules
STUB_RETURN_PATTERNS = {
    "return-empty-tuple": re.compile(r"^\s*return\s*\(\s*\)\s*(?:#.*)?$"),
    "return-True": re.compile(r"^\s*return\s+True\s*(?:#.*)?$"),
    "return-0.0": re.compile(r"^\s*return\s+0\.0\s*(?:#.*)?$"),
    "return-None": re.compile(r"^\s*return\s+None\s*(?:#.*)?$"),
}

# Justification comment pattern
JUSTIFICATION_PATTERN = re.compile(r"#\s*(justified|reason:|note:|nocover|noqa)", re.IGNORECASE)

# Exceptions (files/patterns to skip)
EXCEPTIONS = {
    "migration-matrix.md",
    "check_migration_gates.py",
    "check-production-quality.py",
    "__pycache__",
    "__init__.py",  # __init__.py often has bare pass legitimately
}

# Patterns that make bare pass acceptable
PROTOCOL_PATTERNS = [
    re.compile(r"class\s+\w+.*Protocol"),
    re.compile(r"class\s+\w+.*ABC"),
    re.compile(r"@abstractmethod"),
]

# Partial modules where stub returns are flagged
# These are the modules listed as "partial" in migration-matrix.md
PARTIAL_MODULES = [
    "math/symbol/operation",
    "framework/csp1d/domain/cutting_plan_generation",
    "framework/csp1d/domain/material",
    "framework/bpp1d",
    "framework/bpp2d",
    "framework/csp2d",
    "framework/network_scheduling",
    "framework/persistence",
]


def should_skip(path: str) -> bool:
    """Check if path should be skipped."""
    return any(exc in path for exc in EXCEPTIONS)


def is_in_partial_module(path: str) -> bool:
    """Check if path is in a partial module (where stub returns are flagged)."""
    normalized = path.replace("\\", "/")
    return any(mod in normalized for mod in PARTIAL_MODULES)


def read_excluded_whitelist(project_root: Path) -> set[str]:
    """Read excluded whitelist from migration-matrix.md."""
    whitelist: set[str] = set()
    matrix_path = project_root / "migration-matrix.md"
    if not matrix_path.exists():
        return whitelist

    try:
        content = matrix_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return whitelist

    # Parse excluded modules from the Excluded Whitelist section
    in_excluded = False
    for line in content.splitlines():
        if "排除清单" in line or "Excluded Whitelist" in line:
            in_excluded = True
            continue
        if in_excluded and line.startswith("|"):
            parts = [p.strip() for p in line.split("|")]
            # Skip header rows and separator rows
            if len(parts) >= 2 and parts[1] and parts[1] not in ("模块", "Module", "---", "------"):
                # Skip if the cell contains only dashes
                if re.match(r"^[-:]+$", parts[1]):
                    continue
                whitelist.add(parts[1])
        elif in_excluded and not line.startswith("|") and line.strip():
            if line.startswith("#") or line.startswith("-"):
                in_excluded = False

    return whitelist


def is_protocol_context(lines: list[str], line_idx: int) -> bool:
    """Check if a bare pass is inside a Protocol/ABC class."""
    for i in range(max(0, line_idx - 20), line_idx + 1):
        for pattern in PROTOCOL_PATTERNS:
            if pattern.search(lines[i]):
                return True
    return False


def is_exception_handler(lines: list[str], line_idx: int) -> bool:
    """Check if a bare pass is inside an except block."""
    for i in range(max(0, line_idx - 5), line_idx + 1):
        if re.match(r"\s*except\s+", lines[i]):
            return True
    return False


def is_type_checking_block(lines: list[str], line_idx: int) -> bool:
    """Check if a bare pass is in a TYPE_CHECKING or conditional import block."""
    for i in range(max(0, line_idx - 10), line_idx + 1):
        stripped = lines[i].strip()
        if stripped.startswith("if TYPE_CHECKING:"):
            return True
        if stripped.startswith("try:") and i + 1 < len(lines) and "import" in lines[i + 1]:
            return True
    return False


def is_conditional_import_block(lines: list[str], line_idx: int) -> bool:
    """Check if a bare pass is in a conditional import try/except block."""
    return is_type_checking_block(lines, line_idx)


def is_sentinel_class(lines: list[str], line_idx: int) -> bool:
    """Check if a bare pass is in a sentinel/utility class (single-word class name starting with _)."""
    for i in range(max(0, line_idx - 5), line_idx + 1):
        m = re.match(r"^class\s+(_\w+)", lines[i])
        if m:
            return True
    return False


def check_file(
    path: str,
    *,
    check_bare_pass: bool = True,
    check_stub_returns: bool = True,
) -> list[tuple[str, int, str]]:
    """Check a single file for violations."""
    violations: list[tuple[str, int, str]] = []
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
    except (OSError, UnicodeDecodeError):
        return violations

    in_partial = is_in_partial_module(path)

    for i, line in enumerate(lines):
        # Check pattern-based violations (all production code)
        for name, pattern in PATTERNS.items():
            if pattern.search(line):
                violations.append((path, i + 1, f"{name}: {line.strip()}"))

        # Check bare pass (all production code, with context-awareness)
        if (
            check_bare_pass
            and BARE_PASS_PATTERN.match(line)
            and not is_protocol_context(lines, i)
            and not is_exception_handler(lines, i)
            and not is_conditional_import_block(lines, i)
            and not is_sentinel_class(lines, i)
        ):
            violations.append((path, i + 1, f"bare-pass: {line.strip()}"))

        # Check stub returns (ONLY in partial modules)
        if check_stub_returns and in_partial:
            for name, pattern in STUB_RETURN_PATTERNS.items():
                if pattern.match(line):
                    # Allow if there's a justification comment
                    if JUSTIFICATION_PATTERN.search(line):
                        continue
                    if i > 0 and JUSTIFICATION_PATTERN.search(lines[i - 1]):
                        continue
                    violations.append((path, i + 1, f"stub-return({name}): {line.strip()}"))

    return violations


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Migration gates check")
    parser.add_argument("--whitelist", action="store_true", help="Show current excluded whitelist")
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    excluded = read_excluded_whitelist(project_root)

    if args.whitelist:
        print("Excluded whitelist from migration-matrix.md:")
        for item in sorted(excluded):
            print(f"  - {item}")
        if not excluded:
            print("  (empty)")
        print("\nPartial modules (stub returns flagged):")
        for mod in PARTIAL_MODULES:
            print(f"  - {mod}")
        return 0

    violations: list[tuple[str, int, str]] = []
    scan_dirs = ["ospf_python"]

    for scan_dir in scan_dirs:
        dir_path = project_root / scan_dir
        if not dir_path.exists():
            continue

        for root, dirs, files in os.walk(dir_path):
            dirs[:] = [d for d in dirs if d != "__pycache__"]

            for file in files:
                if not file.endswith(".py"):
                    continue
                path = os.path.join(root, file)
                if should_skip(path):
                    continue
                violations.extend(check_file(path))

    if violations:
        print(f"FAIL: {len(violations)} migration gate violations found:")
        for path, line, msg in violations:
            print(f"  {path}:{line}: {msg}")
        return 1

    print("PASS: No migration gate violations found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
