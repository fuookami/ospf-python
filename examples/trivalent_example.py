"""公开三值逻辑显式Result示例。 / Public trivalent logic with explicit Results."""

from ospf_python.math.ordinary import Trivalent as Ordinary
from ospf_python.math.trivalent import (
    BalancedTrivalent,
    Trivalent,
    and_,
    balanced_or,
    not_,
)


def main() -> None:
    """验证三个家族各自的单例与未知值。 / Check singleton and unknown values within all three families."""
    ready = and_(Trivalent.TRUE, not_(Trivalent.FALSE).unwrap()).unwrap()
    assert ready is Trivalent.TRUE
    uncertain = balanced_or(
        BalancedTrivalent.FALSE, BalancedTrivalent.BALANCED
    ).unwrap()
    assert uncertain is BalancedTrivalent.BALANCED
    gate = (Ordinary.TRUE & Ordinary.UNKNOWN).unwrap()
    assert gate is Ordinary.UNKNOWN and gate.to_bool().unwrap() is None


if __name__ == "__main__":
    main()
