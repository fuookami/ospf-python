"""单次来源证明及开放扩展边界。 / Single-pass provenance and open-extension boundaries."""

from __future__ import annotations

from fractions import Fraction
from types import MethodType
from typing import Any

import pytest

from ospf_python._binding import unit_registry as registry
from ospf_python._binding.quantity_arithmetic import _Arithmetic
from ospf_python.quantities import NumericAdapter, Quantity, Unit
from ospf_python.quantities.unit.length import Length
from ospf_python.quantities.unit.temperature import Temperature
from ospf_python.utils.functional.result import Failed, Ok, Result

_OPERATIONS = ("add", "subtract", "multiply", "divide")
_MUTATIONS = (
    "class-to_si",
    "class-from_si",
    "instance-to_si",
    "instance-from_si",
    "code-to_si",
    "code-from_si",
    "defaults-to_si",
    "defaults-from_si",
    "kwdefaults-to_si",
    "kwdefaults-from_si",
    "descriptor-to_si",
    "descriptor-from_si",
    "getattribute",
    "getattr",
    "field",
)


def _unit(kind: str) -> Any:
    if kind == "runtime":
        return Unit.create(
            name="length", symbol="m", powers=(0, 1, 0, 0, 0, 0, 0, 0, 0, 0)
        ).unwrap()
    return Temperature("t", 1, 0) if kind == "affine" else Length("m", 1)


def _arithmetic() -> _Arithmetic:
    return _Arithmetic(
        operation="multiply", context=None, exact=True, numeric_adapter=None
    )


def _forbidden(*args: Any, **kwargs: Any) -> Any:
    pytest.fail(
        "来源证明不得执行外部协议 / Provenance must not execute external protocols"
    )


def _mutate(*, monkeypatch: pytest.MonkeyPatch, unit: Any, mutation: str) -> None:
    kind, _, name = mutation.partition("-")
    cls = type(unit)
    if kind in ("class", "descriptor"):
        monkeypatch.setattr(
            cls, name, _forbidden if kind == "class" else property(_forbidden)
        )
    elif kind == "instance":
        object.__setattr__(unit, name, MethodType(_forbidden, unit))
    elif kind in ("code", "defaults", "kwdefaults"):
        function = vars(cls)[name]
        attribute = {
            "code": "__code__",
            "defaults": "__defaults__",
            "kwdefaults": "__kwdefaults__",
        }[kind]
        value = {"code": _forbidden.__code__, "defaults": (1,), "kwdefaults": {"x": 1}}[
            kind
        ]
        monkeypatch.setattr(function, attribute, value)
    elif kind == "getattribute":
        monkeypatch.setattr(cls, "__getattribute__", _forbidden, raising=False)
    elif kind == "getattr":
        monkeypatch.setattr(cls, "__getattr__", _forbidden, raising=False)
    else:
        monkeypatch.setattr(
            cls, "_handle" if cls is Unit else "_factor", property(_forbidden)
        )


@pytest.mark.parametrize(
    "family", list(registry._families.values()), ids=lambda family: family.cls.__name__
)
def test_all_33_families_prove_both_original_bound_methods(family: Any) -> None:
    unit = family.cls()
    assert registry.arithmetic_family(unit) is family
    assert (
        registry.native_family(unit=unit, callback=unit.to_si, direction="source")
        is family
    )
    assert (
        registry.native_family(unit=unit, callback=unit.from_si, direction="target")
        is family
    )


@pytest.mark.parametrize("kind", ("legacy", "affine", "runtime"))
@pytest.mark.parametrize("mutation", _MUTATIONS)
@pytest.mark.parametrize("operation", _OPERATIONS)
def test_mutated_provenance_never_executes_descriptors_or_relabels_open_math(
    *, monkeypatch: pytest.MonkeyPatch, kind: str, mutation: str, operation: str
) -> None:
    if kind == "runtime" and mutation.startswith("instance-"):
        # slots 禁止此扩展，不能以 skip 代替实际验证。 / Slots prohibit this extension; verify rejection rather than skipping.
        unit = _unit(kind)
        with pytest.raises(AttributeError):
            object.__setattr__(unit, mutation.partition("-")[2], _forbidden)
        assert registry.arithmetic_family(unit) is registry._runtime_families[id(Unit)]
        return
    unit = _unit(kind)
    _mutate(monkeypatch=monkeypatch, unit=unit, mutation=mutation)
    assert registry.arithmetic_family(unit) is None
    assert _arithmetic().native_unit(unit).unwrap() is None
    owner = Quantity(value=Fraction(6), unit=unit)
    other: Any = (
        Quantity(value=Fraction(2), unit=unit)
        if operation in ("add", "subtract")
        else Fraction(2)
    )
    result = getattr(owner, operation)(other).unwrap()
    assert result.unit is unit
    assert (
        result.value
        == {"add": 8, "subtract": 4, "multiply": 12, "divide": 3}[operation]
    )


@pytest.mark.parametrize("kind", ("legacy", "runtime"))
@pytest.mark.parametrize("operation", _OPERATIONS)
def test_each_capture_revalidates_once_without_cross_call_instance_cache(
    *, monkeypatch: pytest.MonkeyPatch, kind: str, operation: str
) -> None:
    unit = _unit(kind)
    checks: list[object] = []
    original = registry._registered_family

    def record(value: object) -> registry.Family | None:
        checks.append(value)
        return original(value)

    monkeypatch.setattr(registry, "_registered_family", record)
    owner = Quantity(value=Fraction(6), unit=unit)
    other: Any = (
        Quantity(value=Fraction(2), unit=unit)
        if operation in ("add", "subtract")
        else Fraction(2)
    )
    for iteration in (1, 2):
        output = getattr(owner, operation)(other).unwrap()
        assert output.unit is unit
        assert len(checks) == iteration * (3 if operation in ("add", "subtract") else 2)
        assert all(value is unit for value in checks)


@pytest.mark.parametrize(
    ("kind", "mutation"),
    [
        (kind, mutation)
        for kind in ("legacy", "runtime")
        for mutation in _MUTATIONS
        if not mutation.startswith("instance-")
        and not (kind == "runtime" and mutation in ("getattribute", "field"))
    ],
)
@pytest.mark.parametrize("operation", _OPERATIONS)
def test_adapter_mutation_cannot_relabel_the_captured_native_output(
    *, monkeypatch: pytest.MonkeyPatch, kind: str, mutation: str, operation: str
) -> None:
    unit = _unit(kind)
    owner = Quantity(value=Fraction(6), unit=unit)
    other: Any = (
        Quantity(value=Fraction(2), unit=unit)
        if operation in ("add", "subtract")
        else Fraction(2)
    )
    captured = _arithmetic().native_unit(unit).unwrap()
    assert captured is not None
    expected_descriptor = captured.descriptor()
    events: list[str] = []

    class Adapter(NumericAdapter[Fraction]):
        def to_fraction(self, value: Fraction) -> Result[Fraction, Any, Any]:
            events.append("import")
            if len(events) == 1:
                _mutate(monkeypatch=monkeypatch, unit=unit, mutation=mutation)
            return Ok(value)

        def from_fraction(self, value: Fraction) -> Result[Fraction, Any, Any]:
            events.append("export")
            return Ok(value)

    output = getattr(owner, operation)(other, numeric_adapter=Adapter()).unwrap()
    assert output.unit is not unit
    assert events == ["import", "import", "export"]
    # 运行时Unit类本身也可能被修改；直接读取冻结句柄避免测试调用被替换协议。
    # The Unit class may itself be extended; inspect the actual handle without invoking replaced protocols.
    handle = object.__getattribute__(output.unit, "_handle")
    name, symbol, powers, scale, offset = handle.descriptor()
    assert (name, symbol, tuple(powers), scale, offset) == expected_descriptor
    assert (
        output.value
        == {"add": 8, "subtract": 4, "multiply": 12, "divide": 3}[operation]
    )


@pytest.mark.parametrize("attribute", ("_symbol", "_factor"))
@pytest.mark.parametrize("operation", _OPERATIONS)
def test_class_field_metaclass_is_never_executed_during_passive_proof(
    *, monkeypatch: pytest.MonkeyPatch, attribute: str, operation: str
) -> None:
    class Meta(type):
        def __getattribute__(cls, name: str) -> Any:
            pytest.fail(
                "不得执行字段类型的元类 / Must not execute a field-type metaclass"
            )

    class Field(metaclass=Meta):
        pass

    unit = Length("m", 1)
    monkeypatch.setattr(Length, attribute, Field())
    assert registry.arithmetic_family(unit) is registry._families[id(Length)]
    owner = Quantity(value=Fraction(6), unit=unit)
    other: Any = (
        Quantity(value=Fraction(2), unit=unit)
        if operation in ("add", "subtract")
        else Fraction(2)
    )
    output = getattr(owner, operation)(other).unwrap()
    assert output.unit is unit
    assert (
        output.value
        == {"add": 8, "subtract": 4, "multiply": 12, "divide": 3}[operation]
    )


@pytest.mark.parametrize("mutation", ("getattribute", "field"))
@pytest.mark.parametrize("operation", _OPERATIONS)
def test_late_runtime_class_extension_retains_actual_protocol_failure(
    *, monkeypatch: pytest.MonkeyPatch, mutation: str, operation: str
) -> None:
    unit = _unit("runtime")
    owner = Quantity(value=Fraction(6), unit=unit)
    other: Any = (
        Quantity(value=Fraction(2), unit=unit)
        if operation in ("add", "subtract")
        else Fraction(2)
    )
    error = ValueError("late runtime class extension")

    def extension(value: object, name: str = "_handle") -> Any:
        if name == "_handle":
            raise error
        return object.__getattribute__(value, name)

    class Adapter(NumericAdapter[Fraction]):
        def to_fraction(self, value: Fraction) -> Result[Fraction, Any, Any]:
            if mutation == "field":
                monkeypatch.setattr(Unit, "_handle", property(extension))
            else:
                monkeypatch.setattr(Unit, "__getattribute__", extension)
            return Ok(value)

        def from_fraction(self, value: Fraction) -> Result[Fraction, Any, Any]:
            pytest.fail(
                "原生协议失败后不得导出 / Do not export after native protocol failure"
            )

    output = getattr(owner, operation)(other, numeric_adapter=Adapter())
    assert isinstance(output, Failed)
    assert output.error.value.callback_exception is error
    assert output.error.value.error_class == "QUANTITY_ARITHMETIC"
