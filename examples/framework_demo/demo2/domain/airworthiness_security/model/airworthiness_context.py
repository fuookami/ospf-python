"""适航上下文 / Airworthiness context.

管理适航限制的注册与验证流程。
Manages registration and validation of airworthiness limits.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .airworthiness_result import AirworthinessResult
from .security_level import SecurityLevel

if TYPE_CHECKING:
    from .airworthiness_aggregation import AirworthinessAggregation
    from .airworthiness_cert import AirworthinessCert
    from .cargo_restraint import CargoRestraint
    from .envelope import Envelope
    from .floor_loading import FloorLoading
    from .linear_density import LinearDensity
    from .max_clim import MaxCLIM
    from .max_cumulative_load_weight import MaxCumulativeLoadWeight
    from .structural_limit import StructuralLimit


@dataclass
class AirworthinessContext:
    """适航上下文 / Airworthiness context.

    提供可变的注册接口，收集所有适航限制和证书后
    可生成不可变的聚合对象并执行验证。
    Provides a mutable registration interface; after collecting
    all airworthiness limits and certificates, generates an
    immutable aggregation object and performs validation.

    Attributes:
        _envelopes: 已注册包线 / Registered envelopes.
        _structural_limits: 已注册结构限制 / Registered structural limits.
        _floor_loadings: 已注册地板载荷 / Registered floor loadings.
        _cargo_restraints: 已注册限动装置 / Registered restraints.
        _max_clims: 已注册CLIM / Registered CLIMs.
        _cumulative_loads: 已注册累积载荷 / Registered cumulative loads.
        _linear_densities: 已注册线密度 / Registered linear densities.
        _certificates: 已注册证书 / Registered certificates.
        _security_level: 当前安全等级 / Current security level.
    """

    _envelopes: list[Envelope] = field(default_factory=list, init=False)
    _structural_limits: list[StructuralLimit] = field(default_factory=list, init=False)
    _floor_loadings: list[FloorLoading] = field(default_factory=list, init=False)
    _cargo_restraints: list[CargoRestraint] = field(default_factory=list, init=False)
    _max_clims: list[MaxCLIM] = field(default_factory=list, init=False)
    _cumulative_loads: list[MaxCumulativeLoadWeight] = field(
        default_factory=list, init=False
    )
    _linear_densities: list[LinearDensity] = field(default_factory=list, init=False)
    _certificates: list[AirworthinessCert] = field(default_factory=list, init=False)
    _security_level: SecurityLevel = field(default=SecurityLevel.NORMAL, init=False)

    # ---- registration methods ----

    def register_envelope(self, envelope: Envelope) -> None:
        """注册飞行包线 / Register flight envelope.

        Args:
            envelope: 飞行包线。/ Flight envelope.
        """
        self._envelopes.append(envelope)

    def register_structural_limit(self, limit: StructuralLimit) -> None:
        """注册结构限制 / Register structural limit.

        Args:
            limit: 结构限制。/ Structural limit.
        """
        self._structural_limits.append(limit)

    def register_floor_loading(self, loading: FloorLoading) -> None:
        """注册地板载荷 / Register floor loading.

        Args:
            loading: 地板载荷。/ Floor loading.
        """
        self._floor_loadings.append(loading)

    def register_cargo_restraint(self, restraint: CargoRestraint) -> None:
        """注册限动装置 / Register cargo restraint.

        Args:
            restraint: 限动装置。/ Cargo restraint.
        """
        self._cargo_restraints.append(restraint)

    def register_max_clim(self, clim: MaxCLIM) -> None:
        """注册最大CLIM / Register max CLIM.

        Args:
            clim: 最大CLIM。/ Max CLIM.
        """
        self._max_clims.append(clim)

    def register_cumulative_load(self, load: MaxCumulativeLoadWeight) -> None:
        """注册累积载荷限制 / Register cumulative load limit.

        Args:
            load: 累积载荷限制。/ Cumulative load limit.
        """
        self._cumulative_loads.append(load)

    def register_linear_density(self, density: LinearDensity) -> None:
        """注册线密度 / Register linear density.

        Args:
            density: 线密度。/ Linear density.
        """
        self._linear_densities.append(density)

    def register_certificate(self, cert: AirworthinessCert) -> None:
        """注册适航证书 / Register airworthiness certificate.

        Args:
            cert: 适航证书。/ Airworthiness certificate.
        """
        self._certificates.append(cert)

    def set_security_level(self, level: SecurityLevel) -> None:
        """设置安全等级 / Set security level.

        Args:
            level: 安全等级。/ Security level.
        """
        self._security_level = level

    # ---- query methods ----

    @property
    def security_level(self) -> SecurityLevel:
        """当前安全等级 / Current security level."""
        return self._security_level

    @property
    def envelope_count(self) -> int:
        """已注册包线数 / Registered envelope count."""
        return len(self._envelopes)

    @property
    def limit_count(self) -> int:
        """已注册限制总数 / Total registered limit count."""
        return (
            len(self._envelopes)
            + len(self._structural_limits)
            + len(self._floor_loadings)
            + len(self._cargo_restraints)
            + len(self._max_clims)
            + len(self._cumulative_loads)
            + len(self._linear_densities)
        )

    def has_certificates(self) -> bool:
        """是否已注册证书 / Has registered certificates.

        Returns:
            若存在已注册证书则返回 True。
            True if any certificates are registered.
        """
        return len(self._certificates) > 0

    def build_aggregation(
        self,
    ) -> AirworthinessAggregation:
        """构建不可变聚合对象。

        Build an immutable aggregation object from the
        currently registered data.

        Returns:
            包含所有已注册数据的聚合对象。
            Aggregation object with all registered data.
        """
        from .airworthiness_aggregation import (
            AirworthinessAggregation,
        )

        return AirworthinessAggregation(
            envelopes=tuple(self._envelopes),
            structural_limits=tuple(self._structural_limits),
            floor_loadings=tuple(self._floor_loadings),
            cargo_restraints=tuple(self._cargo_restraints),
            max_clims=tuple(self._max_clims),
            cumulative_loads=tuple(self._cumulative_loads),
            linear_densities=tuple(self._linear_densities),
            certificates=tuple(self._certificates),
        )

    def validate(self) -> AirworthinessResult:
        """执行基础验证 / Perform basic validation.

        检查证书有效性、安全等级一致性等基础项。

        Returns:
            验证结果 / Validation result.
        """
        violations: list[str] = []
        margins: dict[str, float] = {}

        # 检查证书有效性
        for cert in self._certificates:
            if not cert.is_valid():
                violations.append(f"certificate_expired:{cert.cert_id}")
            days = cert.remaining_days()
            margins[f"cert:{cert.cert_id}:days"] = float(days)

        # 高安全等级需确保有证书
        if self._security_level >= SecurityLevel.HIGH and not self._certificates:
            violations.append("high_security_no_certificate")

        status = "pass" if not violations else "fail"
        return AirworthinessResult(
            status=status,
            violations=tuple(violations),
            margins=margins,
        )
