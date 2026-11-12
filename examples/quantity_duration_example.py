"""原生时长换算及两种舍入语义。 / Native duration conversion and two rounding contracts."""

from datetime import timedelta
from fractions import Fraction

from ospf_python.quantities import Quantity, from_hours, from_minutes, to_timedelta
from ospf_python.quantities.unit.length import METER
from ospf_python.quantities.unit.time_unit import SECOND


def main() -> None:
    """显式消费 Result，保留负时长和精确微秒。 / Consume Result with signed/exact microseconds."""
    hours = from_hours(Fraction(-1, 2)).unwrap()
    assert to_timedelta(hours).unwrap() == timedelta(minutes=-30)
    assert to_timedelta(from_minutes(Fraction(1, 3)).unwrap()).unwrap() == timedelta(
        seconds=20
    )
    precise = Fraction(1, 2000000) + Fraction(1, 10**60)
    assert to_timedelta(Quantity(value=precise, unit=SECOND)).unwrap() == timedelta(
        microseconds=1
    )
    assert to_timedelta(Quantity(value=2.5e-6, unit=SECOND)).unwrap() == timedelta(
        microseconds=2
    )
    assert to_timedelta(Quantity(value=1, unit=METER)).is_failed()
    print("Quantity duration: signed/exact microseconds and explicit Result")
    print("Float64 retains CPython timedelta rounding; known nontime units fail")


if __name__ == "__main__":
    main()
