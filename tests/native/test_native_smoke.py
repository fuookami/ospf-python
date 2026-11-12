"""原生绑定安装冒烟 / Native binding installation smoke tests."""

from __future__ import annotations

import tomllib
from pathlib import Path

from ospf_python import __version__, _native

_ROOT = Path(__file__).resolve().parents[2]


def test_native_build_identity_matches_pinned_source() -> None:
    """编译身份与依赖来源一致 / Build identity matches the pinned source."""
    info = _native.build_info()
    baseline = tomllib.loads(
        (_ROOT / "docs/migration/api-map.toml").read_text(encoding="utf-8")
    )["baseline"]
    manifest = tomllib.loads((_ROOT / "native/Cargo.toml").read_text(encoding="utf-8"))
    assert info["binding_version"] == __version__ == _native.__version__
    assert info["rust_revision"] == baseline["rust_revision"]
    assert info["required_toolchain"] == baseline["rust_toolchain"]
    assert manifest["dependencies"]["ospf-rust-base"]["rev"] == info["rust_revision"]
    assert info["target_os"] in {"windows", "linux", "macos"}
    assert info["target_arch"] in {"x86_64", "aarch64"}


def test_build_only_claims_explicit_rust_solver_versions() -> None:
    """仅报告显式 Rust 后端 / Report only explicit Rust backends."""
    solvers = _native.build_info()["native_solvers"]
    declared = set(solvers.split(",")) if solvers else set()
    assert declared <= {"scip", "gurobi10", "gurobi11", "gurobi12"}
    assert len(declared & {"gurobi10", "gurobi11", "gurobi12"}) <= 1


def test_native_success_transport() -> None:
    """成功值通过真实扩展返回 / A value returns through the real extension."""
    assert _native._checked_nonnegative(42) == (42, None)
    assert _native._checked_nonnegative(0) == (0, None)


def test_native_business_failure_is_data_not_exception() -> None:
    """业务失败传输为数据 / A business failure is data rather than an exception."""
    value, error = _native._checked_nonnegative(-1)
    assert value is None
    assert error is not None
    assert error[0] == 0x34
    assert "Value must be nonnegative" in error[1]


def test_build_info_is_a_detached_snapshot() -> None:
    """调用方修改不影响构建身份 / Caller changes cannot mutate build identity."""
    snapshot = _native.build_info()
    snapshot["rust_revision"] = "changed"
    assert _native.build_info()["rust_revision"] != "changed"
