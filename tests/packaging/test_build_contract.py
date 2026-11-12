"""混合包发行配置合同 / Mixed-package distribution configuration contracts."""

from __future__ import annotations

import tomllib
from pathlib import Path

from packaging.requirements import Requirement

_ROOT = Path(__file__).resolve().parents[2]


def test_maturin_build_configuration() -> None:
    """绑定路径和模块名固定 / The binding path and module name are fixed."""
    project = tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["build-system"]["build-backend"] == "maturin"
    assert project["tool"]["maturin"]["module-name"] == "ospf_python._native"
    assert project["tool"]["maturin"]["manifest-path"] == "native/Cargo.toml"
    assert "**/*.pdb" in project["tool"]["maturin"]["exclude"]
    includes = {
        entry["path"]
        for entry in project["tool"]["maturin"]["include"]
        if entry["format"] == "sdist"
    }
    assert {
        "README_ch.md",
        "docs/**/*.md",
        "docs/**/*.toml",
        "examples/**/*.py",
        "examples/**/*.md",
    } <= includes
    assert (_ROOT / "ospf_python/py.typed").is_file()
    assert (_ROOT / "ospf_python/_native.pyi").is_file()


def test_base_install_does_not_require_solver_sdks() -> None:
    """基础依赖不强制 solver SDK / Base dependencies do not require solver SDKs."""
    project = tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    for requirement in project["project"]["dependencies"]:
        assert not requirement.startswith(
            ("gurobipy", "pyscipopt", "coptpy", "mindoptpy")
        )
    assert project["project"]["optional-dependencies"]["gurobi"] == ["gurobipy>=10,<13"]


def test_dev_extra_includes_solver_test_timeout_plugin() -> None:
    """求解器 CI 的超时选项有插件支持 / The solver CI timeout has its plugin."""
    project = tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert any(
        Requirement(requirement).name == "pytest-timeout"
        for requirement in project["project"]["optional-dependencies"]["dev"]
    )


def test_native_dependency_is_not_a_machine_local_path() -> None:
    """发行依赖无开发机相邻路径 / Distribution dependencies have no local sibling path."""
    manifest = tomllib.loads((_ROOT / "native/Cargo.toml").read_text(encoding="utf-8"))
    revisions = set()
    for crate in (
        "ospf-rust-base",
        "ospf-rust-core",
        "ospf-rust-framework",
        "ospf-rust-framework-bpp",
        "ospf-rust-framework-bpp1d",
        "ospf-rust-framework-gantt-scheduling",
        "ospf-rust-math",
        "ospf-rust-multiarray",
        "ospf-rust-quantities",
        # 新布局里 scip/gurobi 是独立 crate（crates/core-plugin/*），
        # 它们同样必须是远端 URL + 40 位 rev——这条契约升级后更强。
        # In the new layout scip/gurobi are separate crates; they must obey the same rule.
        "ospf-rust-core-plugin-scip",
        "ospf-rust-core-plugin-gurobi",
    ):
        source = manifest["dependencies"][crate]
        assert source["git"] == "https://github.com/fuookami/ospf-rust.git"
        assert len(source["rev"]) == 40
        assert "path" not in source
        assert "branch" not in source
        revisions.add(source["rev"])
    assert len(revisions) == 1
    baseline = tomllib.loads(
        (_ROOT / "docs/migration/api-map.toml").read_text(encoding="utf-8")
    )["baseline"]
    assert revisions == {baseline["rust_revision"]}
    assert "patch" not in manifest
    assert manifest["features"]["default"] == []


def test_all_locked_ospf_crates_use_the_fixed_remote_revision() -> None:
    """传递依赖也不能悄然跟随邻仓库 / Transitive dependencies cannot follow the adjacent checkout."""
    baseline = tomllib.loads(
        (_ROOT / "docs/migration/api-map.toml").read_text(encoding="utf-8")
    )["baseline"]
    lock = tomllib.loads((_ROOT / "native/Cargo.lock").read_text(encoding="utf-8"))
    revision = baseline["rust_revision"]
    expected = f"git+{baseline['rust_repository']}?rev={revision}#{revision}"
    packages = [
        item for item in lock["package"] if item["name"].startswith("ospf-rust-")
    ]
    assert packages
    assert all(item["source"] == expected for item in packages)


def test_solver_features_match_rust_version_policy() -> None:
    """不引入 Gurobi 13 或默认别名 / Do not add Gurobi 13 or a default-version alias."""
    manifest = tomllib.loads((_ROOT / "native/Cargo.toml").read_text(encoding="utf-8"))
    # 新布局：scip/gurobi 是独立 crate，特性从 `ospf-rust-core/<name>` 变成
    # `dep:<plugin-crate>` + `<plugin-crate>/<name>`。契约的意图不变
    # （不引入 Gurobi 13、不引入默认别名），只是换掉旧布局假设。
    # New layout: scip/gurobi are separate crates. The contract's intent is unchanged.
    expected = {
        "scip": [
            "dep:ospf-rust-core-plugin-scip",
            "ospf-rust-core-plugin-scip/scip",
        ],
        "gurobi10": [
            "dep:ospf-rust-core-plugin-gurobi",
            "ospf-rust-core-plugin-gurobi/gurobi10",
        ],
        "gurobi11": [
            "dep:ospf-rust-core-plugin-gurobi",
            "ospf-rust-core-plugin-gurobi/gurobi11",
        ],
        "gurobi12": [
            "dep:ospf-rust-core-plugin-gurobi",
            "ospf-rust-core-plugin-gurobi/gurobi12",
        ],
    }
    for name, want in expected.items():
        assert manifest["features"][name] == want
    assert "gurobi13" not in manifest["features"]
    assert "gurobi" not in manifest["features"]
