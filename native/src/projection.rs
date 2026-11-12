//! 列池与主问题只驻留在源模型所有者线程。 / Keep the column pool and master on the source owner thread.

use std::collections::{BTreeMap, BTreeSet};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Weak};

use num_rational::BigRational;
use num_traits::{ToPrimitive, Zero};
use ospf_rust_core::error::CoreError;
use ospf_rust_core::model::intermediate::LinearTriadModel;
use ospf_rust_core::model::{
    LinearModelCompilationFlt64, LinearModelSnapshot, LinearObjectiveEvaluationFlt64, MetaModel,
    ObjectiveCategory,
};
use ospf_rust_core::solver::{
    SolveReport, TerminationReason, linear_model_fingerprint, linear_model_mapping,
};
use ospf_rust_core::variable::VariableId;
use ospf_rust_framework::solver::column_projection::{
    ColumnDecision, ColumnMasterOptions, ColumnMasterRegistration, ColumnPricingRequest,
    ColumnProjection, ColumnProjectionRevision, ProjectedColumn,
};
use pyo3::prelude::*;

use crate::control::SolveHandle;
use crate::failure::{Failure, Transport, transport, transport_unit};
use crate::model::{Model, VariableHandle};
use crate::numeric::compare_rationals;
use crate::owner::Owner;
use crate::solve::SolveRequest;

type ColumnInput = (String, String, BTreeMap<String, f64>);
type MasterInfo = (u64, bool, usize, usize, usize, bool);
type MasterSolve = (u64, u64, String, Option<Failure>);
type PricingInfo = (String, BTreeMap<String, f64>, f64, BTreeMap<String, f64>);
type PricingCandidate = (BTreeMap<String, f64>, f64);
type PricingBoundInfo = (String, f64, f64, bool);
type PricingSolve = (
    u64,
    u64,
    String,
    Option<PricingCandidate>,
    Option<Failure>,
    Option<PricingBound>,
    Option<Failure>,
);
type IntegerSolve = (
    u64,
    u64,
    String,
    Option<ProjectionSolution>,
    Option<Failure>,
);
type PricedBatch = Vec<(PricingRequest, Vec<ColumnInput>)>;

pub(crate) struct ProjectionState {
    projection: ColumnProjection<f64>,
    master: Option<Master>,
    decisions: BTreeMap<VariableId, String>,
}

impl ProjectionState {
    pub(crate) fn new(
        projection: ColumnProjection<f64>,
        decisions: BTreeMap<VariableId, String>,
    ) -> Self {
        Self {
            projection,
            master: None,
            decisions,
        }
    }
}

struct Master {
    registration: ColumnMasterRegistration<f64>,
    generation: u64,
    integer: bool,
    phase_one: bool,
}

struct Lease {
    owner: Arc<Owner>,
    id: u64,
    closed: AtomicBool,
}

impl Drop for Lease {
    fn drop(&mut self) {
        if !self.closed.load(Ordering::Acquire) {
            self.owner.release_projection(self.id);
        }
    }
}

#[pyclass(frozen, module = "ospf_python._native", name = "ColumnProjection")]
pub struct Projection {
    lease: Arc<Lease>,
}

#[pyclass(
    frozen,
    from_py_object,
    module = "ospf_python._native",
    name = "ColumnPricingRequest"
)]
#[derive(Clone)]
pub struct PricingRequest {
    lease: Weak<Lease>,
    generation: u64,
    request: ColumnPricingRequest<f64>,
}

#[pyclass(
    frozen,
    from_py_object,
    module = "ospf_python._native",
    name = "ColumnPricingBound"
)]
#[derive(Clone)]
pub struct PricingBound {
    request: PricingRequest,
    reported_cx_lower: f64,
}

#[pyclass(
    frozen,
    from_py_object,
    module = "ospf_python._native",
    name = "ColumnProjectionSolution"
)]
#[derive(Clone)]
pub struct ProjectionSolution {
    lease: Weak<Lease>,
    generation: u64,
    revision: ColumnProjectionRevision,
    values: Arc<BTreeMap<VariableId, f64>>,
}

impl Projection {
    pub(crate) fn create(
        owner: Arc<Owner>,
        decisions: Vec<(String, String, VariableHandle)>,
        blocks: Vec<String>,
    ) -> Result<Self, Failure> {
        let provenance = Arc::clone(&owner.provenance);
        let id = owner.with_state(move |state| {
            let count = blocks.len();
            let blocks: BTreeSet<_> = blocks.into_iter().collect();
            if blocks.len() != count {
                return Err(Failure::input("配置块重复 / Duplicate projection block"));
            }
            let decisions = decisions
                .into_iter()
                .map(|(id, block_id, variable)| {
                    let index = Model::variable_index(&state.model, &variable, &provenance)?;
                    Ok(ColumnDecision {
                        id,
                        block_id,
                        variable: state.model.tokens()[index].id(),
                    })
                })
                .collect::<Result<Vec<_>, Failure>>()?;
            let identities = decisions
                .iter()
                .map(|decision| (decision.variable, decision.id.clone()))
                .collect();
            let projection =
                ColumnProjection::new(&state.model, decisions, blocks).map_err(Failure::from)?;
            state.insert_projection(ProjectionState::new(projection, identities))
        })?;
        Ok(Self {
            lease: Arc::new(Lease {
                owner,
                id,
                closed: AtomicBool::new(false),
            }),
        })
    }

    fn with_projection<T: Send + 'static>(
        &self,
        operation: impl FnOnce(&MetaModel<f64>, u64, &mut ProjectionState) -> Result<T, Failure>
        + Send
        + 'static,
    ) -> Result<T, Failure> {
        if self.lease.closed.load(Ordering::Acquire) {
            return Err(closed());
        }
        let id = self.lease.id;
        self.lease.owner.with_state(move |state| {
            let projection = state.projections.get_mut(&id).ok_or_else(closed)?;
            operation(&state.model, state.generation, projection)
        })
    }
}

fn closed() -> Failure {
    Failure::binding("NOT_INITIALIZED", "投影已关闭 / Projection is closed")
}

fn master_info(master: &Master) -> MasterInfo {
    (
        master.generation,
        master.integer,
        master.registration.column_variables().len(),
        master.registration.snapshot().variables.len(),
        master.registration.snapshot().rows.len(),
        master.phase_one,
    )
}

fn projected((id, block_id, values): ColumnInput) -> ProjectedColumn<f64> {
    ProjectedColumn {
        id,
        block_id,
        values,
    }
}

fn validate_tolerance(tolerance: f64) -> Result<(), Failure> {
    if !tolerance.is_finite() || !(0.0..0.5).contains(&tolerance) {
        return Err(Failure::input(
            "容差必须有限且在 [0, 0.5) / Tolerance must be finite and in [0, 0.5)",
        ));
    }
    Ok(())
}

fn validated_values(
    snapshot: &LinearModelSnapshot<f64>,
    compilation: &LinearModelCompilationFlt64,
    report: &SolveReport<f64>,
    tolerance: f64,
) -> Result<(BTreeMap<VariableId, f64>, LinearObjectiveEvaluationFlt64), Failure> {
    report.validate().map_err(Failure::from)?;
    if report.model_mapping.as_ref()
        != Some(&linear_model_mapping(&compilation.model).map_err(Failure::from)?)
        || report.fingerprints.model.as_ref()
            != Some(&linear_model_fingerprint(&compilation.model).map_err(Failure::from)?)
    {
        return Err(Failure::binding(
            "FAILED_PRECONDITION",
            "报告不属于本次编译模型 / Report does not match the compiled model",
        ));
    }
    let solution = report.solution.as_ref().ok_or_else(|| {
        Failure::binding(
            "NO_SOLUTION",
            "求解报告没有可行解 / Solve report has no incumbent",
        )
    })?;
    if solution.values.len() != snapshot.variables.len() {
        return Err(Failure::binding(
            "FAILED_PRECONDITION",
            "解向量维度不匹配 / Solution dimension mismatch",
        ));
    }
    let values: BTreeMap<_, _> = snapshot
        .variables
        .iter()
        .zip(&solution.values)
        .map(|(variable, value)| (variable.variable, *value))
        .collect();
    snapshot
        .validate_solution(&values, &tolerance)
        .map_err(Failure::from)?;
    let objective = snapshot
        .evaluate_objective_flt64(&values)
        .map_err(Failure::from)?;
    objective
        .validate_reported(solution.objective_value.or(solution.objective), tolerance)
        .map_err(Failure::from)?;
    Ok((values, objective))
}

fn reported_pricing_bound(
    snapshot: &LinearModelSnapshot<f64>,
    compilation: &LinearModelCompilationFlt64,
    report: &SolveReport<f64>,
    request: &ColumnPricingRequest<f64>,
    identities: &BTreeMap<VariableId, String>,
    values: &BTreeMap<String, f64>,
    cancelled: bool,
) -> Result<f64, Failure> {
    let rejected = || {
        Failure::binding(
            "FAILED_PRECONDITION",
            "定价界不可用或不一致 / Pricing bound is unavailable or inconsistent",
        )
    };
    if cancelled
        || report.termination_reason != TerminationReason::Completed
        || snapshot.objective_category != ObjectiveCategory::Minimum
        || compilation.model.objective_category != ObjectiveCategory::Minimum
        || snapshot.objective_constant != -*request.convexity_price()
        || compilation.objective_constant != snapshot.objective_constant
        || snapshot.variables.len() != request.coefficients().len()
        || compilation.model.c.len() != snapshot.variables.len()
        || values.keys().ne(request.coefficients().keys())
    {
        return Err(rejected());
    }
    let mut seen = BTreeSet::new();
    let mut variable_ids = BTreeSet::new();
    for (index, variable) in snapshot.variables.iter().enumerate() {
        let name = identities.get(&variable.variable).ok_or_else(rejected)?;
        let coefficient = request.coefficients().get(name).ok_or_else(rejected)?;
        if !seen.insert(name)
            || !variable_ids.insert(variable.variable)
            || snapshot
                .objective
                .get(&variable.variable)
                .copied()
                .unwrap_or(0.0)
                != *coefficient
            || compilation.model.c[index] != *coefficient
        {
            return Err(rejected());
        }
    }
    if snapshot
        .objective
        .keys()
        .any(|id| !variable_ids.contains(id))
    {
        return Err(rejected());
    }
    let bound = match (
        report.statistics.best_bound,
        report.statistics.best_bound_value,
    ) {
        (Some(typed), Some(value)) if value.is_finite() && typed == value => value,
        _ => return Err(rejected()),
    };
    let floor = LinearObjectiveEvaluationFlt64::new(
        request
            .coefficients()
            .iter()
            .map(|(name, coefficient)| (*coefficient, values[name])),
        0.0,
    )
    .map_err(Failure::from)?
    .lower_bound()
    .map_err(Failure::from)?;
    if bound > floor {
        return Err(rejected());
    }
    Ok(bound)
}

fn current_master<'a>(
    source: &MetaModel<f64>,
    generation: u64,
    projection: &ColumnProjection<f64>,
    master: Option<&'a Master>,
) -> Result<&'a Master, Failure> {
    let master = master.ok_or_else(|| {
        Failure::binding(
            "FAILED_PRECONDITION",
            "主问题不存在或已失效 / Master is absent or stale",
        )
    })?;
    if master.generation != generation {
        return Err(Failure::binding(
            "FAILED_PRECONDITION",
            "源模型已修改，主问题失效 / Source changed; master is stale",
        ));
    }
    projection
        .require_current(source, &master.registration)
        .map_err(Failure::from)?;
    Ok(master)
}

fn current_pricing(
    source: &MetaModel<f64>,
    generation: u64,
    state: &ProjectionState,
    lease: &Weak<Lease>,
    request: &PricingRequest,
) -> Result<(), Failure> {
    if !Weak::ptr_eq(lease, &request.lease) {
        return Err(Failure::input(
            "定价请求属于其他投影 / Pricing request belongs to another projection",
        ));
    }
    let master = current_master(source, generation, &state.projection, state.master.as_ref())?;
    if request.generation != generation {
        return Err(Failure::binding(
            "FAILED_PRECONDITION",
            "源模型已修改，定价请求失效 / Source changed; pricing request is stale",
        ));
    }
    state
        .projection
        .require_pricing_current(source, Some(&master.registration), &request.request)
        .map_err(Failure::from)
}

fn create_pricing_request(
    source: &MetaModel<f64>,
    generation: u64,
    state: &ProjectionState,
    lease: Weak<Lease>,
    block: &str,
) -> Result<PricingRequest, Failure> {
    let master = current_master(source, generation, &state.projection, state.master.as_ref())?;
    let request = state
        .projection
        .pricing_request(source, Some(&master.registration), block, master.phase_one)
        .map_err(Failure::from)?;
    let snapshot = state.projection.snapshot(source).map_err(Failure::from)?;
    let expected_rows: BTreeSet<_> = snapshot.rows.iter().map(|row| &row.id).collect();
    if request.row_prices().keys().collect::<BTreeSet<_>>() != expected_rows {
        return Err(Failure::binding(
            "FAILED_PRECONDITION",
            "定价行映射不完整 / Incomplete pricing row mapping",
        ));
    }
    let mut seen = BTreeSet::new();
    for (variable, name) in &state.decisions {
        let Some(coefficient) = request.coefficients().get(name) else {
            continue;
        };
        if !seen.insert(name) {
            return Err(Failure::binding(
                "FAILED_PRECONDITION",
                "定价决策重复 / Duplicate pricing decision",
            ));
        }
        let mut expected = if master.phase_one {
            BigRational::zero()
        } else {
            crate::dual::exact(snapshot.objective.get(variable).copied().unwrap_or(0.0))?
        };
        for row in &snapshot.rows {
            if let Some(value) = row.coefficients.get(variable) {
                expected -= crate::dual::exact(request.row_prices()[&row.id])?
                    * crate::dual::exact(*value)?;
            }
        }
        if !compare_rationals(&expected, &crate::dual::exact(*coefficient)?).is_eq() {
            return Err(Failure::binding(
                "FAILED_PRECONDITION",
                "定价系数与精确值不一致 / Pricing coefficient differs from its exact value",
            ));
        }
    }
    if seen.len() != request.coefficients().len() {
        return Err(Failure::binding(
            "FAILED_PRECONDITION",
            "定价决策映射不完整 / Incomplete pricing decision mapping",
        ));
    }
    Ok(PricingRequest {
        lease,
        generation,
        request,
    })
}

fn reduced_cost(
    request: &ColumnPricingRequest<f64>,
    values: &BTreeMap<String, f64>,
) -> Result<f64, Failure> {
    if values.keys().ne(request.coefficients().keys()) || values.values().any(|v| !v.is_finite()) {
        return Err(Failure::input(
            "定价向量必须完整且有限 / Pricing vector must be complete and finite",
        ));
    }
    let mut result = -crate::dual::exact(*request.convexity_price())?;
    for (id, coefficient) in request.coefficients() {
        result += crate::dual::exact(*coefficient)? * crate::dual::exact(values[id])?;
    }
    result
        .to_f64()
        .filter(|value| value.is_finite() && (*value != 0.0 || result.is_zero()))
        .ok_or_else(|| {
            Failure::binding(
                "FAILED_PRECONDITION",
                "检验数超出有效 Float64 范围 / Reduced cost is outside the usable Float64 range",
            )
        })
}

fn require_exact_contributions(
    source: &MetaModel<f64>,
    projection: &ColumnProjection<f64>,
    master: &ColumnMasterRegistration<f64>,
    decisions: &BTreeMap<VariableId, String>,
    phase_one: bool,
) -> Result<(), Failure> {
    let source = projection.snapshot(source).map_err(Failure::from)?;
    let snapshot = master.snapshot();
    let rejected = || {
        Failure::binding(
            "FAILED_PRECONDITION",
            "主问题列贡献不精确 / Master column contribution is inexact",
        )
    };
    if projection.columns().len() != master.column_variables().len()
        || source.rows.len() != master.source_rows().len()
    {
        return Err(rejected());
    }
    let master_rows: BTreeMap<_, _> = snapshot.rows.iter().map(|row| (&row.id, row)).collect();
    for column in projection.columns() {
        let variable = master
            .column_variables()
            .get(&column.id)
            .ok_or_else(rejected)?;
        let mut inputs = Vec::new();
        for (id, name) in decisions {
            if let Some(value) = column.values.get(name) {
                inputs.push((*id, crate::dual::exact(*value)?));
            }
        }
        if inputs.len() != column.values.len() {
            return Err(rejected());
        }
        let contribution = |coefficients: &BTreeMap<VariableId, f64>| {
            inputs
                .iter()
                .try_fold(BigRational::zero(), |sum, (id, value)| {
                    match coefficients.get(id) {
                        Some(coefficient) if !value.is_zero() => {
                            Ok::<_, Failure>(sum + crate::dual::exact(*coefficient)? * value)
                        }
                        _ => Ok(sum),
                    }
                })
        };
        let expected_objective = if phase_one {
            BigRational::zero()
        } else {
            contribution(&source.objective)?
        };
        let actual = snapshot.objective.get(variable).copied().unwrap_or(0.0);
        if !compare_rationals(&expected_objective, &crate::dual::exact(actual)?).is_eq() {
            return Err(rejected());
        }
        for row in &source.rows {
            let master_id = master.source_rows().get(&row.id).ok_or_else(rejected)?;
            let master_row = master_rows.get(master_id).ok_or_else(rejected)?;
            let actual = master_row
                .coefficients
                .get(variable)
                .copied()
                .unwrap_or(0.0);
            if !compare_rationals(
                &contribution(&row.coefficients)?,
                &crate::dual::exact(actual)?,
            )
            .is_eq()
            {
                return Err(rejected());
            }
        }
    }
    Ok(())
}

fn solve_master<F>(
    projection: &mut ColumnProjection<f64>,
    source: &MetaModel<f64>,
    master: &ColumnMasterRegistration<f64>,
    decisions: &BTreeMap<VariableId, String>,
    phase_one: bool,
    solve: F,
) -> Result<(String, Option<Failure>), Failure>
where
    F: FnOnce(&LinearTriadModel) -> Result<(SolveReport<f64>, bool), Failure>,
{
    let mut captured = None;
    let mut rejection = None;
    let contributions =
        require_exact_contributions(source, projection, master, decisions, phase_one);
    let result = projection.solve_master_lp(source, master, |compiled| {
        let (report, cancelled) = match solve(compiled) {
            Ok(result) => result,
            Err(error) => {
                captured = Some(Err(error));
                return Err(CoreError::Internal("solver boundary failed".into()));
            }
        };
        captured = Some(crate::solve::serialize(&report));
        if captured.as_ref().is_some_and(Result::is_err) {
            return Err(CoreError::Internal("report serialization failed".into()));
        }
        if report.termination_reason != TerminationReason::Completed || cancelled {
            rejection = Some(Failure::binding(
                "FAILED_PRECONDITION",
                "求解未完成或已取消，不能定价 / Incomplete or cancelled solve cannot price",
            ));
            return Err(CoreError::Internal("pricing gate rejected report".into()));
        }
        let verification = (|| {
            let dual = crate::dual::require_exact_lp(&report, compiled)?;
            let compilation = master.snapshot().compile_flt64().map_err(Failure::from)?;
            if linear_model_fingerprint(compiled).map_err(Failure::from)?
                != linear_model_fingerprint(&compilation.model).map_err(Failure::from)?
                || linear_model_mapping(compiled).map_err(Failure::from)?
                    != linear_model_mapping(&compilation.model).map_err(Failure::from)?
            {
                return Err(Failure::binding(
                    "FAILED_PRECONDITION",
                    "主问题编译不一致 / Master compilation differs",
                ));
            }
            crate::dual::source_prices(master.snapshot(), &compilation, dual, false)?;
            contributions
        })();
        if let Err(error) = verification {
            rejection = Some(error);
            return Err(CoreError::Internal(
                "exact pricing gate rejected report".into(),
            ));
        }
        Ok(report)
    });
    match captured {
        Some(Ok(raw)) => Ok((
            raw,
            result
                .err()
                .map(|error| rejection.unwrap_or_else(|| error.into())),
        )),
        Some(Err(error)) => Err(error),
        None => match result {
            Err(error) => Err(error.into()),
            Ok(_) => Err(Failure::binding(
                "APPLICATION_ERROR",
                "求解报告缺失 / Solve report is missing",
            )),
        },
    }
}

#[pymethods]
impl Projection {
    fn close(&self, py: Python<'_>) -> Transport<()> {
        transport_unit(py.detach(|| {
            if self.lease.closed.load(Ordering::Acquire) {
                return Ok(());
            }
            self.lease.owner.close_projection(self.lease.id)?;
            self.lease.closed.store(true, Ordering::Release);
            Ok(())
        }))
    }

    fn columns(&self, py: Python<'_>) -> Transport<Vec<ColumnInput>> {
        transport(py.detach(|| {
            self.with_projection(|_, _, state| {
                Ok(state
                    .projection
                    .columns()
                    .iter()
                    .map(|column| {
                        (
                            column.id.clone(),
                            column.block_id.clone(),
                            column.values.clone(),
                        )
                    })
                    .collect())
            })
        }))
    }

    fn add_columns(&self, py: Python<'_>, inputs: Vec<ColumnInput>) -> Transport<()> {
        transport_unit(py.detach(|| {
            self.with_projection(move |source, _, state| {
                let changed = !inputs.is_empty();
                let columns = inputs.into_iter().map(projected).collect();
                state
                    .projection
                    .add_columns(source, columns)
                    .map_err(Failure::from)?;
                if changed {
                    state.master = None;
                }
                Ok(())
            })
        }))
    }

    fn remove_columns(&self, py: Python<'_>, ids: Vec<String>) -> Transport<()> {
        transport_unit(py.detach(|| {
            self.with_projection(move |_, _, state| {
                let ids: BTreeSet<_> = ids.into_iter().collect();
                state
                    .projection
                    .remove_columns(&ids)
                    .map_err(Failure::from)?;
                if !ids.is_empty() {
                    state.master = None;
                }
                Ok(())
            })
        }))
    }

    #[pyo3(signature = (*, integer=false, phase_one=false))]
    fn build_master(
        &self,
        py: Python<'_>,
        integer: bool,
        phase_one: bool,
    ) -> Transport<MasterInfo> {
        transport(py.detach(|| {
            self.with_projection(move |source, generation, state| {
                let registration = state
                    .projection
                    .master(
                        source,
                        ColumnMasterOptions {
                            integer,
                            phase_one,
                            ..Default::default()
                        },
                    )
                    .map_err(Failure::from)?;
                let master = Master {
                    registration,
                    generation,
                    integer,
                    phase_one,
                };
                let info = master_info(&master);
                state.master = Some(master);
                Ok(info)
            })
        }))
    }

    fn master_info(&self, py: Python<'_>) -> Transport<MasterInfo> {
        transport(py.detach(|| {
            self.with_projection(|source, generation, state| {
                let master =
                    current_master(source, generation, &state.projection, state.master.as_ref())?;
                Ok(master_info(master))
            })
        }))
    }

    #[pyo3(signature = (*, solver, time_limit=None, cancellation=None, on_progress=None))]
    fn solve_master_lp(
        &self,
        py: Python<'_>,
        solver: String,
        time_limit: Option<f64>,
        cancellation: Option<SolveHandle>,
        on_progress: Option<Py<PyAny>>,
    ) -> Transport<MasterSolve> {
        if on_progress
            .as_ref()
            .is_some_and(|callback| !callback.bind(py).is_callable())
        {
            return transport(Err(Failure::input(
                "进度回调必须可调用 / Progress callback must be callable",
            )));
        }
        let request = SolveRequest {
            solver,
            time_limit,
            cancellation,
            on_progress,
        };
        transport(py.detach(|| {
            self.with_projection(move |source, generation, state| {
                let ProjectionState {
                    projection,
                    master,
                    decisions,
                } = state;
                let master = current_master(source, generation, projection, master.as_ref())?;
                let identity = master.registration.model().model_identity();
                let cancellation = request.cancellation.clone();
                let (raw, error) = solve_master(
                    projection,
                    source,
                    &master.registration,
                    decisions,
                    master.phase_one,
                    |compiled| {
                        let report = crate::solve::execute(
                            master.registration.model(),
                            request,
                            Some(compiled),
                        )?;
                        let cancelled = cancellation.as_ref().is_some_and(|handle| {
                            handle.inner().cancellation_preceded_completion()
                        });
                        Ok((report, cancelled))
                    },
                )?;
                Ok((identity, generation, raw, error))
            })
        }))
    }

    #[pyo3(signature = (*, block))]
    fn pricing_request(&self, py: Python<'_>, block: String) -> Transport<PricingRequest> {
        let lease = Arc::downgrade(&self.lease);
        transport(py.detach(|| {
            self.with_projection(move |source, generation, state| {
                create_pricing_request(source, generation, state, lease, &block)
            })
        }))
    }

    #[pyo3(signature = (*, request))]
    fn pricing_info(&self, py: Python<'_>, request: PricingRequest) -> Transport<PricingInfo> {
        let lease = Arc::downgrade(&self.lease);
        transport(py.detach(|| {
            self.with_projection(move |source, generation, state| {
                current_pricing(source, generation, state, &lease, &request)?;
                Ok((
                    request.request.block_id().to_owned(),
                    request.request.coefficients().clone(),
                    *request.request.convexity_price(),
                    request.request.row_prices().clone(),
                ))
            })
        }))
    }

    #[pyo3(signature = (*, request, values))]
    fn reduced_cost(
        &self,
        py: Python<'_>,
        request: PricingRequest,
        values: BTreeMap<String, f64>,
    ) -> Transport<f64> {
        let lease = Arc::downgrade(&self.lease);
        transport(py.detach(|| {
            self.with_projection(move |source, generation, state| {
                current_pricing(source, generation, state, &lease, &request)?;
                reduced_cost(&request.request, &values)
            })
        }))
    }

    #[pyo3(signature = (*, bound))]
    fn pricing_bound_info(
        &self,
        py: Python<'_>,
        bound: PricingBound,
    ) -> Transport<PricingBoundInfo> {
        let lease = Arc::downgrade(&self.lease);
        transport(py.detach(|| {
            self.with_projection(move |source, generation, state| {
                current_pricing(source, generation, state, &lease, &bound.request)?;
                let request = &bound.request.request;
                let price = *request.convexity_price();
                Ok((
                    request.block_id().to_owned(),
                    bound.reported_cx_lower,
                    price,
                    bound.reported_cx_lower >= price,
                ))
            })
        }))
    }

    // PyO3 需要独立命名参数。 / PyO3 requires distinct keyword arguments.
    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (*, request, solver, time_limit=None, cancellation=None, on_progress=None, tolerance=1e-7))]
    fn solve_pricing(
        &self,
        py: Python<'_>,
        request: PricingRequest,
        solver: String,
        time_limit: Option<f64>,
        cancellation: Option<SolveHandle>,
        on_progress: Option<Py<PyAny>>,
        tolerance: f64,
    ) -> Transport<PricingSolve> {
        if let Err(error) = validate_tolerance(tolerance) {
            return transport(Err(error));
        }
        if on_progress
            .as_ref()
            .is_some_and(|callback| !callback.bind(py).is_callable())
        {
            return transport(Err(Failure::input(
                "进度回调必须可调用 / Progress callback must be callable",
            )));
        }
        let solve = SolveRequest {
            solver,
            time_limit,
            cancellation,
            on_progress,
        };
        let lease = Arc::downgrade(&self.lease);
        transport(py.detach(|| {
            self.with_projection(move |source, generation, state| {
                current_pricing(source, generation, state, &lease, &request)?;
                let master =
                    current_master(source, generation, &state.projection, state.master.as_ref())?;
                let model = state
                    .projection
                    .pricing_model(source, Some(&master.registration), &request.request)
                    .map_err(Failure::from)?;
                let snapshot = model.linear_model_snapshot().map_err(Failure::from)?;
                let compilation = snapshot.compile_flt64().map_err(Failure::from)?;
                let cancellation = solve.cancellation.clone();
                let report = crate::solve::execute(&model, solve, Some(&compilation.model))?;
                let raw = crate::solve::serialize(&report)?;
                let candidate = (|| {
                    let (values, objective) =
                        validated_values(&snapshot, &compilation, &report, tolerance)?;
                    let decisions: BTreeMap<_, _> = values
                        .iter()
                        .map(|(id, value)| {
                            state
                                .decisions
                                .get(id)
                                .cloned()
                                .map(|name| (name, *value))
                                .ok_or_else(|| {
                                    Failure::binding(
                                        "FAILED_PRECONDITION",
                                        "定价变量来源未知 / Unknown pricing variable identity",
                                    )
                                })
                        })
                        .collect::<Result<_, _>>()?;
                    if decisions.keys().ne(request.request.coefficients().keys()) {
                        return Err(Failure::binding(
                            "FAILED_PRECONDITION",
                            "定价变量映射不完整 / Incomplete pricing variable mapping",
                        ));
                    }
                    let expected = LinearObjectiveEvaluationFlt64::new(
                        request
                            .request
                            .coefficients()
                            .iter()
                            .map(|(id, coefficient)| (*coefficient, decisions[id])),
                        -*request.request.convexity_price(),
                    )
                    .map_err(Failure::from)?;
                    objective
                        .validate_total(&expected, tolerance)
                        .map_err(Failure::from)?;
                    let cost = reduced_cost(&request.request, &decisions)?;
                    Ok((decisions, cost))
                })();
                let bound = candidate
                    .as_ref()
                    .map_err(Clone::clone)
                    .and_then(|(values, _)| {
                        reported_pricing_bound(
                            &snapshot,
                            &compilation,
                            &report,
                            &request.request,
                            &state.decisions,
                            values,
                            cancellation.as_ref().is_some_and(|handle| {
                                handle.inner().cancellation_preceded_completion()
                            }),
                        )
                        .map(|reported_cx_lower| PricingBound {
                            request,
                            reported_cx_lower,
                        })
                    });
                let (candidate, error) = transport(candidate);
                let (bound, bound_error) = transport(bound);
                Ok((
                    model.model_identity(),
                    generation,
                    raw,
                    candidate,
                    error,
                    bound,
                    bound_error,
                ))
            })
        }))
    }

    fn add_priced_batch(&self, py: Python<'_>, batches: PricedBatch) -> Transport<()> {
        let lease = Arc::downgrade(&self.lease);
        transport_unit(py.detach(|| {
            self.with_projection(move |source, generation, state| {
                for (request, _) in &batches {
                    current_pricing(source, generation, state, &lease, request)?;
                }
                for (request, columns) in &batches {
                    for (_, _, values) in columns {
                        reduced_cost(&request.request, values)?;
                    }
                }
                let changed = batches.iter().any(|(_, columns)| !columns.is_empty());
                let batches = batches
                    .into_iter()
                    .map(|(request, columns)| {
                        (
                            request.request,
                            columns.into_iter().map(projected).collect(),
                        )
                    })
                    .collect();
                let ProjectionState {
                    projection, master, ..
                } = state;
                let registration =
                    &current_master(source, generation, projection, master.as_ref())?.registration;
                projection
                    .add_priced_batch(source, registration, batches)
                    .map_err(Failure::from)?;
                if changed {
                    *master = None;
                }
                Ok(())
            })
        }))
    }

    #[pyo3(signature = (*, solver, time_limit=None, cancellation=None, on_progress=None, tolerance=1e-7))]
    fn solve_master_integer(
        &self,
        py: Python<'_>,
        solver: String,
        time_limit: Option<f64>,
        cancellation: Option<SolveHandle>,
        on_progress: Option<Py<PyAny>>,
        tolerance: f64,
    ) -> Transport<IntegerSolve> {
        if let Err(error) = validate_tolerance(tolerance) {
            return transport(Err(error));
        }
        if on_progress
            .as_ref()
            .is_some_and(|callback| !callback.bind(py).is_callable())
        {
            return transport(Err(Failure::input(
                "进度回调必须可调用 / Progress callback must be callable",
            )));
        }
        let solve = SolveRequest {
            solver,
            time_limit,
            cancellation,
            on_progress,
        };
        let lease = Arc::downgrade(&self.lease);
        transport(py.detach(|| {
            self.with_projection(move |source, generation, state| {
                let master =
                    current_master(source, generation, &state.projection, state.master.as_ref())?;
                if !master.integer {
                    return Err(Failure::binding(
                        "FAILED_PRECONDITION",
                        "主问题不是整数模型 / Master is not an integer model",
                    ));
                }
                let compilation = master
                    .registration
                    .snapshot()
                    .compile_flt64()
                    .map_err(Failure::from)?;
                let report = crate::solve::execute(
                    master.registration.model(),
                    solve,
                    Some(&compilation.model),
                )?;
                let raw = crate::solve::serialize(&report)?;
                let solution = (|| {
                    let (_, objective) = validated_values(
                        master.registration.snapshot(),
                        &compilation,
                        &report,
                        tolerance,
                    )?;
                    let values = &report
                        .solution
                        .as_ref()
                        .ok_or_else(|| {
                            Failure::binding("NO_SOLUTION", "缺少解 / Missing solution")
                        })?
                        .values;
                    let original = state
                        .projection
                        .extract_solution(source, &master.registration, values, &tolerance)
                        .map_err(Failure::from)?;
                    let source_objective = state
                        .projection
                        .snapshot(source)
                        .and_then(|snapshot| snapshot.evaluate_objective_flt64(&original))
                        .map_err(Failure::from)?;
                    objective
                        .validate_total(&source_objective, tolerance)
                        .map_err(Failure::from)?;
                    Ok(ProjectionSolution {
                        lease,
                        generation,
                        revision: master.registration.revision(),
                        values: Arc::new(original),
                    })
                })();
                let (solution, error) = transport(solution);
                Ok((
                    master.registration.model().model_identity(),
                    generation,
                    raw,
                    solution,
                    error,
                ))
            })
        }))
    }

    #[pyo3(signature = (*, solution, handle))]
    fn solution_value(
        &self,
        py: Python<'_>,
        solution: ProjectionSolution,
        handle: VariableHandle,
    ) -> Transport<f64> {
        let lease = Arc::downgrade(&self.lease);
        let provenance = Arc::clone(&self.lease.owner.provenance);
        transport(py.detach(|| {
            self.with_projection(move |source, generation, state| {
                if !Weak::ptr_eq(&lease, &solution.lease) {
                    return Err(Failure::input(
                        "解属于其他投影 / Solution belongs to another projection",
                    ));
                }
                let master =
                    current_master(source, generation, &state.projection, state.master.as_ref())?;
                if !master.integer
                    || solution.generation != generation
                    || solution.revision != master.registration.revision()
                {
                    return Err(Failure::binding(
                        "FAILED_PRECONDITION",
                        "主问题已修改，解失效 / Master changed; solution is stale",
                    ));
                }
                let index = Model::variable_index(source, &handle, &provenance)?;
                solution
                    .values
                    .get(&source.tokens()[index].id())
                    .copied()
                    .ok_or_else(|| {
                        Failure::binding("NOT_FOUND", "解不含此变量 / Solution lacks this variable")
                    })
            })
        }))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ospf_rust_core::model::LinearObjectiveInput;
    use ospf_rust_core::solver::{
        ProblemStatus, SolveFingerprints, SolveProof, SolveSolution, SolveStatistics,
        require_optimal_lp_certificate_for_linear_model,
    };
    use ospf_rust_core::variable::Binary;
    use std::sync::mpsc::sync_channel;

    fn zero_report(model: &LinearTriadModel, dual: Vec<f64>) -> SolveReport<f64> {
        let mut solution = SolveSolution::vector(vec![1.0; model.num_variables()]);
        solution.objective_value = Some(0.0);
        solution.dual_solution = Some(dual);
        SolveReport::builder(ProblemStatus::Feasible, TerminationReason::Completed)
            .solution(solution)
            .proof(SolveProof::optimality())
            .model_mapping(Some(linear_model_mapping(model).unwrap()))
            .fingerprints(SolveFingerprints {
                model: Some(linear_model_fingerprint(model).unwrap()),
                ..Default::default()
            })
            .build()
            .unwrap()
    }

    #[test]
    fn synthetic_split_price_rounding_clears_master_pricing() {
        let mut source = MetaModel::<f64>::new("split price rounding");
        let x = source.register_auto_variable::<Binary>("x").unwrap();
        let identities = BTreeMap::from([(source.tokens()[x].id(), "x".to_owned())]);
        source
            .add_linear_constraint(
                &[],
                ospf_rust_core::model::ConstraintRelation::Equal,
                0.0,
                "row",
            )
            .unwrap();
        source.set_linear_objective_input(LinearObjectiveInput::minimize("zero"));
        let mut projection = ColumnProjection::new(
            &source,
            vec![ColumnDecision {
                id: "x".into(),
                block_id: "a".into(),
                variable: source.tokens()[x].id(),
            }],
            BTreeSet::from(["a".into()]),
        )
        .unwrap();
        projection
            .add_columns(
                &source,
                vec![ProjectedColumn {
                    id: "zero".into(),
                    block_id: "a".into(),
                    values: BTreeMap::from([("x".into(), 0.0)]),
                }],
            )
            .unwrap();
        let master = projection
            .master(&source, ColumnMasterOptions::default())
            .unwrap();
        let compilation = master.snapshot().compile_flt64().unwrap();
        let source_row = master.source_rows().values().next().unwrap();
        let positions: Vec<_> = compilation
            .rows
            .iter()
            .enumerate()
            .filter(|(_, row)| &row.source == source_row)
            .map(|(index, _)| index)
            .collect();
        assert_eq!(positions.len(), 2);
        let make = |model: &LinearTriadModel, small: f64| {
            let mut dual = vec![0.0; model.num_constraints()];
            dual[positions[0]] = -1.0;
            dual[positions[1]] = -small;
            zero_report(model, dual)
        };
        assert!(
            solve_master(
                &mut projection,
                &source,
                &master,
                &identities,
                false,
                |model| { Ok((make(model, 0.0), false)) }
            )
            .unwrap()
            .1
            .is_none()
        );
        let old = projection
            .pricing_request(&source, Some(&master), "a", false)
            .unwrap();
        let (_, error) = solve_master(
            &mut projection,
            &source,
            &master,
            &identities,
            false,
            |model| {
                let report = make(model, 2.0_f64.powi(-54));
                assert!(crate::dual::require_exact_lp(&report, model).is_ok());
                Ok((report, false))
            },
        )
        .unwrap();
        assert!(error.is_some());
        assert!(
            projection
                .pricing_request(&source, Some(&master), "a", false)
                .is_err()
        );
        assert!(
            projection
                .require_pricing_current(&source, Some(&master), &old)
                .is_err()
        );
    }

    #[test]
    fn synthetic_rounded_master_contributions_do_not_issue_pricing() {
        for objective_case in [false, true] {
            let mut source = MetaModel::<f64>::new("master contribution rounding");
            let vars: Vec<_> = ["x", "y", "z"]
                .into_iter()
                .map(|name| source.register_auto_variable::<Binary>(name).unwrap())
                .collect();
            let terms = vec![(vars[0], 1e16), (vars[1], 1.0), (vars[2], -1e16)];
            if objective_case {
                source.set_linear_objective_input(
                    LinearObjectiveInput::minimize("cost").terms(terms),
                );
            } else {
                source.add_le_constraint(&terms, 1.0, "row").unwrap();
                source.set_linear_objective_input(LinearObjectiveInput::minimize("zero"));
            }
            let decisions: Vec<_> = ["x", "y", "z"]
                .into_iter()
                .zip(&vars)
                .map(|(id, index)| ColumnDecision {
                    id: id.into(),
                    block_id: "a".into(),
                    variable: source.tokens()[*index].id(),
                })
                .collect();
            let identities = decisions
                .iter()
                .map(|d| (d.variable, d.id.clone()))
                .collect();
            let mut projection =
                ColumnProjection::new(&source, decisions, BTreeSet::from(["a".into()])).unwrap();
            projection
                .add_columns(
                    &source,
                    vec![ProjectedColumn {
                        id: "one".into(),
                        block_id: "a".into(),
                        values: BTreeMap::from([
                            ("x".into(), 1.0),
                            ("y".into(), 1.0),
                            ("z".into(), 1.0),
                        ]),
                    }],
                )
                .unwrap();
            let master = projection
                .master(&source, ColumnMasterOptions::default())
                .unwrap();
            projection
                .solve_master_lp(&source, &master, |model| {
                    Ok(zero_report(model, vec![0.0; model.num_constraints()]))
                })
                .unwrap();
            let old = projection
                .pricing_request(&source, Some(&master), "a", false)
                .unwrap();
            let (_, error) = solve_master(
                &mut projection,
                &source,
                &master,
                &identities,
                false,
                |model| {
                    assert_eq!(model.c[0], 0.0);
                    let report = zero_report(model, vec![0.0; model.num_constraints()]);
                    assert!(crate::dual::require_exact_lp(&report, model).is_ok());
                    Ok((report, false))
                },
            )
            .unwrap();
            assert!(error.is_some(), "objective case: {objective_case}");
            assert!(
                projection
                    .require_pricing_current(&source, Some(&master), &old)
                    .is_err()
            );
            assert!(
                projection
                    .pricing_request(&source, Some(&master), "a", false)
                    .is_err()
            );
        }
    }

    #[test]
    fn master_contributions_cover_phase_one_and_global_cross_rows() {
        use ospf_rust_core::variable::{Continuous, VariableRange};

        let check = |phase_one, with_row, value| {
            let mut source = MetaModel::<f64>::new("phase-one contribution");
            let x = source
                .register_auto_variable_with_range::<Continuous>(
                    "x",
                    VariableRange::bounded(0.0, 1.0),
                )
                .unwrap();
            let global = source
                .register_auto_variable_with_range::<Continuous>(
                    "global",
                    VariableRange::bounded(0.0, 1.0),
                )
                .unwrap();
            if with_row {
                source
                    .add_le_constraint(&[(x, 0.1), (global, 1.0)], 1.0, "cross")
                    .unwrap();
            }
            source.set_linear_objective_input(
                LinearObjectiveInput::minimize("cost").terms(vec![(x, 0.1)]),
            );
            let id = source.tokens()[x].id();
            let identities = BTreeMap::from([(id, "x".to_owned())]);
            let mut projection = ColumnProjection::new(
                &source,
                vec![ColumnDecision {
                    id: "x".into(),
                    block_id: "a".into(),
                    variable: id,
                }],
                BTreeSet::from(["a".into()]),
            )
            .unwrap();
            projection
                .add_columns(
                    &source,
                    vec![ProjectedColumn {
                        id: "column".into(),
                        block_id: "a".into(),
                        values: BTreeMap::from([("x".into(), value)]),
                    }],
                )
                .unwrap();
            let master = projection
                .master(
                    &source,
                    ColumnMasterOptions {
                        phase_one,
                        ..Default::default()
                    },
                )
                .unwrap();
            assert_eq!(master.global_variables().len(), 1);
            require_exact_contributions(&source, &projection, &master, &identities, phase_one)
        };
        assert!(check(true, false, 0.3).is_ok());
        assert!(check(false, false, 0.3).is_err());
        assert!(check(true, true, 0.3).is_err());
        assert!(check(true, true, 0.5).is_ok());
        assert!(check(false, true, 0.5).is_ok());
    }

    #[test]
    fn synthetic_rounded_pricing_coefficients_are_not_published() {
        let eps = 2.0_f64.powi(-52);
        let mut source = MetaModel::<f64>::new("pricing coefficient rounding");
        let x = source.register_auto_variable::<Binary>("x").unwrap();
        let y = source.register_auto_variable::<Binary>("y").unwrap();
        source
            .add_le_constraint(&[(x, -1.0 - eps), (y, 1.0)], 0.0, "cross")
            .unwrap();
        source.set_linear_objective_input(
            LinearObjectiveInput::minimize("cost").terms(vec![(x, 1.0 + 2.0 * eps)]),
        );
        let decisions: Vec<_> = [("x", "a", x), ("y", "b", y)]
            .into_iter()
            .map(|(id, block, index)| ColumnDecision {
                id: id.into(),
                block_id: block.into(),
                variable: source.tokens()[index].id(),
            })
            .collect();
        let identities = decisions
            .iter()
            .map(|d| (d.variable, d.id.clone()))
            .collect();
        let mut projection =
            ColumnProjection::new(&source, decisions, BTreeSet::from(["a".into(), "b".into()]))
                .unwrap();
        projection
            .add_columns(
                &source,
                [("x0", "a", "x"), ("y0", "b", "y")]
                    .into_iter()
                    .map(|(id, block, name)| ProjectedColumn {
                        id: id.into(),
                        block_id: block.into(),
                        values: BTreeMap::from([(name.into(), 0.0)]),
                    })
                    .collect(),
            )
            .unwrap();
        let registration = projection
            .master(&source, ColumnMasterOptions::default())
            .unwrap();
        let compilation = registration.snapshot().compile_flt64().unwrap();
        let row = compilation
            .rows
            .iter()
            .position(|r| Some(&r.source) == registration.source_rows().values().next())
            .unwrap();
        assert!(
            solve_master(
                &mut projection,
                &source,
                &registration,
                &identities,
                false,
                |model| {
                    let mut dual = vec![0.0; model.num_constraints()];
                    dual[row] = -1.0 - eps;
                    let report = zero_report(model, dual);
                    assert!(crate::dual::require_exact_lp(&report, model).is_ok());
                    Ok((report, false))
                }
            )
            .unwrap()
            .1
            .is_none()
        );
        let mut state = ProjectionState::new(projection, identities);
        state.master = Some(Master {
            registration,
            generation: 0,
            integer: false,
            phase_one: false,
        });
        let sibling = create_pricing_request(&source, 0, &state, Weak::new(), "b").unwrap();
        assert!(create_pricing_request(&source, 0, &state, Weak::new(), "a").is_err());
        assert!(current_pricing(&source, 0, &state, &Weak::new(), &sibling).is_ok());
    }

    #[test]
    fn reduced_cost_uses_exact_accumulation_and_never_loses_nonzero_sign() {
        let mut source = MetaModel::<f64>::new("reduced cost rounding");
        let vars: Vec<_> = ["x", "y", "z"]
            .into_iter()
            .map(|name| source.register_auto_variable::<Binary>(name).unwrap())
            .collect();
        source.set_linear_objective_input(LinearObjectiveInput::minimize("cost").terms(vec![
            (vars[0], 1e16),
            (vars[1], -1.0),
            (vars[2], -1e16),
        ]));
        let decisions: Vec<_> = ["x", "y", "z"]
            .into_iter()
            .zip(&vars)
            .map(|(id, index)| ColumnDecision {
                id: id.into(),
                block_id: "a".into(),
                variable: source.tokens()[*index].id(),
            })
            .collect();
        let identities = decisions
            .iter()
            .map(|d| (d.variable, d.id.clone()))
            .collect();
        let mut projection =
            ColumnProjection::new(&source, decisions, BTreeSet::from(["a".into()])).unwrap();
        projection
            .add_columns(
                &source,
                vec![ProjectedColumn {
                    id: "zero".into(),
                    block_id: "a".into(),
                    values: BTreeMap::from([
                        ("x".into(), 0.0),
                        ("y".into(), 0.0),
                        ("z".into(), 0.0),
                    ]),
                }],
            )
            .unwrap();
        let registration = projection
            .master(&source, ColumnMasterOptions::default())
            .unwrap();
        assert!(
            solve_master(
                &mut projection,
                &source,
                &registration,
                &identities,
                false,
                |model| {
                    Ok((
                        zero_report(model, vec![0.0; model.num_constraints()]),
                        false,
                    ))
                }
            )
            .unwrap()
            .1
            .is_none()
        );
        let mut state = ProjectionState::new(projection, identities);
        state.master = Some(Master {
            registration,
            generation: 0,
            integer: false,
            phase_one: false,
        });
        let request = create_pricing_request(&source, 0, &state, Weak::new(), "a").unwrap();
        let values = BTreeMap::from([("x".into(), 1.0), ("y".into(), 1.0), ("z".into(), 1.0)]);
        assert_eq!(request.request.reduced_cost(&values).unwrap(), 0.0);
        assert_eq!(reduced_cost(&request.request, &values).unwrap(), -1.0);
    }

    #[test]
    fn reduced_cost_checks_underflow_overflow_and_vector_completeness() {
        let request_for = |coefficient: f64| {
            let mut source = MetaModel::<f64>::new("pricing limits");
            let x = source.register_auto_variable::<Binary>("x").unwrap();
            source.set_linear_objective_input(
                LinearObjectiveInput::minimize("cost").terms(vec![(x, coefficient)]),
            );
            let projection = ColumnProjection::new(
                &source,
                vec![ColumnDecision {
                    id: "x".into(),
                    block_id: "a".into(),
                    variable: source.tokens()[x].id(),
                }],
                BTreeSet::from(["a".into()]),
            )
            .unwrap();
            projection
                .pricing_request(&source, None, "a", false)
                .unwrap()
        };
        let tiny = request_for(f64::from_bits(1));
        let vector = |value| BTreeMap::from([("x".to_owned(), value)]);
        assert_eq!(
            reduced_cost(&tiny, &vector(1.0)).unwrap(),
            f64::from_bits(1)
        );
        assert!(reduced_cost(&tiny, &vector(0.5)).is_err());
        assert!(reduced_cost(&tiny, &vector(-0.5)).is_err());
        assert!(reduced_cost(&tiny, &vector(f64::NAN)).is_err());
        assert!(reduced_cost(&tiny, &BTreeMap::new()).is_err());
        assert!(
            reduced_cost(
                &tiny,
                &BTreeMap::from([("x".to_owned(), 1.0), ("y".to_owned(), 0.0)])
            )
            .is_err()
        );
        let huge = request_for(f64::MAX);
        assert!(reduced_cost(&huge, &vector(2.0)).is_err());
        assert_eq!(reduced_cost(&huge, &vector(0.5)).unwrap(), f64::MAX * 0.5);
    }

    #[test]
    fn synthetic_near_optimal_master_report_clears_prior_pricing() {
        let mut source = MetaModel::<f64>::new("synthetic master gap");
        let x = source.register_auto_variable::<Binary>("x").unwrap();
        let identities = BTreeMap::from([(source.tokens()[x].id(), "x".to_owned())]);
        source
            .add_linear_constraint(
                &[(x, 1.0)],
                ospf_rust_core::model::ConstraintRelation::GreaterEqual,
                1.0,
                "demand",
            )
            .unwrap();
        source.set_linear_objective_input(
            LinearObjectiveInput::minimize("objective").terms(vec![(x, 1.0)]),
        );
        let mut projection = ColumnProjection::new(
            &source,
            vec![ColumnDecision {
                id: "x".into(),
                block_id: "a".into(),
                variable: source.tokens()[x].id(),
            }],
            BTreeSet::from(["a".into()]),
        )
        .unwrap();
        projection
            .add_columns(
                &source,
                vec![ProjectedColumn {
                    id: "one".into(),
                    block_id: "a".into(),
                    values: BTreeMap::from([("x".into(), 1.0)]),
                }],
            )
            .unwrap();
        let master = projection
            .master(&source, ColumnMasterOptions::default())
            .unwrap();
        let compilation = master.snapshot().compile_flt64().unwrap();
        let source_row = master.source_rows().values().next().unwrap();
        let row = compilation
            .rows
            .iter()
            .position(|row| &row.source == source_row && row.multiplier == -1)
            .unwrap();
        let make_report = |model: &LinearTriadModel, delta: f64| {
            let mut solution = SolveSolution::vector(vec![1.0]);
            solution.objective_value = Some(1.0);
            let mut dual = vec![0.0; model.num_constraints()];
            dual[row] = -1.0 + delta;
            solution.dual_solution = Some(dual);
            SolveReport::builder(ProblemStatus::Feasible, TerminationReason::Completed)
                .solution(solution)
                .proof(SolveProof::optimality())
                .model_mapping(Some(linear_model_mapping(model).unwrap()))
                .fingerprints(SolveFingerprints {
                    model: Some(linear_model_fingerprint(model).unwrap()),
                    ..Default::default()
                })
                .build()
                .unwrap()
        };
        assert!(
            solve_master(
                &mut projection,
                &source,
                &master,
                &identities,
                false,
                |model| { Ok((make_report(model, 0.0), false)) }
            )
            .unwrap()
            .1
            .is_none()
        );
        let old = projection
            .pricing_request(&source, Some(&master), "a", false)
            .unwrap();
        let (raw, error) = solve_master(
            &mut projection,
            &source,
            &master,
            &identities,
            false,
            |model| {
                let report = make_report(model, 2.0_f64.powi(-25));
                assert!(require_optimal_lp_certificate_for_linear_model(&report, model).is_ok());
                Ok((report, false))
            },
        )
        .unwrap();
        assert_eq!(
            serde_json::from_str::<serde_json::Value>(&raw).unwrap()["solution"]["objectiveValue"],
            1.0
        );
        assert!(error.is_some());
        assert!(
            projection
                .pricing_request(&source, Some(&master), "a", false)
                .is_err()
        );
        assert!(
            projection
                .require_pricing_current(&source, Some(&master), &old)
                .is_err()
        );
        assert!(
            solve_master(
                &mut projection,
                &source,
                &master,
                &identities,
                false,
                |model| { Ok((make_report(model, 0.0), false)) }
            )
            .unwrap()
            .1
            .is_none()
        );
        assert!(
            projection
                .pricing_request(&source, Some(&master), "a", false)
                .is_ok()
        );
        assert!(
            projection
                .require_pricing_current(&source, Some(&master), &old)
                .is_err()
        );
    }

    #[test]
    fn dropping_projection_while_owner_is_busy_never_waits_and_releases_state() {
        let owner = Arc::new(Owner::new("projection release".into()).unwrap());
        let projection = Projection::create(Arc::clone(&owner), vec![], vec!["a".into()]).unwrap();
        let (ready, started) = sync_channel(0);
        let (finish, wait) = sync_channel(0);
        let worker = Arc::clone(&owner);
        let task = std::thread::spawn(move || {
            worker.with_model(move |_| {
                ready.send(()).unwrap();
                wait.recv().unwrap();
                Ok(())
            })
        });
        started.recv().unwrap();
        drop(projection);
        finish.send(()).unwrap();
        task.join().unwrap().unwrap();
        assert_eq!(
            owner
                .with_state(|state| Ok(state.projections.len()))
                .unwrap(),
            0
        );
        owner.close().unwrap();
    }

    #[test]
    fn pricing_requests_and_bounds_do_not_retain_projection_or_owner_state() {
        let owner = Arc::new(Owner::new("pricing request lifetime".into()).unwrap());
        let projection = Projection::create(Arc::clone(&owner), vec![], vec!["a".into()]).unwrap();
        let lease = Arc::downgrade(&projection.lease);
        let request = projection
            .with_projection(|source, _, state| {
                state
                    .projection
                    .pricing_request(source, None, "a", false)
                    .map_err(Failure::from)
            })
            .unwrap();
        let request = PricingRequest {
            lease: lease.clone(),
            generation: 0,
            request,
        };
        let bound = PricingBound {
            request: request.clone(),
            reported_cx_lower: 0.0,
        };
        assert!(request.lease.upgrade().is_some());
        assert!(bound.request.lease.upgrade().is_some());
        drop(projection);
        assert!(request.lease.upgrade().is_none());
        assert!(bound.request.lease.upgrade().is_none());
        assert_eq!(
            owner
                .with_state(|state| Ok(state.projections.len()))
                .unwrap(),
            0
        );
        owner.close().unwrap();
    }

    #[test]
    fn incumbent_validation_rejects_foreign_incomplete_and_infeasible_reports() {
        let mut model = MetaModel::<f64>::new("incumbent validation");
        let x = model.register_auto_variable::<Binary>("x").unwrap();
        model.set_linear_objective_input(
            LinearObjectiveInput::minimize("objective").terms(vec![(x, 2.0)]),
        );
        let snapshot = model.linear_model_snapshot().unwrap();
        let compiled = snapshot.compile_flt64().unwrap();
        let mut solution = SolveSolution::vector(vec![1.0]);
        solution.objective_value = Some(2.0);
        let report = SolveReport::builder(ProblemStatus::Feasible, TerminationReason::Completed)
            .solution(solution)
            .fingerprints(SolveFingerprints {
                model: Some(linear_model_fingerprint(&compiled.model).unwrap()),
                ..Default::default()
            })
            .model_mapping(Some(linear_model_mapping(&compiled.model).unwrap()))
            .build()
            .unwrap();
        assert!(validated_values(&snapshot, &compiled, &report, 1e-7).is_ok());
        let mut near_integer = report.clone();
        let near = f64::from_bits(1.0_f64.to_bits() - 1);
        let solution = near_integer.solution.as_mut().unwrap();
        solution.values = vec![near];
        solution.objective_value = Some(2.0 * near);
        assert!(validated_values(&snapshot, &compiled, &near_integer, 1e-7).is_ok());
        assert!(validated_values(&snapshot, &compiled, &near_integer, 0.0).is_err());
        let mut cancelled_incumbent = report.clone();
        cancelled_incumbent.termination_reason = TerminationReason::Cancelled;
        assert!(validated_values(&snapshot, &compiled, &cancelled_incumbent, 1e-7).is_ok());

        let mut foreign = report.clone();
        foreign.fingerprints.model = None;
        assert!(validated_values(&snapshot, &compiled, &foreign, 1e-7).is_err());
        foreign = report.clone();
        foreign.model_mapping = None;
        assert!(validated_values(&snapshot, &compiled, &foreign, 1e-7).is_err());
        for (values, objective) in [
            (vec![], Some(0.0)),
            (vec![0.5], Some(1.0)),
            (vec![2.0], Some(4.0)),
            (vec![1.0], Some(99.0)),
            (vec![1.0], None),
        ] {
            let mut invalid = report.clone();
            let solution = invalid.solution.as_mut().unwrap();
            solution.values = values;
            solution.objective_value = objective;
            assert!(validated_values(&snapshot, &compiled, &invalid, 1e-7).is_err());
        }
    }

    #[test]
    fn pricing_bound_requires_consistent_completed_model_and_incumbent() {
        let mut source = MetaModel::<f64>::new("bound validation");
        let x = source.register_auto_variable::<Binary>("x").unwrap();
        source.set_linear_objective_input(
            LinearObjectiveInput::minimize("objective").terms(vec![(x, 2.0)]),
        );
        let id = source.tokens()[x].id();
        let projection = ColumnProjection::new(
            &source,
            vec![ColumnDecision {
                id: "x".into(),
                block_id: "a".into(),
                variable: id,
            }],
            BTreeSet::from(["a".into()]),
        )
        .unwrap();
        let request = projection
            .pricing_request(&source, None, "a", false)
            .unwrap();
        let pricing = projection.pricing_model(&source, None, &request).unwrap();
        let snapshot = pricing.linear_model_snapshot().unwrap();
        let compiled = snapshot.compile_flt64().unwrap();
        let mut solution = SolveSolution::vector(vec![1.0]);
        solution.objective_value = Some(2.0);
        let report = SolveReport::builder(ProblemStatus::Feasible, TerminationReason::Completed)
            .solution(solution)
            .statistics(SolveStatistics {
                best_bound: Some(2.0),
                best_bound_value: Some(2.0),
                ..Default::default()
            })
            .fingerprints(SolveFingerprints {
                model: Some(linear_model_fingerprint(&compiled.model).unwrap()),
                ..Default::default()
            })
            .model_mapping(Some(linear_model_mapping(&compiled.model).unwrap()))
            .build()
            .unwrap();
        let identities = BTreeMap::from([(id, "x".to_owned())]);
        let values = BTreeMap::from([("x".to_owned(), 1.0)]);
        assert!(validated_values(&snapshot, &compiled, &report, 0.0).is_ok());
        let check = |snapshot: &LinearModelSnapshot<f64>,
                     compiled: &LinearModelCompilationFlt64,
                     report: &SolveReport<f64>,
                     identities: &BTreeMap<VariableId, String>,
                     values: &BTreeMap<String, f64>,
                     cancelled| {
            reported_pricing_bound(
                snapshot, compiled, report, &request, identities, values, cancelled,
            )
        };
        assert_eq!(
            check(&snapshot, &compiled, &report, &identities, &values, false).unwrap(),
            2.0
        );
        assert!(check(&snapshot, &compiled, &report, &identities, &values, true).is_err());
        let mut altered = report.clone();
        altered.termination_reason = TerminationReason::Cancelled;
        assert!(check(&snapshot, &compiled, &altered, &identities, &values, false).is_err());
        for (typed, value) in [
            (None, Some(2.0)),
            (Some(2.0), None),
            (Some(1.0), Some(2.0)),
            (Some(f64::NAN), Some(f64::NAN)),
            (Some(f64::NEG_INFINITY), Some(f64::NEG_INFINITY)),
            (Some(f64::INFINITY), Some(f64::INFINITY)),
            (Some(2.0_f64.next_up()), Some(2.0_f64.next_up())),
        ] {
            altered = report.clone();
            altered.statistics.best_bound = typed;
            altered.statistics.best_bound_value = value;
            assert!(check(&snapshot, &compiled, &altered, &identities, &values, false).is_err());
        }
        let mut changed_snapshot = snapshot.clone();
        changed_snapshot.objective_constant = 1.0;
        assert!(
            check(
                &changed_snapshot,
                &compiled,
                &report,
                &identities,
                &values,
                false
            )
            .is_err()
        );
        changed_snapshot = snapshot.clone();
        changed_snapshot.objective_category = ObjectiveCategory::Maximum;
        assert!(
            check(
                &changed_snapshot,
                &compiled,
                &report,
                &identities,
                &values,
                false
            )
            .is_err()
        );
        changed_snapshot = snapshot.clone();
        changed_snapshot.objective.insert(id, 3.0);
        assert!(
            check(
                &changed_snapshot,
                &compiled,
                &report,
                &identities,
                &values,
                false
            )
            .is_err()
        );
        let mut changed_compiled = compiled.clone();
        changed_compiled.model.c[0] = 3.0;
        assert!(
            check(
                &snapshot,
                &changed_compiled,
                &report,
                &identities,
                &values,
                false
            )
            .is_err()
        );
        changed_compiled = compiled.clone();
        changed_compiled.objective_constant = 1.0;
        assert!(
            check(
                &snapshot,
                &changed_compiled,
                &report,
                &identities,
                &values,
                false
            )
            .is_err()
        );
        changed_compiled = compiled.clone();
        changed_compiled.model.objective_category = ObjectiveCategory::Maximum;
        assert!(
            check(
                &snapshot,
                &changed_compiled,
                &report,
                &identities,
                &values,
                false
            )
            .is_err()
        );
        changed_compiled = compiled.clone();
        changed_compiled.model.c.clear();
        assert!(
            check(
                &snapshot,
                &changed_compiled,
                &report,
                &identities,
                &values,
                false
            )
            .is_err()
        );
        assert!(
            check(
                &snapshot,
                &compiled,
                &report,
                &BTreeMap::new(),
                &values,
                false
            )
            .is_err()
        );
        assert!(
            check(
                &snapshot,
                &compiled,
                &report,
                &identities,
                &BTreeMap::new(),
                false
            )
            .is_err()
        );
    }

    #[test]
    fn pricing_bound_accepts_a_sparse_zero_objective() {
        let mut source = MetaModel::<f64>::new("zero bound validation");
        let x = source.register_auto_variable::<Binary>("x").unwrap();
        source.set_linear_objective_input(
            LinearObjectiveInput::minimize("objective").terms(vec![(x, 2.0)]),
        );
        let id = source.tokens()[x].id();
        let projection = ColumnProjection::new(
            &source,
            vec![ColumnDecision {
                id: "x".into(),
                block_id: "a".into(),
                variable: id,
            }],
            BTreeSet::from(["a".into()]),
        )
        .unwrap();
        let request = projection
            .pricing_request(&source, None, "a", true)
            .unwrap();
        let pricing = projection.pricing_model(&source, None, &request).unwrap();
        let mut snapshot = pricing.linear_model_snapshot().unwrap();
        snapshot.objective.remove(&id);
        let compiled = snapshot.compile_flt64().unwrap();
        let mut solution = SolveSolution::vector(vec![1.0]);
        solution.objective_value = Some(0.0);
        let report = SolveReport::builder(ProblemStatus::Feasible, TerminationReason::Completed)
            .solution(solution)
            .statistics(SolveStatistics {
                best_bound: Some(0.0),
                best_bound_value: Some(0.0),
                ..Default::default()
            })
            .fingerprints(SolveFingerprints {
                model: Some(linear_model_fingerprint(&compiled.model).unwrap()),
                ..Default::default()
            })
            .model_mapping(Some(linear_model_mapping(&compiled.model).unwrap()))
            .build()
            .unwrap();
        let identities = BTreeMap::from([(id, "x".to_owned())]);
        let values = BTreeMap::from([("x".to_owned(), 1.0)]);
        assert!(validated_values(&snapshot, &compiled, &report, 0.0).is_ok());
        assert_eq!(
            reported_pricing_bound(
                &snapshot,
                &compiled,
                &report,
                &request,
                &identities,
                &values,
                false
            )
            .unwrap(),
            0.0
        );
    }

    #[test]
    fn pricing_bound_rejects_rounded_value_above_exact_incumbent() {
        let mut source = MetaModel::<f64>::new("bound rounding");
        let x = source.register_auto_variable::<Binary>("x").unwrap();
        let y = source.register_auto_variable::<Binary>("y").unwrap();
        source.set_linear_objective_input(
            LinearObjectiveInput::minimize("objective").terms(vec![(x, 1e16), (y, 1.0)]),
        );
        let x_id = source.tokens()[x].id();
        let y_id = source.tokens()[y].id();
        let projection = ColumnProjection::new(
            &source,
            vec![
                ColumnDecision {
                    id: "x".into(),
                    block_id: "a".into(),
                    variable: x_id,
                },
                ColumnDecision {
                    id: "y".into(),
                    block_id: "a".into(),
                    variable: y_id,
                },
            ],
            BTreeSet::from(["a".into()]),
        )
        .unwrap();
        let request = projection
            .pricing_request(&source, None, "a", false)
            .unwrap();
        let pricing = projection.pricing_model(&source, None, &request).unwrap();
        let snapshot = pricing.linear_model_snapshot().unwrap();
        let compiled = snapshot.compile_flt64().unwrap();
        let mut solution = SolveSolution::vector(vec![1.0, 1.0]);
        solution.objective_value = Some(1e16);
        let report = SolveReport::builder(ProblemStatus::Feasible, TerminationReason::Completed)
            .solution(solution)
            .statistics(SolveStatistics {
                best_bound: Some(1e16_f64.next_up()),
                best_bound_value: Some(1e16_f64.next_up()),
                ..Default::default()
            })
            .fingerprints(SolveFingerprints {
                model: Some(linear_model_fingerprint(&compiled.model).unwrap()),
                ..Default::default()
            })
            .model_mapping(Some(linear_model_mapping(&compiled.model).unwrap()))
            .build()
            .unwrap();
        let identities = BTreeMap::from([(x_id, "x".to_owned()), (y_id, "y".to_owned())]);
        let values = BTreeMap::from([("x".to_owned(), 1.0), ("y".to_owned(), 1.0)]);
        assert!(validated_values(&snapshot, &compiled, &report, 1e-7).is_ok());
        assert!(
            reported_pricing_bound(
                &snapshot,
                &compiled,
                &report,
                &request,
                &identities,
                &values,
                false
            )
            .is_err()
        );
    }

    #[test]
    fn source_solution_does_not_retain_projection_or_owner_state() {
        let owner = Arc::new(Owner::new("solution lifetime".into()).unwrap());
        let projection = Projection::create(Arc::clone(&owner), vec![], vec!["a".into()]).unwrap();
        let lease = Arc::downgrade(&projection.lease);
        let revision = projection
            .with_projection(|source, _, state| {
                state
                    .projection
                    .master(source, ColumnMasterOptions::default())
                    .map(|master| master.revision())
                    .map_err(Failure::from)
            })
            .unwrap();
        let solution = ProjectionSolution {
            lease: lease.clone(),
            generation: 0,
            revision,
            values: Arc::new(BTreeMap::new()),
        };
        assert!(solution.lease.upgrade().is_some());
        drop(projection);
        assert!(solution.lease.upgrade().is_none());
        assert_eq!(
            owner
                .with_state(|state| Ok(state.projections.len()))
                .unwrap(),
            0
        );
        owner.close().unwrap();
    }
}
