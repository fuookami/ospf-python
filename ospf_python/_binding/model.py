"""私有 Float64 求解边界；不复制 Python 模型 / Private Float64 boundary without a Python model copy."""

from __future__ import annotations

import json
import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any

from ospf_python import _native
from ospf_python._binding.control import ProgressCallback, SolveHandle, SolveProgress
from ospf_python._binding.result import BindingResult, invalid, invoke
from ospf_python.utils.error.error import ExErr
from ospf_python.utils.functional.result import Failed, Ok, Result


@dataclass(frozen=True, kw_only=True)
class VariableSpec:
    """变量输入快照，不是可变模型状态 / Variable input snapshot, not mutable model state.

    Attributes:
        name: 名称 / Name.
        kind: continuous、integer 或 binary / Variable kind.
        lower: 下界，None 表示无界 / Lower bound, None for unbounded.
        upper: 上界，None 表示无界 / Upper bound, None for unbounded.
    """

    name: str
    kind: str = "continuous"
    lower: int | float | None = None
    upper: int | float | None = None


@dataclass(frozen=True, kw_only=True)
class ConstraintSpec:
    """约束输入快照 / Constraint input snapshot.

    Attributes:
        name: 名称 / Name.
        terms: 身份句柄和系数 / Identity handles and coefficients.
        relation: <=、>= 或 == / Constraint relation.
        rhs: 右端值 / Right-hand side.
    """

    name: str
    terms: Sequence[tuple[_native.VariableHandle, int | float]]
    relation: str
    rhs: int | float


@dataclass(frozen=True, kw_only=True)
class ColumnDecisionSpec:
    """局部决策输入 / Local decision input.

    Attributes:
        id: 决策身份 / Decision identity.
        block: 配置块身份 / Block identity.
        variable: 来源变量句柄 / Source variable handle.
    """

    id: str
    block: str
    variable: _native.VariableHandle


@dataclass(frozen=True, kw_only=True)
class ColumnSpec:
    """完整列输入或独立快照 / Complete column input or detached snapshot.

    Attributes:
        id: 列身份 / Column identity.
        block: 配置块身份 / Block identity.
        values: 该块每个决策的值 / Value for each decision in the block.
    """

    id: str
    block: str
    values: Mapping[str, int | float]


@dataclass(frozen=True, kw_only=True)
class LinearVariableExport:
    """Rust 模型变量快照 / Rust-model variable snapshot.

    Attributes:
        name: 变量名称 / Variable name.
        kind: continuous、integer 或 binary / Variable kind.
        lower: 显式下界或 None / Explicit lower bound or None.
        upper: 显式上界或 None / Explicit upper bound or None.
    """

    name: str
    kind: str
    lower: float | None
    upper: float | None


@dataclass(frozen=True, kw_only=True)
class LinearRowExport:
    """Rust 模型约束快照 / Rust-model row snapshot.

    Attributes:
        identity: 模型内行身份 / Model-local row identity.
        name: 原始约束名 / Original constraint name.
        coefficients: 变量名到系数 / Variable names and coefficients.
        rhs: 右端值 / Right-hand side.
        relation: <=、>= 或 == / Row relation.
    """

    identity: str
    name: str
    coefficients: dict[str, float]
    rhs: float
    relation: str


@dataclass(frozen=True, kw_only=True)
class LinearTriadExport:
    """完整线性模型快照，不是求解证书 / Complete linear snapshot, not a solve certificate.

    Attributes:
        name: 模型名称 / Model name.
        variables: 变量表 / Variable table.
        rows: 约束表 / Constraint table.
        objective: 变量名到目标系数 / Objective coefficients by variable.
        sense: minimize 或 maximize / Objective sense.
        constant: 目标常数 / Objective constant.
    """

    name: str
    variables: tuple[LinearVariableExport, ...]
    rows: tuple[LinearRowExport, ...]
    objective: dict[str, float]
    sense: str
    constant: float


@dataclass(frozen=True, kw_only=True)
class ProjectionMasterInfo:
    """主问题元数据快照，不是求解证书 / Master metadata, not a solve certificate.

    Attributes:
        source_generation: 构建时的源模型代次 / Source generation at construction.
        integer: 是否整数主问题 / Whether this is an integer master.
        columns: 列数量 / Number of columns.
        variables: 主问题变量数 / Number of master variables.
        rows: 主问题约束数 / Number of master rows.
        phase_one: 是否使用人工变量可行性目标 / Whether artificials define the feasibility objective.
    """

    source_generation: int
    integer: bool
    columns: int
    variables: int
    rows: int
    phase_one: bool = False


@dataclass(frozen=True, kw_only=True)
class SolveReport:
    """不可变的上游报告快照，不是独立最优性证书 / Immutable upstream report snapshot, not independent optimality proof.

    Attributes:
        model_identity: 来源模型身份 / Originating model identity.
        model_generation: 求解时的修改代次，不是来源证书 / Mutation generation at solve, not an origin certificate.
        problem_status: 数学结论 / Mathematical conclusion.
        termination_reason: 执行终止原因 / Execution termination reason.
        solution_presence: 上游报告的解状态，并非独立认证 / Upstream solution status, not independent certification.
        objective: 可选目标值 / Optional objective.
        values: 按 solver 列顺序的解向量 / Solution in solver-column order.
        raw_json: 含证明、映射、诊断和 trace 的完整报告 / Full proof, mapping, diagnostics and trace.
    """

    model_identity: int
    model_generation: int
    problem_status: str
    termination_reason: str
    solution_presence: str
    objective: float | None
    values: tuple[float, ...]
    raw_json: str


@dataclass(frozen=True, kw_only=True)
class CompiledSolveReport:
    """标准最小化模型的历史报告与可选证书。

    Historical normalized-minimum report and optional certificate.
    编译模型须通过精确二进制零间隙门禁；价格计算仍可能舍入，不证明定价完成。
    The compiled model must pass an exact binary zero-gap gate; price arithmetic can still round and does not prove pricing completion.

    Attributes:
        report: 原样保留的编译模型报告 / Unmodified compiled-model report.
        certificate: 不透明证书或不可认证的原因 / Opaque certificate or the reason it was unavailable.
    """

    report: SolveReport
    certificate: BindingResult[_native.DualCertificate]


@dataclass(frozen=True, kw_only=True)
class ProjectionMasterSolve:
    """主 LP 报告与独立定价门禁。

    Master LP report and independent pricing gate.
    编译主模型须通过精确零间隙门禁；投影及定价仍可舍入，不证明全局完成。
    The compiled master must pass an exact zero-gap gate; projection and pricing can still round and do not prove global completion.

    Attributes:
        report: 主模型身份、源代次和标准最小化报告 / Master identity, source generation and normalized-minimum report.
        pricing: 精确编译模型门禁通过或失败原因 / Exact compiled-model gate success or rejection reason.
    """

    report: SolveReport
    pricing: BindingResult[None]


@dataclass(frozen=True, kw_only=True)
class PricingInfo:
    """定价输入的独立历史快照 / Detached historical snapshot of pricing inputs.

    Attributes:
        block: 配置块身份 / Block identity.
        coefficients: 决策系数 / Decision coefficients.
        convexity_price: 凸性约束价格 / Convexity-row price.
        row_prices: 原行价格 / Source-row prices.
    """

    block: str
    coefficients: dict[str, float]
    convexity_price: float
    row_prices: dict[str, float]


@dataclass(frozen=True, kw_only=True)
class PricingCandidate:
    """经复核的局部可行解，不证明定价完成 / Validated local incumbent, not a proof of pricing completion.

    Attributes:
        values: 独立的局部决策快照 / Detached local-decision values.
        reduced_cost: 包含凸性常数的检验数 / Reduced cost including the convexity constant.
    """

    values: dict[str, float]
    reduced_cost: float


@dataclass(frozen=True, kw_only=True)
class PricingBoundInfo:
    """后端界的历史快照，不是完成证书 / Historical backend-bound snapshot, not a completion certificate.

    Attributes:
        block: 当前定价块 / Current pricing block.
        reported_cx_lower: 后端报告的 c*x 下界 / Backend-reported c*x lower bound.
        convexity_price: 当前凸性价格 / Current convexity price.
        reported_nonnegative: 报告界不小于凸性价格，不认证求解器数值误差 / Whether the reported bound is at least the price, without certifying solver numerical error.
    """

    block: str
    reported_cx_lower: float
    convexity_price: float
    reported_nonnegative: bool


@dataclass(frozen=True, kw_only=True)
class ProjectionPricingSolve:
    """定价报告与独立可行解复核 / Pricing report and independent incumbent validation.

    Attributes:
        report: solver 的 c*x 原始报告，不证明定价完成 / Raw solver c*x report, not proof of pricing completion.
        candidate: 可行解快照或复核失败 / Incumbent snapshot or validation failure.
        bound: 同次求解的后端界观察或不可用原因，不是证书 / Same-attempt backend-bound observation or failure, not a certificate.
    """

    report: SolveReport
    candidate: BindingResult[PricingCandidate]
    bound: BindingResult[_native.ColumnPricingBound]


@dataclass(frozen=True, kw_only=True)
class ProjectionIntegerSolve:
    """整数主问题报告与独立源解复核 / Integer-master report and independent source-solution validation.

    Attributes:
        report: 整数主问题的 c*x 报告，不含常数 / Integer-master c*x report, excluding the objective constant.
        solution: 不透明可行源解或复核失败，不单独证明最优 / Opaque feasible source solution or validation failure, not a standalone optimality proof.
    """

    report: SolveReport
    solution: BindingResult[_native.ColumnProjectionSolution]


def _report(*, identity: int, generation: int, raw: str) -> SolveReport:
    report = json.loads(raw)
    solution = report["solution"]
    return SolveReport(
        model_identity=identity,
        model_generation=generation,
        problem_status=report["problemStatus"],
        termination_reason=report["terminationReason"],
        solution_presence=report["solutionPresence"],
        objective=None if solution is None else solution["objectiveValue"],
        values=() if solution is None else tuple(solution["values"]),
        raw_json=raw,
    )


def _number(value: int | float) -> BindingResult[float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return invalid("需要 int 或 float 数值 / Expected an int or float value")
    if isinstance(value, int) and abs(value) > 2**53 - 1:
        return invalid(
            "整数超出 Float64 精确边界 / Integer exceeds the exact Float64 boundary"
        )
    result = float(value)
    if not math.isfinite(result):
        return invalid("数值必须有限 / Numeric value must be finite")
    return Ok(result)


type _NativeSolveArgs = tuple[
    str,
    float | None,
    _native.SolveHandle | None,
    Callable[[SolveProgress], str | None] | None,
]


def _invoke_solve[T](
    *,
    solver: str,
    time_limit: int | float | None,
    cancellation: SolveHandle | None,
    on_progress: ProgressCallback | None,
    call: Callable[[_NativeSolveArgs], tuple[T | None, _native.Failure | None]],
) -> BindingResult[T]:
    seconds = None
    if cancellation is not None and not isinstance(cancellation, SolveHandle):
        return invalid("需要 SolveHandle / Expected a SolveHandle")
    if on_progress is not None and not callable(on_progress):
        return invalid("进度回调必须可调用 / Progress callback must be callable")
    if time_limit is not None:
        number = _number(time_limit)
        if isinstance(number, Failed):
            return Failed(number.error)
        seconds = number.unwrap()
    callback_results: list[Result[None, Any, Any]] = []

    def report_progress(event: SolveProgress) -> str | None:
        if on_progress is None:
            return None
        returned = on_progress(event)
        if returned is None or (isinstance(returned, Ok) and returned.value is None):
            return None
        if isinstance(returned, Result) and not callback_results:
            callback_results.append(returned)
        return (
            "回调必须返回 None 或 Ok(None)，失败以 Result 保留 / "
            f"Callback must return None or Ok(None); received {type(returned).__name__}"
        )

    result = invoke(
        lambda: call(
            (
                solver,
                seconds,
                None if cancellation is None else cancellation._handle,
                None if on_progress is None else report_progress,
            )
        )
    )
    if isinstance(result, Failed) and callback_results:
        return Failed(
            ExErr(
                _code=result.error.code,
                _message=result.error.message,
                value=replace(result.error.value, callback_result=callback_results[0]),
            )
        )
    return result


def _terms(
    values: Sequence[tuple[_native.VariableHandle, int | float]],
) -> BindingResult[list[tuple[_native.VariableHandle, float]]]:
    result = []
    for handle, coefficient in values:
        number = _number(coefficient)
        if isinstance(number, Failed):
            return Failed(number.error)
        result.append((handle, number.unwrap()))
    return Ok(result)


def _column_inputs(
    columns: Sequence[ColumnSpec],
) -> BindingResult[list[tuple[str, str, dict[str, float]]]]:
    converted = []
    for column in columns:
        values = {}
        for key, value in column.values.items():
            number = _number(value)
            if isinstance(number, Failed):
                return Failed(number.error)
            values[key] = number.unwrap()
        converted.append((column.id, column.block, values))
    return Ok(converted)


def _master_info(value: tuple[int, bool, int, int, int, bool]) -> ProjectionMasterInfo:
    return ProjectionMasterInfo(
        source_generation=value[0],
        integer=value[1],
        columns=value[2],
        variables=value[3],
        rows=value[4],
        phase_one=value[5],
    )


class ColumnProjectionFloat64:
    """Rust 所有者上的私有列池与主问题 / Private column pool and master on the Rust owner."""

    def __init__(self, handle: _native.ColumnProjection) -> None:
        self._handle = handle

    def close(self) -> BindingResult[None]:
        """幂等释放投影 / Release the projection idempotently."""
        return invoke(self._handle.close)

    def columns(self) -> BindingResult[list[ColumnSpec]]:
        """返回独立列快照 / Return detached column snapshots."""
        return invoke(self._handle.columns).map(
            lambda columns: [
                ColumnSpec(id=id, block=block, values=values)
                for id, block, values in columns
            ]
        )

    def add_columns(self, columns: Sequence[ColumnSpec]) -> BindingResult[None]:
        """原子加入初始列，不证明定价完成 / Atomically add seed columns without proving pricing completion.

        Args:
            columns: 完整列输入 / Complete column inputs.

        Returns:
            unit 成功或失败 / Unit success or failure.
        """
        converted = _column_inputs(columns)
        if isinstance(converted, Failed):
            return Failed(converted.error)
        return invoke(lambda: self._handle.add_columns(converted.unwrap()))

    def remove_columns(self, ids: Sequence[str]) -> BindingResult[None]:
        """原子删除指定列 / Atomically remove named columns.

        Args:
            ids: 待删除的列身份 / Column identities to remove.

        Returns:
            unit 成功或失败 / Unit success or failure.
        """
        return invoke(lambda: self._handle.remove_columns(list(ids)))

    def build_master(
        self, *, integer: bool = False, phase_one: bool = False
    ) -> BindingResult[ProjectionMasterInfo]:
        """从当前源模型和列池重建主问题，不证明可行性 / Rebuild the master without proving feasibility.

        Args:
            integer: 是否恢复整数选列 / Whether to use integer column selection.
            phase_one: 是否使用人工变量目标，不能与 integer 同时使用 / Whether to use artificials; incompatible with integer.

        Returns:
            历史元数据或失败 / Historical metadata or failure.
        """
        return invoke(
            lambda: self._handle.build_master(integer=integer, phase_one=phase_one)
        ).map(_master_info)

    def master_info(self) -> BindingResult[ProjectionMasterInfo]:
        """仅在源模型及列池未改变时查询当前主问题 / Inspect only a current master."""
        return invoke(self._handle.master_info).map(_master_info)

    def solve_master_lp(
        self,
        *,
        solver: str,
        time_limit: int | float | None = None,
        cancellation: SolveHandle | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> BindingResult[ProjectionMasterSolve]:
        """求解主 LP 并验证编译模型的精确零间隙。

        Solve the master LP and require an exact zero gap for the compiled model.
        列贡献和拆行价格还需精确匹配；通过不证明定价完成。
        Column contributions and split prices must also match exactly; this does not prove completion.

        Args:
            solver: 已编译后端 / Compiled backend.
            time_limit: 可选秒数 / Optional limit in seconds.
            cancellation: 单次取消句柄 / Single-attempt cancellation handle.
            on_progress: 只读进度回调 / Read-only progress callback.

        Returns:
            原始报告及独立定价门禁，或求解边界失败 / Report with independent pricing gate, or solve-boundary failure.
        """
        return _invoke_solve(
            solver=solver,
            time_limit=time_limit,
            cancellation=cancellation,
            on_progress=on_progress,
            call=lambda args: self._handle.solve_master_lp(
                solver=args[0],
                time_limit=args[1],
                cancellation=args[2],
                on_progress=args[3],
            ),
        ).map(
            lambda value: ProjectionMasterSolve(
                report=_report(identity=value[0], generation=value[1], raw=value[2]),
                pricing=invoke(lambda: (None, value[3])),
            )
        )

    def pricing_request(
        self, *, block: str
    ) -> BindingResult[_native.ColumnPricingRequest]:
        """取得绑定投影和当前对偶的定价能力 / Obtain a projection- and dual-bound pricing capability.

        块内定价系数须与精确二进制计算一致，否则返回失败。
        Block coefficients must match exact binary arithmetic or the request fails.

        Args:
            block: 配置块身份 / Block identity.

        Returns:
            不可构造的原生请求或失败 / Nonconstructible native request or failure.
        """
        return invoke(lambda: self._handle.pricing_request(block=block))

    def pricing_info(
        self, *, request: _native.ColumnPricingRequest
    ) -> BindingResult[PricingInfo]:
        """校验后返回独立定价快照 / Validate and return a detached pricing snapshot.

        Args:
            request: 当前投影的定价请求 / Current pricing request for this projection.

        Returns:
            历史快照或失败 / Historical snapshot or failure.
        """
        return invoke(lambda: self._handle.pricing_info(request=request)).map(
            lambda value: PricingInfo(
                block=value[0],
                coefficients=value[1],
                convexity_price=value[2],
                row_prices=value[3],
            )
        )

    def reduced_cost(
        self,
        *,
        request: _native.ColumnPricingRequest,
        values: Mapping[str, int | float],
    ) -> BindingResult[float]:
        """精确累加检验数，结果舍入为有限 Float64 / Sum reduced cost exactly and round to finite Float64.

        非零结果若下溢为零则失败 / Fail if a nonzero exact result underflows to zero.

        Args:
            request: 当前投影的定价请求 / Current pricing request for this projection.
            values: 该块完整决策向量 / Complete decision vector for the block.

        Returns:
            完整检验数或失败 / Complete reduced cost or failure.
        """
        converted = {}
        for key, value in values.items():
            number = _number(value)
            if isinstance(number, Failed):
                return Failed(number.error)
            converted[key] = number.unwrap()
        return invoke(
            lambda: self._handle.reduced_cost(request=request, values=converted)
        )

    def pricing_bound_info(
        self, *, bound: _native.ColumnPricingBound
    ) -> BindingResult[PricingBoundInfo]:
        """校验来源和代次后查看后端界，不证明定价完成 / Inspect a current backend bound without certifying completion.

        Args:
            bound: 同一投影和当前对偶的界观察 / Bound observation for this projection and current duals.

        Returns:
            界与价格的历史快照或失败 / Historical bound and price snapshot or failure.
        """
        return invoke(lambda: self._handle.pricing_bound_info(bound=bound)).map(
            lambda value: PricingBoundInfo(
                block=value[0],
                reported_cx_lower=value[1],
                convexity_price=value[2],
                reported_nonnegative=value[3],
            )
        )

    def solve_pricing(
        self,
        *,
        request: _native.ColumnPricingRequest,
        solver: str,
        time_limit: int | float | None = None,
        cancellation: SolveHandle | None = None,
        on_progress: ProgressCallback | None = None,
        tolerance: int | float = 1e-7,
    ) -> BindingResult[ProjectionPricingSolve]:
        """求解上游定价模型并复核候选解 / Solve upstream pricing and validate its incumbent.

        Args:
            request: 当前投影定价请求 / Current pricing request.
            solver: 已编译后端 / Compiled backend.
            time_limit: 可选秒数 / Optional limit in seconds.
            cancellation: 单次取消句柄 / Single-attempt cancellation handle.
            on_progress: 只读进度回调 / Read-only progress callback.
            tolerance: 边界、行、整数性及目标复核容差 / Bound, row, integrality and objective validation tolerance.

        Returns:
            原始报告、候选和后端界观察，不证明定价完成 / Original report, candidate and backend-bound observation, not pricing completion.
        """
        converted = _number(tolerance)
        if isinstance(converted, Failed):
            return Failed(converted.error)
        return _invoke_solve(
            solver=solver,
            time_limit=time_limit,
            cancellation=cancellation,
            on_progress=on_progress,
            call=lambda args: self._handle.solve_pricing(
                request=request,
                solver=args[0],
                time_limit=args[1],
                cancellation=args[2],
                on_progress=args[3],
                tolerance=converted.unwrap(),
            ),
        ).map(
            lambda value: ProjectionPricingSolve(
                report=_report(identity=value[0], generation=value[1], raw=value[2]),
                candidate=invoke(lambda: (value[3], value[4])).map(
                    lambda item: PricingCandidate(values=item[0], reduced_cost=item[1])
                ),
                bound=invoke(lambda: (value[5], value[6])),
            )
        )

    def add_priced_batch(
        self,
        batches: Sequence[tuple[_native.ColumnPricingRequest, Sequence[ColumnSpec]]],
    ) -> BindingResult[None]:
        """原子加入同一轮的完整定价列 / Atomically add complete columns from one pricing round.

        Args:
            batches: 当前请求与对应列 / Current requests and their columns.

        Returns:
            unit 成功或失败；失败不发布任何列 / Unit success or failure without partial publication.
        """
        converted = []
        for request, columns in batches:
            values = _column_inputs(columns)
            if isinstance(values, Failed):
                return Failed(values.error)
            converted.append((request, values.unwrap()))
        return invoke(lambda: self._handle.add_priced_batch(converted))

    def solve_master_integer(
        self,
        *,
        solver: str,
        time_limit: int | float | None = None,
        cancellation: SolveHandle | None = None,
        on_progress: ProgressCallback | None = None,
        tolerance: int | float = 1e-7,
    ) -> BindingResult[ProjectionIntegerSolve]:
        """求解整数主问题并复核原模型解 / Solve the integer master and validate the source solution.

        Args:
            solver: 已编译后端 / Compiled backend.
            time_limit: 可选秒数 / Optional limit in seconds.
            cancellation: 单次取消句柄 / Single-attempt cancellation handle.
            on_progress: 只读进度回调 / Read-only progress callback.
            tolerance: 边界、行、整数性及目标复核容差 / Bound, row, integrality and objective validation tolerance.

        Returns:
            原始报告与独立源解 Result / Original report and independent source-solution Result.
        """
        converted = _number(tolerance)
        if isinstance(converted, Failed):
            return Failed(converted.error)
        return _invoke_solve(
            solver=solver,
            time_limit=time_limit,
            cancellation=cancellation,
            on_progress=on_progress,
            call=lambda args: self._handle.solve_master_integer(
                solver=args[0],
                time_limit=args[1],
                cancellation=args[2],
                on_progress=args[3],
                tolerance=converted.unwrap(),
            ),
        ).map(
            lambda value: ProjectionIntegerSolve(
                report=_report(identity=value[0], generation=value[1], raw=value[2]),
                solution=invoke(lambda: (value[3], value[4])),
            )
        )

    def solution_value(
        self,
        *,
        solution: _native.ColumnProjectionSolution,
        handle: _native.VariableHandle,
    ) -> BindingResult[float]:
        """按源变量身份读取当前源解 / Read the current source solution by source-variable identity.

        Args:
            solution: 当前投影的不透明源解 / Opaque source solution from this projection.
            handle: 当前源变量句柄 / Current source-variable handle.

        Returns:
            数值或来源/代次失败 / Value or provenance/generation failure.
        """
        return invoke(
            lambda: self._handle.solution_value(solution=solution, handle=handle)
        )


class MetaModelFloat64:
    """Rust 状态的私有薄门面，不替换公共泛型模型 / Private facade, not a replacement of the public generic model.

    Attributes:
        model_identity: 不随关闭改变的 Rust 身份 / Stable Rust identity even after close.
    """

    def __init__(self, handle: _native.MetaModel) -> None:
        self._handle = handle

    @classmethod
    def create(cls, name: str) -> BindingResult[MetaModelFloat64]:
        """通过 Result 创建，含线程启动失败 / Create through Result, including owner startup failure.

        Args:
            name: 模型名称 / Model name.

        Returns:
            私有薄门面或失败 / Private facade or failure.
        """
        return invoke(lambda: _native._create_model(name)).map(cls)

    @property
    def model_identity(self) -> int:
        """Rust 模型生命周期身份 / Rust model-lifecycle identity."""
        return self._handle.model_identity

    def snapshot(self) -> BindingResult[tuple[int, str, int, int]]:
        """返回身份、名称、变量数及约束数 / Return identity, name and variable/constraint counts."""
        return invoke(self._handle.snapshot)

    def generation(self) -> BindingResult[int]:
        """查询所有者的修改代次 / Query the owner's mutation generation."""
        return invoke(self._handle.generation)

    def to_linear_triad(self) -> BindingResult[LinearTriadExport]:
        """导出完整线性结构 / Export the complete linear structure.

        Returns:
            与 Rust 所有者代次绑定的独立快照或失败 / A detached snapshot of the current Rust structure or failure.
        """
        return invoke(self._handle.to_linear_triad).map(
            lambda value: LinearTriadExport(
                name=value[0],
                variables=tuple(
                    LinearVariableExport(
                        name=name,
                        kind=kind,
                        lower=lower,
                        upper=upper,
                    )
                    for name, kind, lower, upper in value[1]
                ),
                rows=tuple(
                    LinearRowExport(
                        identity=identity,
                        name=name,
                        coefficients=coefficients,
                        rhs=rhs,
                        relation=relation,
                    )
                    for identity, name, coefficients, rhs, relation in value[2]
                ),
                objective=value[3],
                sense=value[4],
                constant=value[5],
            )
        )

    def constraint_handles(self) -> BindingResult[list[_native.ConstraintHandle]]:
        """查询直接线性原约束的身份快照，不返回 solver 行 / Snapshot source identities, not solver rows."""
        return invoke(self._handle.constraint_handles)

    def constraint_index(
        self, *, handle: _native.ConstraintHandle
    ) -> BindingResult[int]:
        """检查身份并解析当前原约束索引 / Validate identity and resolve the current source index.

        Args:
            handle: 本模型的原约束身份 / Source-constraint identity from this model.

        Returns:
            当前原约束索引或失败，不是 solver 行号 / Current source index or failure, not a solver row.
        """
        return invoke(lambda: self._handle.constraint_index(handle=handle))

    def close(self) -> BindingResult[None]:
        """幂等关闭，忙时返回失败 / Close idempotently, failing when busy."""
        return invoke(self._handle.close)

    def create_projection(
        self, *, decisions: Sequence[ColumnDecisionSpec], blocks: Sequence[str]
    ) -> BindingResult[ColumnProjectionFloat64]:
        """创建源模型所有者持有的私有投影 / Create a private projection on the source owner.

        Args:
            decisions: 局部决策与来源变量 / Local decisions and source variables.
            blocks: 配置块身份 / Block identities.

        Returns:
            投影薄门面或失败 / Projection facade or failure.
        """
        inputs = [(item.id, item.block, item.variable) for item in decisions]
        return invoke(
            lambda: self._handle.create_projection(
                decisions=inputs, blocks=list(blocks)
            )
        ).map(ColumnProjectionFloat64)

    def add_variables(
        self, inputs: Sequence[VariableSpec]
    ) -> BindingResult[list[_native.VariableHandle]]:
        """原子批量注册 / Register a batch atomically.

        Args:
            inputs: 变量输入 / Variable inputs.

        Returns:
            不可变句柄或失败；失败不发布部分结果 / Handles or failure without partial publication.
        """
        converted = []
        for spec in inputs:
            bounds: list[float | None] = []
            for bound in (spec.lower, spec.upper):
                if bound is None:
                    bounds.append(None)
                else:
                    number = _number(bound)
                    if isinstance(number, Failed):
                        return Failed(number.error)
                    bounds.append(number.unwrap())
            converted.append((spec.name, spec.kind, bounds[0], bounds[1]))
        return invoke(lambda: self._handle.add_variables(converted))

    def add_constraints(self, inputs: Sequence[ConstraintSpec]) -> BindingResult[None]:
        """原子批量增加约束 / Add constraints atomically.

        Args:
            inputs: 约束输入 / Constraint inputs.

        Returns:
            unit 成功或失败 / Unit success or failure.
        """
        converted = []
        for spec in inputs:
            terms = _terms(spec.terms)
            rhs = _number(spec.rhs)
            if isinstance(terms, Failed):
                return Failed(terms.error)
            if isinstance(rhs, Failed):
                return Failed(rhs.error)
            converted.append((spec.name, terms.unwrap(), spec.relation, rhs.unwrap()))
        return invoke(lambda: self._handle.add_constraints(converted))

    def set_bounds(
        self,
        *,
        handle: _native.VariableHandle,
        lower: int | float | None,
        upper: int | float | None,
    ) -> BindingResult[None]:
        """替换变量范围 / Replace a variable's bounds.

        Args:
            handle: 模型内变量句柄 / Variable handle from this model.
            lower: 下界或 None / Lower bound or None.
            upper: 上界或 None / Upper bound or None.

        Returns:
            unit 成功或失败 / Unit success or failure.
        """
        bounds: list[float | None] = []
        for bound in (lower, upper):
            if bound is None:
                bounds.append(None)
            else:
                number = _number(bound)
                if isinstance(number, Failed):
                    return Failed(number.error)
                bounds.append(number.unwrap())
        return invoke(
            lambda: self._handle.set_bounds(
                handle=handle, lower=bounds[0], upper=bounds[1]
            )
        )

    def set_objective(
        self,
        *,
        terms: Sequence[tuple[_native.VariableHandle, int | float]],
        sense: str,
        name: str = "objective",
        constant: int | float = 0,
    ) -> BindingResult[None]:
        """验证后替换目标 / Replace the objective after validation.

        Args:
            terms: 项列表 / Terms.
            sense: minimize 或 maximize / Objective sense.
            name: 名称 / Name.
            constant: 常数项 / Constant term.

        Returns:
            unit 成功或失败 / Unit success or failure.
        """
        converted = _terms(terms)
        number = _number(constant)
        if isinstance(converted, Failed):
            return Failed(converted.error)
        if isinstance(number, Failed):
            return Failed(number.error)
        return invoke(
            lambda: self._handle.set_objective(
                terms=converted.unwrap(),
                sense=sense,
                name=name,
                constant=number.unwrap(),
            )
        )

    def solve(
        self,
        *,
        solver: str,
        time_limit: int | float | None = None,
        cancellation: SolveHandle | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> BindingResult[SolveReport]:
        """释放 GIL 调用真实 Rust solver / Call the real Rust solver with the GIL released.

        Args:
            solver: 显式选择已编译后端 / Explicit compiled backend name.
            time_limit: 可选秒数 / Optional limit in seconds.
            cancellation: 独立的单次取消句柄 / Independent single-attempt cancellation handle.
            on_progress: 只读快照回调，返回 None 或 unit Result / Snapshot callback returning None or a unit Result.

        Returns:
            正常终态报告或环境/输入失败，不静默回退 / Terminal report or failure, never fallback.
        """
        return self._solve(
            solver=solver,
            time_limit=time_limit,
            cancellation=cancellation,
            on_progress=on_progress,
            compiled=False,
            relaxed=False,
        ).map(
            lambda value: _report(
                identity=self.model_identity, generation=value[0], raw=value[1]
            )
        )

    def solve_compiled(
        self,
        *,
        solver: str,
        time_limit: int | float | None = None,
        cancellation: SolveHandle | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> BindingResult[CompiledSolveReport]:
        """求解同次编译的标准模型；报告目标是最小化口径 / Solve one compiled normalized-minimum model.

        Args:
            solver: 已编译后端 / Compiled backend.
            time_limit: 可选秒数 / Optional limit in seconds.
            cancellation: 单次取消句柄 / Single-attempt cancellation handle.
            on_progress: 只读进度回调 / Read-only progress callback.

        Returns:
            原始报告及证书 Result，或输入/环境失败 / Original report and certificate Result, or input/environment failure.
        """
        return self._solve(
            solver=solver,
            time_limit=time_limit,
            cancellation=cancellation,
            on_progress=on_progress,
            compiled=True,
            relaxed=False,
        ).map(
            lambda value: CompiledSolveReport(
                report=_report(
                    identity=self.model_identity, generation=value[0], raw=value[1]
                ),
                certificate=invoke(lambda: (value[2], value[3])),
            )
        )

    def solve_relaxed_compiled(
        self,
        *,
        solver: str,
        time_limit: int | float | None = None,
        cancellation: SolveHandle | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> BindingResult[CompiledSolveReport]:
        """求解同一快照的整数松弛编译模型 / Solve the integrality relaxation of one compiled snapshot.

        Args:
            solver: 已编译后端 / Compiled backend.
            time_limit: 可选秒数 / Optional limit in seconds.
            cancellation: 单次取消句柄 / Single-attempt cancellation handle.
            on_progress: 只读进度回调 / Read-only progress callback.

        Returns:
            原始报告及证书 Result，或输入/环境失败 / Original report and certificate Result, or input/environment failure.
        """
        return self._solve(
            solver=solver,
            time_limit=time_limit,
            cancellation=cancellation,
            on_progress=on_progress,
            compiled=True,
            relaxed=True,
        ).map(
            lambda value: CompiledSolveReport(
                report=_report(
                    identity=self.model_identity, generation=value[0], raw=value[1]
                ),
                certificate=invoke(lambda: (value[2], value[3])),
            )
        )

    def source_price(
        self, *, certificate: _native.DualCertificate, handle: _native.ConstraintHandle
    ) -> BindingResult[float]:
        """校验证书及源行后返回原目标口径的价格。

        Validate the certificate and return the source-objective price.
        拆行合并可能舍入，不能作为精确定价证明 / Split-row merging can round and is not an exact pricing proof.

        Args:
            certificate: 同模型未过期的原生证书 / Current native certificate from this model.
            handle: 原约束身份 / Source-constraint identity.

        Returns:
            价格或失败 / Price or failure.
        """
        return invoke(
            lambda: self._handle.source_price(certificate=certificate, handle=handle)
        )

    def _solve(
        self,
        *,
        solver: str,
        time_limit: int | float | None,
        cancellation: SolveHandle | None,
        on_progress: ProgressCallback | None,
        compiled: bool,
        relaxed: bool,
    ) -> BindingResult[
        tuple[int, str, _native.DualCertificate | None, _native.Failure | None]
    ]:
        def native_call(
            args: _NativeSolveArgs,
        ) -> tuple[
            tuple[int, str, _native.DualCertificate | None, _native.Failure | None]
            | None,
            _native.Failure | None,
        ]:
            if relaxed:
                return self._handle.solve_relaxed_compiled(
                    solver=args[0],
                    time_limit=args[1],
                    cancellation=args[2],
                    on_progress=args[3],
                )
            if compiled:
                return self._handle.solve_compiled(
                    solver=args[0],
                    time_limit=args[1],
                    cancellation=args[2],
                    on_progress=args[3],
                )
            value, error = self._handle.solve(
                solver=args[0],
                time_limit=args[1],
                cancellation=args[2],
                on_progress=args[3],
            )
            if value is None:
                return None, error
            return (value[0], value[1], None, None), error

        return _invoke_solve(
            solver=solver,
            time_limit=time_limit,
            cancellation=cancellation,
            on_progress=on_progress,
            call=native_call,
        )
