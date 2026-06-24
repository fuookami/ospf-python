"""单位系统。/ Unit systems."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UnitSystem:
    """单位系统，用于统一管理一组单位。/

    Unit system for managing a group of units uniformly.

    Attributes:
        name: 系统名称。/ System name.
        description: 系统描述。/ System description.
        length: 长度单位。/ Length unit.
        mass: 质量单位。/ Mass unit.
        time: 时间单位。/ Time unit.
        current: 电流单位。/ Current unit.
        temperature: 温度单位。/ Temperature unit.
        amount: 物质的量单位。/ Amount unit.
        luminous_intensity: 发光强度单位。/ Luminous intensity unit.
    """

    name: str
    description: str = ""
    length: str = "m"
    mass: str = "kg"
    time: str = "s"
    current: str = "A"
    temperature: str = "K"
    amount: str = "mol"
    luminous_intensity: str = "cd"


# 预定义单位系统 / Predefined unit systems
SI = UnitSystem(
    name="SI",
    description=(
        "国际单位制（法语：Système international d'unités）。/"
        "International System of Units."
    ),
    length="m",
    mass="kg",
    time="s",
    current="A",
    temperature="K",
    amount="mol",
    luminous_intensity="cd",
)

CGS = UnitSystem(
    name="CGS",
    description=("厘米-克-秒单位系统。/Centimetre-gram-second system of units."),
    length="cm",
    mass="g",
    time="s",
    current="A",
    temperature="K",
    amount="mol",
    luminous_intensity="cd",
)

IMPERIAL = UnitSystem(
    name="Imperial",
    description=("英制单位系统。/ Imperial system of units."),
    length="ft",
    mass="lb",
    time="s",
    current="A",
    temperature="F",
    amount="mol",
    luminous_intensity="cd",
)

US_CUSTOMARY = UnitSystem(
    name="US Customary",
    description=("美国惯用单位系统。/ United States customary system."),
    length="ft",
    mass="lb",
    time="s",
    current="A",
    temperature="F",
    amount="mol",
    luminous_intensity="cd",
)
