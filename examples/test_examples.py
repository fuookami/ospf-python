"""Example 兼容性测试 / Example compatibility tests."""

from __future__ import annotations


def test_core_demo_runs() -> None:
    from examples.core_demo.basic_model import run_demo

    run_demo()


def test_bpp3d_demo_runs() -> None:
    from examples.framework_demo.demo1.bpp3d_demo import run_demo

    run_demo()


def test_extended_bpp3d_demo_runs() -> None:
    from examples.framework_demo.demo2.extended_bpp3d_demo import run_demo

    run_demo()


def test_gantt_demo_runs() -> None:
    from examples.framework_demo.demo4.gantt_demo import run_demo

    run_demo()
