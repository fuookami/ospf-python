"""固定 Rust BPP1D 的私有精确领域上下文和有限候选求解。

Private exact BPP1D domain context and bounded-candidate solve backed by pinned Rust.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from contextvars import ContextVar
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any, cast

from ospf_python import _native
from ospf_python._binding.model import SolveReport, _invoke_solve, _report
from ospf_python._binding.numeric import Rational
from ospf_python._binding.quantities import Unit
from ospf_python._binding.result import BindingResult, invalid, invoke
from ospf_python.utils.error.error import ExErr
from ospf_python.utils.functional.result import Failed, Ok, Result

if TYPE_CHECKING:
    from ospf_python._binding.control import ProgressCallback, SolveHandle

type Ratio = tuple[int, int]
"""规范化的精确分数 / Normalized exact fraction."""
type Pattern = tuple[str, dict[str, int]]
"""箱型身份及物品件数快照 / Bin-type identity and item-count snapshot."""
type PatternPolicy = Callable[[Pattern], bool | Result[bool, Any, Any]]
"""候选接受策略 / Candidate acceptance policy."""
type Packed = tuple[
    list[tuple[str, str, list[tuple[str, Ratio, Ratio]]]],
    list[tuple[str, Ratio, Ratio]],
    dict[str, int],
    Ratio,
    Ratio,
    Ratio,
]
"""放置、空闲区间、物料、总箱长、净长度、目标 / Placements, free intervals, materials, total length, net length and objective."""
type Usage = tuple[str, dict[str, int], int]
"""箱型、组合件数及使用次数 / Bin type, pattern counts and usage count."""


@dataclass(frozen=True, kw_only=True)
class VariableRef:
    """仅在单次模型注册内有效的变量身份 / Variable identity valid only within one model registration.

    Attributes:
        model_identity: 来源模型 / Originating model.
        variable_identity: 候选变量的原生身份 / Native candidate identity.
        auxiliary: 此次注册声明的辅助变量名 / Auxiliary name declared in this registration.
    """

    model_identity: int
    variable_identity: tuple[int, int] | None = None
    auxiliary: str | None = None


@dataclass(frozen=True, kw_only=True)
class PatternRegistration:
    """独立领域及候选快照，不持有模型 / Detached domain and candidate snapshot, without a model.

    Attributes:
        model_identity: 此次注册的模型身份 / This registration's model identity.
        stage: milp、lp 或 final_milp / Registration stage.
        items: 物品的精确数值及物料 / Items with exact values and materials.
        bins: 箱型的精确数值及库存 / Bins with exact values and inventory.
        spacing: 声明长度单位的间距 / Gap in the declared length unit.
        length_unit: 长度单位的独立句柄 / Independent length-unit handle.
        weight_unit: 重量单位的独立句柄 / Independent weight-unit handle.
        objective: 基础装箱目标 / Base packing objective.
        candidates: 模型内身份及候选快照 / Model-local identities and candidate snapshots.
    """

    model_identity: int
    stage: str
    items: list[tuple[str, Ratio, Ratio, int, dict[str, int]]]
    bins: list[tuple[str, Ratio, Ratio, Ratio, int | None]]
    spacing: Ratio
    length_unit: Unit
    weight_unit: Unit
    objective: str
    candidates: list[tuple[VariableRef, Pattern]]

    def auxiliary(self, name: str) -> VariableRef:
        """引用此次声明的辅助变量 / Reference an auxiliary declared in this registration.

        Args:
            name: 辅助变量名 / Auxiliary variable name.

        Returns:
            模型内身份 / Model-local identity.
        """
        return VariableRef(model_identity=self.model_identity, auxiliary=name)


@dataclass(frozen=True, kw_only=True)
class AuxiliaryVariable:
    """辅助变量声明 / Auxiliary variable declaration.

    Attributes:
        name: 此次注册内唯一的名称 / Name unique within this registration.
        kind: continuous、integer 或 binary / Variable kind.
        lower: 精确下界，None 表示无显式界 / Exact lower bound or no explicit bound.
        upper: 精确上界，None 表示无显式界 / Exact upper bound or no explicit bound.
    """

    name: str
    kind: str = "continuous"
    lower: Ratio | None = None
    upper: Ratio | None = None


@dataclass(frozen=True, kw_only=True)
class ExtensionConstraint:
    """精确线性约束声明 / Exact linear constraint declaration.

    Attributes:
        name: 此次扩展中唯一的名称 / Name unique within this extension.
        terms: 模型内身份和精确系数 / Model-local identities and exact coefficients.
        relation: <=、>= 或 == / Constraint relation.
        rhs: 精确右端值 / Exact right-hand side.
    """

    name: str
    terms: list[tuple[VariableRef, Ratio]]
    relation: str
    rhs: Ratio


@dataclass(frozen=True, kw_only=True)
class PatternExtensionSpec:
    """待追加的精确线性模型数据 / Exact linear model data to append.

    Attributes:
        variables: 辅助变量 / Auxiliary variables.
        constraints: 线性约束 / Linear constraints.
        objective: 追加到最小化目标的变量项 / Terms added to the minimizing objective.
        objective_constant: 目标常数，目前非零会被拒绝 / Objective constant, currently rejected if nonzero.
    """

    variables: list[AuxiliaryVariable] = field(default_factory=list)
    constraints: list[ExtensionConstraint] = field(default_factory=list)
    objective: list[tuple[VariableRef, Ratio]] = field(default_factory=list)
    objective_constant: Ratio = (0, 1)


@dataclass(frozen=True, kw_only=True)
class PatternExtraction:
    """完整源模型复核后的独立快照 / Detached snapshot after complete-source validation.

    Attributes:
        items: 物品的精确数值及物料 / Items with exact values and materials.
        bins: 箱型的精确数值及库存 / Bins with exact values and inventory.
        spacing: 声明长度单位的间距 / Gap in the declared length unit.
        length_unit: 长度单位的独立句柄 / Independent length-unit handle.
        weight_unit: 重量单位的独立句柄 / Independent weight-unit handle.
        objective: 基础装箱目标 / Base packing objective.
        candidates: 模型内身份及候选快照 / Model-local identities and candidate snapshots.
        values: 所有候选和辅助变量的精确值 / Exact values of all candidates and auxiliaries.
    """

    items: list[tuple[str, Ratio, Ratio, int, dict[str, int]]]
    bins: list[tuple[str, Ratio, Ratio, Ratio, int | None]]
    spacing: Ratio
    length_unit: Unit
    weight_unit: Unit
    objective: str
    candidates: list[tuple[VariableRef, Pattern]]
    values: dict[VariableRef, Ratio]


@dataclass(frozen=True, kw_only=True)
class PatternExtension:
    """无模型句柄的注册和指标回调 / Registration and indicator callbacks without model handles.

    Attributes:
        register: 以领域及候选快照生成声明 / Produce declarations from a domain and candidate snapshot.
        extract_solution: 完整源模型验证后的领域、候选及数值快照到字符串指标 / Domain, candidate and value snapshots to string indicators after full-source validation.
    """

    register: Callable[
        [PatternRegistration],
        PatternExtensionSpec | Result[PatternExtensionSpec, Any, Any],
    ]
    extract_solution: (
        Callable[
            [PatternExtraction],
            dict[str, str] | Result[dict[str, str], Any, Any],
        ]
        | None
    ) = None


@dataclass(frozen=True, kw_only=True)
class CompiledColumn:
    """报告解向量中的真实编译列 / Actual compiled column in the report solution vector.

    Attributes:
        reference: 模型内候选或辅助变量身份 / Model-local candidate or auxiliary reference.
        variable_identity: 上游原变量身份 / Upstream source-variable identity.
        pattern: 候选快照；辅助列为 None / Candidate snapshot, or None for auxiliaries.
    """

    reference: VariableRef
    variable_identity: tuple[int, int]
    pattern: Pattern | None


@dataclass(frozen=True, kw_only=True)
class PatternPoolSnapshot:
    """已发布列池的独立快照 / Detached snapshot of a published pattern pool.

    Attributes:
        generation: 列池代次 / Pool generation.
        model_identity: 精确 LP 快照的来源身份 / Origin identity of the exact LP snapshot.
        patterns: 完整候选池 / Complete candidate pool.
        compiled_columns: 编译顺序的候选及辅助列 / Candidate and auxiliary columns in compiled order.
    """

    generation: int
    model_identity: int
    patterns: list[Pattern]
    compiled_columns: list[CompiledColumn]


@dataclass(frozen=True, kw_only=True)
class PackingLpSolution:
    """按精确源快照零容差复核的 LP 解 / LP solution checked against the exact source snapshot with zero tolerance.

    Attributes:
        values: 全部候选及辅助变量的精确二进制值 / Exact binary values for all candidate and auxiliary variables.
        model_objective: 以原域系数重算的完整目标 / Complete objective recomputed with native-domain coefficients.
    """

    values: dict[VariableRef, Ratio]
    model_objective: Ratio


@dataclass(frozen=True, kw_only=True)
class PackingLpSolve:
    """已发布 LP 的原报告与独立源域复核 / Raw published-LP report and separate native-domain validation.

    Attributes:
        report: 保留来源身份及池代次的报告 / Report retaining source identity and pool generation.
        compiled_columns: 与报告解向量对齐的列 / Columns aligned with the report solution vector.
        solution: 零容差复核结果，不是最优性证明 / Zero-tolerance validation, not an optimality proof.
    """

    report: SolveReport
    compiled_columns: list[CompiledColumn]
    solution: BindingResult[PackingLpSolution]


@dataclass(frozen=True, kw_only=True)
class PackingSolution:
    """经原域验证的方案，不证明最优 / Native-domain verified solution, not an optimality proof.

    Attributes:
        usages: 非零组合用量 / Nonzero pattern usages.
        packed: 精确坐标及基础装箱目标 / Exact placements and base packing objective.
        model_objective: 按源变量身份重算的完整模型目标 / Complete model objective evaluated by source variable identity.
        indicators: 上游扩展的指标快照 / Indicator snapshot from the upstream extension.
    """

    usages: list[Usage]
    packed: Packed
    model_objective: Ratio
    indicators: dict[str, str]


@dataclass(frozen=True, kw_only=True)
class PackingFinalSolve:
    """列池代次的整数报告与独立方案复核 / Integer report and separate validation for a pool generation.

    Attributes:
        report: 独立最终模型身份及捕获的池代次 / Independent final-model identity and captured pool generation.
        compiled_columns: 与报告解向量对齐的列 / Columns aligned with the report solution vector.
        solution: 原域方案复核，不是全局最优性证明 / Native-domain solution validation, not a global optimality proof.
    """

    report: SolveReport
    compiled_columns: list[CompiledColumn]
    solution: BindingResult[PackingSolution]


@dataclass(frozen=True, kw_only=True)
class PackingSolve:
    """有限候选模型的后端报告和独立方案复核 / Backend report and separate solution validation for the bounded candidate model.

    Attributes:
        report: 完整原始浮点报告 / Complete original floating-point report.
        columns: 按报告顺序排列的候选快照，不含辅助列 / Candidates in report order, excluding auxiliaries.
        compiled_columns: 与报告解向量一一对应的候选和辅助列 / Candidate and auxiliary columns aligned with the report vector.
        candidate_complete: 当前策略的上游搜索截断标记 / Upstream search completeness for this policy.
        visited_nodes: 候选生成访问节点数 / Nodes visited during candidate generation.
        solution: 精确复核方案或失败，独立于原报告 / Exact solution validation or failure, separate from the original report.
    """

    report: SolveReport
    columns: list[Pattern]
    compiled_columns: list[CompiledColumn]
    candidate_complete: bool
    visited_nodes: int
    solution: BindingResult[PackingSolution]


@dataclass(frozen=True, kw_only=True)
class ItemSpec:
    """领域物品输入，不保留在 Python 模型中 / Domain item input, not Python model state.

    Attributes:
        id: 唯一身份 / Unique identity.
        length: 声明长度单位下的单件长度 / Piece length in the declared length unit.
        weight: 声明重量单位下的单件重量 / Piece weight in the declared weight unit.
        amount: 精确需求件数 / Exact demand.
        materials: 单件物料贡献 / Per-piece material contributions.
    """

    id: str
    length: Rational
    weight: Rational
    amount: int
    materials: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True, kw_only=True)
class BinSpec:
    """领域箱型输入 / Domain bin-type input.

    Attributes:
        id: 唯一箱型身份 / Unique bin-type identity.
        length: 声明长度单位下的容量 / Capacity in the declared length unit.
        max_weight: 声明重量单位下的容量 / Capacity in the declared weight unit.
        cost: 每箱成本 / Per-bin cost.
        inventory: 可用数量，None 表示无限 / Available count, or None for unlimited.
    """

    id: str
    length: Rational
    max_weight: Rational
    cost: Rational
    inventory: int | None = None


def _counts(value: object) -> bool:
    return type(value) is dict and all(
        type(key) is str and type(count) is int for key, count in value.items()
    )


def _patterns(value: object) -> list[Pattern] | None:
    if type(value) not in (list, tuple):
        return None
    captured = []
    for item in cast("list[object] | tuple[object, ...]", value):
        if (
            type(item) is not tuple
            or len(item) != 2
            or type(item[0]) is not str
            or type(item[1]) is not dict
            or not _counts(item[1])
        ):
            return None
        captured.append((item[0], item[1].copy()))
    return captured


def _valid_extension(value: PatternExtension) -> bool:
    return (
        type(value) is PatternExtension
        and callable(value.register)
        and (value.extract_solution is None or callable(value.extract_solution))
    )


def _valid_ratio(value: object) -> bool:
    return (
        type(value) is tuple
        and len(value) == 2
        and type(value[0]) is int
        and type(value[1]) is int
        and value[1] > 0
    )


def _wire_reference(value: object) -> _native._Bpp1dReference | None:
    if (
        type(value) is not VariableRef
        or type(value.model_identity) is not int
        or not 0 <= value.model_identity < 2**64
    ):
        return None
    identity, auxiliary = value.variable_identity, value.auxiliary
    if identity is not None:
        if (
            type(identity) is not tuple
            or len(identity) != 2
            or any(
                type(part) is not int or not 0 <= part <= 2 * sys.maxsize + 1
                for part in identity
            )
            or auxiliary is not None
        ):
            return None
    elif type(auxiliary) is not str:
        return None
    return value.model_identity, identity, auxiliary


def _wire_terms(value: object) -> list[_native._Bpp1dTerm] | None:
    if type(value) is not list:
        return None
    terms = []
    for item in value:
        if type(item) is not tuple or len(item) != 2 or not _valid_ratio(item[1]):
            return None
        reference = _wire_reference(item[0])
        if reference is None:
            return None
        terms.append((reference, cast("Ratio", item[1])))
    return terms


def _wire_spec(value: object) -> _native._Bpp1dRegistration | None:
    if (
        type(value) is not PatternExtensionSpec
        or type(value.variables) is not list
        or type(value.constraints) is not list
        or not _valid_ratio(value.objective_constant)
    ):
        return None
    variables: list[_native._Bpp1dVariable] = []
    for variable in value.variables:
        if (
            type(variable) is not AuxiliaryVariable
            or type(variable.name) is not str
            or type(variable.kind) is not str
            or (variable.lower is not None and not _valid_ratio(variable.lower))
            or (variable.upper is not None and not _valid_ratio(variable.upper))
        ):
            return None
        variables.append((variable.name, variable.kind, variable.lower, variable.upper))
    rows: list[_native._Bpp1dRow] = []
    for row in value.constraints:
        if (
            type(row) is not ExtensionConstraint
            or type(row.name) is not str
            or type(row.relation) is not str
            or not _valid_ratio(row.rhs)
        ):
            return None
        terms = _wire_terms(row.terms)
        if terms is None:
            return None
        rows.append((row.name, terms, row.relation, row.rhs))
    objective = _wire_terms(value.objective)
    if objective is None:
        return None
    return variables, rows, objective, value.objective_constant


def _reference(value: _native._Bpp1dReference) -> VariableRef:
    return VariableRef(
        model_identity=value[0], variable_identity=value[1], auxiliary=value[2]
    )


def _compiled_columns(values: list[_native._Bpp1dColumn]) -> list[CompiledColumn]:
    return [
        CompiledColumn(
            reference=_reference(value[0]),
            variable_identity=value[1],
            pattern=value[2],
        )
        for value in values
    ]


def _pool_snapshot(value: _native._Bpp1dPoolInfo) -> PatternPoolSnapshot:
    return PatternPoolSnapshot(
        generation=value[0],
        model_identity=value[1],
        patterns=value[2],
        compiled_columns=_compiled_columns(value[3]),
    )


type _ExtensionFailure = tuple[str, Result[Any, Any, Any] | None, Exception | None]
"""回调阶段及原始失败 / Callback phase and original failure."""


def _extension_callbacks(
    extension: PatternExtension,
    *,
    failure_context: ContextVar[list[_ExtensionFailure] | None] | None = None,
) -> tuple[
    Callable[[_native._Bpp1dRegistrationSnapshot], _native._Bpp1dRegistration | None],
    Callable[[_native._Bpp1dExtractionSnapshot], dict[str, str] | None],
    list[_ExtensionFailure],
]:
    failures: list[_ExtensionFailure] = []
    register = extension.register
    extract = extension.extract_solution

    def record(failure: _ExtensionFailure) -> None:
        target = failures if failure_context is None else failure_context.get()
        if target is not None:
            target.append(failure)

    def register_callback(
        raw: _native._Bpp1dRegistrationSnapshot,
    ) -> _native._Bpp1dRegistration | None:
        returned_result: Result[Any, Any, Any] | None = None
        try:
            snapshot = PatternRegistration(
                model_identity=raw[0],
                stage=raw[1],
                items=raw[2],
                bins=raw[3],
                spacing=raw[4],
                length_unit=Unit(raw[5]),
                weight_unit=Unit(raw[6]),
                objective=raw[7],
                candidates=[(_reference(key), pattern) for key, pattern in raw[8]],
            )
            returned = register(snapshot)
            if isinstance(returned, Result):
                returned_result = returned
            value = returned.value if isinstance(returned, Ok) else returned
            result = _wire_spec(value)
            if result is not None:
                return result
        except Exception as error:
            record(("register", returned_result, error))
            return None
        record(("register", returned_result, None))
        return None

    def extract_callback(
        raw: _native._Bpp1dExtractionSnapshot,
    ) -> dict[str, str] | None:
        if extract is None:
            return {}
        returned_result: Result[Any, Any, Any] | None = None
        try:
            snapshot = PatternExtraction(
                items=raw[0],
                bins=raw[1],
                spacing=raw[2],
                length_unit=Unit(raw[3]),
                weight_unit=Unit(raw[4]),
                objective=raw[5],
                candidates=[
                    (_reference(key), pattern)
                    for key, pattern, _ in raw[6]
                    if pattern is not None
                ],
                values={_reference(key): value for key, _, value in raw[6]},
            )
            returned = extract(snapshot)
            if isinstance(returned, Result):
                returned_result = returned
            value = returned.value if isinstance(returned, Ok) else returned
            if type(value) is dict and all(
                type(key) is str and type(item) is str for key, item in value.items()
            ):
                return value.copy()
        except Exception as error:
            record(("extract_solution", returned_result, error))
            return None
        record(("extract_solution", returned_result, None))
        return None

    return register_callback, extract_callback, failures


def _extension_failure[T](
    result: BindingResult[T], failures: list[_ExtensionFailure]
) -> BindingResult[T]:
    if not isinstance(result, Failed) or not failures:
        return result
    phase, original, exception = failures[0]
    return Failed(
        ExErr(
            _code=result.error.code,
            _message=f"{result.error.message}: 扩展回调失败 / Extension callback failed: {phase}",
            value=replace(
                result.error.value,
                callback_result=original,
                callback_exception=exception,
            ),
        )
    )


class _PoolExtension:
    def __init__(self, extension: PatternExtension) -> None:
        self.failures: ContextVar[list[_ExtensionFailure] | None] = ContextVar(
            "bpp1d_pool_failures", default=None
        )
        register, extract, _ = _extension_callbacks(
            extension, failure_context=self.failures
        )
        self.callbacks: _native._Bpp1dExtension = register, extract

    def invoke[T](
        self, operation: Callable[[], tuple[T | None, _native.Failure | None]]
    ) -> BindingResult[T]:
        result, failures = self.capture(lambda: invoke(operation))
        return _extension_failure(result, failures)

    def capture[T](
        self, operation: Callable[[], BindingResult[T]]
    ) -> tuple[BindingResult[T], list[_ExtensionFailure]]:
        failures: list[_ExtensionFailure] = []
        token = self.failures.set(failures)
        try:
            result = operation()
        finally:
            self.failures.reset(token)
        return result, failures


def _invoke_policy[T](
    *,
    policy: PatternPolicy | None,
    operation: Callable[[Callable[[Pattern], bool | None] | None], BindingResult[T]],
) -> BindingResult[T]:
    if policy is None:
        return operation(None)
    if not callable(policy):
        return invalid("候选策略必须可调用 / Pattern policy must be callable")
    original: Result[Any, Any, Any] | None = None
    exception: Exception | None = None
    failure_index: int | None = None
    position = 0
    reason = ""

    def adapted(candidate: Pattern) -> bool | None:
        nonlocal original, exception, failure_index, position, reason
        index = position
        position += 1
        returned_result: Result[Any, Any, Any] | None = None
        try:
            returned = policy(candidate)
            if isinstance(returned, Result):
                returned_result = returned
            value = returned.value if isinstance(returned, Ok) else returned
            if type(value) is bool:
                return value
            original = returned_result
            reason = "策略须返回 bool 或 Ok(bool) / Policy must return bool or Ok(bool)"
        except Exception as error:
            original = returned_result
            exception = error
            reason = f"候选策略异常 / Pattern policy raised {type(error).__name__}"
        failure_index = index
        return None

    result = operation(adapted)
    if isinstance(result, Failed) and failure_index is not None:
        return Failed(
            ExErr(
                _code=result.error.code,
                _message=f"{result.error.message}: {reason}",
                value=replace(
                    result.error.value,
                    callback_result=original,
                    callback_exception=exception,
                    callback_index=failure_index,
                ),
            )
        )
    return result


class PatternPool:
    """精确 LP 快照列池；变更先完整准备再按代次发布。

    Exact LP snapshot pool; changes are fully prepared before generation-checked publication.
    """

    def __init__(
        self, *, handle: _native.Bpp1dPool, extension: _PoolExtension | None
    ) -> None:
        self._handle = handle
        self._extension = extension

    def snapshot(self) -> BindingResult[PatternPoolSnapshot]:
        """读取独立的已发布快照 / Read a detached published snapshot."""
        return invoke(self._handle.snapshot).map(_pool_snapshot)

    def _change(
        self, *, patterns: list[Pattern] | tuple[Pattern, ...], add: bool
    ) -> BindingResult[PatternPoolSnapshot]:
        captured = _patterns(patterns)
        if captured is None:
            return invalid("无效组合列 / Invalid pattern columns")
        extension = self._extension
        callbacks = None if extension is None else extension.callbacks
        operation = self._handle.add_columns if add else self._handle.remove_columns
        call = lambda: operation(patterns=captured, extension=callbacks)
        result = invoke(call) if extension is None else extension.invoke(call)
        return result.map(_pool_snapshot)

    def add_columns(
        self, *, patterns: list[Pattern] | tuple[Pattern, ...]
    ) -> BindingResult[PatternPoolSnapshot]:
        """去重添加列，失败或并发冲突时不发布 / Add deduplicated columns without publishing failed or conflicting rebuilds.

        Args:
            patterns: 待添加的组合 / Patterns to add.

        Returns:
            已发布或未变化的快照，或失败 / Published or unchanged snapshot, or failure.
        """
        return self._change(patterns=patterns, add=True)

    def remove_columns(
        self, *, patterns: list[Pattern] | tuple[Pattern, ...]
    ) -> BindingResult[PatternPoolSnapshot]:
        """移除列并完整重建 / Remove columns and rebuild the complete model.

        Args:
            patterns: 待移除的组合 / Patterns to remove.

        Returns:
            已发布或未变化的快照，或失败 / Published or unchanged snapshot, or failure.
        """
        return self._change(patterns=patterns, add=False)

    def solve_lp(
        self,
        *,
        solver: str,
        time_limit: int | float | None = None,
        cancellation: SolveHandle | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> BindingResult[PackingLpSolve]:
        """求解已发布 LP，并独立复核精确源快照 / Solve the published LP and separately validate its exact source snapshot.

        Args:
            solver: 显式选择的后端 / Explicit backend.
            time_limit: 后端秒数限制 / Backend limit in seconds.
            cancellation: 单次求解取消句柄 / Single-attempt cancellation handle.
            on_progress: 只读进度回调 / Read-only progress callback.

        Returns:
            原始报告及独立复核，或求解失败 / Raw report and separate validation, or solve failure.
        """
        result = _invoke_solve(
            solver=solver,
            time_limit=time_limit,
            cancellation=cancellation,
            on_progress=on_progress,
            call=lambda args: self._handle.solve_lp(
                solver=args[0],
                time_limit=args[1],
                cancellation=args[2],
                on_progress=args[3],
            ),
        )
        return result.map(
            lambda value: PackingLpSolve(
                report=_report(identity=value[1], generation=value[0], raw=value[2]),
                compiled_columns=_compiled_columns(value[3]),
                solution=invoke(lambda: (value[4], value[5])).map(
                    lambda solution: PackingLpSolution(
                        values={_reference(key): item for key, item in solution[0]},
                        model_objective=solution[1],
                    )
                ),
            )
        )

    def solve_final_milp(
        self,
        *,
        solver: str,
        expansion_limit: int,
        time_limit: int | float | None = None,
        cancellation: SolveHandle | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> BindingResult[PackingFinalSolve]:
        """按捕获的列池代次求解并复核最终整数模型 / Solve and validate a final integer model for the captured pool generation.

        Args:
            solver: 显式选择的后端 / Explicit backend.
            expansion_limit: 最大输出件数 / Maximum output pieces.
            time_limit: 后端秒数限制 / Backend limit in seconds.
            cancellation: 单次求解取消句柄 / Single-attempt cancellation handle.
            on_progress: 只读进度回调 / Read-only progress callback.

        Returns:
            原始报告及独立复核，或建模/求解失败 / Raw report and separate validation, or modeling/solve failure.
        """
        if type(expansion_limit) is not int:
            return invalid("展开预算必须为整数 / Expansion budget must be an integer")
        extension = self._extension
        callbacks = None if extension is None else extension.callbacks

        def operation() -> BindingResult[tuple[int, _native._Bpp1dFinalSolve]]:
            return _invoke_solve(
                solver=solver,
                time_limit=time_limit,
                cancellation=cancellation,
                on_progress=on_progress,
                call=lambda args: self._handle.solve_final_milp(
                    solver=args[0],
                    expansion_limit=expansion_limit,
                    time_limit=args[1],
                    cancellation=args[2],
                    on_progress=args[3],
                    extension=callbacks,
                ),
            )

        if extension is None:
            result = operation()
            failures: list[_ExtensionFailure] = []
        else:
            result, failures = extension.capture(operation)
        result = _extension_failure(result, failures)
        return result.map(
            lambda value: PackingFinalSolve(
                report=_report(
                    identity=value[1][0], generation=value[0], raw=value[1][1]
                ),
                compiled_columns=_compiled_columns(value[1][2]),
                solution=_extension_failure(
                    invoke(lambda: (value[1][3], value[1][4])), failures
                ).map(
                    lambda solution: PackingSolution(
                        usages=solution[0],
                        packed=solution[1],
                        model_objective=solution[2],
                        indicators=solution[3],
                    )
                ),
            )
        )

    def close(self) -> BindingResult[None]:
        """关闭列池并释放扩展引用；已开始的求解仍持有旧快照 / Close the pool and release its extension; in-flight solves retain their old snapshots."""
        result: BindingResult[None] = invoke(self._handle.close)
        if result.is_ok():
            self._extension = None
        return result


class PackingContext:
    """只持有原生上下文；所有输入必须已归一到声明的同一单位。

    Holds only the native context; inputs must already use the declared units.
    """

    def __init__(self, handle: _native.Bpp1dContext) -> None:
        self._handle = handle

    @classmethod
    def create(
        cls,
        *,
        items: list[ItemSpec] | tuple[ItemSpec, ...],
        bins: list[BinSpec] | tuple[BinSpec, ...],
        spacing: Rational,
        length_unit: Unit,
        weight_unit: Unit,
        objective: str = "bin_count",
    ) -> BindingResult[PackingContext]:
        """创建原生领域上下文 / Create a native domain context.

        Args:
            items: 内置列表或元组，长度和重量已使用声明单位 / Builtin list or tuple with lengths and weights in the declared units.
            bins: 内置列表或元组，长度和重量已使用声明单位 / Builtin list or tuple with lengths and weights in the declared units.
            spacing: 声明长度单位下的间距 / Gap in the declared length unit.
            length_unit: 线性且比例为正的原生长度单位 / Positive linear native length unit.
            weight_unit: 线性且比例为正的原生重量单位 / Positive linear native weight unit.
            objective: bin_count、consumed_length 或 cost / Objective metric.

        Returns:
            上下文或结构化失败 / Context or structured failure.
        """
        if (
            type(items) not in (list, tuple)
            or type(bins) not in (list, tuple)
            or type(spacing) is not Rational
            or type(length_unit) is not Unit
            or type(weight_unit) is not Unit
            or type(objective) is not str
        ):
            return invalid("无效装箱输入 / Invalid packing input")
        item_snapshot, bin_snapshot = tuple(items), tuple(bins)
        native_items: list[
            tuple[str, _native.Rational, _native.Rational, int, dict[str, int]]
        ] = []
        for item in item_snapshot:
            if (
                type(item) is not ItemSpec
                or type(item.id) is not str
                or type(item.length) is not Rational
                or type(item.weight) is not Rational
                or type(item.amount) is not int
                or type(item.materials) is not dict
            ):
                return invalid("无效物品或箱型 / Invalid item or bin type")
            materials = item.materials.copy()
            if not _counts(materials):
                return invalid("无效物品或箱型 / Invalid item or bin type")
            native_items.append(
                (
                    item.id,
                    item.length._handle,
                    item.weight._handle,
                    item.amount,
                    materials,
                )
            )
        if any(
            type(bin_) is not BinSpec
            or type(bin_.id) is not str
            or type(bin_.length) is not Rational
            or type(bin_.max_weight) is not Rational
            or type(bin_.cost) is not Rational
            or (bin_.inventory is not None and type(bin_.inventory) is not int)
            for bin_ in bin_snapshot
        ):
            return invalid("无效物品或箱型 / Invalid item or bin type")
        return invoke(
            lambda: _native._create_bpp1d_context(
                items=native_items,
                bins=[
                    (
                        bin_.id,
                        bin_.length._handle,
                        bin_.max_weight._handle,
                        bin_.cost._handle,
                        bin_.inventory,
                    )
                    for bin_ in bin_snapshot
                ],
                spacing=spacing._handle,
                length_unit=length_unit._handle,
                weight_unit=weight_unit._handle,
                objective=objective,
            )
        ).map(cls)

    def generate_patterns(
        self, *, max_patterns: int, max_nodes: int, policy: PatternPolicy | None = None
    ) -> BindingResult[tuple[list[Pattern], bool, int]]:
        """生成候选及上游截断状态，不认证全局最优。

        Generate candidates and upstream truncation status, not global optimality.

        Args:
            max_patterns: 最大保留候选数 / Maximum retained patterns.
            max_nodes: 最大访问节点数 / Maximum visited nodes.
            policy: 逐候选接受策略 / Per-candidate acceptance policy.

        Returns:
            候选、上游完整标记及节点数，或失败 / Candidates, upstream completeness flag and visited nodes, or failure.
        """
        if type(max_patterns) is not int or type(max_nodes) is not int:
            return invalid("搜索预算必须为整数 / Search budgets must be integers")
        return _invoke_policy(
            policy=policy,
            operation=lambda callback: invoke(
                lambda: self._handle.generate_patterns(
                    max_patterns=max_patterns, max_nodes=max_nodes, policy=callback
                )
            ),
        )

    def validate_pattern(
        self, *, bin_type_id: str, amounts: dict[str, int]
    ) -> BindingResult[None]:
        """按原域校验单列，不证明全局需求 / Validate one pattern, not global demand.

        Args:
            bin_type_id: 箱型身份 / Bin-type identity.
            amounts: 非零物品件数 / Nonzero item counts.

        Returns:
            成功或结构化失败 / Success or structured failure.
        """
        if type(bin_type_id) is not str or type(amounts) is not dict:
            return invalid("无效组合 / Invalid pattern")
        amount_snapshot = amounts.copy()
        if not _counts(amount_snapshot):
            return invalid("无效组合 / Invalid pattern")
        return invoke(
            lambda: self._handle.validate_pattern(
                bin_type_id=bin_type_id, amounts=amount_snapshot
            )
        )

    def column_pool(
        self,
        *,
        patterns: list[Pattern] | tuple[Pattern, ...],
        extension: PatternExtension | None = None,
    ) -> BindingResult[PatternPool]:
        """创建已完整验证的精确 LP 列池 / Create a fully validated exact LP pattern pool.

        Args:
            patterns: 初始候选 / Initial candidates.
            extension: 每次完整重建时注册的扩展 / Extension registered on each complete rebuild.

        Returns:
            已发布列池或失败 / Published pool or failure.
        """
        captured = _patterns(patterns)
        if captured is None:
            return invalid("无效组合列 / Invalid pattern columns")
        bridge = None
        if extension is not None:
            if not _valid_extension(extension):
                return invalid("无效建模扩展 / Invalid modeling extension")
            bridge = _PoolExtension(extension)
        callbacks = None if bridge is None else bridge.callbacks
        call = lambda: self._handle.column_pool(patterns=captured, extension=callbacks)
        result = invoke(call) if bridge is None else bridge.invoke(call)
        return result.map(lambda handle: PatternPool(handle=handle, extension=bridge))

    def pack(
        self, *, usages: list[tuple[str, dict[str, int], int]], expansion_limit: int
    ) -> BindingResult[Packed]:
        """校验完整需求和库存并展开精确坐标，不进行求解。

        Validate complete demand and inventory and expand exact coordinates, without solving.

        Args:
            usages: 箱型、物品件数、组合使用次数 / Bin type, item counts and pattern usage.
            expansion_limit: 最大输出件数 / Maximum output pieces.

        Returns:
            原域结果快照或失败 / Native-domain result snapshot or failure.
        """
        if type(usages) is not list or type(expansion_limit) is not int:
            return invalid("无效组合用量 / Invalid pattern usages")
        captured = []
        for usage in tuple(usages):
            if (
                type(usage) is not tuple
                or len(usage) != 3
                or type(usage[0]) is not str
                or type(usage[1]) is not dict
                or type(usage[2]) is not int
            ):
                return invalid("无效组合用量 / Invalid pattern usages")
            amounts = usage[1].copy()
            if not _counts(amounts):
                return invalid("无效组合用量 / Invalid pattern usages")
            captured.append((usage[0], amounts, usage[2]))
        return invoke(
            lambda: self._handle.pack(usages=captured, expansion_limit=expansion_limit)
        )

    def solve(
        self,
        *,
        solver: str,
        max_patterns: int,
        max_nodes: int,
        expansion_limit: int,
        time_limit: int | float | None = None,
        cancellation: SolveHandle | None = None,
        on_progress: ProgressCallback | None = None,
        policy: PatternPolicy | None = None,
        extension: PatternExtension | None = None,
    ) -> BindingResult[PackingSolve]:
        """求解有限候选整数模型，并独立复核原域方案。

        Solve the bounded-candidate integer model and independently verify its native-domain solution.

        Args:
            solver: 显式选择已编译后端 / Explicit compiled backend.
            max_patterns: 最大候选数 / Maximum candidate count.
            max_nodes: 最大搜索节点数 / Maximum search nodes.
            expansion_limit: 最大输出件数 / Maximum output pieces.
            time_limit: 后端秒数限制；SCIP 编译模型目前不支持 / Backend limit in seconds; unsupported for compiled SCIP models.
            cancellation: 后端单次取消句柄，不中断候选生成 / Single backend-attempt handle; does not interrupt candidate generation.
            on_progress: 后端只读进度回调 / Read-only backend progress callback.
            policy: 逐候选接受策略 / Per-candidate acceptance policy.
            extension: 声明式精确模型扩展 / Declarative exact-model extension.

        Returns:
            原始报告及独立方案复核，或建模/求解失败 / Raw report and separate solution validation, or modeling/solve failure.
        """
        if any(
            type(value) is not int
            for value in (max_patterns, max_nodes, expansion_limit)
        ):
            return invalid("装箱预算必须为整数 / Packing budgets must be integers")
        callbacks = None
        failures: list[_ExtensionFailure] = []
        if extension is not None:
            if not _valid_extension(extension):
                return invalid("无效建模扩展 / Invalid modeling extension")
            register, extract, failures = _extension_callbacks(extension)
            callbacks = register, extract
        result = _invoke_policy(
            policy=policy,
            operation=lambda callback: _invoke_solve(
                solver=solver,
                time_limit=time_limit,
                cancellation=cancellation,
                on_progress=on_progress,
                call=lambda args: self._handle.solve(
                    solver=args[0],
                    max_patterns=max_patterns,
                    max_nodes=max_nodes,
                    expansion_limit=expansion_limit,
                    time_limit=args[1],
                    cancellation=args[2],
                    on_progress=args[3],
                    policy=callback,
                    extension=callbacks,
                ),
            ),
        )
        result = _extension_failure(result, failures)
        return result.map(
            lambda value: PackingSolve(
                report=_report(identity=value[0], generation=0, raw=value[1]),
                columns=value[2],
                compiled_columns=_compiled_columns(value[3]),
                candidate_complete=value[4],
                visited_nodes=value[5],
                solution=_extension_failure(
                    invoke(lambda: (value[6], value[7])), failures
                ).map(
                    lambda solution: PackingSolution(
                        usages=solution[0],
                        packed=solution[1],
                        model_objective=solution[2],
                        indicators=solution[3],
                    )
                ),
            )
        )
