"""Crew context 测试 / Crew context tests.

覆盖 Crew/CrewMember/Pilot 创建、CrewContext 注册和
资质检查。
Covers Crew/CrewMember/Pilot creation, CrewContext
registration, and qualification checks.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from examples.framework_demo.demo4.domain.crew.model.crew import Crew
from examples.framework_demo.demo4.domain.crew.model.crew_context import (
    CrewContext,
)
from examples.framework_demo.demo4.domain.crew.model.crew_member import (
    CrewMember,
    CrewRole,
)
from examples.framework_demo.demo4.domain.crew.model.crew_schedule import (
    CrewAssignment,
    CrewSchedule,
)
from examples.framework_demo.demo4.domain.crew.model.pilot import (
    LicenseType,
    Pilot,
)
from examples.framework_demo.demo4.domain.crew.service.limits.crew_qualification_constraint import (
    CrewQualificationConstraint,
)


class TestCrew:
    """Crew 测试 / Crew tests."""

    def test_qualification_count(self) -> None:
        """资质数量 / Qualification count."""
        c = Crew(
            crew_id="CR1",
            name="Alpha Team",
            base_airport="PEK",
            qualifications=("A320", "B737"),
        )
        assert c.qualification_count == 2

    def test_is_multi_qualification(self) -> None:
        """多资质 / Multi qualification."""
        multi = Crew(
            crew_id="CR1",
            name="Alpha",
            base_airport="PEK",
            qualifications=("A320", "B737"),
        )
        single = Crew(
            crew_id="CR2",
            name="Beta",
            base_airport="PVG",
            qualifications=("A320",),
        )
        assert multi.is_multi_qualification is True
        assert single.is_multi_qualification is False

    def test_is_qualified_for(self) -> None:
        """资质检查 / Qualification check."""
        c = Crew(
            crew_id="CR1",
            name="Alpha",
            base_airport="PEK",
            qualifications=("A320", "B737"),
        )
        assert c.is_qualified_for("A320") is True
        assert c.is_qualified_for("A380") is False

    def test_frozen(self) -> None:
        """不可变 / Frozen."""
        c = Crew(
            crew_id="CR1",
            name="Alpha",
            base_airport="PEK",
        )
        with pytest.raises(AttributeError):
            c.name = "X"  # type: ignore[misc]


class TestCrewMember:
    """CrewMember 测试 / CrewMember tests."""

    def test_is_pilot(self) -> None:
        """是否飞行员 / Is pilot."""
        pilot = CrewMember(
            member_id="M1",
            name="Zhang San",
            role=CrewRole.CAPTAIN,
        )
        cabin = CrewMember(
            member_id="M2",
            name="Li Si",
            role=CrewRole.CABIN_ATTENDANT,
        )
        assert pilot.is_pilot is True
        assert cabin.is_pilot is False

    def test_is_senior(self) -> None:
        """是否资深 / Is senior."""
        senior = CrewMember(
            member_id="M1",
            name="Zhang",
            role=CrewRole.CAPTAIN,
            experience_hours=6_000,
        )
        junior = CrewMember(
            member_id="M2",
            name="Li",
            role=CrewRole.CAPTAIN,
            experience_hours=500,
        )
        assert senior.is_senior is True
        assert junior.is_senior is False

    def test_experience_years(self) -> None:
        """经验年数 / Experience years."""
        m = CrewMember(
            member_id="M1",
            name="Zhang",
            role=CrewRole.CAPTAIN,
            experience_hours=5_000,
        )
        assert m.experience_years == pytest.approx(5_000 / 1_000)


class TestPilot:
    """Pilot 测试 / Pilot tests."""

    def test_can_fly(self) -> None:
        """飞行能力 / Can fly."""
        p = Pilot(
            pilot_id="P1",
            name="Zhang",
            license_type=LicenseType.ATPL,
            aircraft_ratings=("A320", "A321"),
            flight_hours=5_000,
        )
        assert p.can_fly("A320") is True
        assert p.can_fly("B747") is False

    def test_is_atpl(self) -> None:
        """ATPL 资质 / ATPL license."""
        atpl = Pilot(
            pilot_id="P1",
            name="Zhang",
            license_type=LicenseType.ATPL,
            aircraft_ratings=("A320",),
        )
        cpl = Pilot(
            pilot_id="P2",
            name="Li",
            license_type=LicenseType.CPL,
            aircraft_ratings=("A320",),
        )
        assert atpl.is_atpl is True
        assert cpl.is_atpl is False

    def test_is_experienced(self) -> None:
        """是否有经验 / Is experienced."""
        exp = Pilot(
            pilot_id="P1",
            name="Zhang",
            license_type=LicenseType.ATPL,
            aircraft_ratings=("A320",),
            flight_hours=3_500,
        )
        novice = Pilot(
            pilot_id="P2",
            name="Li",
            license_type=LicenseType.CPL,
            aircraft_ratings=("A320",),
            flight_hours=200,
        )
        assert exp.is_experienced is True
        assert novice.is_experienced is False

    def test_experience_level(self) -> None:
        """经验等级 / Experience level."""
        p = Pilot(
            pilot_id="P1",
            name="Zhang",
            license_type=LicenseType.ATPL,
            aircraft_ratings=("A320",),
            flight_hours=10_000,
        )
        assert p.experience_level in ("expert", "senior", "intermediate", "junior")


class TestCrewContext:
    """CrewContext 测试 / CrewContext tests."""

    def test_register_crew(self) -> None:
        """注册机组 / Register crew."""
        ctx = CrewContext()
        c = Crew(
            crew_id="CR1",
            name="Alpha",
            base_airport="PEK",
            qualifications=("A320",),
        )
        ctx.register_crew(c)
        assert ctx.crew_count == 1
        assert ctx.get_crew("CR1") is c

    def test_register_member(self) -> None:
        """注册成员 / Register member."""
        ctx = CrewContext()
        m = CrewMember(
            member_id="M1",
            name="Zhang",
            role=CrewRole.CAPTAIN,
        )
        ctx.register_member(m)
        assert ctx.member_count == 1

    def test_register_pilot(self) -> None:
        """注册飞行员 / Register pilot."""
        ctx = CrewContext()
        p = Pilot(
            pilot_id="P1",
            name="Zhang",
            license_type=LicenseType.ATPL,
            aircraft_ratings=("A320",),
        )
        ctx.register_pilot(p)
        assert ctx.get_pilot("P1") is p

    def test_get_members_by_role(self) -> None:
        """按角色查询成员 / Get members by role."""
        ctx = CrewContext()
        ctx.register_member(
            CrewMember(
                member_id="M1",
                name="Zhang",
                role=CrewRole.CAPTAIN,
            )
        )
        ctx.register_member(
            CrewMember(
                member_id="M2",
                name="Li",
                role=CrewRole.CABIN_ATTENDANT,
            )
        )
        captains = ctx.get_members_by_role(CrewRole.CAPTAIN)
        assert len(list(captains)) == 1

    def test_get_pilots_for_aircraft(self) -> None:
        """按机型查询飞行员 / Get pilots for aircraft."""
        ctx = CrewContext()
        ctx.register_pilot(
            Pilot(
                pilot_id="P1",
                name="Zhang",
                license_type=LicenseType.ATPL,
                aircraft_ratings=("A320", "A321"),
            )
        )
        ctx.register_pilot(
            Pilot(
                pilot_id="P2",
                name="Li",
                license_type=LicenseType.ATPL,
                aircraft_ratings=("B737",),
            )
        )
        a320_pilots = ctx.get_pilots_for_aircraft("A320")
        assert len(list(a320_pilots)) == 1


class TestCrewSchedule:
    """CrewSchedule 测试 / CrewSchedule tests."""

    def test_assignment_count(self) -> None:
        """任务数 / Assignment count."""
        base = datetime(2025, 6, 1, 8, 0)
        assignments = (
            CrewAssignment(
                task_id="T1",
                member_id="M1",
                start_time=base,
                end_time=base + timedelta(hours=4),
            ),
        )
        schedule = CrewSchedule(
            crew_id="CR1",
            assignments=assignments,
            rest_periods=(),
        )
        assert schedule.assignment_count == 1

    def test_total_duty_hours(self) -> None:
        """总值班时间 / Total duty hours."""
        base = datetime(2025, 6, 1, 8, 0)
        assignments = (
            CrewAssignment(
                task_id="T1",
                member_id="M1",
                start_time=base,
                end_time=base + timedelta(hours=4),
            ),
            CrewAssignment(
                task_id="T2",
                member_id="M1",
                start_time=base + timedelta(hours=5),
                end_time=base + timedelta(hours=9),
            ),
        )
        schedule = CrewSchedule(
            crew_id="CR1",
            assignments=assignments,
            rest_periods=(),
        )
        assert schedule.total_duty_hours == pytest.approx(8.0)


class TestCrewQualificationConstraint:
    """CrewQualificationConstraint 测试 / Qualification tests."""

    def test_qualified_pilot(self) -> None:
        """合格飞行员 / Qualified pilot."""
        constraint = CrewQualificationConstraint(
            require_atpl_for_captain=True,
            min_captain_hours=3_000,
        )
        p = Pilot(
            pilot_id="P1",
            name="Zhang",
            license_type=LicenseType.ATPL,
            aircraft_ratings=("A320",),
            flight_hours=5_000,
        )
        assert constraint.is_pilot_qualified(p, CrewRole.CAPTAIN, "A320")

    def test_unqualified_captain(self) -> None:
        """不合格机长 / Unqualified captain."""
        constraint = CrewQualificationConstraint(
            require_atpl_for_captain=True,
            min_captain_hours=3_000,
        )
        p = Pilot(
            pilot_id="P1",
            name="Zhang",
            license_type=LicenseType.CPL,
            aircraft_ratings=("A320",),
            flight_hours=5_000,
        )
        errors = constraint.validate_pilot(p, CrewRole.CAPTAIN, "A320")
        assert len(list(errors)) > 0
