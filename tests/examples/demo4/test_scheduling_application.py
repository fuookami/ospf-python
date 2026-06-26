"""Scheduling application 测试 / Scheduling application tests.

覆盖 SchedulingApplication.run() 输入/输出、结果验证和
上下文集成。
Covers SchedulingApplication.run() input/output,
result validation, and context integration.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from examples.framework_demo.demo4.application.scheduling_application import (
    SchedulingApplication,
    SchedulingResult,
)
from examples.framework_demo.demo4.domain.bunch_compilation.model.bunch_context import (
    BunchContext,
)
from examples.framework_demo.demo4.domain.bunch_generation.model.generation_context import (
    GenerationContext,
)
from examples.framework_demo.demo4.domain.cargo.model.cargo import (
    Cargo,
)
from examples.framework_demo.demo4.domain.crew.model.crew import Crew
from examples.framework_demo.demo4.domain.crew.model.crew_context import (
    CrewContext,
)
from examples.framework_demo.demo4.domain.passenger.model.booking_class import (
    BookingClass,
)
from examples.framework_demo.demo4.domain.passenger.model.passenger import (
    Passenger,
)
from examples.framework_demo.demo4.domain.passenger.model.passenger_context import (
    PassengerContext,
)
from examples.framework_demo.demo4.domain.rule.model.rule_context import (
    RuleContext,
)
from examples.framework_demo.demo4.domain.task.model.flight_task import (
    FlightTask,
)
from examples.framework_demo.demo4.domain.task.model.task_context import (
    TaskContext,
)
from examples.framework_demo.demo4.domain.task.model.task_priority import (
    TaskPriority,
)


def _make_app() -> SchedulingApplication:
    """创建测试应用 / Create test application."""
    return SchedulingApplication(
        task_context=TaskContext(),
        crew_context=CrewContext(),
        passenger_context=PassengerContext(),
        bunch_context=BunchContext(),
        generation_context=GenerationContext(),
        rule_context=RuleContext(),
    )


def _make_tasks(count: int = 2) -> tuple[FlightTask, ...]:
    """创建测试任务 / Create test tasks."""
    base = datetime(2025, 6, 1, 8, 0)
    return tuple(
        FlightTask(
            task_id=f"T{i}",
            flight_no=f"CA{1000 + i}",
            origin="PEK",
            destination="PVG",
            departure_time=base + timedelta(hours=i * 3),
            arrival_time=base + timedelta(hours=i * 3 + 2),
            aircraft_type="A320",
            priority=TaskPriority.NORMAL,
        )
        for i in range(count)
    )


def _make_crews() -> tuple[Crew, ...]:
    """创建测试机组 / Create test crews."""
    return (
        Crew(
            crew_id="CR1",
            name="Alpha",
            base_airport="PEK",
            qualifications=("A320",),
        ),
    )


def _make_passengers() -> tuple[Passenger, ...]:
    """创建测试旅客 / Create test passengers."""
    return (
        Passenger(
            passenger_id="P1",
            name="Zhang",
            booking_class=BookingClass.ECONOMY,
        ),
        Passenger(
            passenger_id="P2",
            name="Li",
            booking_class=BookingClass.FIRST,
        ),
    )


class TestSchedulingResult:
    """SchedulingResult 测试 / Result tests."""

    def test_default_values(self) -> None:
        """默认值 / Default values."""
        r = SchedulingResult(
            schedule=(),
            crew_assignments=(),
            passenger_allocations=(),
            violations=(),
        )
        assert r.feasible is False
        assert r.objective_value == float("inf")

    def test_frozen(self) -> None:
        """不可变 / Frozen."""
        r = SchedulingResult(
            schedule=(),
            crew_assignments=(),
            passenger_allocations=(),
            violations=(),
        )
        with pytest.raises(AttributeError):
            r.feasible = True  # type: ignore[misc]


class TestSchedulingApplication:
    """SchedulingApplication 测试 / Application tests."""

    def test_run_with_tasks(self) -> None:
        """带任务运行 / Run with tasks."""
        app = _make_app()
        result = app.run(
            tasks=_make_tasks(2),
            crews=_make_crews(),
            passengers=_make_passengers(),
            cargos=(),
        )
        assert isinstance(result, SchedulingResult)

    def test_run_empty(self) -> None:
        """空输入运行 / Run with empty input."""
        app = _make_app()
        result = app.run(
            tasks=(),
            crews=(),
            passengers=(),
            cargos=(),
        )
        assert isinstance(result, SchedulingResult)

    def test_run_with_cargo(self) -> None:
        """带货物运行 / Run with cargo."""
        app = _make_app()
        cargos = (
            Cargo(
                cargo_id="CG1",
                weight=500.0,
                volume=1.0,
                priority=5,
                destination="PVG",
            ),
        )
        result = app.run(
            tasks=_make_tasks(1),
            crews=_make_crews(),
            passengers=(),
            cargos=cargos,
        )
        assert isinstance(result, SchedulingResult)

    def test_result_has_schedule(self) -> None:
        """结果包含调度 / Result has schedule."""
        app = _make_app()
        result = app.run(
            tasks=_make_tasks(1),
            crews=_make_crews(),
            passengers=_make_passengers(),
            cargos=(),
        )
        assert isinstance(result.schedule, tuple)

    def test_result_has_violations(self) -> None:
        """结果包含违规 / Result has violations."""
        app = _make_app()
        result = app.run(
            tasks=_make_tasks(1),
            crews=_make_crews(),
            passengers=_make_passengers(),
            cargos=(),
        )
        assert isinstance(result.violations, tuple)

    def test_contexts_populated_after_run(self) -> None:
        """运行后上下文已填充 / Contexts populated after run."""
        task_ctx = TaskContext()
        crew_ctx = CrewContext()
        pax_ctx = PassengerContext()
        app = SchedulingApplication(
            task_context=task_ctx,
            crew_context=crew_ctx,
            passenger_context=pax_ctx,
            bunch_context=BunchContext(),
            generation_context=GenerationContext(),
            rule_context=RuleContext(),
        )
        tasks = _make_tasks(2)
        app.run(
            tasks=tasks,
            crews=_make_crews(),
            passengers=_make_passengers(),
            cargos=(),
        )
        assert task_ctx.task_count == 2

    def test_run_with_many_tasks(self) -> None:
        """多任务运行 / Run with many tasks."""
        app = _make_app()
        result = app.run(
            tasks=_make_tasks(5),
            crews=_make_crews(),
            passengers=_make_passengers(),
            cargos=(),
        )
        assert isinstance(result, SchedulingResult)
