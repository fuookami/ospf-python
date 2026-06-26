"""Airworthiness and security 测试 / Airworthiness security tests.

覆盖飞行包线、CG 约束、结构限制、安全等级和
适航验证流程。
Covers flight envelope, CG constraints, structural limits,
security levels, and airworthiness pipeline.
"""

from __future__ import annotations

import pytest

from examples.framework_demo.demo2.domain.airworthiness_security.model.airworthiness_context import (
    AirworthinessContext,
)
from examples.framework_demo.demo2.domain.airworthiness_security.model.envelope import (
    Envelope,
)
from examples.framework_demo.demo2.domain.airworthiness_security.model.security_level import (
    SecurityLevel,
)
from examples.framework_demo.demo2.domain.airworthiness_security.model.structural_limit import (
    LimitType,
    StructuralLimit,
)


class TestEnvelope:
    """Envelope 测试 / Envelope tests."""

    def test_create_envelope(self) -> None:
        """创建飞行包线 / Create flight envelope."""
        env = Envelope.create(
            envelope_id="ENV1",
            max_weight=400_000.0,
            min_weight=100_000.0,
            max_cg=33.0,
            min_cg=18.0,
        )
        assert env.envelope_id == "ENV1"
        assert env.weight_range == pytest.approx(300_000.0)
        assert env.cg_range == pytest.approx(15.0)

    def test_contains_weight(self) -> None:
        """重量在包线内 / Weight within envelope."""
        env = Envelope.create(
            envelope_id="E1",
            max_weight=400_000.0,
            min_weight=100_000.0,
            max_cg=33.0,
            min_cg=18.0,
        )
        assert env.contains_weight(250_000.0) is True
        assert env.contains_weight(50_000.0) is False
        assert env.contains_weight(450_000.0) is False

    def test_contains_cg(self) -> None:
        """CG 在包线内 / CG within envelope."""
        env = Envelope.create(
            envelope_id="E1",
            max_weight=400_000.0,
            min_weight=100_000.0,
            max_cg=33.0,
            min_cg=18.0,
        )
        assert env.contains_cg(25.0) is True
        assert env.contains_cg(10.0) is False

    def test_weight_margin(self) -> None:
        """重量余量 / Weight margin."""
        env = Envelope.create(
            envelope_id="E1",
            max_weight=400_000.0,
            min_weight=100_000.0,
            max_cg=33.0,
            min_cg=18.0,
        )
        margin = env.weight_margin(350_000.0)
        assert margin == pytest.approx(50_000.0)

    def test_cg_margin(self) -> None:
        """CG 余量 / CG margin."""
        env = Envelope.create(
            envelope_id="E1",
            max_weight=400_000.0,
            min_weight=100_000.0,
            max_cg=33.0,
            min_cg=18.0,
        )
        # 25 距 18=7, 距 33=8, 取较小值 7
        margin = env.cg_margin(25.0)
        assert margin == pytest.approx(7.0)


class TestSecurityLevel:
    """SecurityLevel 测试 / Security level tests."""

    def test_ordering(self) -> None:
        """等级排序 / Level ordering."""
        assert SecurityLevel.NORMAL < SecurityLevel.ELEVATED
        assert SecurityLevel.HIGH < SecurityLevel.MAXIMUM

    def test_meets_requirement(self) -> None:
        """满足等级要求 / Meets requirement."""
        assert SecurityLevel.HIGH.meets_requirement(SecurityLevel.NORMAL)
        assert not SecurityLevel.NORMAL.meets_requirement(SecurityLevel.HIGH)

    def test_escalate(self) -> None:
        """升级 / Escalate."""
        assert SecurityLevel.NORMAL.escalate() == SecurityLevel.ELEVATED
        assert SecurityLevel.MAXIMUM.escalate() == SecurityLevel.MAXIMUM

    def test_de_escalate(self) -> None:
        """降级 / De-escalate."""
        assert SecurityLevel.HIGH.de_escalate() == SecurityLevel.ELEVATED
        assert SecurityLevel.NORMAL.de_escalate() == SecurityLevel.NORMAL

    def test_from_string(self) -> None:
        """从字符串解析 / Parse from string."""
        assert SecurityLevel.from_string("high") == SecurityLevel.HIGH
        assert SecurityLevel.from_string("MAXIMUM") == SecurityLevel.MAXIMUM

    def test_labels(self) -> None:
        """标签 / Labels."""
        assert SecurityLevel.NORMAL.label_en == "Normal"
        assert SecurityLevel.HIGH.label_zh == "高"


class TestStructuralLimit:
    """StructuralLimit 测试 / Structural limit tests."""

    def test_within_limit(self) -> None:
        """在限制内 / Within limit."""
        sl = StructuralLimit.create(
            component="floor_1",
            limit_type=LimitType.WEIGHT,
            value=10_000.0,
        )
        assert sl.is_within_limit(8_000.0) is True
        assert sl.is_within_limit(12_000.0) is False

    def test_margin(self) -> None:
        """余量计算 / Margin calculation."""
        sl = StructuralLimit.create(
            component="floor_1",
            limit_type=LimitType.FORCE,
            value=10_000.0,
        )
        assert sl.margin(7_000.0) == pytest.approx(3_000.0)
        assert sl.margin(12_000.0) == pytest.approx(-2_000.0)

    def test_utilization(self) -> None:
        """利用率 / Utilization."""
        sl = StructuralLimit.create(
            component="floor_1",
            limit_type=LimitType.WEIGHT,
            value=10_000.0,
        )
        assert sl.utilization(5_000.0) == pytest.approx(0.5)
        assert sl.utilization(15_000.0) == pytest.approx(1.0)

    def test_scaled(self) -> None:
        """缩放限制 / Scaled limit."""
        sl = StructuralLimit.create(
            component="wing",
            limit_type=LimitType.MOMENT,
            value=50_000.0,
        )
        scaled = sl.scaled(0.8)
        assert scaled.value == pytest.approx(40_000.0)
        assert sl.value == pytest.approx(50_000.0)


class TestAirworthinessContext:
    """AirworthinessContext 测试 / Context tests."""

    def test_register_envelope(self) -> None:
        """注册包线 / Register envelope."""
        ctx = AirworthinessContext()
        env = Envelope.create(
            envelope_id="E1",
            max_weight=400_000.0,
            min_weight=100_000.0,
            max_cg=33.0,
            min_cg=18.0,
        )
        ctx.register_envelope(env)
        assert ctx.envelope_count == 1

    def test_security_level_setting(self) -> None:
        """设置安全等级 / Set security level."""
        ctx = AirworthinessContext()
        assert ctx.security_level == SecurityLevel.NORMAL
        ctx.set_security_level(SecurityLevel.HIGH)
        assert ctx.security_level == SecurityLevel.HIGH  # type: ignore[comparison-overlap]

    def test_limit_count(self) -> None:
        """限制总数 / Total limit count."""
        ctx = AirworthinessContext()
        ctx.register_envelope(
            Envelope.create(
                envelope_id="E1",
                max_weight=400_000.0,
                min_weight=100_000.0,
                max_cg=33.0,
                min_cg=18.0,
            )
        )
        ctx.register_structural_limit(
            StructuralLimit.create(
                component="floor",
                limit_type=LimitType.WEIGHT,
                value=10_000.0,
            )
        )
        assert ctx.limit_count == 2

    def test_validate_pass(self) -> None:
        """验证通过 / Validation pass."""
        ctx = AirworthinessContext()
        result = ctx.validate()
        assert result.status == "pass"
        assert len(result.violations) == 0

    def test_high_security_no_cert_violation(self) -> None:
        """高安全等级无证书违规 / High security no cert violation."""
        ctx = AirworthinessContext()
        ctx.set_security_level(SecurityLevel.HIGH)
        result = ctx.validate()
        assert result.status == "fail"
        assert "high_security_no_certificate" in result.violations

    def test_build_aggregation(self) -> None:
        """构建聚合 / Build aggregation."""
        ctx = AirworthinessContext()
        ctx.register_envelope(
            Envelope.create(
                envelope_id="E1",
                max_weight=400_000.0,
                min_weight=100_000.0,
                max_cg=33.0,
                min_cg=18.0,
            )
        )
        agg = ctx.build_aggregation()
        assert len(agg.envelopes) == 1
