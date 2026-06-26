"""Demo1 DTO — Data Transfer Objects for network routing."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NetworkDTO:
    """Network topology DTO."""

    nodes: tuple[str, ...]
    edges: tuple[tuple[str, str, float], ...]  # (source, target, capacity)


@dataclass
class ServiceDTO:
    """Service request DTO."""

    service_id: str
    source: str
    target: str
    demand: float


@dataclass
class SolutionDTO:
    """Solution result DTO."""

    routes: dict[str, list[str]]
    total_cost: float
    feasible: bool
