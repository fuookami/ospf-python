"""数量的版本化纯数据边界，不复制单位数学。 / Versioned quantity data boundary without duplicated unit math."""

from __future__ import annotations

import json
import math
from decimal import Decimal
from fractions import Fraction
from typing import TYPE_CHECKING, Any, cast

from ospf_python._binding import quantity_arithmetic as _arithmetic
from ospf_python._binding import unit_conversion as _conversion
from ospf_python._binding.numeric import Rational
from ospf_python._binding.quantities import Unit
from ospf_python._binding.result import (
    BindingResult,
    FailureContext,
    invalid,
    unsupported,
)
from ospf_python._binding.unit_registry import _families
from ospf_python.math.algebra.number.floating import Floating
from ospf_python.math.algebra.number.rational import Rational as PublicRational
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import ExErr
from ospf_python.utils.functional.result import Failed, Ok

if TYPE_CHECKING:
    from collections.abc import Callable

    from ospf_python.quantities.quantity.snapshot_adapter import SnapshotAdapter


def _boundary(call: Callable[[], BindingResult[Any]]) -> BindingResult[Any]:
    try:
        return call()
    except Exception as error:
        return Failed(
            ExErr(
                _code=ErrorCode.APPLICATION_ERROR,
                _message="数量快照协议失败 / Quantity snapshot protocol failed",
                value=FailureContext(
                    source="ospf-python",
                    category="APPLICATION_ERROR",
                    rust_code=None,
                    error_class="QUANTITY_SNAPSHOT",
                    callback_exception=error,
                ),
            )
        )


def _clone(value: Any, active: set[int]) -> BindingResult[Any]:
    if value is None or type(value) in (str, int, bool):
        return Ok(value)
    if type(value) is float:
        return (
            Ok(value)
            if math.isfinite(value)
            else invalid(
                "JSON 快照需要有限数值 / JSON snapshot requires finite numbers"
            )
        )
    if type(value) not in (dict, list):
        return invalid("需要纯 JSON 数据 / Pure JSON data required")
    identity = id(value)
    if identity in active:
        return invalid("快照不能包含循环 / Snapshots must not contain cycles")
    active.add(identity)
    try:
        result: Any = {} if type(value) is dict else []
        items = value.items() if type(value) is dict else enumerate(value)
        for key, part in items:
            if type(value) is dict and type(key) is not str:
                return invalid(
                    "JSON 字段名必须为内置 str / JSON keys must be builtin str"
                )
            copied = _clone(part, active)
            if isinstance(copied, Failed):
                return copied
            if type(value) is dict:
                result[key] = copied.unwrap()
            else:
                result.append(copied.unwrap())
        return Ok(result)
    finally:
        active.remove(identity)


def _native_unit(unit: Any) -> BindingResult[Unit | None]:
    return _arithmetic._Arithmetic(
        operation="multiply", context=None, exact=True, numeric_adapter=None
    ).native_unit(unit)


def _value(value: Any) -> BindingResult[dict[str, Any]]:
    kind = type(value)
    if kind is int:
        return Ok(dict(kind="int", data=hex(value)))
    if kind is bool:
        return Ok(dict(kind="bool", data=value))
    if kind is float:
        return (
            Ok(dict(kind="float", data=value.hex()))
            if math.isfinite(value)
            else invalid("快照需要有限 Float64 / Snapshot requires finite Float64")
        )
    if kind is Decimal:
        return (
            Ok(dict(kind="decimal", data=str(value)))
            if value.is_finite()
            else invalid("快照需要有限 Decimal / Snapshot requires finite Decimal")
        )
    if kind is Floating:
        if type(value.value) not in (int, float):
            return unsupported(
                "Floating 载荷需要 int/float / Floating payload requires int/float"
            )
        return _value(value.value).map(
            lambda payload: dict(kind="floating", data=payload)
        )
    if kind in (Fraction, PublicRational, Rational):
        imported = (
            Ok(value)
            if kind is Rational
            else Rational.create(
                numerator=value.numerator, denominator=value.denominator
            )
        )
        return imported.map(
            lambda raw: dict(
                kind={
                    Fraction: "fraction",
                    PublicRational: "public-rational",
                    Rational: "rational",
                }[kind],
                data=raw.to_json(),
            )
        )
    return unsupported(
        "开放数值需要显式 SnapshotAdapter / Open values require an explicit SnapshotAdapter"
    )


def _restore_value(payload: Any) -> BindingResult[Any]:
    if (
        type(payload) is not dict
        or set(payload) != {"kind", "data"}
        or type(payload["kind"]) is not str
    ):
        return invalid("无效数值快照 / Invalid value snapshot")
    kind, data = payload["kind"], payload["data"]
    if kind == "bool" and type(data) is bool:
        return Ok(data)
    if kind == "floating":
        return _restore_value(data).flat_map(
            lambda raw: (
                Ok(Floating(raw))
                if type(raw) in (int, float)
                else invalid(
                    "Floating 载荷需要 int/float / Floating payload requires int/float"
                )
            )
        )
    if type(data) is not str:
        return invalid("无效数值编码 / Invalid value encoding")
    if kind == "int":
        raw = int(data, 16)
        return (
            Ok(raw)
            if hex(raw) == data
            else invalid("非规范整数编码 / Noncanonical integer encoding")
        )
    if kind == "float":
        raw_float = float.fromhex(data)
        return (
            Ok(raw_float)
            if math.isfinite(raw_float) and raw_float.hex() == data
            else invalid("无效有限 Float64 编码 / Invalid finite Float64 encoding")
        )
    if kind == "decimal":
        raw_decimal = Decimal(data)
        return (
            Ok(raw_decimal)
            if raw_decimal.is_finite() and str(raw_decimal) == data
            else invalid("无效有限 Decimal 编码 / Invalid finite Decimal encoding")
        )
    if kind in ("fraction", "public-rational", "rational"):
        return Rational.from_json(data).map(
            lambda raw: (
                raw
                if kind == "rational"
                else (Fraction if kind == "fraction" else PublicRational)(
                    *raw.as_integer_ratio()
                )
            )
        )
    return unsupported("不支持的数值快照类型 / Unsupported value snapshot kind")


def _adapt(value: Any, adapter: SnapshotAdapter[Any]) -> BindingResult[dict[str, Any]]:
    return _conversion._adapter_result(adapter.to_snapshot(value)).flat_map(
        lambda data: _clone(data, set()).map(
            lambda copied: dict(kind="custom", data=copied)
        )
    )


def _unit(
    unit: Any, adapter: SnapshotAdapter[Any] | None
) -> BindingResult[dict[str, Any]]:
    if adapter is not None:
        return _adapt(unit, adapter)
    family = _families.get(id(type(unit)))
    captured = _native_unit(unit)
    if isinstance(captured, Failed):
        # 精确绑定缺口不应阻止原始字段存档；null 明确表示没有可用原生单位。
        # A binding precision gap must not destroy source data; null explicitly means no native unit exists.
        if (
            family is None
            or family.cls is not type(unit)
            or captured.error.code is not ErrorCode.DATA_LOSS
        ):
            return captured
        native = None
    else:
        native = captured.unwrap()
    if native is None and not isinstance(captured, Failed):
        return unsupported(
            "开放单位需要显式 SnapshotAdapter / Open units require an explicit SnapshotAdapter"
        )
    wire: dict[str, Any] = dict(
        kind="native", native=native.to_json() if native is not None else None
    )
    if family is not None and family.cls is type(unit):
        fields: dict[str, Any] = {"_symbol": object.__getattribute__(unit, "_symbol")}
        for name in ("_factor", "_offset") if family.affine else ("_factor",):
            encoded = _value(object.__getattribute__(unit, name))
            if isinstance(encoded, Failed):
                return encoded
            fields[name] = encoded.unwrap()
        wire.update(
            kind="builtin",
            family=f"{family.cls.__module__}:{family.cls.__qualname__}",
            fields=fields,
        )
    return Ok(wire)


def _restore_unit(
    payload: Any, adapter: SnapshotAdapter[Any] | None
) -> BindingResult[Any]:
    if type(payload) is not dict or type(payload.get("kind")) is not str:
        return invalid("无效单位快照 / Invalid unit snapshot")
    if payload["kind"] == "custom":
        if set(payload) != {"kind", "data"}:
            return invalid("无效开放单位快照 / Invalid open unit snapshot")
        return (
            unsupported("需要单位 SnapshotAdapter / A unit SnapshotAdapter is required")
            if adapter is None
            else _conversion._adapter_result(adapter.from_snapshot(payload["data"]))
        )
    builtin = payload["kind"] == "builtin"
    if payload["kind"] not in ("native", "builtin") or set(payload) != (
        {"kind", "native", "family", "fields"} if builtin else {"kind", "native"}
    ):
        return invalid("无效单位快照字段 / Invalid unit snapshot fields")
    if not builtin:
        return Unit.from_json(payload["native"])
    native = None
    if payload["native"] is not None:
        restored = Unit.from_json(payload["native"])
        if isinstance(restored, Failed):
            return restored
        native = restored.unwrap()
    family = next(
        (
            family
            for family in _families.values()
            if f"{family.cls.__module__}:{family.cls.__qualname__}" == payload["family"]
        ),
        None,
    )
    if family is None:
        return unsupported("单位类型不在已登记清单中 / Unit family is not registered")
    fields = payload["fields"]
    names = (
        {"_symbol", "_factor", "_offset"} if family.affine else {"_symbol", "_factor"}
    )
    if type(fields) is not dict or set(fields) != names:
        return invalid("无效单位表示字段 / Invalid unit representation fields")
    if type(fields["_symbol"]) is not str:
        return invalid("单位符号需要内置 str / Unit symbol requires builtin str")
    keywords: dict[str, Any] = {"_symbol": fields["_symbol"]}
    for name, encoded in fields.items():
        if name == "_symbol":
            continue
        decoded = _restore_value(encoded)
        if isinstance(decoded, Failed):
            return decoded
        coefficient = decoded.unwrap()
        if type(coefficient) not in (int, float, Decimal):
            return invalid("无效单位系数类型 / Invalid unit coefficient type")
        keywords[name] = coefficient
    unit = family.cls(**keywords)
    checked = _native_unit(unit)
    if isinstance(checked, Failed):
        if native is None and checked.error.code is ErrorCode.DATA_LOSS:
            return Ok(unit)
        return checked
    captured = checked.unwrap()
    if (
        native is None
        or captured is None
        or captured.descriptor() != native.descriptor()
    ):
        return invalid(
            "单位表示与原生元数据不一致 / Unit representation conflicts with native metadata"
        )
    return Ok(unit)


def encode(
    *,
    owner: object,
    value_adapter: SnapshotAdapter[Any] | None,
    unit_adapter: SnapshotAdapter[Any] | None,
    as_json: bool,
) -> BindingResult[Any]:
    def operation() -> BindingResult[Any]:
        # 单位快照在数值回调前冻结，adapter 后续修改不能重标已编码单位。
        # Freeze the unit before value callbacks so later adapter mutations cannot relabel it.
        current = cast("Any", owner)
        unit = _unit(current.unit, unit_adapter)
        if isinstance(unit, Failed):
            return unit
        original = current.value
        value = (
            _value(original)
            if value_adapter is None
            else _adapt(original, value_adapter)
        )
        if isinstance(value, Failed):
            return value
        wire = dict(
            schema="ospf.quantity", version=1, value=value.unwrap(), unit=unit.unwrap()
        )
        return Ok(
            json.dumps(wire, ensure_ascii=True, allow_nan=False, separators=(",", ":"))
            if as_json
            else wire
        )

    return _boundary(operation)


def decode(
    *,
    payload: Any,
    factory: Any,
    value_adapter: SnapshotAdapter[Any] | None,
    unit_adapter: SnapshotAdapter[Any] | None,
    as_json: bool,
) -> BindingResult[Any]:
    def operation() -> BindingResult[Any]:
        source = payload
        if as_json:
            if type(source) is not str:
                return invalid("需要内置 JSON str / A builtin JSON str is required")
            duplicates = []

            def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
                result = {}
                for key, value in items:
                    if key in result:
                        duplicates.append(key)
                    result[key] = value
                return result

            source = json.loads(source, object_pairs_hook=pairs)
            if duplicates:
                return invalid("JSON 字段不能重复 / Duplicate JSON keys are forbidden")
        copied = _clone(source, set())
        if isinstance(copied, Failed):
            return copied
        source = copied.unwrap()
        if (
            type(source) is not dict
            or set(source) != {"schema", "version", "value", "unit"}
            or source["schema"] != "ospf.quantity"
            or type(source["version"]) is not int
            or source["version"] != 1
        ):
            return invalid("不支持的数量快照 / Unsupported quantity snapshot")
        unit = _restore_unit(source["unit"], unit_adapter)
        if isinstance(unit, Failed):
            return unit
        value_wire = source["value"]
        if type(value_wire) is dict and value_wire.get("kind") == "custom":
            if set(value_wire) != {"kind", "data"}:
                return invalid("无效开放数值快照 / Invalid open value snapshot")
            value = (
                unsupported(
                    "需要数值 SnapshotAdapter / A value SnapshotAdapter is required"
                )
                if value_adapter is None
                else _conversion._adapter_result(
                    value_adapter.from_snapshot(value_wire["data"])
                )
            )
        else:
            value = _restore_value(value_wire)
        if isinstance(value, Failed):
            return value
        return Ok(factory(value=value.unwrap(), unit=unit.unwrap()))

    return _boundary(operation)
