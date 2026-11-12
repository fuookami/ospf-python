"""绝对预算测量：给"无切换前实现"的构造类合同一个有依据的每次调用上限。

Absolute budget runner: for contracts without a pre-cutover implementation, a ratio
gate is meaningless. This measures the current cost per call and compares it with a
ceiling expressed relative to a bare frozen dataclass of the SAME keyword arity, measured
in the same round. Absolute nanosecond ceilings proved unreproducible (B140): they move with
machine load, while the ratio does not.

**本脚本只在当前树运行**（绝对预算不需要基线树）。

用法 / Usage:
  python benchmarks/absolute_budget.py --output report.json [--rounds 3]
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

ANCHOR_FACTOR = 1.3
"""相对上限：同轮、同关键字数量的裸冻结 dataclass 为标尺。

上限定为 1.3 倍：被测算的 DTO 本身就是裸 dataclass，额外开销必须来自真实验证或转换，
而这部分应被 30% 的余量覆盖；再多就说明 `__post_init__` 里在做不合算的事。
Relative ceiling against a bare frozen dataclass with the same keyword arity.
"""

_ARITY_CACHE: dict[int, type] = {}
"""按关键字数量缓存的裸 dataclass。 / Bare dataclasses cached per keyword arity."""

REPEATS = 2000
"""每例总重复次数。 / Total repetitions per case."""
BLOCKS_PER_ROUND = 4
"""每轮的交替块数。 / Alternating blocks per round."""


def anchor_factory(arity: int) -> Callable[[], object]:
    """给出任意关键字数量的裸冻结 dataclass 工厂。 / A bare frozen dataclass factory of any arity.

    用 `eval` 生成**显式关键字**调用：`**mapping` 解包本身要约 200 ns，
    若标尺用解包而用例用显式关键字，标尺会系统性偏慢，判定随之失真。
    The anchor must call with explicit keywords, because `**mapping` unpacking costs about
    200 ns; an unpacking anchor would be systematically slower than the cases it measures.
    """
    if arity not in _ARITY_CACHE:
        namespace = {"__annotations__": {f"f{index}": object for index in range(arity)}}
        _ARITY_CACHE[arity] = dataclass(frozen=True)(
            type(f"_Anchor{arity}", (), namespace)
        )
    anchor_type = _ARITY_CACHE[arity]
    keywords = ", ".join(f"f{index}={index}" for index in range(arity))
    return eval(  # noqa: S307 - 受控构造：名字与类型都由本函数生成
        f"lambda anchor_type=anchor_type: anchor_type({keywords})",
        {"anchor_type": anchor_type},
    )


def measure(factory: Callable[[], object], repeats: int = REPEATS) -> float:
    """测一个块的平均纳秒。 / Average nanoseconds over one block."""
    for _ in range(max(20, repeats // 20)):
        factory()
    started = time.perf_counter_ns()
    for _ in range(repeats):
        factory()
    return (time.perf_counter_ns() - started) / repeats


def measure_paired(
    factory: Callable[[], object], anchor: Callable[[], object], rounds: int
) -> tuple[float, float, float]:
    """逐轮交错测量用例与锚点，返回中位纳秒、中位锚点、中位倍数。

    交错而非"先测锚点再测用例"，因为 CPU 干扰是突发性的：
    Measure the case and the anchor in every round and pair them, because interference
    arrives in bursts; an anchor measured once at the start cannot absorb a burst that
    lands on the case.
    """
    case_samples: list[float] = []
    anchor_samples: list[float] = []
    ratios: list[float] = []
    block = max(1, REPEATS // BLOCKS_PER_ROUND)
    for _ in range(rounds):
        for _ in range(BLOCKS_PER_ROUND):
            # 块级交替：干扰往往是秒级突发，块比"整轮"细，才能落到同一侧。
            # Alternate at block granularity: interference arrives in bursts of seconds,
            # so blocks must be finer than a whole round to land on both sides alike.
            anchor_ns = measure(anchor, block)
            case_ns = measure(factory, block)
            case_samples.append(case_ns)
            anchor_samples.append(anchor_ns)
            ratios.append(case_ns / anchor_ns if anchor_ns else 0.0)
    return (
        statistics.median(case_samples),
        statistics.median(anchor_samples),
        statistics.median(ratios),
    )


def build_cases() -> list[dict]:
    """构造用例表。 / Build the case table."""

    from ospf_python._binding import model as model_module
    from ospf_python._binding.bpp1d import (
        AuxiliaryVariable,
        BinSpec,
        CompiledColumn,
        ExtensionConstraint,
        ItemSpec,
        PackingLpSolution,
        PackingSolution,
        PatternExtensionSpec,
        PatternExtraction,
        PatternPoolSnapshot,
        PatternRegistration,
        VariableRef,
    )
    from ospf_python._binding.gantt_activity import (
        Activity,
        Mode,
        Placement,
        Precedence,
        Resource,
        Row,
        Schedule,
    )
    from ospf_python._binding.unit_registry import Family
    from ospf_python.math.algebra.number.rational import Rational as PublicRational
    from ospf_python.quantities.unit.length import METER

    # 参数对象在计时外预置：否则测到的是"造字典/元组"的成本，而不是 DTO 构造成本。
    # Pre-build argument objects outside the timed call, so the measurement is the DTO,
    # not the literal allocation.
    coefficient_map = {"x": 1.0}
    row_price_map = {"r": 0.2}
    # 用公共 Rational 预置值：字段注解是 `Rational`，`_binding.numeric.Rational` 只能由原生
    # 工厂创建，公共类型才是真实入参；用 Fraction 虽不报错但不是真实调用形态。
    # Public Rational values: the annotation names `Rational`, and the binding-side
    # Rational only exists behind a native factory, so the public type is what real
    # callers pass; Fraction would not raise but would not model a real call.
    length_value = PublicRational(3, 1)
    weight_value = PublicRational(2, 1)
    bin_length = PublicRational(10, 1)
    bin_weight = PublicRational(20, 1)
    bin_cost = PublicRational(5, 1)
    capacity_value = PublicRational(10, 1)
    one_rational = PublicRational(1, 1)
    two_rational = PublicRational(2, 1)
    mode_resources = (("r1", one_rational),)

    # 别名是纯元组：Ratio = (int, int)，Pattern = (str, dict)，Usage = (str, dict, int)。
    # Aliases are plain tuples: Ratio = (int, int), Pattern = (str, dict), Usage = (str, dict, int).
    ratio_one = (1, 1)
    item_rows = [("i0", (3, 1), (2, 1), 1, {})]
    bin_rows = [("b0", (10, 1), (20, 1), (5, 1), None)]
    reference = VariableRef(model_identity=7)
    extension_terms = [(reference, one_rational)]
    pattern = ("p0", {})
    usage_rows = [("i0", {}, 1)]
    packed_value = tuple()
    mode_starts = (0,)
    empty_values: dict[object, object] = {}
    mode_value = Mode(
        id="m1",
        duration_ns=3,
        starts_ns=mode_starts,
        resources=mode_resources,
        cost=one_rational,
    )
    placement_value = Placement(task="t1", mode="m1", start_ns=0, end_ns=3)

    # `unit_registry.Family` 是**按设计就是纯 Python** 的静态证据 DTO：它的模块里
    # 一处 `_native` 都没有，归档基线树里也是同一份代码，所以比值门禁对它无意义，
    # 只能用绝对预算（同关键字数量的裸冻结 dataclass × 1.3）来判定。
    # `unit_registry.Family` is a pure-Python static-evidence DTO by design: its module
    # references `_native` nowhere and the archived baseline tree holds the same code, so a
    # ratio gate is meaningless for it; only the absolute budget applies.
    family_methods: dict[str, tuple[object, object]] = {}
    family_powers = (1, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    return [
        {
            "family": "model",
            "label": "VariableSpec",
            "keywords": 4,
            "factory": lambda: model_module.VariableSpec(name="x"),
        },
        {
            "family": "model",
            "label": "ColumnSpec",
            "keywords": 3,
            "factory": lambda: model_module.ColumnSpec(
                id="c", block="b", values=coefficient_map
            ),
        },
        {
            "family": "model",
            "label": "ProjectionMasterInfo",
            "keywords": 6,
            "factory": lambda: model_module.ProjectionMasterInfo(
                source_generation=1, integer=True, columns=2, variables=3, rows=4
            ),
        },
        {
            "family": "model",
            "label": "PricingInfo",
            "keywords": 4,
            "factory": lambda: model_module.PricingInfo(
                block="b",
                coefficients=coefficient_map,
                convexity_price=0.5,
                row_prices=row_price_map,
            ),
        },
        {
            "family": "bpp1d",
            "label": "VariableRef",
            "keywords": 3,
            "factory": lambda: VariableRef(model_identity=7),
        },
        {
            "family": "bpp1d",
            "label": "ItemSpec",
            "keywords": 5,
            "factory": lambda: ItemSpec(
                id="i0", length=length_value, weight=weight_value, amount=1
            ),
        },
        {
            "family": "bpp1d",
            "label": "BinSpec",
            "keywords": 5,
            "factory": lambda: BinSpec(
                id="b0", length=bin_length, max_weight=bin_weight, cost=bin_cost
            ),
        },
        {
            "family": "gantt_activity",
            "label": "Precedence",
            "keywords": 3,
            "factory": lambda: Precedence(
                predecessor="t1", successor="t2", min_gap_ns=0
            ),
        },
        {
            "family": "gantt_activity",
            "label": "Placement",
            "keywords": 4,
            "factory": lambda: Placement(task="t1", mode="m1", start_ns=0, end_ns=3),
        },
        {
            "family": "gantt_activity",
            "label": "Resource",
            "keywords": 4,
            "factory": lambda: Resource(id="r1", capacity=capacity_value, unit=METER),
        },
        {
            "family": "bpp1d",
            "label": "AuxiliaryVariable",
            "keywords": 4,
            "factory": lambda: AuxiliaryVariable(name="x"),
        },
        {
            "family": "bpp1d",
            "label": "ExtensionConstraint",
            "keywords": 4,
            "factory": lambda: ExtensionConstraint(
                name="c",
                terms=extension_terms,
                relation="le",
                rhs=two_rational,
            ),
        },
        {
            "family": "bpp1d",
            "label": "PatternExtensionSpec",
            "keywords": 4,
            "factory": lambda: PatternExtensionSpec(),
        },
        {
            "family": "bpp1d",
            "label": "CompiledColumn",
            "keywords": 3,
            "factory": lambda: CompiledColumn(
                reference=reference, variable_identity=(1, 2), pattern=None
            ),
        },
        {
            "family": "bpp1d",
            "label": "PatternPoolSnapshot",
            "keywords": 4,
            "factory": lambda: PatternPoolSnapshot(
                generation=1, model_identity=7, patterns=[pattern], compiled_columns=[]
            ),
        },
        {
            "family": "bpp1d",
            "label": "PackingLpSolution",
            "keywords": 2,
            "factory": lambda: PackingLpSolution(
                values=empty_values, model_objective=one_rational
            ),
        },
        {
            "family": "bpp1d",
            "label": "PackingSolution",
            "keywords": 4,
            "factory": lambda: PackingSolution(
                usages=usage_rows,
                packed=packed_value,
                model_objective=one_rational,
                indicators=empty_values,
            ),
        },
        {
            "family": "bpp1d",
            "label": "PatternRegistration",
            "keywords": 9,
            "factory": lambda: PatternRegistration(
                model_identity=7,
                stage="lp",
                items=item_rows,
                bins=bin_rows,
                spacing=ratio_one,
                length_unit=METER,
                weight_unit=METER,
                objective="min",
                candidates=[(reference, pattern)],
            ),
        },
        {
            "family": "bpp1d",
            "label": "PatternExtraction",
            "keywords": 8,
            "factory": lambda: PatternExtraction(
                items=item_rows,
                bins=bin_rows,
                spacing=ratio_one,
                length_unit=METER,
                weight_unit=METER,
                objective="min",
                candidates=[(reference, pattern)],
                values={},
            ),
        },
        {
            "family": "gantt_activity",
            "label": "Mode",
            "keywords": 5,
            "factory": lambda: Mode(
                id="m1",
                duration_ns=3,
                starts_ns=mode_starts,
                resources=mode_resources,
                cost=one_rational,
            ),
        },
        {
            "family": "gantt_activity",
            "label": "Activity",
            "keywords": 3,
            "factory": lambda: Activity(id="a1", modes=(mode_value,)),
        },
        {
            "family": "gantt_activity",
            "label": "Row",
            "keywords": 6,
            "factory": lambda: Row(id="row1", unit=METER, coefficients=()),
        },
        {
            "family": "gantt_activity",
            "label": "Schedule",
            "keywords": 3,
            "factory": lambda: Schedule(placements=(placement_value,), cost=(0, 0)),
        },
        {
            "family": "model",
            "label": "SolveReport",
            "keywords": 8,
            "factory": lambda: model_module.SolveReport(
                model_identity=1,
                model_generation=1,
                problem_status="optimal",
                termination_reason="ok",
                solution_presence="present",
                objective=1.0,
                values=(),
                raw_json="{}",
            ),
        },
        {
            "family": "model",
            "label": "PricingCandidate",
            "keywords": 2,
            "factory": lambda: model_module.PricingCandidate(
                values={}, reduced_cost=0.0
            ),
        },
        {
            "family": "model",
            "label": "PricingBoundInfo",
            "keywords": 4,
            "factory": lambda: model_module.PricingBoundInfo(
                block="b",
                reported_cx_lower=0.0,
                convexity_price=0.0,
                reported_nonnegative=True,
            ),
        },
        {
            "family": "unit_registry",
            "label": "Family",
            "keywords": 4,
            "factory": lambda: Family(
                cls=dict,
                powers=family_powers,
                affine=False,
                methods=family_methods,
            ),
        },
    ]


def main() -> int:
    """执行测量并判定。 / Measure and decide."""
    parser = argparse.ArgumentParser(
        description="绝对预算测量 / Absolute budget runner"
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--rounds", type=int, default=3)
    arguments = parser.parse_args()

    started = time.perf_counter()
    cases = build_cases()
    # 守卫：用例的计时路径里不得再构造参数。这个失误已经出现过三次（Fraction、字面量字典），
    # 每次都会把"参数开销"记成"DTO 开销"，因此改成机械拦截。
    # Guard: no case may build its arguments inside the timed call. This mistake has
    # already happened three times and always books argument cost as DTO cost.
    polluted = [
        case["label"]
        for case in cases
        if {"Fraction", "Rational", "PublicRational"}
        & (set(case["factory"].__code__.co_names) | set(case["factory"].__code__.co_freevars))
    ]
    if polluted:
        print(f"refusing to measure: arguments built inside the timed call: {polluted}")
        return 2

    results = []
    for case in cases:
        # 标尺按用例自己的关键字数量匹配，隔离"Python 关键字参数本身的开销"。
        # Match the anchor to the case's own keyword arity, isolating the cost of keyword
        # arguments themselves.
        median, anchor, ratio = measure_paired(
            case["factory"], anchor_factory(case["keywords"]), arguments.rounds
        )

        results.append(
            {
                "family": case["family"],
                "label": case["label"],
                "keywords": case["keywords"],
                "median_ns": round(median, 1),
                "anchor_ns": round(anchor, 1),
                "ratio": round(ratio, 2),
                "within_budget": ratio <= ANCHOR_FACTOR,
            }
        )
    elapsed = time.perf_counter() - started
    document = {
        "mode": "absolute-budget",
        "rounds": arguments.rounds,
        "repeats_per_round": REPEATS,
        "elapsed_seconds": round(elapsed, 1),
        "anchor_median_ns": round(
            statistics.median([item["anchor_ns"] for item in results]), 1
        ),
        "anchor_note": (
            "Anchor is the same-run, same-arity cost of a bare frozen dataclass. It tracks the "
            "interpreter and machine load, so the ratio is reproducible while absolute ns are not."
        ),
        "anchor_factor": ANCHOR_FACTOR,
        "ceiling_formula": (
            f"ratio <= {ANCHOR_FACTOR} * bare frozen dataclass of the same keyword arity"
        ),
        "cases": results,
        "within_budget": sum(1 for item in results if item["within_budget"]),
        "total": len(results),
        "note": (
            "Ceilings are derived from the measured floor (B138) and are NOT yet approved; "
            "this run only shows whether the current implementation would fit them."
        ),
    }
    Path(arguments.output).write_text(
        json.dumps(document, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    for item in results:
        print(
            f"{item['label']:22} median={item['median_ns']:>8.0f} ns  "
            f"kw={item['keywords']} anchor={item['anchor_ns']:>5.0f} ns  "
            f"ratio={item['ratio']}x  within={item['within_budget']}"
        )
    print(
        f"within budget: {document['within_budget']}/{document['total']} | {elapsed:.1f}s"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
