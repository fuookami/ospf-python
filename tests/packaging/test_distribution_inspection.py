"""发行物检查器的负向合同 / Negative contracts for distribution inspection."""

from __future__ import annotations

import io
import tarfile
import zipfile
from pathlib import Path

import pytest
from packaging.requirements import Requirement

from scripts.verify_binding_distribution import (
    _inspect_sdist,
    _inspect_wheel,
    _sdist_build_args,
)

_NATIVE = "ospf_python/_native.cp313-win_amd64.pyd"


def _sdist(
    path: Path,
    *,
    omit: tuple[str, ...] = (),
    extra: dict[str, str] | None = None,
    extra_members: tuple[tarfile.TarInfo, ...] = (),
) -> Path:
    files = {
        "native/Cargo.toml": "",
        "native/Cargo.lock": "",
        "rust-toolchain.toml": "",
        "pyproject.toml": "",
        "README.md": "[中文](README_ch.md)\n[Guide](docs/index.md)",
        "README_ch.md": "[English](README.md)",
        "docs/index.md": "[Contract](migration/api-map.toml)",
        "docs/migration/api-map.toml": "",
        "examples/__init__.py": "",
    }
    if extra:
        files.update(extra)
    with tarfile.open(path, "w:gz") as archive:
        for name, text in files.items():
            if name not in omit:
                data = text.encode("utf-8")
                entry = tarfile.TarInfo(f"sample/{name}")
                entry.size = len(data)
                archive.addfile(entry, io.BytesIO(data))
        for entry in extra_members:
            archive.addfile(entry)
    return path


def _wheel(*, path: Path, requirement: str = "", extra: str = "") -> Path:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("ospf_python/py.typed", "")
        archive.writestr("ospf_python/_native.pyi", "")
        archive.writestr(_NATIVE, b"")
        archive.writestr(
            "ospf_python-0.1.0.dist-info/METADATA",
            "Metadata-Version: 2.3\nName: ospf-python\nVersion: 0.1.0\n" + requirement,
        )
        if extra:
            archive.writestr(extra, "")
    return path


def test_optional_solver_sdk_is_allowed(tmp_path: Path) -> None:
    """extras 不成为必选依赖 / Extras do not become mandatory dependencies."""
    wheel = _wheel(
        path=tmp_path / "sample.whl",
        requirement="Requires-Dist: gurobipy<13,>=10; extra == 'gurobi'\n",
    )
    assert not _inspect_wheel(wheel)


@pytest.mark.parametrize("marker", [' extra=="x" ', "extra == 'all-solvers'"])
def test_other_single_extra_markers_are_allowed(*, tmp_path: Path, marker: str) -> None:
    """单个 extra 可以含空格或连字符 / Allow whitespace and hyphens in extras."""
    wheel = _wheel(
        path=tmp_path / "sample.whl",
        requirement=f"Requires-Dist: gurobipy<13,>=10; {marker}\n",
    )
    assert not _inspect_wheel(wheel)


def test_mandatory_solver_sdk_is_rejected(tmp_path: Path) -> None:
    """拒绝基础包强制 solver / Reject mandatory solver dependencies."""
    wheel = _wheel(
        path=tmp_path / "sample.whl",
        requirement="Requires-Dist: gurobipy>=10\n",
    )
    assert any("Mandatory solver SDK" in issue for issue in _inspect_wheel(wheel))


@pytest.mark.parametrize(
    "marker",
    [
        "extra == 'gurobi' or python_version >= '3.13'",
        "extra == 'gurobi' or sys_platform == 'win32'",
        "extra == 'gurobi' or extra == ''",
        "extra == 'gurobi' or extra != 'gurobi'",
    ],
)
@pytest.mark.parametrize("sdk", ["gurobipy", "pyscipopt", "coptpy", "mindoptpy"])
def test_solver_marker_cannot_require_sdk_without_an_extra(
    *, tmp_path: Path, marker: str, sdk: str
) -> None:
    """拒绝默认环境下可能安装的 SDK / Reject SDKs required without an extra."""
    requirement = f"{sdk}>=10; {marker}"
    parsed = Requirement(requirement)
    assert parsed.marker is not None
    assert parsed.marker.evaluate(
        {"extra": "", "python_version": "3.13", "sys_platform": "win32"}
    )
    wheel = _wheel(
        path=tmp_path / "sample.whl", requirement=f"Requires-Dist: {requirement}\n"
    )
    assert any("solver sdk" in issue.lower() for issue in _inspect_wheel(wheel))


def test_complex_optional_solver_marker_is_rejected_conservatively(
    tmp_path: Path,
) -> None:
    """复杂标记须审查 / Complex markers require review even when optional."""
    requirement = "gurobipy>=10; extra == 'gurobi' and python_version >= '3.13'"
    parsed = Requirement(requirement)
    assert parsed.marker is not None
    assert not parsed.marker.evaluate({"extra": "", "python_version": "3.13"})
    assert parsed.marker.evaluate({"extra": "gurobi", "python_version": "3.13"})
    wheel = _wheel(
        path=tmp_path / "sample.whl", requirement=f"Requires-Dist: {requirement}\n"
    )
    assert any(
        "Unsupported solver SDK marker" in issue for issue in _inspect_wheel(wheel)
    )


@pytest.mark.parametrize(
    "entry",
    [
        "logs/run.log",
        "../escape.py",
        "native/target/run",
        "ospf_python/__pycache__/module.cpython-313.pyc",
        "ospf_python/module.pyc",
        "ospf_python/module.pyo",
    ],
)
def test_development_or_unsafe_wheel_entries_are_rejected(
    tmp_path: Path,
    entry: str,
) -> None:
    """拒绝开发产物和越界路径 / Reject development artifacts and unsafe paths."""
    assert _inspect_wheel(_wheel(path=tmp_path / "sample.whl", extra=entry))


def test_duplicate_native_extension_is_rejected(tmp_path: Path) -> None:
    """扩展不得重复 / The native extension must not be duplicated."""
    wheel = _wheel(path=tmp_path / "sample.whl", extra="ospf_python/_native.so")
    assert "Expected exactly one native extension" in _inspect_wheel(wheel)


@pytest.mark.parametrize(
    ("name", "issue"),
    [
        ("ospf_python.libs/libscip.so.9.2.4.0", "Bundled solver runtime"),
        ("ospf_python.libs/gurobi120.dll", "Bundled solver runtime"),
        ("ospf_python/core/solver/gurobi/gurobi_solver.py", None),
    ],
)
def test_solver_runtime_binaries_are_not_bundled(
    *, tmp_path: Path, name: str, issue: str | None
) -> None:
    """求解器运行时由外部提供 / Solver runtimes stay external to the wheel."""
    issues = _inspect_wheel(_wheel(path=tmp_path / "sample.whl", extra=name))
    if issue is None:
        assert not issues
    else:
        assert any(issue in item for item in issues)


@pytest.mark.parametrize(
    ("solvers", "platform", "expected"),
    [
        ([], "linux", "--locked"),
        (
            ["scip"],
            "linux",
            "--locked --features=scip --compatibility linux --auditwheel skip",
        ),
        (["gurobi10"], "win32", "--locked --features=gurobi10"),
    ],
)
def test_sdist_solver_builds_keep_runtime_external(
    *, solvers: list[str], platform: str, expected: str
) -> None:
    """Linux solver 包不得被 auditwheel 修复 / Linux solver wheels stay external."""
    assert _sdist_build_args(solvers, platform) == expected


def test_missing_typing_entries_are_rejected(tmp_path: Path) -> None:
    """类型声明必须随包发行 / Typing declarations must ship with the wheel."""
    wheel = tmp_path / "sample.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(_NATIVE, b"")
    assert "Missing wheel entry: ospf_python/py.typed" in _inspect_wheel(wheel)


def test_sdist_rejects_compiled_debug_symbols(tmp_path: Path) -> None:
    """源码包不包含 PDB / Source distributions exclude compiled debug symbols."""
    source = _sdist(tmp_path / "sample.tar.gz", extra={"ospf_python/_native.pdb": ""})
    issues = _inspect_sdist(source)
    assert issues == ["Compiled artifact in sdist: sample/ospf_python/_native.pdb"]


def test_sdist_accepts_complete_relative_documentation(tmp_path: Path) -> None:
    """相对链接按文档位置解析 / Resolve local links relative to each document."""
    source = _sdist(
        tmp_path / "sample.tar.gz",
        extra={
            "docs/index.md": (
                "[Readme](../README.md) [External](https://example.com/x) "
                "[Anchor](#part) [Contract](migration/api-map.toml)"
            ),
            "README.md": (
                "[中文](README_ch.md) `examples/demo.py`\nRun `python -m examples.demo`"
            ),
            "examples/demo.py": "",
        },
    )
    assert _inspect_sdist(source) == []


def test_sdist_resolves_encoded_and_nested_links(tmp_path: Path) -> None:
    """编码路径和嵌套目录可解析 / Resolve encoded paths and nested directories."""
    source = _sdist(
        tmp_path / "sample.tar.gz",
        extra={
            "docs/index.md": "见[文档](nested/a%20b.md#part)",
            "docs/nested/a b.md": "返回[主页](../../README.md)",
        },
    )
    assert _inspect_sdist(source) == []


@pytest.mark.parametrize(
    "text",
    [
        "见[不存在](docs/missing.md)",
        "[Outside](%2E%2E%2Foutside.md)",
    ],
)
def test_sdist_checks_non_ascii_and_encoded_links(*, tmp_path: Path, text: str) -> None:
    """检查中文前缀和编码越界 / Check links after Chinese text and encoded escapes."""
    source = _sdist(tmp_path / "sample.tar.gz", extra={"README.md": text})
    assert _inspect_sdist(source)


def test_sdist_ignores_code_block_links(tmp_path: Path) -> None:
    """代码中的链接不是文档引用 / Links in code blocks are not prose references."""
    source = _sdist(
        tmp_path / "sample.tar.gz",
        extra={
            "README.md": (
                "`[inline](missing.md)`\n"
                "```md\n[backtick](missing.md)\n```\n"
                "~~~md\n[tilde](missing.md)\n~~~\n"
            )
        },
    )
    assert _inspect_sdist(source) == []


@pytest.mark.parametrize(
    "kind", ["symbolic", "hard", "duplicate", "other-root", "backslash"]
)
def test_sdist_rejects_ambiguous_or_unsafe_entries(
    *, tmp_path: Path, kind: str
) -> None:
    """拒绝歧义或不安全条目 / Reject ambiguous or unsafe archive entries."""
    names = {
        "symbolic": "sample/link",
        "hard": "sample/link",
        "duplicate": "sample/README.md",
        "other-root": "other/file",
        "backslash": r"sample\..\escape.py",
    }
    entry = tarfile.TarInfo(names[kind])
    if kind in {"symbolic", "hard"}:
        entry.type = tarfile.SYMTYPE if kind == "symbolic" else tarfile.LNKTYPE
        entry.linkname = "../../outside"
    source = _sdist(tmp_path / "sample.tar.gz", extra_members=(entry,))
    assert _inspect_sdist(source)


def test_sdist_requires_pyproject_at_the_archive_root(tmp_path: Path) -> None:
    """嵌套配置不能伪装根配置 / Nested configuration cannot replace the root file."""
    source = _sdist(
        tmp_path / "sample.tar.gz",
        omit=("pyproject.toml",),
        extra={"nested/pyproject.toml": ""},
    )
    assert _inspect_sdist(source)


@pytest.mark.parametrize(
    "missing", ["README_ch.md", "docs/index.md", "examples/__init__.py"]
)
def test_sdist_requires_release_documentation(*, tmp_path: Path, missing: str) -> None:
    """缺少双语文档或示例包即失败 / Reject missing bilingual docs or examples."""
    source = _sdist(tmp_path / "sample.tar.gz", omit=(missing,))
    assert any(missing in issue for issue in _inspect_sdist(source))


@pytest.mark.parametrize(
    "text",
    [
        "[Missing](docs/migration/missing.md)",
        "[Outside](../../outside.md)",
        "`examples/missing.py`",
        "Run `python -m examples.missing`",
    ],
)
def test_sdist_rejects_broken_local_documentation_references(
    *, tmp_path: Path, text: str
) -> None:
    """拒绝不存在或越界的本地引用 / Reject missing or escaping local references."""
    source = _sdist(tmp_path / "sample.tar.gz", extra={"README.md": text})
    assert _inspect_sdist(source)
