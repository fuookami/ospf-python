"""定义时登记单位家族，不缓存实例数值。 / Register unit families at definition time, without instance-value caches."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from types import CodeType, FunctionType, MethodType
from typing import Any


@dataclass(frozen=True, slots=True)
class Family:
    """单位家族的静态证据。 / Static evidence for a unit family.

    Attributes:
        cls: 原始精确类型。 / Original exact type.
        powers: 显式十维指数。 / Explicit ten-dimensional powers.
        affine: 是否为温度点。 / Whether this is an affine temperature point.
        methods: 定义时函数及代码身份。 / Function and code identities at definition time.
        handle_descriptor: 原生句柄槽的原始描述符，非实例状态。 / Original native-handle slot descriptor, not instance state.
    """

    cls: type[Any]
    powers: tuple[int, ...]
    affine: bool
    methods: dict[str, tuple[FunctionType, CodeType]]
    handle_descriptor: object | None = None


_families: dict[int, Family] = {}
_runtime_families: dict[int, Family] = {}


def register_runtime_unit(cls: type[Any]) -> type[Any]:
    """登记真实原生单位类型，不加入33个旧家族清单。 / Register the real native type separately from the 33 legacy families.

    Args:
        cls: dataclass完成后的原生单位类型。 / Native unit class after dataclass creation.

    Returns:
        原类，不缓存实例或元数据。 / The same class, without instance/metadata caching.
    """
    namespace = vars(cls)
    _runtime_families[id(cls)] = Family(
        cls=cls,
        powers=(),
        affine=False,
        methods={
            name: (namespace[name], namespace[name].__code__)
            for name in ("to_si", "from_si")
        },
        handle_descriptor=namespace["_handle"],
    )
    return cls


def register_unit_family(
    *, powers: tuple[int, ...], affine: bool = False
) -> Callable[[type[Any]], type[Any]]:
    """在 dataclass 装饰后捕获原方法，返回原类。 / Capture original methods after dataclass decoration, returning the same class.

    Args:
        powers: 明确的十维指数。 / Explicit ten powers.
        affine: 零偏移也保留 affine 身份。 / Retain affine identity even at zero offset.

    Returns:
        只登记类型元数据的装饰器。 / Decorator recording only type metadata.
    """

    def register(cls: type[Any]) -> type[Any]:
        methods = {
            name: (vars(cls)[name], vars(cls)[name].__code__)
            for name in ("to_si", "from_si")
        }
        _families[id(cls)] = Family(cls, powers, affine, methods)
        return cls

    return register


def _registered_family(unit: object) -> Family | None:
    cls = type(unit)
    family = _families.get(id(cls)) or _runtime_families.get(id(cls))
    if family is None or family.cls is not cls or type(cls) is not type:
        return None
    namespace = vars(cls)
    bases = cls.__bases__
    if (
        len(bases) != 1
        or bases[0] is not object
        or namespace.get("__getattribute__", object.__getattribute__)
        is not object.__getattribute__
        or "__getattr__" in namespace
    ):
        return None
    # 动态字段必须执行开放协议，不提前触发 descriptor。
    # Dynamic fields use the open protocol without speculative descriptor calls.
    if family.handle_descriptor is not None:
        if namespace.get("_handle") is not family.handle_descriptor:
            return None
        fields: tuple[str, ...] = ()
    else:
        fields = ("_factor", "_offset") if family.affine else ("_factor",)
    if any(
        "__get__" in type.__getattribute__(base, "__dict__")
        for name in fields
        for base in type.__getattribute__(type(namespace.get(name)), "__mro__")
    ):
        return None
    return family


def native_family(*, unit: object, callback: object, direction: str) -> Family | None:
    """仅为未扩展的精确单位类型选择原生通道。 / Select the native lane only for unextended exact unit types.

    Args:
        unit: 实际单位，不读取 symbol 或系数。 / Actual unit; no symbol or coefficient reads.
        callback: 已按 Python 顺序捕获的 callable。 / Callable already captured in Python order.
        direction: source 或 target。 / Source or target.

    Returns:
        静态家族，或保留开放回调的 None。 / Static family, or None preserving open callbacks.
    """
    family = _registered_family(unit)
    if family is None:
        return None
    if type(callback) is not MethodType or callback.__self__ is not unit:
        return None
    function, code = family.methods["to_si" if direction == "source" else "from_si"]
    if (
        callback.__func__ is not function
        or function.__code__ is not code
        or function.__defaults__ is not None
        or function.__kwdefaults__ is not None
    ):
        return None
    return family


def arithmetic_family(unit: object) -> Family | None:
    """一次证明两个原始单位方法，不读取动态系数。 / Prove both original unit methods once, without reading dynamic coefficients.

    Args:
        unit: 本次四则实际单位。 / Actual unit for this arithmetic call.

    Returns:
        静态类型证据或 None；不缓存实例或数值。 / Static type evidence or None; no instance/value cache.
    """
    family = _registered_family(unit)
    if family is None:
        return None
    namespace = vars(type(unit))
    for name in ("to_si", "from_si"):
        function, code = family.methods[name]
        # 先证明类槽仍是原函数，再捕获实例绑定；不执行替换的 descriptor。
        # Prove the class slot is the original function before capturing an instance binding.
        if namespace.get(name) is not function:
            return None
        callback = object.__getattribute__(unit, name)
        if (
            type(callback) is not MethodType
            or callback.__self__ is not unit
            or callback.__func__ is not function
            or function.__code__ is not code
            or function.__defaults__ is not None
            or function.__kwdefaults__ is not None
        ):
            return None
    if family.handle_descriptor is None and any(
        "__get__" in type.__getattribute__(base, "__dict__")
        for base in type.__getattribute__(type(namespace.get("_symbol")), "__mro__")
    ):
        return None
    return family
