"""Example 兼容性测试 / Example compatibility tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_EXAMPLES_DIR = Path(__file__).resolve().parent

# 脚本式示例没有 main()，只能作为脚本执行 / script-style examples have no main()
_SCRIPT_EXAMPLE_NAMES = (
    "bpp1d_example",
    "bpp2d_example",
    "csp2d_example",
    "math_symbol_example",
    "network_scheduling_example",
)


def test_bpp1d_column_pool_example_runs(capsys: pytest.CaptureFixture[str]) -> None:
    from examples.bpp1d_column_pool_example import main

    main()
    assert capsys.readouterr().out in {
        "BPP1D pool: generation=1, LP=3/2, final=2\n",
        "BPP1D pool: generation=1, compile a solver to run models\n",
    }


def test_bpp1d_pattern_policy_example_runs(capsys: pytest.CaptureFixture[str]) -> None:
    from examples.bpp1d_pattern_policy_example import main

    main()
    assert capsys.readouterr().out == "BPP1D policy: 2 single-identity candidates\n"


def test_clamp_binding_example_runs(capsys: pytest.CaptureFixture[str]) -> None:
    from examples.clamp_binding_example import main

    main()
    assert capsys.readouterr().out == "clamp: 1\n"


def test_ordinary_extrema_example_runs(capsys: pytest.CaptureFixture[str]) -> None:
    """普通极值示例消费 Result。 / Ordinary extrema example consumes Result."""
    from examples.ordinary_extrema_example import main

    main()
    assert "Extrema:" in capsys.readouterr().out


def test_runtime_unit_example_runs() -> None:
    """真实原生温差单位可公开消费。 / Actual native difference units can be consumed publicly."""
    from examples.runtime_unit_example import main

    main()


def test_quantity_duration_example_runs(capsys: pytest.CaptureFixture[str]) -> None:
    from examples.quantity_duration_example import main

    main()
    assert "signed/exact microseconds" in capsys.readouterr().out


def test_quantity_ordering_example_runs(capsys: pytest.CaptureFixture[str]) -> None:
    """极值和范围示例显式消费 Result。 / Extrema and range examples consume Result explicitly."""
    from examples.quantity_ordering_example import main

    main()
    assert capsys.readouterr().out.splitlines() == [
        "Quantity extrema: original objects, exact SI ordering, explicit Result",
        "QuantityValueRange: inclusive Rust comparison; dimension mismatch=Failed",
    ]


def test_quantity_conversion_example_runs(capsys: pytest.CaptureFixture[str]) -> None:
    """自然转换示例显式消费 Result。 / Natural conversion example consumes Result explicitly."""
    from examples.quantity_conversion_example import main

    main()
    assert capsys.readouterr().out.splitlines() == [
        "Quantity.to: 1/3 km -> 1000/3 m (Result, exact Fraction)",
        "Quantity.to: explicit custom numeric adapter, no implicit float",
        "Quantity.to: Decimal canonical export=1.23; dimension mismatch=Failed",
    ]


def test_integer_binding_example_runs(capsys: pytest.CaptureFixture[str]) -> None:
    """四种整数政策保留精度与零兼容。 / Four integer policies retain precision and zero compatibility."""
    from examples.integer_binding_example import main

    main()
    assert capsys.readouterr().out.splitlines() == [
        "Integer: unbounded / floor(-7/3)=-3 / zero sentinel=0",
        "UInteger: subtraction clamps to zero",
        "NumericInteger: exact arithmetic before bounded result",
        "NumericUInteger: nonnegative without a u64 ceiling",
    ]


def test_selection_example_runs(capsys: pytest.CaptureFixture[str]) -> None:
    """四入口均保留分数单位并显式消费成功结果。 / All four entries consume Result and retain exact units."""
    from examples.selection_example import main

    main()
    assert capsys.readouterr().out.splitlines() == [
        "combinations: 3 patterns; first=['1/2 m', '3/2 m']",
        "permutations: 6 patterns; first=['1/2 m', '3/2 m']",
        "combinations_async: 3 patterns; first=['1/2 m', '3/2 m']",
        "permutations_async: 6 patterns; first=['1/2 m', '3/2 m']",
    ]


def test_view_materialization_example_runs() -> None:
    from examples.view_materialization_example import main

    main()


def test_array_nested_example_runs() -> None:
    from examples.array_nested_example import main

    main()


def test_mapped_materialization_example_runs() -> None:
    from examples.mapped_materialization_example import main

    main()


def test_array_mapping_example_runs() -> None:
    from examples.array_mapping_example import main

    main()


def test_array_reduction_example_runs() -> None:
    from examples.array_reduction_example import main

    main()


def test_cartesian_product_example_runs() -> None:
    from examples.cartesian_product_example import main

    main()


def test_floating_binding_example_runs() -> None:
    from examples.floating_binding_example import main

    main()


def test_core_demo_runs() -> None:
    from examples.core_demo.demo1 import main

    main()


def test_demo1_runs() -> None:
    from examples.framework_demo.demo1.interface import Demo1Interface

    iface = Demo1Interface()
    result = iface.create_and_solve(
        nodes=["A", "B"],
        edges=[("e1", "A", "B", 10.0)],
        services=[("s1", "A", "B", 1.0)],
    )
    assert result.feasible is True


def test_demo3_runs() -> None:
    from examples.framework_demo.demo3.main import run_demo

    result = run_demo()
    assert int(str(result["iterations"])) > 0


def test_demo2_runs() -> None:
    from examples.framework_demo.demo2.extended_bpp3d_demo import run_demo

    run_demo()


def test_demo4_runs() -> None:
    from examples.framework_demo.demo4.gantt_demo import run_demo

    run_demo()


def test_quantity_arithmetic_example_runs() -> None:
    from examples.quantity_arithmetic_example import main

    main()


def test_quantity_snapshot_example_runs() -> None:
    """原生数量快照示例。 / Native quantity snapshot example."""
    from examples.quantity_snapshot_example import main

    main()


def test_prime_sieve_example_runs() -> None:
    """公开素数筛 Result 示例。 / Public prime-sieve Result example."""
    from examples.prime_sieve_example import main

    main()


def test_integer_power_example_runs() -> None:
    """公开整数幂Result示例。 / Public integer-power Result example."""
    from examples.integer_power_example import main

    main()


def test_trivalent_example_runs() -> None:
    """三值逻辑Result示例。 / Trivalent Result example."""
    from examples.trivalent_example import main

    main()


def test_logarithm_example_runs() -> None:
    """公开对数Result示例。 / Public logarithm Result example."""
    from examples.logarithm_example import main

    main()


def test_elementary_operators_example_runs(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """12个公开初等运算符显式消费Result。 / All twelve public operators consume Result."""
    from examples.elementary_operators_example import main

    main()
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 3
    assert lines[0].startswith("Elementary:")
    assert lines[1].startswith("Logs:")
    assert lines[2].startswith("Trig:")


def test_fractal_example_runs() -> None:
    """分形Result示例。 / Fractal Result example."""
    from examples.fractal_example import main

    main()


@pytest.mark.parametrize("name", _SCRIPT_EXAMPLE_NAMES)
def test_script_example_exits_cleanly(name: str) -> None:
    """脚本式示例真实执行且退出码为 0。 / Script-style examples run and exit 0."""
    completed = subprocess.run(
        [sys.executable, str(_EXAMPLES_DIR / f"{name}.py")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip()
