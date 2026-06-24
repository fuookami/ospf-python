# ospf_python.quantities.unit

"""物理单位包。/ Physical units package.

包含所有物理单位的定义和单位系统。/
Contains definitions of all physical units and unit systems.
"""

from __future__ import annotations

from .acceleration import Acceleration
from .amount import Amount
from .angular_acceleration import AngularAcceleration
from .angular_velocity import AngularVelocity
from .area import Area
from .bandwidth import Bandwidth
from .catalytic_activity import CatalyticActivity
from .current import Current
from .electric_charge import ElectricCharge
from .energy import Energy
from .flow_rate import FlowRate
from .force import Force
from .frequency import Frequency
from .information import Information
from .length import Length
from .luminous_intensity import LuminousIntensity
from .mass import Mass
from .mass_density import MassDensity
from .momentum import Momentum
from .physical_unit import PhysicalUnit
from .plane_angle import PlaneAngle
from .power import Power
from .pressure import Pressure
from .resistance import Resistance
from .solid_angle import SolidAngle
from .stress import Stress
from .surface_density import SurfaceDensity
from .temperature import Temperature
from .time_unit import TimeUnit
from .torque import Torque
from .unit_system import (
    CGS,
    IMPERIAL,
    SI,
    US_CUSTOMARY,
    UnitSystem,
)
from .velocity import Velocity
from .voltage import Voltage
from .volume import Volume
from .wavenumber import Wavenumber

__all__ = [
    # 协议 / Protocol
    "PhysicalUnit",
    # 单位系统 / Unit systems
    "UnitSystem",
    "SI",
    "CGS",
    "IMPERIAL",
    "US_CUSTOMARY",
    # 具体单位 / Concrete units
    "Acceleration",
    "Amount",
    "AngularAcceleration",
    "AngularVelocity",
    "Area",
    "Bandwidth",
    "CatalyticActivity",
    "Current",
    "ElectricCharge",
    "Energy",
    "FlowRate",
    "Force",
    "Frequency",
    "Information",
    "Length",
    "LuminousIntensity",
    "Mass",
    "MassDensity",
    "Momentum",
    "PlaneAngle",
    "Power",
    "Pressure",
    "Resistance",
    "SolidAngle",
    "Stress",
    "SurfaceDensity",
    "Temperature",
    "TimeUnit",
    "Torque",
    "Velocity",
    "Voltage",
    "Volume",
    "Wavenumber",
]
