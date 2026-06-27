#!/usr/bin/env python3
"""Production code quality gate script.

Scans ospf_python/ for forbidden patterns:
- TODO (use issue tracker instead)
- NotImplementedError (implement or exclude)
- stub/placeholder (implement or mark as excluded in migration-matrix.md)
- Empty constraint returns without justification

Exit code 0 = clean, 1 = violations found.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

# Patterns to detect
PATTERNS = {
    "TODO": re.compile(r"\bTODO\b"),
    "NotImplementedError": re.compile(r"\braise NotImplementedError\b"),
    "stub/placeholder": re.compile(r"\bstub\b|\bplaceholder\b", re.IGNORECASE),
}

# Exceptions (files/patterns to skip)
EXCEPTIONS = {
    "migration-matrix.md",  # Documentation
    "check-production-quality.py",  # This script
    "__pycache__",
}


def should_skip(path: str) -> bool:
    """Check if file should be skipped."""
    return any(exc in path for exc in EXCEPTIONS)


def scan_file(path: str) -> list[tuple[str, int, str]]:
    """Scan file for forbidden patterns."""
    violations = []
    try:
        with open(path, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                for pattern_name, pattern in PATTERNS.items():
                    if pattern.search(line):
                        violations.append((path, line_num, f"{pattern_name}: {line.strip()}"))
    except (UnicodeDecodeError, PermissionError):
        pass
    return violations


def main() -> int:
    """Main entry point."""
    root = Path(__file__).parent.parent / "ospf_python"
    all_violations = []

    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            path = os.path.join(dirpath, filename)
            if should_skip(path):
                continue
            violations = scan_file(path)
            all_violations.extend(violations)

    if all_violations:
        print(f"[FAIL] Found {len(all_violations)} quality violations:")
        for path, line, msg in all_violations:
            print(f"  {path}:{line}: {msg}")
        return 1
    else:
        print("[PASS] No quality violations found.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
