"""适航聚合 / Airworthiness aggregation.

聚合所有适航限制与证书信息。
Aggregates all airworthiness limits and certificates.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .airworthiness_cert import AirworthinessCert
    from .cargo_restraint import CargoRestraint
    from .envelope import Envelope
    from .floor_loading import FloorLoading
    from .linear_density import LinearDensity
    from .max_clim import DeckType, MaxCLIM
    from .max_cumulative_load_weight import MaxCumulativeLoadWeight
    from .structural_limit import StructuralLimit


@dataclass(frozen=True)
class AirworthinessAggregation:
    """适航聚合 / Airworthiness aggregation.

    将所有适航相关限制和证书汇聚为单一数据结构，
    作为约束验证管道的输入载体。
    Collects all airworthiness-related limits and certificates
    into a single data structure, serving as the input carrier
    for the constraint validation pipeline.

    Attributes:
        envelopes: 飞行包线集合 / Flight envelopes.
        structural_limits: 结构限制集合 / Structural limits.
        floor_loadings: 地板载荷集合 / Floor loadings.
        cargo_restraints: 货物限动装置集合 / Cargo restraints.
        max_clims: 最大CLIM集合 / Max CLIMs.
        cumulative_loads: 累积载荷集合 / Cumulative loads.
        linear_densities: 线密度集合 / Linear densities.
        certificates: 适航证书集合 / Airworthiness certificates.
    """

    envelopes: tuple[Envelope, ...] = ()
    structural_limits: tuple[StructuralLimit, ...] = ()
    floor_loadings: tuple[FloorLoading, ...] = ()
    cargo_restraints: tuple[CargoRestraint, ...] = ()
    max_clims: tuple[MaxCLIM, ...] = ()
    cumulative_loads: tuple[MaxCumulativeLoadWeight, ...] = ()
    linear_densities: tuple[LinearDensity, ...] = ()
    certificates: tuple[AirworthinessCert, ...] = ()

    def find_envelope(self, envelope_id: str) -> Envelope | None:
        """按标识查找飞行包线。

        Find a flight envelope by its identifier.

        Args:
            envelope_id: 包线标识。/ Envelope identifier.

        Returns:
            匹配的包线，未找到返回 None。
            Matching envelope, or None if not found.
        """
        for env in self.envelopes:
            if env.envelope_id == envelope_id:
                return env
        return None

    def find_structural_limit(self, component: str) -> tuple[StructuralLimit, ...]:
        """按部件查找结构限制。

        Find structural limits by component.

        Args:
            component: 部件标识。/ Component identifier.

        Returns:
            匹配的结构限制元组。
            Tuple of matching structural limits.
        """
        return tuple(sl for sl in self.structural_limits if sl.component == component)

    def find_floor_loading(self, area_id: str) -> FloorLoading | None:
        """按区域查找地板载荷。

        Find floor loading by area identifier.

        Args:
            area_id: 区域标识。/ Area identifier.

        Returns:
            匹配的地板载荷，未找到返回 None。
            Matching floor loading, or None if not found.
        """
        for fl in self.floor_loadings:
            if fl.area_id == area_id:
                return fl
        return None

    def find_clims_for_deck(
        self,
        deck: DeckType,  # noqa: F821
    ) -> tuple[MaxCLIM, ...]:
        """按甲板查找CLIM限制。

        Find CLIM limits by deck type.

        Args:
            deck: 甲板类型。/ Deck type.

        Returns:
            匹配的CLIM限制元组。
            Tuple of matching CLIM limits.
        """
        return tuple(cl for cl in self.max_clims if cl.deck == deck)

    def active_certificates(self) -> tuple[AirworthinessCert, ...]:
        """获取当前有效的证书。

        Get currently valid certificates.

        Returns:
            当前有效的适航证书元组。
            Tuple of currently valid airworthiness certificates.
        """
        return tuple(cert for cert in self.certificates if cert.is_valid())

    @property
    def is_empty(self) -> bool:
        """是否为空聚合 / Is empty aggregation.

        Returns:
            所有集合均为空则返回 True。
            True if all collections are empty.
        """
        return not any(
            (
                self.envelopes,
                self.structural_limits,
                self.floor_loadings,
                self.cargo_restraints,
                self.max_clims,
                self.cumulative_loads,
                self.linear_densities,
                self.certificates,
            )
        )

    @property
    def total_limits_count(self) -> int:
        """限制总数 / Total limits count.

        Returns:
            所有限制条目的数量。
            Total number of all limit entries.
        """
        return (
            len(self.envelopes)
            + len(self.structural_limits)
            + len(self.floor_loadings)
            + len(self.cargo_restraints)
            + len(self.max_clims)
            + len(self.cumulative_loads)
            + len(self.linear_densities)
        )
