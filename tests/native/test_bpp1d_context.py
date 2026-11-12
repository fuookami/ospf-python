"""固定 Rust BPP1D 精确上下文的真实边界 / Real pinned-Rust exact BPP1D context boundary."""

from __future__ import annotations

import itertools
import random
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

from ospf_python import _native
from ospf_python._binding import bpp1d as bpp1d_binding
from ospf_python._binding.bpp1d import BinSpec, ItemSpec, PackingContext
from ospf_python._binding.numeric import Rational
from ospf_python._binding.quantities import Unit
from ospf_python.utils.functional.result import Failed

_LENGTH = (0, 1, 0, 0, 0, 0, 0, 0, 0, 0)
_MASS = (1, 0, 0, 0, 0, 0, 0, 0, 0, 0)


def _r(value: int | float | Fraction) -> Rational:
    if isinstance(value, float):
        return Rational.from_float(value).unwrap()
    return Rational.from_value(value).unwrap()


def _unit(powers: tuple[int, ...], *, scale: int = 1) -> Unit:
    return Unit.create(name="unit", symbol="u", powers=powers, scale=scale).unwrap()


def _item(
    *, id_: str, length: int | float | Fraction, weight: int = 0, amount: int = 1
) -> ItemSpec:
    return ItemSpec(id=id_, length=_r(length), weight=_r(weight), amount=amount)


def _bin(
    *,
    id_: str,
    length: int | float | Fraction,
    weight: int = 0,
    inventory: int | None = None,
) -> BinSpec:
    return BinSpec(
        id=id_,
        length=_r(length),
        max_weight=_r(weight),
        cost=_r(1),
        inventory=inventory,
    )


def _context(
    *,
    items: list[ItemSpec],
    bins: list[BinSpec],
    spacing: int | Fraction = 0,
    objective: str = "bin_count",
) -> PackingContext:
    return PackingContext.create(
        items=items,
        bins=bins,
        spacing=_r(spacing),
        length_unit=_unit(_LENGTH),
        weight_unit=_unit(_MASS),
        objective=objective,
    ).unwrap()


def test_original_float_omission_has_complete_exact_candidates_and_placements() -> None:
    ctx = _context(
        items=[
            _item(id_="a", length=0.1),
            _item(id_="c", length=0.2),
            _item(id_="b", length=0.03),
        ],
        bins=[_bin(id_="bin", length=0.33)],
    )
    patterns, complete, visited = ctx.generate_patterns(
        max_patterns=100, max_nodes=1000
    ).unwrap()
    assert complete and visited > 0 and len(patterns) == 7
    assert ("bin", {"a": 1, "b": 1, "c": 1}) in patterns
    assert ctx.validate_pattern(
        bin_type_id="bin", amounts={"a": 1, "b": 1, "c": 1}
    ).is_ok()
    plans, _, _, total, packed, objective = ctx.pack(
        usages=[("bin", {"a": 1, "b": 1, "c": 1}, 1)], expansion_limit=3
    ).unwrap()
    assert len(plans) == 1 and plans[0][:2] == ("bin_0", "bin")
    end = Fraction()
    expected = {
        "a": Fraction.from_float(0.1),
        "b": Fraction.from_float(0.03),
        "c": Fraction.from_float(0.2),
    }
    for id_, start, length in plans[0][2]:
        assert Fraction(*start) == end
        assert Fraction(*length) == expected[id_]
        end += Fraction(*length)
    assert end == Fraction(*total) == Fraction(*packed) == Fraction.from_float(0.33)
    assert Fraction(*objective) == 1


def test_inventory_spacing_materials_and_exact_cost_are_preserved() -> None:
    a = ItemSpec(id="a", length=_r(1), weight=_r(2), amount=2, materials={"fragile": 2})
    b = ItemSpec(id="b", length=_r(2), weight=_r(1), amount=1, materials={"fragile": 1})
    small = BinSpec(
        id="small",
        length=_r(3),
        max_weight=_r(5),
        cost=_r(Fraction(1, 10)),
        inventory=1,
    )
    big = BinSpec(
        id="big", length=_r(4), max_weight=_r(5), cost=_r(Fraction(1, 4)), inventory=1
    )
    ctx = _context(
        items=[a, b], bins=[small, big], spacing=Fraction(1, 2), objective="cost"
    )
    usages = [("small", {"a": 1}, 1), ("big", {"a": 1, "b": 1}, 1)]
    plans, intervals, materials, total, packed, objective = ctx.pack(
        usages=usages, expansion_limit=3
    ).unwrap()
    assert len(plans) == 2 and len(intervals) == 3
    assert materials == {"fragile": 5}
    assert Fraction(*total) == 7 and Fraction(*packed) == 4
    assert Fraction(*objective) == Fraction(7, 20)
    assert ctx.validate_pattern(
        bin_type_id="small", amounts={"a": 1, "b": 1}
    ).is_failed()
    assert ctx.pack(usages=usages, expansion_limit=2).is_failed()
    assert ctx.pack(usages=[usages[0]], expansion_limit=3).is_failed()
    assert ctx.pack(usages=[usages[0], usages[0]], expansion_limit=3).is_failed()
    assert ctx.pack(
        usages=[("small", {"a": 1}, 2), ("big", {"b": 1}, 1)], expansion_limit=3
    ).is_failed()


def test_search_budgets_units_and_invalid_inputs_fail_without_mutation() -> None:
    ctx = _context(
        items=[_item(id_="a", length=1, amount=2)], bins=[_bin(id_="bin", length=2)]
    )
    patterns, complete, visited = ctx.generate_patterns(
        max_patterns=1, max_nodes=100
    ).unwrap()
    assert len(patterns) == 1 and not complete and visited <= 100
    patterns, complete, visited = ctx.generate_patterns(
        max_patterns=100, max_nodes=1
    ).unwrap()
    assert not patterns and not complete and visited == 1
    assert ctx.generate_patterns(max_patterns=0, max_nodes=1).is_failed()
    assert ctx.generate_patterns(max_patterns=True, max_nodes=1).is_failed()
    assert ctx.validate_pattern(bin_type_id="bin", amounts={"a": True}).is_failed()
    assert ctx.pack(usages=[("bin", {"a": 2}, 1)], expansion_limit=True).is_failed()
    assert ctx.generate_patterns(max_patterns=100, max_nodes=100).unwrap()[1]
    args: dict[str, Any] = dict(
        items=[_item(id_="a", length=1)],
        bins=[_bin(id_="bin", length=2)],
        spacing=_r(0),
        length_unit=_unit(_LENGTH),
        weight_unit=_unit(_MASS),
    )
    assert PackingContext.create(**(args | {"length_unit": _unit(_MASS)})).is_failed()
    affine = Unit.create(
        name="affine", symbol="a", powers=_LENGTH, scale=1, offset=0
    ).unwrap()
    assert PackingContext.create(**(args | {"length_unit": affine})).is_failed()
    assert PackingContext.create(
        **(args | {"length_unit": _unit(_LENGTH, scale=-1)})
    ).is_failed()
    assert PackingContext.create(**(args | {"objective": "unknown"})).is_failed()
    assert PackingContext.create(
        **(args | {"items": [_item(id_="a", length=1), _item(id_="a", length=1)]})
    ).is_failed()


def test_unit_dimensions_are_checked_independently_of_display_symbols() -> None:
    args: dict[str, Any] = dict(
        items=[_item(id_="a", length=1)],
        bins=[_bin(id_="bin", length=2)],
        spacing=_r(0),
        length_unit=_unit(_LENGTH, scale=100),
        weight_unit=_unit(_MASS, scale=1000),
    )
    assert PackingContext.create(**args).is_ok()
    invalid_unit = PackingContext.create(**(args | {"length_unit": _unit(_MASS)}))
    assert isinstance(invalid_unit, Failed)
    assert invalid_unit.error.value.source == "ospf-python-native"
    assert invalid_unit.error.value.category == "ILLEGAL_ARGUMENT"
    for field, expected in (("length_unit", _LENGTH), ("weight_unit", _MASS)):
        for axis in range(10):
            powers = list(expected)
            powers[axis] += 1
            assert PackingContext.create(
                **(args | {field: _unit(tuple(powers))})
            ).is_failed()
        assert PackingContext.create(**(args | {field: _unit((0,) * 10)})).is_failed()


def test_empty_unfillable_and_invalid_counts_are_explicit() -> None:
    empty = _context(items=[], bins=[_bin(id_="bin", length=1)])
    patterns, complete, _ = empty.generate_patterns(
        max_patterns=10, max_nodes=10
    ).unwrap()
    assert patterns == [] and complete
    assert empty.pack(usages=[], expansion_limit=0).unwrap() == (
        [],
        [],
        {},
        (0, 1),
        (0, 1),
        (0, 1),
    )
    for item in (
        _item(id_="long", length=2),
        _item(id_="heavy", length=1, weight=2),
    ):
        ctx = _context(items=[item], bins=[_bin(id_="bin", length=1, weight=1)])
        patterns, complete, _ = ctx.generate_patterns(
            max_patterns=10, max_nodes=100
        ).unwrap()
        assert patterns == [] and complete
        assert ctx.validate_pattern(bin_type_id="bin", amounts={item.id: 1}).is_failed()
        assert ctx.pack(usages=[], expansion_limit=1).is_failed()

    ctx = _context(items=[_item(id_="a", length=1)], bins=[_bin(id_="bin", length=1)])
    for count in (-1, 0, 2, 2**64, True):
        assert ctx.validate_pattern(bin_type_id="bin", amounts={"a": count}).is_failed()
        assert ctx.pack(
            usages=[("bin", {"a": 1}, count)], expansion_limit=2
        ).is_failed()
    assert ctx.validate_pattern(bin_type_id="bin", amounts={}).is_failed()
    assert ctx.validate_pattern(bin_type_id="bin", amounts={"missing": 1}).is_failed()
    assert ctx.validate_pattern(bin_type_id="missing", amounts={"a": 1}).is_failed()
    assert ctx.generate_patterns(max_patterns=2**64, max_nodes=1).is_failed()
    assert ctx.pack(usages=[("bin", {"a": 1}, 1)], expansion_limit=-1).is_failed()


def test_non_dyadic_coordinates_and_material_overflow() -> None:
    ctx = _context(
        items=[
            _item(id_="a", length=Fraction(1, 3)),
            _item(id_="b", length=Fraction(1, 5)),
        ],
        bins=[_bin(id_="bin", length=2)],
        spacing=Fraction(1, 7),
        objective="consumed_length",
    )
    plans, intervals, _, total, packed, objective = ctx.pack(
        usages=[("bin", {"a": 1, "b": 1}, 1)], expansion_limit=2
    ).unwrap()
    assert [
        (id_, Fraction(*start), Fraction(*length)) for id_, start, length in plans[0][2]
    ] == [
        ("a", Fraction(0), Fraction(1, 3)),
        ("b", Fraction(10, 21), Fraction(1, 5)),
    ]
    assert [
        (Fraction(*start), Fraction(*length)) for _, start, length in intervals
    ] == [
        (Fraction(1, 3), Fraction(1, 7)),
        (Fraction(71, 105), Fraction(139, 105)),
    ]
    assert Fraction(*total) == Fraction(*objective) == 2
    assert Fraction(*packed) == Fraction(8, 15)

    overflow = _context(
        items=[
            ItemSpec(
                id="a",
                length=_r(1),
                weight=_r(0),
                amount=2,
                materials={"material": 2**64 - 1},
            )
        ],
        bins=[_bin(id_="bin", length=2)],
    )
    assert overflow.validate_pattern(bin_type_id="bin", amounts={"a": 2}).is_ok()
    assert overflow.pack(usages=[("bin", {"a": 2}, 1)], expansion_limit=2).is_failed()


def test_context_owns_input_and_output_snapshots_across_threads() -> None:
    materials = {"material": 2}
    items = [
        ItemSpec(id="a", length=_r(1), weight=_r(0), amount=2, materials=materials)
    ]
    bins = [_bin(id_="bin", length=2)]
    ctx = _context(items=items, bins=bins)
    materials["material"] = 100
    items.clear()
    bins.clear()

    expected_patterns = ctx.generate_patterns(max_patterns=10, max_nodes=100).unwrap()
    expected_packed = ctx.pack(
        usages=[("bin", {"a": 2}, 1)], expansion_limit=2
    ).unwrap()
    assert expected_packed[2] == {"material": 4}
    patterns = ctx.generate_patterns(max_patterns=10, max_nodes=100).unwrap()
    patterns[0][0][1]["a"] = 999
    packed = ctx.pack(usages=[("bin", {"a": 2}, 1)], expansion_limit=2).unwrap()
    packed[0][0][2].clear()
    packed[2]["material"] = 999

    def read_snapshot(_: int) -> None:
        assert (
            ctx.generate_patterns(max_patterns=10, max_nodes=100).unwrap()
            == expected_patterns
        )
        assert (
            ctx.pack(usages=[("bin", {"a": 2}, 1)], expansion_limit=2).unwrap()
            == expected_packed
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(read_snapshot, range(64)))


def test_mutable_arguments_are_captured_before_count_validation(
    *, monkeypatch: pytest.MonkeyPatch
) -> None:
    materials = {"material": 2}
    items = [
        ItemSpec(id="a", length=_r(1), weight=_r(0), amount=1, materials=materials)
    ]
    original_counts = bpp1d_binding._counts

    def mutate_input(value: object) -> bool:
        valid = original_counts(value)
        materials["material"] = 99
        items.clear()
        return valid

    monkeypatch.setattr(bpp1d_binding, "_counts", mutate_input)
    ctx = _context(items=items, bins=[_bin(id_="bin", length=1)])
    monkeypatch.setattr(bpp1d_binding, "_counts", original_counts)
    packed = ctx.pack(usages=[("bin", {"a": 1}, 1)], expansion_limit=1).unwrap()
    assert packed[2] == {"material": 2}

    amounts = {"a": 1}

    def mutate_amounts(value: object) -> bool:
        valid = original_counts(value)
        amounts["a"] = 0
        return valid

    monkeypatch.setattr(bpp1d_binding, "_counts", mutate_amounts)
    assert ctx.validate_pattern(bin_type_id="bin", amounts=amounts).is_ok()
    amounts["a"] = 1
    usages = [("bin", amounts, 1)]

    def mutate_usages(value: object) -> bool:
        valid = original_counts(value)
        amounts["a"] = 0
        usages.clear()
        return valid

    monkeypatch.setattr(bpp1d_binding, "_counts", mutate_usages)
    assert ctx.pack(usages=usages, expansion_limit=1).unwrap() == packed


def test_candidates_match_independent_exact_enumeration() -> None:
    rng = random.Random(318)
    for _ in range(30):
        items = [
            _item(
                id_=chr(97 + i),
                length=Fraction(rng.randint(1, 6), rng.randint(1, 4)),
                weight=rng.randint(0, 3),
                amount=rng.randint(0, 3),
            )
            for i in range(3)
        ]
        bins = [
            _bin(
                id_="x",
                length=Fraction(rng.randint(1, 7), 2),
                weight=rng.randint(0, 8),
                inventory=rng.choice([0, 1, None]),
            ),
            _bin(
                id_="y",
                length=Fraction(rng.randint(1, 7), 2),
                weight=rng.randint(0, 8),
            ),
        ]
        spacing = Fraction(rng.randint(0, 2), 3)
        ctx = _context(items=items, bins=bins, spacing=spacing)
        patterns, complete, _ = ctx.generate_patterns(
            max_patterns=1000, max_nodes=10000
        ).unwrap()
        actual = {
            (bin_id, tuple(sorted(amounts.items()))) for bin_id, amounts in patterns
        }
        expected = set()
        for bin_ in bins:
            if bin_.inventory == 0:
                continue
            for counts in itertools.product(
                *(range(item.amount + 1) for item in items)
            ):
                pieces = sum(counts)
                if not pieces:
                    continue
                length = sum(
                    (
                        Fraction(*item.length.as_integer_ratio()) * count
                        for item, count in zip(items, counts, strict=True)
                    ),
                    Fraction(),
                )
                weight = sum(
                    (
                        Fraction(*item.weight.as_integer_ratio()) * count
                        for item, count in zip(items, counts, strict=True)
                    ),
                    Fraction(),
                )
                if length + spacing * (pieces - 1) <= Fraction(
                    *bin_.length.as_integer_ratio()
                ) and weight <= Fraction(*bin_.max_weight.as_integer_ratio()):
                    expected.add(
                        (
                            bin_.id,
                            tuple(
                                (item.id, count)
                                for item, count in zip(items, counts, strict=True)
                                if count
                            ),
                        )
                    )
        assert complete and actual == expected


@pytest.mark.parametrize("depth", [8192, 16384])
def test_deep_exact_domain_comparison_in_fresh_process(depth: int) -> None:
    code = f"""
from fractions import Fraction
import os
from pathlib import Path
handles = [os.add_dll_directory(path) for path in os.environ.get('OSPF_NATIVE_DLL_DIRS', '').split(os.pathsep) if path] if os.name == 'nt' else []
from ospf_python import _native
from ospf_python._binding.bpp1d import BinSpec, ItemSpec, PackingContext
from ospf_python._binding.numeric import Rational
from ospf_python._binding.quantities import Unit
assert Path(_native.__file__).resolve() == Path({_native.__file__!r}).resolve()
a, b = 0, 1
for _ in range({depth}): a, b = b, a+b
left = Rational.create(numerator=a, denominator=b).unwrap()
right = Rational.create(numerator=b, denominator=a+b).unwrap()
zero = Rational.create(numerator=0).unwrap()
one = Rational.create(numerator=1).unwrap()
length = Unit.create(name='length', symbol='m', powers={_LENGTH!r}).unwrap()
weight = Unit.create(name='mass', symbol='kg', powers={_MASS!r}).unwrap()
ctx = PackingContext.create(items=[ItemSpec(id='a', length=left, weight=zero, amount=1)],
    bins=[BinSpec(id='bin', length=right, max_weight=zero, cost=one)], spacing=zero,
    length_unit=length, weight_unit=weight).unwrap()
patterns, complete, _ = ctx.generate_patterns(max_patterns=10, max_nodes=100).unwrap()
expected = Fraction(a, b) <= Fraction(b, a+b)
assert complete and bool(patterns) == expected
if expected:
    plans, _, _, _, _, _ = ctx.pack(usages=[('bin', {{'a': 1}}, 1)], expansion_limit=1).unwrap()
    assert Fraction(*plans[0][2][0][2]) == Fraction(a, b)
print('deep BPP1D context passed')
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=90,
        cwd=Path.cwd(),
    )
    assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
    assert result.stdout.strip() == "deep BPP1D context passed"
