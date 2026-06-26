"""Example 兼容性测试 / Example compatibility tests."""

from __future__ import annotations


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
