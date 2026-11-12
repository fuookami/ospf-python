"""私有 Rust 边界的类型提示 / Type declarations for the private Rust boundary."""

from collections.abc import Callable, Iterable
from typing import Any, TypeVar, overload

__version__: str

_IntegerT = TypeVar("_IntegerT")
"""公开构造器的结果类型。 / Public constructor result type."""

def build_info() -> dict[str, str]:
    """构建身份与已编译后端，不探测许可证 / Build identity without license probing."""
    ...

def _checked_nonnegative(value: int) -> tuple[int | None, tuple[int, str] | None]: ...
def _quantity_arithmetic(
    *,
    owner: object,
    other: object,
    operation: str,
    namespace: dict[str, Any],
    builtins: dict[str, Any],
    protocols: tuple[
        Callable[[tuple[Any, Any]], bool],
        Callable[[tuple[Any, Any]], tuple[bool, bool, Any, Any]],
    ],
) -> tuple[bool, Any, tuple[str, Exception] | None]: ...
def _convert_quantity_callback(
    *,
    owner: object,
    target: object,
    namespace: dict[str, Any],
    builtins: dict[str, Any],
) -> tuple[Any, tuple[str, Exception] | None]: ...
def _convert_quantity_dispatched(
    *,
    owner: object,
    target: object,
    namespace: dict[str, Any],
    builtins: dict[str, Any],
    prepare: Callable[..., tuple[Any, bool]],
) -> tuple[bool, Any, tuple[str, Exception] | None]: ...
def _quantity_extreme(
    *,
    items: object,
    maximum: bool,
    prepare: Callable[
        [tuple[Any, Any, Any]], tuple[bool, int, Any, tuple[int, ...] | None]
    ],
    export: Callable[[int, Any], Any],
) -> tuple[bool, Any, Failure | None, tuple[str, Exception, int | None] | None]: ...
def _quantity_contains(
    *,
    bounds: object,
    quantity: object,
    prepare: Callable[
        [tuple[Any, Any, Any]], tuple[bool, int, Any, tuple[int, ...] | None]
    ],
    export: Callable[[int, Any], Any],
) -> tuple[bool, Any, Failure | None, tuple[str, Exception, int | None] | None]: ...
def _quantity_duration_from(
    *,
    value: object,
    factor: int,
    namespace: dict[str, Any],
    builtins: dict[str, Any],
    prepare: Callable[[tuple[Any, int]], tuple[bool, bool, Any]],
) -> tuple[bool, Any, Failure | None, tuple[str, Exception] | None]: ...
def _quantity_to_timedelta(
    *,
    owner: object,
    namespace: dict[str, Any],
    builtins: dict[str, Any],
    prepare: Callable[
        [tuple[Any, Any, Any]], tuple[bool, int, Any, tuple[int, ...] | None]
    ],
    export: Callable[[Any], Any],
) -> tuple[bool, Any, Failure | None, tuple[str, Exception] | None]: ...
def _create_model(name: str) -> tuple[MetaModel | None, Failure | None]: ...

type _ActivityResource = tuple[str, Rational, _QuantityUnit, list[tuple[int, int]]]
type _ActivityMode = tuple[str, int, list[int], list[tuple[str, Rational]], Rational]
type _ActivityInput = tuple[str, list[_ActivityMode], Rational | None]
type _ActivityRow = tuple[
    str,
    _QuantityUnit,
    list[tuple[str, str, int, Rational]],
    list[tuple[str, Rational]],
    Rational | None,
    Rational | None,
]
type _ActivitySchedule = tuple[
    list[tuple[str, str, int, int]], tuple[int, int], list[str]
]
type _ActivitySolve = tuple[int, str, _ActivitySchedule | None, Failure | None]

def _solve_activity(
    *,
    horizon: tuple[int, int],
    resources: list[_ActivityResource],
    activities: list[_ActivityInput],
    dependencies: list[tuple[str, str, int]],
    rows: list[_ActivityRow],
    cost_unit: _QuantityUnit,
    max_work: int,
    solver: str,
    time_limit: float | None,
    cancellation: SolveHandle | None,
    on_progress: Callable[[SolveProgress], str | None] | None,
) -> tuple[_ActivitySolve | None, Failure | None]: ...
def _task_shadow_prices(
    *,
    task_count: int,
    dual_values: list[float],
    constraint_name_to_index: dict[str, int],
) -> tuple[dict[int, float] | None, Failure | None]: ...
def _task_improving_columns(
    *,
    columns: list[tuple[str, float, dict[str, float]]],
    dual_values: dict[str, float],
    tolerance: float,
) -> tuple[dict[str, bool] | None, Failure | None]: ...

type _TaskPricingColumn = tuple[int, int, float]
type _TaskPricingBatch = tuple[
    list[_TaskPricingColumn], str, bool, bool | None, int
]
type _TaskPricingLpReport = tuple[bool, bool, float | None, str, str]

def _create_task_pricing_algorithm(
    *, task_count: int, executor_count: int, max_iterations: int = 100
) -> tuple[TaskPricingAlgorithm | None, Failure | None]: ...

class TaskPricingAlgorithm:
    """GIL-affine unslotted task-executor pricing bridge."""

    def add_columns(
        self, columns: list[_TaskPricingColumn]
    ) -> tuple[list[_TaskPricingColumn] | None, Failure | None]: ...
    def add_priced_columns(
        self, columns: list[_TaskPricingColumn]
    ) -> tuple[list[_TaskPricingColumn] | None, Failure | None]: ...
    def solve_lp(
        self,
        *,
        solver: str,
        time_limit: float | None = None,
        cancellation: SolveHandle | None = None,
        on_progress: Callable[[SolveProgress], str | None] | None = None,
    ) -> tuple[_TaskPricingLpReport | None, Failure | None]: ...
    def generate(
        self, policy: Callable[[dict[str, Any]], dict[str, Any]]
    ) -> tuple[_TaskPricingBatch | None, Failure | None]: ...
    def certified_lower_bound(
        self,
    ) -> tuple[float | None, Failure | None]: ...
    def completion(self) -> str | None: ...

class _IntegerOps:
    """临时整数计算与外部协议派发，不持有用户值 / Temporary integer arithmetic and external dispatch, without retained user values."""

    def binary(self, *, left: object, right: object, operation: str) -> int: ...
    def facade(self, *, reference: object, domain: str) -> _IntegerFacade: ...
    def negated(self, value: object) -> int: ...
    def relation(self, *, left: object, right: object, operation: str) -> bool: ...
    def maximum(self, *, callable: object, left: object, right: object) -> int: ...
    def clamp(
        self,
        *,
        maximum: object,
        lower: object,
        minimum: object,
        upper: object,
        value: object,
    ) -> int: ...

_public_integer: _IntegerOps

_FloatingT = TypeVar("_FloatingT")
"""公开浮点构造器的结果类型。 / Public floating constructor result type."""

class _FloatingOps:
    """临时浮点计算和外部数值协议，不保存用户值。 / Temporary floating arithmetic and external protocols without retained user values."""

    def binary(
        self, *, owner: _FloatingT, other: object, operation: str
    ) -> _FloatingT: ...
    def negated(self, owner: _FloatingT) -> _FloatingT: ...
    def relation(self, *, left: object, right: object, operation: str) -> bool: ...

_public_floating: _FloatingOps

class _IntegerFacade:
    """保留命名空间身份的整数协议编排。 / Integer protocol composition with namespace identity."""

    def add(self, *, owner: _IntegerT, other: object) -> _IntegerT: ...
    def multiply(self, *, owner: _IntegerT, other: object) -> _IntegerT: ...
    def subtract(self, *, owner: _IntegerT, other: object) -> _IntegerT: ...
    def divide(self, *, owner: _IntegerT, other: object) -> _IntegerT: ...
    def negate(self, owner: _IntegerT) -> _IntegerT: ...
    def subtract_values(self, *, left: object, right: object) -> int: ...
    def unsigned_result(
        self, *, constructor: Callable[[int], _IntegerT], result: object
    ) -> _IntegerT: ...
    def bounded_add(self, *, owner: object, rhs: object) -> int: ...
    def bounded_multiply(self, *, owner: object, rhs: object) -> int: ...
    def clamp_owner(self, owner: object) -> int: ...
    def clamp_result(self, *, owner: object, value: object) -> int: ...
    def initialize(self, owner: object) -> None: ...
    def equal(self, *, left: object, right: object) -> bool: ...
    def not_equal(self, *, left: object, right: object) -> bool: ...
    def less(self, *, left: object, right: object) -> bool: ...
    def less_equal(self, *, left: object, right: object) -> bool: ...
    def greater(self, *, left: object, right: object) -> bool: ...
    def greater_equal(self, *, left: object, right: object) -> bool: ...

def _shape_size(owner: object, rank: int | None) -> int: ...
def _shape_strides(
    *, dims: object, storage_order: object, row_major: object
) -> tuple[int, ...]: ...
def _shape_flat_index(*, dims: object, strides: object, indices: object) -> int: ...
def _create_coordinate_plan(
    dims: list[int],
) -> tuple[CoordinatePlan | None, Failure | None]: ...

class CoordinatePlan:
    """临时坐标计划，不持有源或叶 / Temporary coordinate plan without source or leaf ownership."""

    def sample(self, owner: object) -> list[object]: ...
    def transpose_into(
        self, *, owner: object, strides: tuple[Any, ...], destination: object
    ) -> tuple[tuple[object, ...] | None, Failure | None]: ...
    def permutation(
        self, *, column_major: bool, indexer: object | None = None
    ) -> tuple[list[int] | None, Failure | None]: ...

def _map_shared_array(
    *, owner: object, scalar_type: type[Any], callback: object, flat: bool
) -> tuple[list[object] | None, Failure | None]: ...
def _reduce_shared_array(
    *, owner: object, scalar_type: type[Any], callback: object
) -> tuple[object | None, Failure | None]: ...
def _cross(
    inputs: tuple[Iterable[Any], ...],
) -> tuple[list[tuple[Any, ...]] | None, Failure | None]: ...
def _selection(
    *, items: object, k: object, permutations: bool
) -> tuple[list[list[Any]] | None, Failure | None]: ...
def _primes_up_to(*, limit: int) -> tuple[list[int] | None, Failure | None]: ...
def _pow_int(*, base: int, exponent: int) -> tuple[int | None, Failure | None]: ...
def _logistic_float64_step(
    *, rate: object, value: object
) -> tuple[float | None, Failure | None]: ...
def _chaotic_system_step(
    *,
    system: str,
    params: list[float] | tuple[float, ...],
    state: list[float] | tuple[float, ...],
) -> tuple[list[float] | None, Failure | None]: ...
def _minmax_pair(
    *,
    left: _IntegerT,
    right: _IntegerT,
    callable: object,
    minimum: bool,
    ops: _IntegerOps,
) -> _IntegerT: ...
def _ordinary_extreme(
    *, items: Iterable[_IntegerT], callable: object, minimum: bool, ops: _IntegerOps
) -> _IntegerT: ...
def _fractal_escape_time(
    z: complex,
    c: complex,
    max_iterations: int,
) -> tuple[int | None, Failure | None]: ...
def _iterate_shared_array(
    *, owner: object, scalar_type: type[Any], count: int
) -> SharedArrayIterator: ...
def _read_shared_array(
    *,
    data: object,
    count: int,
    offsets: list[int] | None = None,
    scalar_type: type[Any] | None = None,
) -> list[Any]: ...
def _nested_shared_array(
    *,
    owner: object,
    shape_types: tuple[type[Any], ...],
    row_major: object,
    column_major: object,
) -> tuple[Any | None, Failure | None]: ...

class _SharedNested:
    """仅保留嵌套导出协议配置的原生边界 / Native boundary retaining nested-export protocol configuration only."""

    def __init__(
        self,
        *,
        shape_types: tuple[type[Any], ...],
        row_major: object,
        column_major: object,
        success: object,
        failure: object,
    ) -> None: ...
    def to_list(self, owner: object) -> Any: ...

def _materialize_shared_view(
    *,
    owner: object,
    shape_types: tuple[type[Any], ...],
    row_major: object,
    column_major: object,
    make_shape: object,
    resolve: object,
) -> tuple[Any | None, Failure | None]: ...

class _SharedView:
    """仅保留协议配置的物化边界 / Materialization boundary retaining protocol configuration only."""

    def __init__(
        self,
        *,
        shape_types: tuple[type[Any], ...],
        row_major: object,
        column_major: object,
        success: object,
        failure: object,
    ) -> None: ...
    def materialize(
        self, owner: object, make_shape: object, resolve: object
    ) -> Any: ...

class SharedArrayIterator:
    """共享外部存储的原生协议游标，无元素镜像 / Native protocol cursor over shared external storage, without an element mirror."""

    def __iter__(self) -> SharedArrayIterator: ...
    def __next__(self) -> Any: ...
    def send(self, value: object) -> Any: ...
    def close(self) -> None: ...

def _create_rational(
    *, numerator: int, denominator: int
) -> tuple[Rational | None, Failure | None]: ...
def _public_rational_normalize(
    numerator: object, denominator: object
) -> tuple[int, int]: ...
@overload
def _public_rational_binary[R](
    *,
    left: tuple[int, int],
    right: tuple[int, int],
    operation: str,
    constructor: Callable[[int, int], R],
) -> R:
    """实际构造原生规范结果 / Construct the native canonical result through the callable."""
    ...

@overload
def _public_rational_binary(
    *,
    left: tuple[int, int],
    right: tuple[int, int],
    operation: str,
    constructor: None = None,
) -> tuple[int, int]:
    """仅返回规范整数对 / Return only the canonical integer pair."""
    ...

@overload
def _public_rational_negated[R](
    value: tuple[int, int], *, constructor: Callable[[int, int], R]
) -> R:
    """实际构造规范取负结果 / Construct the canonical negation through the callable."""
    ...

@overload
def _public_rational_negated(
    value: tuple[int, int], *, constructor: None = None
) -> tuple[int, int]:
    """仅返回规范取负整数对 / Return only the canonical negated integer pair."""
    ...

def _public_rational_less(left: tuple[int, int], right: tuple[int, int]) -> bool: ...
def _rational_from_json(text: str) -> tuple[Rational | None, Failure | None]: ...
def _create_quantity_unit(
    *,
    name: str,
    symbol: str,
    powers: list[int],
    scale: tuple[int, int],
    offset: tuple[int, int] | None = None,
) -> tuple[_QuantityUnit | None, Failure | None]: ...
def _quantity_unit_from_json(
    text: str,
) -> tuple[_QuantityUnit | None, Failure | None]: ...
def _restore_quantity_unit(text: str) -> _QuantityUnit: ...
def _restore_rational(text: str) -> Rational: ...
def _create_quantity_unit_encoded(
    *,
    name: str,
    symbol: str,
    powers: list[int],
    scale: int | float | tuple[int, int],
    offset: int | float | tuple[int, int] | None = None,
) -> tuple[_QuantityUnit | None, Failure | None]: ...

class _QuantityUnit:
    """固定 Rust 运行时单位，不持有 Python 载荷。 / Pinned runtime unit without Python payloads."""

    def __copy__(self) -> _QuantityUnit: ...
    def __deepcopy__(self, memo: dict[int, Any]) -> _QuantityUnit: ...
    def __reduce__(self) -> tuple[Callable[[str], _QuantityUnit], tuple[str]]: ...
    def same_dimension(self, other: _QuantityUnit) -> bool: ...
    def same_unit(self, other: _QuantityUnit) -> bool: ...
    def descriptor(
        self,
    ) -> tuple[str, str, list[int], tuple[int, int], tuple[int, int] | None]: ...
    def convert_exact(
        self, *, value: Rational, target: _QuantityUnit
    ) -> tuple[Rational | None, Failure | None]: ...
    def convert_float64(
        self, *, value: float, target: _QuantityUnit
    ) -> tuple[float | None, Failure | None]: ...
    def binary_exact(
        self,
        *,
        value: Rational,
        other: Rational,
        other_unit: _QuantityUnit,
        subtract: bool = False,
    ) -> tuple[tuple[Rational, _QuantityUnit] | None, Failure | None]: ...
    def binary_float64(
        self,
        *,
        value: float,
        other: float,
        other_unit: _QuantityUnit,
        subtract: bool = False,
    ) -> tuple[tuple[float, _QuantityUnit] | None, Failure | None]: ...
    def scalar_exact(
        self,
        *,
        value: Rational,
        scalar: Rational,
        divide: bool = False,
    ) -> tuple[tuple[Rational, _QuantityUnit] | None, Failure | None]: ...
    def scalar_float64(
        self,
        *,
        value: float,
        scalar: float,
        divide: bool = False,
    ) -> tuple[tuple[float, _QuantityUnit] | None, Failure | None]: ...
    def to_json(self) -> str: ...

def _create_rational_array(
    inputs: list[tuple[int, int]],
) -> tuple[RationalArray | None, Failure | None]: ...
def _create_shape(
    *, dims: list[int], column_major: bool
) -> tuple[Shape | None, Failure | None]: ...
def _checked_shared_offset(
    *, dims: tuple[int, ...], column_major: bool, indices: tuple[int, ...]
) -> tuple[tuple[int, int] | None, Failure | None]: ...

class _SharedAccess:
    """只持共享访问协议配置的原生边界 / Native boundary retaining shared-access protocol configuration only."""

    def __init__(
        self,
        *,
        shape_types: tuple[type[Any], ...],
        row_major: object,
        column_major: object,
        ndarray_type: type[Any],
        scalar_type: type[Any],
        success: object,
        failure: object,
    ) -> None: ...
    def read(
        self, *, owner: object, indices: object, standard_layout: object
    ) -> Any: ...
    def write(
        self,
        *,
        owner: object,
        indices: object,
        value: object,
        standard_layout: object,
    ) -> Any: ...

def _reshape_storage_shape(
    *, count: int, dims: tuple[int, ...]
) -> tuple[list[int] | None, Failure | None]: ...
def _flatten_storage_shape(count: int) -> tuple[list[int] | None, Failure | None]: ...
def _transform_storage(
    *,
    owner: object,
    target: object,
    flatten: bool,
    types: tuple[type[Any], object],
    resolve: object,
) -> tuple[Any | None, Failure | None]: ...

class _StorageTransform:
    def __init__(
        self, *, types: tuple[type[Any], object], success: object, failure: object
    ) -> None: ...
    def flatten(self, owner: object, resolve: object) -> Any: ...
    def flatten_value(self, owner: object, shape: object, resolve: object) -> Any: ...
    def flatten_value_result(
        self, owner: object, shape: object, resolve: object
    ) -> Any: ...
    def flatten_value_result_checked(
        self, owner: object, count: object, shape: object, resolve: object
    ) -> Any: ...
    def flatten_counted(
        self,
        owner: object,
        count: object,
        resolve: object,
        *,
        shape_resolve: object = None,
    ) -> Any: ...
    def reshape(
        self, *, owner: object, target: object, precopy: bool, resolve: object
    ) -> Any: ...

def _create_rational_multiarray(
    *, values: RationalArray, shape: Shape, column_major: bool
) -> tuple[RationalMultiArray | None, Failure | None]: ...
def _create_multiarray(
    *, values: list[Any], shape: Shape, column_major: bool
) -> tuple[MultiArray | None, Failure | None]: ...
def _create_mutable_multiarray(
    *, values: list[Any], shape: Shape, column_major: bool
) -> tuple[MutableMultiArray | None, Failure | None]: ...
def _full_multiarray(
    *, shape: Shape, value: Any
) -> tuple[MultiArray | None, Failure | None]: ...
def _full_mutable_multiarray(
    *, shape: Shape, value: Any
) -> tuple[MutableMultiArray | None, Failure | None]: ...
def _multiarray_from_nested(
    *, data: object, shape: Shape
) -> tuple[MultiArray | None, Failure | None]: ...
def _mutable_multiarray_from_nested(
    *, data: object, shape: Shape
) -> tuple[MutableMultiArray | None, Failure | None]: ...
def _compare_reference_arrays(
    *,
    left: MultiArray | MutableMultiArray,
    right: MultiArray | MutableMultiArray,
    callback: Callable[[Any], tuple[bool, Any]],
    left_region: MultiArrayView | None = None,
    right_region: MultiArrayView | None = None,
    builtin_equality: bool = False,
) -> tuple[bool | None, Failure | None]: ...
def _describe_reference_array(
    *,
    source: MultiArray | MutableMultiArray,
    callback: Callable[[Any], tuple[bool, Any]],
    max_items: int,
    max_chars: int,
    region: MultiArrayView | None = None,
) -> tuple[str | None, Failure | None]: ...
def _create_multiarray_view(
    *, source_shape: Shape, offsets: list[int] | None = None, shape: Shape | None = None
) -> tuple[MultiArrayView | None, Failure | None]: ...
def _create_reference_iterator(
    *,
    source: MultiArray | MutableMultiArray,
    owner: object,
    column_major: bool | None = None,
    region: MultiArrayView | None = None,
) -> tuple[MultiArrayIterator | None, Failure | None]: ...
def _unpickle_shape(metadata: tuple[int, list[int], bool]) -> Shape: ...
def _unpickle_multiarray(metadata: tuple[int, list[int], bool]) -> MultiArray: ...
def _unpickle_mutable_multiarray(
    metadata: tuple[int, list[int], bool],
) -> MutableMultiArray: ...
def _unpickle_multiarray_view(
    metadata: tuple[int, list[int], bool, list[int], list[int]],
) -> MultiArrayView: ...

class MultiArrayIterator:
    """原生源保活、逐次读取的游标 / Cursor retaining its native source and reading per advance."""

    def __iter__(self) -> MultiArrayIterator: ...
    def __next__(self) -> Any: ...
    def __length_hint__(self) -> int: ...
    def advance(self) -> tuple[tuple[bool, Any] | None, Failure | None]: ...
    def close(self) -> None: ...

class MultiArrayView:
    """无元素缓冲的受检区域描述 / Checked region descriptor without an element buffer."""

    @property
    def shape(self) -> Shape: ...
    def subview(
        self, offsets: list[int] | None = None, shape: Shape | None = None
    ) -> tuple[MultiArrayView | None, Failure | None]: ...

class MutableMultiArray:
    """GC 可见的单一可变 Rust 存储 / Single mutable Rust storage visible to GC."""

    @property
    def shape(self) -> Shape: ...
    def __reduce__(self) -> tuple[Any, ...]: ...
    def __setstate__(self, state: object) -> None: ...
    def at(self, indices: list[int]) -> tuple[Any, Failure | None]: ...
    def reduced(
        self,
        *,
        callback: Callable[[Any], tuple[bool, Any]],
        column_major: bool,
        region: MultiArrayView | None = None,
    ) -> tuple[Any, Failure | None]: ...
    def to_list(
        self, *, region: MultiArrayView | None = None
    ) -> tuple[Any, Failure | None]: ...
    def mapped_at(
        self,
        *,
        indices: list[int],
        callback: Callable[[Any], tuple[bool, Any]],
        region: MultiArrayView | None = None,
    ) -> tuple[Any, Failure | None]: ...
    def flatten(
        self, column_major: bool
    ) -> tuple[list[Any] | None, Failure | None]: ...
    def set_many(
        self, updates: list[tuple[list[int], Any]]
    ) -> tuple[None, Failure | None]: ...
    def to_immutable(self) -> tuple[MultiArray | None, Failure | None]: ...
    def transpose(self) -> tuple[MultiArray | None, Failure | None]: ...
    def mapped(
        self,
        *,
        callback: Callable[[Any], tuple[bool, Any]],
        column_major: bool,
        output_shape: Shape | None = None,
    ) -> tuple[MultiArray | None, Failure | None]: ...
    def region_at(
        self, region: MultiArrayView, indices: list[int]
    ) -> tuple[Any, Failure | None]: ...
    def region_flatten(
        self, region: MultiArrayView, column_major: bool
    ) -> tuple[list[Any] | None, Failure | None]: ...
    def region_materialize(
        self, region: MultiArrayView
    ) -> tuple[MultiArray | None, Failure | None]: ...
    def region_transpose(
        self, region: MultiArrayView
    ) -> tuple[MultiArray | None, Failure | None]: ...
    def region_mapped(
        self,
        *,
        region: MultiArrayView,
        callback: Callable[[Any], tuple[bool, Any]],
        column_major: bool,
        output_shape: Shape | None = None,
    ) -> tuple[MultiArray | None, Failure | None]: ...
    def region_set_many(
        self, region: MultiArrayView, updates: list[tuple[list[int], Any]]
    ) -> tuple[None, Failure | None]: ...

class MultiArray:
    """Rust 持有 Python 元素强引用的数组 / Rust-owned array of strong Python references."""

    @property
    def shape(self) -> Shape: ...
    def __reduce__(self) -> tuple[Any, ...]: ...
    def __setstate__(self, state: object) -> None: ...
    def at(self, indices: list[int]) -> tuple[Any, Failure | None]: ...
    def at_many(
        self, indices: list[list[int]]
    ) -> tuple[list[Any] | None, Failure | None]:
        """按完整坐标批量读取，允许重复坐标 / Batch read by complete coordinates; repeats allowed."""
        ...
    def get(self, indices: list[int]) -> tuple[Any, Failure | None]:
        """旧 `get` 的绑定侧等价物 / Binding-side equivalent of the legacy `get`."""
        ...
    def reduced(
        self,
        *,
        callback: Callable[[Any], tuple[bool, Any]],
        column_major: bool,
        region: MultiArrayView | None = None,
    ) -> tuple[Any, Failure | None]: ...
    def to_list(
        self, *, region: MultiArrayView | None = None
    ) -> tuple[Any, Failure | None]: ...
    def mapped_at(
        self,
        *,
        indices: list[int],
        callback: Callable[[Any], tuple[bool, Any]],
        region: MultiArrayView | None = None,
    ) -> tuple[Any, Failure | None]: ...
    def flatten(
        self, column_major: bool
    ) -> tuple[list[Any] | None, Failure | None]: ...
    def to_storage_order(
        self, column_major: bool
    ) -> tuple[MultiArray | None, Failure | None]: ...
    def reshape(self, shape: Shape) -> tuple[MultiArray | None, Failure | None]: ...
    def transpose(self) -> tuple[MultiArray | None, Failure | None]: ...
    def mapped(
        self,
        *,
        callback: Callable[[Any], tuple[bool, Any]],
        column_major: bool,
        output_shape: Shape | None = None,
    ) -> tuple[MultiArray | None, Failure | None]: ...
    def region_at(
        self, region: MultiArrayView, indices: list[int]
    ) -> tuple[Any, Failure | None]: ...
    def region_flatten(
        self, region: MultiArrayView, column_major: bool
    ) -> tuple[list[Any] | None, Failure | None]: ...
    def region_materialize(
        self, region: MultiArrayView
    ) -> tuple[MultiArray | None, Failure | None]: ...
    def region_transpose(
        self, region: MultiArrayView
    ) -> tuple[MultiArray | None, Failure | None]: ...
    def region_mapped(
        self,
        *,
        region: MultiArrayView,
        callback: Callable[[Any], tuple[bool, Any]],
        column_major: bool,
        output_shape: Shape | None = None,
    ) -> tuple[MultiArray | None, Failure | None]: ...

class Shape:
    """不可变 Rust 动态形状 / Immutable Rust dynamic shape."""

    @property
    def dims(self) -> list[int]: ...
    @property
    def size(self) -> int: ...
    @property
    def column_major(self) -> bool: ...
    def strides(self) -> list[int]: ...
    def index_of(self, indices: list[int]) -> tuple[int | None, Failure | None]: ...
    def vector_of(self, index: int) -> tuple[list[int] | None, Failure | None]: ...
    def indices_of(
        self, vectors: list[list[int]]
    ) -> tuple[list[int] | None, Failure | None]: ...

class RationalMultiArray:
    """不可变 Rust 精确多维数组 / Immutable Rust exact multiarray."""

    @property
    def shape(self) -> Shape: ...
    def at(self, indices: list[int]) -> tuple[Rational | None, Failure | None]: ...
    def flatten(self, column_major: bool) -> RationalArray: ...
    def to_storage_order(self, column_major: bool) -> RationalMultiArray: ...
    def reshape(
        self, shape: Shape
    ) -> tuple[RationalMultiArray | None, Failure | None]: ...

class RationalArray:
    """不可变 Rust 一维精确批量值 / Immutable Rust one-dimensional exact batch."""

    def __len__(self) -> int: ...
    def as_integer_ratios(self) -> list[tuple[int, int]]: ...
    def at(self, index: int) -> tuple[Rational | None, Failure | None]: ...
    def sum(self) -> Rational: ...
    def dot(self, other: RationalArray) -> tuple[Rational | None, Failure | None]: ...
    def add(
        self, other: RationalArray
    ) -> tuple[RationalArray | None, Failure | None]: ...
    def subtract(
        self, other: RationalArray
    ) -> tuple[RationalArray | None, Failure | None]: ...
    def multiply(
        self, other: RationalArray
    ) -> tuple[RationalArray | None, Failure | None]: ...
    def divide(
        self, other: RationalArray
    ) -> tuple[RationalArray | None, Failure | None]: ...

class Rational:
    """由 Rust 持有的任意精度有理数 / Rust-owned arbitrary-precision rational."""

    def __copy__(self) -> Rational: ...
    def __deepcopy__(self, memo: dict[int, Any]) -> Rational: ...
    def __reduce__(self) -> tuple[Callable[[str], Rational], tuple[str]]: ...
    def as_integer_ratio(self) -> tuple[int, int]: ...
    def add(self, other: Rational) -> Rational: ...
    def subtract(self, other: Rational) -> Rational: ...
    def multiply(self, other: Rational) -> Rational: ...
    def divide(self, other: Rational) -> tuple[Rational | None, Failure | None]: ...
    def negated(self) -> Rational: ...
    def reciprocal(self) -> tuple[Rational | None, Failure | None]: ...
    def compare(self, other: Rational) -> int: ...
    def to_float(
        self, *, exact: bool = True
    ) -> tuple[float | None, Failure | None]: ...
    def to_json(self) -> str: ...

class Failure:
    """不可变结构错误 / Immutable structured failure."""

    @property
    def category(self) -> str: ...
    @property
    def source(self) -> str: ...
    @property
    def rust_code(self) -> int | None: ...
    @property
    def error_class(self) -> str: ...
    @property
    def message(self) -> str: ...

type _Bpp1dRatio = tuple[int, int]
"""规范化分子及正分母。 / Normalized numerator and positive denominator."""
type _Bpp1dPattern = tuple[str, dict[str, int]]
"""箱型身份及逐物品件数。 / Bin-type identity and item counts."""
type _Bpp1dReference = tuple[int, tuple[int, int] | None, str | None]
"""模型内候选或辅助身份。 / Model-local candidate or auxiliary identity."""
type _Bpp1dTerm = tuple[_Bpp1dReference, _Bpp1dRatio]
"""变量身份与精确系数。 / Variable identity and exact coefficient."""
type _Bpp1dVariable = tuple[str, str, _Bpp1dRatio | None, _Bpp1dRatio | None]
"""辅助变量名称、类型和范围。 / Auxiliary name, type and bounds."""
type _Bpp1dRow = tuple[str, list[_Bpp1dTerm], str, _Bpp1dRatio]
"""精确线性约束。 / Exact linear constraint."""
type _Bpp1dRegistration = tuple[
    list[_Bpp1dVariable], list[_Bpp1dRow], list[_Bpp1dTerm], _Bpp1dRatio
]
"""声明式模型扩展。 / Declarative model extension."""
type _Bpp1dRegistrationSnapshot = tuple[
    int,
    str,
    list[tuple[str, _Bpp1dRatio, _Bpp1dRatio, int, dict[str, int]]],
    list[tuple[str, _Bpp1dRatio, _Bpp1dRatio, _Bpp1dRatio, int | None]],
    _Bpp1dRatio,
    _QuantityUnit,
    _QuantityUnit,
    str,
    list[tuple[_Bpp1dReference, _Bpp1dPattern]],
]
"""独立领域及候选快照。 / Detached domain and candidate snapshot."""
type _Bpp1dExtractionSnapshot = tuple[
    list[tuple[str, _Bpp1dRatio, _Bpp1dRatio, int, dict[str, int]]],
    list[tuple[str, _Bpp1dRatio, _Bpp1dRatio, _Bpp1dRatio, int | None]],
    _Bpp1dRatio,
    _QuantityUnit,
    _QuantityUnit,
    str,
    list[tuple[_Bpp1dReference, _Bpp1dPattern | None, _Bpp1dRatio]],
]
"""复核后的领域、候选及变量值。 / Validated domain, candidate and variable values."""
type _Bpp1dExtension = tuple[
    Callable[[_Bpp1dRegistrationSnapshot], _Bpp1dRegistration | None],
    Callable[[_Bpp1dExtractionSnapshot], dict[str, str] | None],
]
"""单次注册和指标回调。 / Per-operation registration and indicator callbacks."""
type _Bpp1dColumn = tuple[_Bpp1dReference, tuple[int, int], _Bpp1dPattern | None]
"""编译列及源变量身份。 / Compiled column and source-variable identity."""
type _Bpp1dPoolInfo = tuple[int, int, list[_Bpp1dPattern], list[_Bpp1dColumn]]
"""列池代次、来源模型、组合及编译列。 / Pool generation, source model, patterns and compiled columns."""
type _Bpp1dPacked = tuple[
    list[tuple[str, str, list[tuple[str, _Bpp1dRatio, _Bpp1dRatio]]]],
    list[tuple[str, _Bpp1dRatio, _Bpp1dRatio]],
    dict[str, int],
    _Bpp1dRatio,
    _Bpp1dRatio,
    _Bpp1dRatio,
]
"""放置、空闲区间、物料、总箱长、净长度和原域目标。 / Placements, free intervals, materials, total and net lengths, and native-domain objective."""
type _Bpp1dVerifiedSolution = tuple[
    list[tuple[str, dict[str, int], int]], _Bpp1dPacked, _Bpp1dRatio, dict[str, str]
]
"""原域复核的用量、放置、目标和指标。 / Validated usages, placements, objective and indicators."""
type _Bpp1dFinalSolve = tuple[
    int, str, list[_Bpp1dColumn], _Bpp1dVerifiedSolution | None, Failure | None
]
"""最终模型身份、报告、列及复核。 / Final-model identity, report, columns and validation."""

def _create_bpp1d_context(
    *,
    items: list[tuple[str, Rational, Rational, int, dict[str, int]]],
    bins: list[tuple[str, Rational, Rational, Rational, int | None]],
    spacing: Rational,
    length_unit: _QuantityUnit,
    weight_unit: _QuantityUnit,
    objective: str,
) -> tuple[Bpp1dContext | None, Failure | None]: ...

class Bpp1dContext:
    """Rust 精确领域上下文及有限候选求解。 / Exact Rust domain context and bounded-candidate solve."""

    def generate_patterns(
        self,
        *,
        max_patterns: int,
        max_nodes: int,
        policy: Callable[[_Bpp1dPattern], bool | None] | None = None,
    ) -> tuple[tuple[list[_Bpp1dPattern], bool, int] | None, Failure | None]: ...
    def validate_pattern(
        self, *, bin_type_id: str, amounts: dict[str, int]
    ) -> tuple[None, Failure | None]: ...
    def pack(
        self, *, usages: list[tuple[str, dict[str, int], int]], expansion_limit: int
    ) -> tuple[_Bpp1dPacked | None, Failure | None]: ...
    def column_pool(
        self,
        *,
        patterns: list[_Bpp1dPattern],
        extension: _Bpp1dExtension | None = None,
    ) -> tuple[Bpp1dPool | None, Failure | None]: ...
    def solve(
        self,
        *,
        solver: str,
        max_patterns: int,
        max_nodes: int,
        expansion_limit: int,
        time_limit: float | None = None,
        cancellation: SolveHandle | None = None,
        on_progress: Callable[[SolveProgress], str | None] | None = None,
        policy: Callable[[_Bpp1dPattern], bool | None] | None = None,
        extension: _Bpp1dExtension | None = None,
    ) -> tuple[
        tuple[
            int,
            str,
            list[_Bpp1dPattern],
            list[_Bpp1dColumn],
            bool,
            int,
            _Bpp1dVerifiedSolution | None,
            Failure | None,
        ]
        | None,
        Failure | None,
    ]: ...

class Bpp1dPool:
    """已发布的精确 LP 快照列池。 / Published exact LP snapshot pool."""

    def snapshot(self) -> tuple[_Bpp1dPoolInfo | None, Failure | None]: ...
    def add_columns(
        self,
        *,
        patterns: list[_Bpp1dPattern],
        extension: _Bpp1dExtension | None = None,
    ) -> tuple[_Bpp1dPoolInfo | None, Failure | None]: ...
    def remove_columns(
        self,
        *,
        patterns: list[_Bpp1dPattern],
        extension: _Bpp1dExtension | None = None,
    ) -> tuple[_Bpp1dPoolInfo | None, Failure | None]: ...
    def close(self) -> tuple[None, Failure | None]: ...
    def solve_lp(
        self,
        *,
        solver: str,
        time_limit: float | None = None,
        cancellation: SolveHandle | None = None,
        on_progress: Callable[[SolveProgress], str | None] | None = None,
    ) -> tuple[
        tuple[
            int,
            int,
            str,
            list[_Bpp1dColumn],
            tuple[list[tuple[_Bpp1dReference, _Bpp1dRatio]], _Bpp1dRatio] | None,
            Failure | None,
        ]
        | None,
        Failure | None,
    ]: ...
    def solve_final_milp(
        self,
        *,
        solver: str,
        expansion_limit: int,
        time_limit: float | None = None,
        cancellation: SolveHandle | None = None,
        on_progress: Callable[[SolveProgress], str | None] | None = None,
        extension: _Bpp1dExtension | None = None,
    ) -> tuple[tuple[int, _Bpp1dFinalSolve] | None, Failure | None]: ...

class VariableHandle:
    """不可变变量句柄，隐含所有者身份 / Immutable variable handle with private owner provenance."""

    @property
    def model_identity(self) -> int: ...
    @property
    def index(self) -> int: ...
    @property
    def variable_identity(self) -> tuple[int, int]: ...

class ConstraintHandle:
    """原约束的不可变模型内身份 / Immutable model-local source-constraint identity."""

    @property
    def model_identity(self) -> int: ...
    @property
    def source_identity(self) -> str: ...
    @property
    def name(self) -> str: ...
    @property
    def relation(self) -> str: ...

class DualCertificate:
    """不可构造的同次求解来源凭据 / Nonconstructible provenance for one solve."""

class ColumnPricingRequest:
    """不可构造且绑定投影和对偶代次的请求 / Nonconstructible projection- and dual-epoch-bound request."""

class ColumnPricingBound:
    """不可构造的后端界观察，不是证明 / Nonconstructible backend-bound observation, not a proof."""

class ColumnProjectionSolution:
    """不可构造且绑定整数主问题的源解 / Nonconstructible source solution bound to an integer master."""

class ColumnProjection:
    """源模型所有者线程上的私有投影 / Private projection on the source owner thread."""

    def close(self) -> tuple[None, Failure | None]: ...
    def columns(
        self,
    ) -> tuple[list[tuple[str, str, dict[str, float]]] | None, Failure | None]: ...
    def add_columns(
        self, inputs: list[tuple[str, str, dict[str, float]]]
    ) -> tuple[None, Failure | None]: ...
    def remove_columns(self, ids: list[str]) -> tuple[None, Failure | None]: ...
    def build_master(
        self, *, integer: bool = False, phase_one: bool = False
    ) -> tuple[tuple[int, bool, int, int, int, bool] | None, Failure | None]: ...
    def master_info(
        self,
    ) -> tuple[tuple[int, bool, int, int, int, bool] | None, Failure | None]: ...
    def solve_master_lp(
        self,
        *,
        solver: str,
        time_limit: float | None = None,
        cancellation: SolveHandle | None = None,
        on_progress: Callable[[SolveProgress], str | None] | None = None,
    ) -> tuple[tuple[int, int, str, Failure | None] | None, Failure | None]: ...
    def pricing_request(
        self, *, block: str
    ) -> tuple[ColumnPricingRequest | None, Failure | None]: ...
    def pricing_info(
        self, *, request: ColumnPricingRequest
    ) -> tuple[
        tuple[str, dict[str, float], float, dict[str, float]] | None, Failure | None
    ]: ...
    def reduced_cost(
        self, *, request: ColumnPricingRequest, values: dict[str, float]
    ) -> tuple[float | None, Failure | None]: ...
    def pricing_bound_info(
        self, *, bound: ColumnPricingBound
    ) -> tuple[tuple[str, float, float, bool] | None, Failure | None]: ...
    def solve_pricing(
        self,
        *,
        request: ColumnPricingRequest,
        solver: str,
        time_limit: float | None = None,
        cancellation: SolveHandle | None = None,
        on_progress: Callable[[SolveProgress], str | None] | None = None,
        tolerance: float = 1e-7,
    ) -> tuple[
        tuple[
            int,
            int,
            str,
            tuple[dict[str, float], float] | None,
            Failure | None,
            ColumnPricingBound | None,
            Failure | None,
        ]
        | None,
        Failure | None,
    ]: ...
    def add_priced_batch(
        self,
        batches: list[
            tuple[ColumnPricingRequest, list[tuple[str, str, dict[str, float]]]]
        ],
    ) -> tuple[None, Failure | None]: ...
    def solve_master_integer(
        self,
        *,
        solver: str,
        time_limit: float | None = None,
        cancellation: SolveHandle | None = None,
        on_progress: Callable[[SolveProgress], str | None] | None = None,
        tolerance: float = 1e-7,
    ) -> tuple[
        tuple[int, int, str, ColumnProjectionSolution | None, Failure | None] | None,
        Failure | None,
    ]: ...
    def solution_value(
        self, *, solution: ColumnProjectionSolution, handle: VariableHandle
    ) -> tuple[float | None, Failure | None]: ...

class MetaModel:
    """仅由 Rust 持有状态的私有模型 / Private model with Rust-owned state only."""

    @property
    def model_identity(self) -> int: ...
    def snapshot(self) -> tuple[tuple[int, str, int, int] | None, Failure | None]: ...
    def generation(self) -> tuple[int | None, Failure | None]: ...
    def to_linear_triad(
        self,
    ) -> tuple[
        tuple[
            str,
            list[tuple[str, str, float | None, float | None]],
            list[
                tuple[
                    str,
                    str,
                    dict[str, float],
                    float,
                    str,
                ]
            ],
            dict[str, float],
            str,
            float,
        ]
        | None,
        Failure | None,
    ]: ...
    def constraint_handles(
        self,
    ) -> tuple[list[ConstraintHandle] | None, Failure | None]: ...
    def constraint_index(
        self, *, handle: ConstraintHandle
    ) -> tuple[int | None, Failure | None]: ...
    def close(self) -> tuple[None, Failure | None]: ...
    def create_projection(
        self,
        *,
        decisions: list[tuple[str, str, VariableHandle]],
        blocks: list[str],
    ) -> tuple[ColumnProjection | None, Failure | None]: ...
    def add_variables(
        self, inputs: list[tuple[str, str, float | None, float | None]]
    ) -> tuple[list[VariableHandle] | None, Failure | None]: ...
    def add_constraints(
        self,
        inputs: list[tuple[str, list[tuple[VariableHandle, float]], str, float]],
    ) -> tuple[None, Failure | None]: ...
    def set_bounds(
        self,
        *,
        handle: VariableHandle,
        lower: float | None,
        upper: float | None,
    ) -> tuple[None, Failure | None]: ...
    def set_objective(
        self,
        *,
        terms: list[tuple[VariableHandle, float]],
        sense: str,
        name: str = "objective",
        constant: float = 0.0,
    ) -> tuple[None, Failure | None]: ...
    def solve(
        self,
        *,
        solver: str,
        time_limit: float | None = None,
        cancellation: SolveHandle | None = None,
        on_progress: Callable[[SolveProgress], str | None] | None = None,
    ) -> tuple[tuple[int, str] | None, Failure | None]: ...
    def solve_compiled(
        self,
        *,
        solver: str,
        time_limit: float | None = None,
        cancellation: SolveHandle | None = None,
        on_progress: Callable[[SolveProgress], str | None] | None = None,
    ) -> tuple[
        tuple[int, str, DualCertificate | None, Failure | None] | None, Failure | None
    ]: ...
    def solve_relaxed_compiled(
        self,
        *,
        solver: str,
        time_limit: float | None = None,
        cancellation: SolveHandle | None = None,
        on_progress: Callable[[SolveProgress], str | None] | None = None,
    ) -> tuple[
        tuple[int, str, DualCertificate | None, Failure | None] | None, Failure | None
    ]: ...
    def source_price(
        self, *, certificate: DualCertificate, handle: ConstraintHandle
    ) -> tuple[float | None, Failure | None]: ...

class SolveHandle:
    """单次 attempt 的 Rust 取消句柄 / Rust cancellation handle for one attempt."""

    def __init__(self) -> None: ...
    @property
    def phase(self) -> str: ...
    @property
    def is_cancelled(self) -> bool: ...
    @property
    def completed_at_epoch_ms(self) -> int | None: ...
    @property
    def cancellation_preceded_completion(self) -> bool: ...
    def cancellation(self) -> CancellationRecord | None: ...
    def cancel(
        self, *, origin: str = "user", reason: str | None = None
    ) -> tuple[bool | None, Failure | None]: ...

class CancellationRecord:
    """首次取消事实的只读快照 / Read-only snapshot of the first cancellation fact."""

    @property
    def origin(self) -> str: ...
    @property
    def requested_at_epoch_ms(self) -> int: ...
    @property
    def reason(self) -> str | None: ...

class SolveProgress:
    """只读且脱离模型的快照，容器 getter 返回副本 / Read-only detached snapshot with copied container getters."""

    @property
    def model_identity(self) -> int: ...
    @property
    def attempt_identity(self) -> int: ...
    @property
    def native_attempt_id(self) -> str | None: ...
    @property
    def source(self) -> str: ...
    @property
    def stage(self) -> str: ...
    @property
    def stage_path(self) -> list[str]: ...
    @property
    def stage_progress(self) -> float | None: ...
    @property
    def overall_progress(self) -> float | None: ...
    @property
    def elapsed_nanoseconds(self) -> int: ...
    @property
    def objective_value(self) -> float | None: ...
    @property
    def best_bound(self) -> float | None: ...
    @property
    def relative_gap(self) -> float | None: ...
    @property
    def terminal(self) -> bool: ...
    @property
    def initial_objective_value(self) -> float | None: ...
    @property
    def incumbent_solution(self) -> list[float] | None: ...
    @property
    def objective_direction(self) -> str | None: ...
    @property
    def iterations(self) -> int | None: ...
    @property
    def node_count(self) -> int | None: ...

def _trivalent(
    *, operation: str, left: bool | None, right: bool | None
) -> tuple[bool | None, Failure | None]: ...
def _log_base(*, x: object, base: object) -> tuple[float | None, Failure | None]: ...
def _elementary_operator(
    operation: str, value: object
) -> tuple[float | None, Failure | None]: ...
