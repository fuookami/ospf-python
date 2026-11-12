"""族级比值政策的结构校验 / Structural validation of the family ratio policy.

政策文件是性能门禁的唯一输入，写坏一个字段会让门禁静默跳过用例
（runner 对未知 builder/无法解析的目标只会打印 error 并以 0 退出）。
本测试守住"每个用例都能真正被解析和调用"。
The policy file is the only input to the performance gate, and a broken field makes the gate
silently skip a case (the runner prints an error and exits 0 for unknown builders or
unresolvable targets). This test guards that every case actually resolves and calls.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

import pytest

POLICY = Path(__file__).resolve().parents[2] / "benchmarks" / "family_ratio_policy.json"


def _policy() -> dict[str, Any]:
    """读取政策文件 / Read the policy file."""
    return json.loads(POLICY.read_text(encoding="utf-8"))


def test_policy_is_well_formed() -> None:
    """必填字段存在且阈值合理 / Required fields exist and the threshold is sane."""
    policy = _policy()
    assert policy["mode"] == "acceptance"
    assert policy["threshold"] == pytest.approx(1.15)
    assert policy["gated_minimum"] > 0
    assert policy["cases"]


def test_every_case_has_the_required_fields() -> None:
    """每个用例都有 runner 需要的字段 / Every case carries the fields the runner needs."""
    for case in _policy()["cases"]:
        for key in ("family", "label", "module", "count"):
            assert key in case, f"{case.get('label')} 缺 {key}"
        assert case["count"] >= 10000, f"{case['label']} 的 count 低于 gated_minimum"


def test_every_plain_case_resolves_and_calls() -> None:
    """每个非 builder 用例都能解析并成功调用 / Every non-builder case resolves and calls.

    ``attrs`` 是**候选名列表**：runner 用 ``hasattr`` 逐个尝试，取第一个存在的名字，
    不是属性链。测试必须按同一规则解析，否则会误判。
    ``attrs`` is a list of **candidate names**: the runner probes each with ``hasattr`` and
    takes the first that exists. It is not an attribute path, so the test must resolve the
    same way or it misreads the policy.
    """
    for case in _policy()["cases"]:
        if "builder" in case:
            continue
        module = importlib.import_module(case["module"])
        target = next(
            (getattr(module, attr) for attr in case["attrs"] if hasattr(module, attr)),
            None,
        )
        assert target is not None, f"{case['label']} 的 attrs 一个都解析不到"
        assert callable(target), f"{case['label']} 的目标不可调用"
        # 调用一次：既证明参数形状正确，也证明不会抛异常。
        # 用例可以只有 kwargs（如 `julia_contains_pair` 全是 keyword-only 参数），
        # 所以这里必须同时传 kwargs——runner 一直支持，测试此前漏了。
        # Call once: proves both the argument shape and that nothing raises. A case may carry
        # only kwargs (e.g. all-keyword-only `julia_contains_pair`), so pass them too.
        target(*case.get("args", ()), **case.get("kwargs", {}))


def test_elementary_operators_cover_all_twelve_public_operators() -> None:
    """12 个公开算子全部纳入政策 / All twelve public operators are in the policy."""
    labels = {
        case["label"]
        for case in _policy()["cases"]
        if case["family"] == "elementary_operators"
    }
    expected = {
        f"{name}-complete-call"
        for name in (
            "exp",
            "exp2",
            "exp10",
            "ln",
            "log2",
            "log10",
            "sin",
            "cos",
            "tan",
            "asin",
            "acos",
            "atan",
        )
    }
    assert labels == expected
