"""发行烟测进程合同 / Distribution smoke process contracts."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.verify_binding_distribution import _smoke


def test_smoke_uses_isolated_file_instead_of_command_line(
    *, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """避免系统命令行长度限制 / Avoid system command-line length limits."""
    python = Path("python")
    environment = {"TEST": "value"}
    called = False

    def run(args: list[str], *, cwd: Path, env: dict[str, str], check: bool) -> None:
        nonlocal called
        called = True
        script = tmp_path / "smoke.py"
        assert args == [str(python), "-I", str(script), "scip", "gurobi10"]
        assert cwd == tmp_path and env is environment and check
        compile(script.read_text(encoding="utf-8"), str(script), "exec")

    monkeypatch.setattr(subprocess, "run", run)
    _smoke(
        python=python,
        workspace=tmp_path,
        environment=environment,
        native_solvers=["scip", "gurobi10"],
    )
    assert called
