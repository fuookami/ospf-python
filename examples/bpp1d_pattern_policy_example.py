"""私有 BPP1D 候选策略示例 / Private BPP1D candidate-policy example."""

from __future__ import annotations

from ospf_python._binding.bpp1d import BinSpec, ItemSpec, PackingContext, Pattern
from ospf_python._binding.numeric import Rational
from ospf_python._binding.quantities import Unit


def main() -> None:
    """只接受单一身份的候选 / Accept only single-identity candidates."""
    zero = Rational.from_value(0).unwrap()
    one = Rational.from_value(1).unwrap()
    two = Rational.from_value(2).unwrap()
    length = Unit.create(
        name="length", symbol="m", powers=(0, 1, 0, 0, 0, 0, 0, 0, 0, 0)
    ).unwrap()
    mass = Unit.create(
        name="mass", symbol="kg", powers=(1, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    ).unwrap()
    context = PackingContext.create(
        items=[
            ItemSpec(id="a", length=one, weight=zero, amount=1),
            ItemSpec(id="b", length=one, weight=zero, amount=1),
        ],
        bins=[BinSpec(id="box", length=two, max_weight=zero, cost=one)],
        spacing=zero,
        length_unit=length,
        weight_unit=mass,
    ).unwrap()

    def no_mixed_items(candidate: Pattern) -> bool:
        return len(candidate[1]) == 1

    patterns, complete, _ = context.generate_patterns(
        max_patterns=10, max_nodes=100, policy=no_mixed_items
    ).unwrap()
    assert complete and patterns == [("box", {"a": 1}), ("box", {"b": 1})]
    print("BPP1D policy: 2 single-identity candidates")


if __name__ == "__main__":
    main()
