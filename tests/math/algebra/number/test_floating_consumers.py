"""浮点公开值参与同单位物理量。 / Public floating values in same-unit quantities."""

from __future__ import annotations

import copy
import operator
import pickle

import pytest

from ospf_python.math.algebra.number.floating import Floating
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.unit.length import CENTIMETER, METER
from ospf_python.utils.functional.result import Failed
from tests.quantities._arithmetic_before import legacy_operation


@pytest.mark.parametrize("transport", (copy.copy, copy.deepcopy, pickle.loads))
def test_floating_quantity_add_subtract_and_object_graphs(transport: object) -> None:
    left = Quantity(value=Floating(7.25), unit=METER)
    right = Quantity(value=Floating(2.5), unit=METER)
    pair = [left, left, right]
    if transport is pickle.loads:
        restored = pickle.loads(pickle.dumps(pair))
    elif transport is copy.copy:
        restored = copy.copy(pair)
    else:
        restored = copy.deepcopy(pair)
    assert restored[0] is restored[1]
    total = (restored[0] + restored[2]).unwrap()
    difference = (restored[0] - restored[2]).unwrap()
    assert total.value == Floating(9.75)
    assert difference.value == Floating(4.75)
    assert total.unit is restored[0].unit
    assert difference.unit is restored[0].unit
    assert left.value.value == 7.25 and right.value.value == 2.5


@pytest.mark.parametrize("operation", ("add", "subtract"))
def test_different_units_reject_before_floating_arithmetic(operation: str) -> None:
    class Forbidden(Floating):
        def __add__(self, other: Forbidden) -> Forbidden:
            pytest.fail("unit mismatch must precede value arithmetic")

        def __sub__(self, other: Forbidden) -> Forbidden:
            pytest.fail("unit mismatch must precede value arithmetic")

    left = Quantity(value=Forbidden(1.0), unit=METER)
    right = Quantity(value=Forbidden(2.0), unit=CENTIMETER)
    with pytest.raises(TypeError, match="different units"):
        legacy_operation(
            operation=operator.add if operation == "add" else operator.sub,
            owner=left,
            other=right,
        )
    result = left + right if operation == "add" else left - right
    assert isinstance(result, Failed)
