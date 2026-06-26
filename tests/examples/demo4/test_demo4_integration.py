"""Demo4 integration 测试 / Demo4 integration tests.

端到端集成测试：覆盖完整调度流程。
End-to-end integration: covers full scheduling flow.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from examples.framework_demo.demo4.application.scheduling_application import (
    SchedulingApplication,
)
from examples.framework_demo.demo4.domain.bunch_compilation.model.bunch_context import (
    BunchContext,
)
from examples.framework_demo.demo4.domain.bunch_generation.model.generation_config import (
    GenerationConfig,
)
from examples.framework_demo.demo4.domain.bunch_generation.model.generation_context import (
    GenerationContext,
)
from examples.framework_demo.demo4.domain.bunch_generation.model.generation_strategy import (
    GenerationStrategy,
)
from examples.framework_demo.demo4.domain.bunch_generation.service.generation_selector import (
    GenerationSelector,
)
from examples.framework_demo.demo4.domain.bunch_generation.service.greedy_generator import (
    GreedyGenerator,
    TaskSlot,
)
from examples.framework_demo.demo4.domain.cargo.model.cargo import Cargo
from examples.framework_demo.demo4.domain.cargo.service.cargo_allocator import (
    BunchSlot,
    CargoAllocator,
)
from examples.framework_demo.demo4.domain.crew.model.crew import Crew
from examples.framework_demo.demo4.domain.crew.model.crew_context import (
    CrewContext,
)
from examples.framework_demo.demo4.domain.crew.model.crew_member import (
    CrewMember,
    CrewRole,
)
from examples.framework_demo.demo4.domain.crew.model.pilot import (
    LicenseType,
    Pilot,
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
from examples.framework_demo.demo4.domain.passenger.service.passenger_allocator import (
    PassengerAllocator,
    SeatMap,
)
from examples.framework_demo.demo4.domain.rule.model.rule import Rule
from examples.framework_demo.demo4.domain.rule.model.rule_context import (
    RuleContext,
)
from examples.framework_demo.demo4.domain.rule.model.rule_type import (
    RuleType,
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


class TestFullSchedulingFlow:
    """完整调度流程测试 / Full scheduling flow tests."""

    def test_end_to_end_scheduling(self) -> None:
        """端到端调度 / End-to-end scheduling."""
        task_ctx = TaskContext()
        crew_ctx = CrewContext()
        pax_ctx = PassengerContext()
        bunch_ctx = BunchContext()
        gen_ctx = GenerationContext()
        rule_ctx = RuleContext()

        # 注册任务 / Register tasks
        base = datetime(2025, 6, 1, 8, 0)
        tasks = (
            FlightTask(
                task_id="T1",
                flight_no="CA1001",
                origin="PEK",
                destination="PVG",
                departure_time=base,
                arrival_time=base + timedelta(hours=2),
                aircraft_type="A320",
                priority=TaskPriority.HIGH,
            ),
            FlightTask(
                task_id="T2",
                flight_no="CA1002",
                origin="PEK",
                destination="CAN",
                departure_time=base + timedelta(hours=3),
                arrival_time=base + timedelta(hours=6),
                aircraft_type="A320",
                priority=TaskPriority.NORMAL,
            ),
        )
        for t in tasks:
            task_ctx.register_task(t)

        # 注册机组 / Register crew
        crew = Crew(
            crew_id="CR1",
            name="Alpha",
            base_airport="PEK",
            qualifications=("A320",),
        )
        crew_ctx.register_crew(crew)
        crew_ctx.register_member(
            CrewMember(
                member_id="M1",
                name="Zhang",
                role=CrewRole.CAPTAIN,
                experience_hours=8_000,
            )
        )
        crew_ctx.register_pilot(
            Pilot(
                pilot_id="P1",
                name="Zhang",
                license_type=LicenseType.ATPL,
                aircraft_ratings=("A320",),
                flight_hours=8_000,
            )
        )

        # 注册旅客 / Register passengers
        passengers = (
            Passenger(
                passenger_id="PAX1",
                name="Li",
                booking_class=BookingClass.ECONOMY,
            ),
            Passenger(
                passenger_id="PAX2",
                name="Wang",
                booking_class=BookingClass.FIRST,
            ),
        )
        for p in passengers:
            pax_ctx.register_passenger(p)

        # 注册规则 / Register rules
        rule_ctx.register(
            Rule(
                rule_id="R_SCHED",
                rule_type=RuleType.SCHEDULING,
                parameters={},
                priority=5,
            )
        )

        # 运行应用 / Run application
        app = SchedulingApplication(
            task_context=task_ctx,
            crew_context=crew_ctx,
            passenger_context=pax_ctx,
            bunch_context=bunch_ctx,
            generation_context=gen_ctx,
            rule_context=rule_ctx,
        )
        result = app.run(
            tasks=tasks,
            crews=(crew,),
            passengers=passengers,
            cargos=(),
        )

        # 验证结果 / Verify result
        assert isinstance(result.feasible, bool)
        assert isinstance(result.schedule, tuple)
        assert isinstance(result.violations, tuple)
        assert task_ctx.task_count == 2

    def test_cargo_allocation_flow(self) -> None:
        """货物分配流程 / Cargo allocation flow."""
        allocator = CargoAllocator()
        cargos = (
            Cargo("CG1", 500.0, 1.0, 5, "PVG"),
            Cargo("CG2", 300.0, 0.5, 3, "PVG"),
            Cargo("CG3", 800.0, 2.0, 8, "PEK"),
        )
        slots = (
            BunchSlot("B1", capacity=1_000.0, destination="PVG"),
            BunchSlot("B2", capacity=1_000.0, destination="PEK"),
        )
        allocations = allocator.allocate(cargos, slots)
        assert len(allocations) >= 2

    def test_passenger_allocation_flow(self) -> None:
        "Passenger allocation flow."
        allocator = PassengerAllocator()
        passengers = [
            Passenger(
                passenger_id=f"P{i}",
                name=f"P{i}",
                booking_class=(BookingClass.FIRST if i < 2 else BookingClass.ECONOMY),
            )
            for i in range(10)
        ]
        seat_map = SeatMap(
            aircraft_type="A320",
            first_class_rows=2,
            economy_class_rows=20,
            seats_per_row=6,
        )
        result = allocator.allocate(passengers, seat_map)
        assert result.allocated_count == 10

    def test_bunch_generation_and_selection(self) -> None:
        """任务组生成与选择 / Bunch generation and selection."""
        config = GenerationConfig(
            max_bunch_size=5,
            min_utilization=0.5,
        )
        ctx = GenerationContext()
        gen = GreedyGenerator(config)
        ctx.register(GenerationStrategy.GREEDY, gen)

        tasks = (
            TaskSlot("T1", "aircraft", 1.0),
            TaskSlot("T2", "aircraft", 2.0),
            TaskSlot("T3", "aircraft", 1.5),
        )
        selector = GenerationSelector(ctx)
        result = selector.select_best(tasks)
        assert result is not None
        assert result.strategy == GenerationStrategy.GREEDY

    def test_rule_evaluation_flow(self) -> None:
        """规则评估流程 / Rule evaluation flow."""
        from examples.framework_demo.demo4.domain.rule.service.rule_engine import (
            RuleEngine,
            ScheduleView,
        )

        ctx = RuleContext()
        ctx.register(
            Rule(
                rule_id="R1",
                rule_type=RuleType.SCHEDULING,
                parameters={},
                priority=5,
            )
        )
        engine = RuleEngine(ctx)
        schedule = ScheduleView(
            tasks=({"task_id": "T1", "start": 0.0, "end": 50.0},),
            resources=(),
            time_slots=(),
        )
        results = engine.evaluate(schedule)
        assert len(results) == 1
        assert results[0].rule_id == "R1"
