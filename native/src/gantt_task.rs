//! Gantt task shadow-price, complete-domain pricing and finite-pool boundaries.

use std::cmp::Ordering;
use std::collections::{BTreeMap, HashMap};
use std::sync::{Arc, Mutex};
use std::time::Duration;

use ospf_rust_core::error::{CoreError, SolverError};
use ospf_rust_core::model::intermediate::LinearTriadModel;
use ospf_rust_core::model::{ConstraintGroup, ConstraintRelation, MetaModel, ObjectiveCategory};
use ospf_rust_core::solver::SolveReport;
use ospf_rust_framework::model::{ColumnGenerationBatch, ColumnGenerationCompletion};
use ospf_rust_framework::solver::column_generation_solver::{
    ColumnGenerationSolver, FeasibleSolution, LPResult, LinearDualSolution,
};
use ospf_rust_framework::solver::framework_solve_options::FrameworkSolveOptions;
use ospf_rust_framework_gantt_scheduling::GanttError;
use ospf_rust_framework_gantt_scheduling::application::{
    ColumnGenerationPolicy, TaskColumnGenerationAlgorithm,
};
use ospf_rust_framework_gantt_scheduling::domain::task::{Cost, CostItem};
use ospf_rust_framework_gantt_scheduling::domain::task_compilation::BasicTaskCompilationContext;
use ospf_rust_framework_gantt_scheduling::domain::task_compilation::iterative::AddedTaskColumn;
use ospf_rust_framework_gantt_scheduling::domain::task_generation::{
    TaskCGPolicy, TaskPricingColumn, TaskPricingDomain, TaskPricingRequest,
};
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::control::SolveHandle;
use crate::failure::{Failure, Transport, transport};
use crate::numeric::compare_rationals;
use crate::solve::SolveRequest;

type PricingColumnInput = (usize, usize, f64);
type PricingBatch = (Vec<PricingColumnInput>, String, bool, Option<bool>, usize);
type PricingLpReport = (bool, bool, Option<f64>, String, String);

const TASK_PRICING_GROUP_ID: u64 = 0x4f53_5046_5450_4d31;

/// The pinned algorithm owns this solver, but shadow-price extraction never calls it.
struct ShadowPriceOnlySolver;

impl ColumnGenerationSolver for ShadowPriceOnlySolver {
    fn name(&self) -> &str {
        "shadow-price-only"
    }

    fn solve_milp_with_options(
        &self,
        _: &LinearTriadModel,
        _: FrameworkSolveOptions,
    ) -> ospf_rust_core::error::Result<FeasibleSolution> {
        Err(unavailable())
    }

    fn solve_lp_with_options(
        &self,
        _: &LinearTriadModel,
        _: FrameworkSolveOptions,
    ) -> ospf_rust_core::error::Result<LPResult> {
        Err(unavailable())
    }
}

fn unavailable() -> CoreError {
    CoreError::Solver(SolverError::NotAvailable(
        "shadow-price-only solver cannot solve models".into(),
    ))
}

fn extract(
    task_count: usize,
    dual_values: Vec<f64>,
    constraint_name_to_index: HashMap<String, usize>,
) -> BTreeMap<usize, f64> {
    let context = BasicTaskCompilationContext::new(task_count, 0, false, false);
    let mut algorithm = TaskColumnGenerationAlgorithm::new(
        context,
        ShadowPriceOnlySolver,
        ColumnGenerationPolicy::default(),
    );
    let lp_result = LPResult::new(
        FeasibleSolution::new(0.0, Vec::new()),
        LinearDualSolution::new(dual_values, Vec::new()),
    );
    algorithm.extract_shadow_prices(&lp_result, &constraint_name_to_index);
    algorithm.shadow_prices.into_iter().collect()
}

/// Invoke the pinned task algorithm's actual dual extraction path.
#[pyfunction(signature = (*, task_count, dual_values, constraint_name_to_index))]
pub(crate) fn _task_shadow_prices(
    py: Python<'_>,
    task_count: usize,
    dual_values: Vec<f64>,
    constraint_name_to_index: HashMap<String, usize>,
) -> Transport<BTreeMap<usize, f64>> {
    transport(py.detach(move || Ok(extract(task_count, dual_values, constraint_name_to_index))))
}

fn improving_columns(
    columns: Vec<(String, f64, BTreeMap<String, f64>)>,
    dual_values: HashMap<String, f64>,
    tolerance: f64,
) -> Result<BTreeMap<String, bool>, Failure> {
    if !tolerance.is_finite() || tolerance < 0.0 {
        return Err(Failure::input(
            "缩减成本容差必须有限且非负 / Reduced-cost tolerance must be finite and nonnegative",
        ));
    }
    let threshold = -crate::dual::exact(tolerance)?;
    let mut result = BTreeMap::new();
    for (key, cost, coefficients) in columns {
        if key.is_empty() || result.contains_key(&key) {
            return Err(Failure::input(
                "候选列键为空或重复 / Candidate column key is empty or duplicated",
            ));
        }
        let mut reduced_cost = crate::dual::exact(cost)?;
        for (row, coefficient) in coefficients {
            let dual = dual_values.get(&row).ok_or_else(|| {
                Failure::input(format!(
                    "候选列缺少对偶行 / Candidate column has no dual row: {row}"
                ))
            })?;
            reduced_cost -= crate::dual::exact(coefficient)? * crate::dual::exact(*dual)?;
        }
        result.insert(
            key,
            compare_rationals(&reduced_cost, &threshold) == Ordering::Less,
        );
    }
    Ok(result)
}

/// Compare candidate reduced costs exactly against the finite-pool threshold.
#[pyfunction(signature = (*, columns, dual_values, tolerance))]
pub(crate) fn _task_improving_columns(
    py: Python<'_>,
    columns: Vec<(String, f64, BTreeMap<String, f64>)>,
    dual_values: HashMap<String, f64>,
    tolerance: f64,
) -> Transport<BTreeMap<String, bool>> {
    transport(py.detach(move || improving_columns(columns, dual_values, tolerance)))
}

struct NativePricingSolver {
    solver: String,
    time_limit: Option<f64>,
    cancellation: Option<SolveHandle>,
    on_progress: Mutex<Option<Py<PyAny>>>,
    identity: u64,
}

impl NativePricingSolver {
    fn request(&self) -> SolveRequest {
        SolveRequest {
            solver: self.solver.clone(),
            time_limit: self.time_limit,
            cancellation: self.cancellation.clone(),
            on_progress: Python::attach(|py| {
                self.on_progress
                    .lock()
                    .unwrap_or_else(|error| error.into_inner())
                    .as_ref()
                    .map(|callback| callback.clone_ref(py))
            }),
        }
    }

    fn solve_report(
        &self,
        model: &LinearTriadModel,
    ) -> ospf_rust_core::error::Result<SolveReport<f64>> {
        crate::solve::execute_compiled(self.identity, self.request(), model)
            .map_err(pricing_solver_error)
    }
}

fn pricing_solver_error(failure: Failure) -> CoreError {
    let category = failure.category;
    let message = failure.message;
    match category {
        "ILLEGAL_ARGUMENT" => SolverError::InvalidInput(message).into(),
        "CANCELLED" => SolverError::Cancelled(message).into(),
        "TIMEOUT" => SolverError::Timeout(Duration::ZERO).into(),
        "SOLVER_NOT_AVAILABLE" => SolverError::NotAvailable(message).into(),
        "NO_SOLUTION" => SolverError::NoSolution.into(),
        _ => SolverError::SolveFailed(format!("{category}: {message}")).into(),
    }
}

impl ColumnGenerationSolver for NativePricingSolver {
    fn name(&self) -> &str {
        &self.solver
    }

    fn solve_milp_with_options(
        &self,
        model: &LinearTriadModel,
        _: FrameworkSolveOptions,
    ) -> ospf_rust_core::error::Result<FeasibleSolution> {
        let report = self.solve_report(model)?;
        FeasibleSolution::try_from_report(&report)
    }

    fn solve_lp_with_options(
        &self,
        model: &LinearTriadModel,
        _: FrameworkSolveOptions,
    ) -> ospf_rust_core::error::Result<LPResult> {
        let report = self.solve_report(model)?;
        LPResult::try_from_solve_report(&report)
    }

    fn solve_lp_report_with_options(
        &self,
        model: &LinearTriadModel,
        _: FrameworkSolveOptions,
    ) -> ospf_rust_core::error::Result<SolveReport<f64>> {
        self.solve_report(model)
    }
}

fn pricing_cost(value: f64) -> Cost<f64> {
    Cost::new(vec![CostItem::with_quantity("candidate", value)])
}

fn pricing_column(column: &AddedTaskColumn) -> PricingColumnInput {
    (
        column.task_index,
        column.executor_index,
        column.cost.solver_cost(0.0),
    )
}

fn completion_name(completion: ColumnGenerationCompletion) -> &'static str {
    match completion {
        ColumnGenerationCompletion::Exhausted => "EXHAUSTED",
        ColumnGenerationCompletion::BudgetLimit => "BUDGET_LIMIT",
        ColumnGenerationCompletion::Interrupted => "INTERRUPTED",
        ColumnGenerationCompletion::Heuristic => "HEURISTIC",
    }
}

fn parse_completion(value: &str) -> Result<ColumnGenerationCompletion, String> {
    match value {
        "EXHAUSTED" => Ok(ColumnGenerationCompletion::Exhausted),
        "BUDGET_LIMIT" => Ok(ColumnGenerationCompletion::BudgetLimit),
        "INTERRUPTED" => Ok(ColumnGenerationCompletion::Interrupted),
        "HEURISTIC" => Ok(ColumnGenerationCompletion::Heuristic),
        _ => Err(format!(
            "未知定价完成状态 / Unknown pricing completion: {value}"
        )),
    }
}

fn gantt_failure(error: GanttError) -> Failure {
    match error {
        GanttError::InvalidInput { message } => Failure::input(message),
        GanttError::Unsupported { message } => Failure::binding("NOT_SUPPORTED", message),
        error => Failure::binding("SOLVE_FAILED", error.to_string()),
    }
}

struct PythonTaskPricingPolicy {
    callback: Py<PyAny>,
    error: Mutex<Option<PyErr>>,
}

impl PythonTaskPricingPolicy {
    fn request(py: Python<'_>, request: &TaskPricingRequest) -> PyResult<Py<PyAny>> {
        let value = PyDict::new(py);
        value.set_item("request", &request.scope.request)?;
        value.set_item("model", &request.scope.model)?;
        value.set_item("dual", &request.scope.dual)?;
        value.set_item("branch", &request.scope.branch)?;
        value.set_item("global", request.scope.global)?;
        value.set_item("iteration", request.iteration)?;
        value.set_item(
            "tasks",
            request.domain.tasks.iter().copied().collect::<Vec<_>>(),
        )?;
        value.set_item(
            "executor_slots",
            request
                .domain
                .executor_slots
                .iter()
                .copied()
                .collect::<Vec<_>>(),
        )?;
        value.set_item(
            "shadow_prices",
            request
                .shadow_prices
                .iter()
                .map(|(task, price)| (*task, *price))
                .collect::<BTreeMap<_, _>>(),
        )?;
        value.set_item("row_duals", &request.row_duals)?;
        let mut fixed_columns = request.fixed_columns.iter().copied().collect::<Vec<_>>();
        fixed_columns.sort_unstable();
        value.set_item("fixed_columns", fixed_columns)?;
        let mut kept_columns = request.kept_columns.iter().copied().collect::<Vec<_>>();
        kept_columns.sort_unstable();
        value.set_item("kept_columns", kept_columns)?;
        value.set_item("verified_duals", request.verified_duals.is_some())?;
        Ok(value.into_any().unbind())
    }

    fn batch(
        request: &TaskPricingRequest,
        returned: &Bound<'_, PyAny>,
    ) -> PyResult<ColumnGenerationBatch<TaskPricingColumn>> {
        let mapping = returned.cast::<PyDict>()?;
        let columns = mapping
            .get_item("columns")?
            .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err("columns"))?
            .extract::<Vec<PricingColumnInput>>()?;
        let completion = mapping
            .get_item("completion")?
            .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err("completion"))?
            .extract::<String>()?;
        let completion =
            parse_completion(&completion).map_err(pyo3::exceptions::PyValueError::new_err)?;
        let no_improving_columns = mapping
            .get_item("no_improving_columns")?
            .map(|value| value.extract::<bool>())
            .transpose()?;
        Ok(ColumnGenerationBatch {
            columns: columns
                .into_iter()
                .map(|(task_index, executor_index, cost)| TaskPricingColumn {
                    task_index,
                    executor_index,
                    cost: pricing_cost(cost),
                })
                .collect(),
            completion,
            scope: Some(request.scope.clone()),
            no_improving_columns,
            children: Vec::new(),
        })
    }
}

impl TaskCGPolicy for PythonTaskPricingPolicy {
    fn generate_tasks(
        &self,
        _: &TaskPricingRequest,
    ) -> ospf_rust_framework_gantt_scheduling::GanttResult<Vec<TaskPricingColumn>> {
        Err(GanttError::Calculation {
            message: "完整定价策略必须返回批次 / Complete pricing policy must return a batch"
                .into(),
        })
    }

    fn generate_task_batch(
        &self,
        request: &TaskPricingRequest,
    ) -> ospf_rust_framework_gantt_scheduling::GanttResult<ColumnGenerationBatch<TaskPricingColumn>>
    {
        let result = Python::attach(|py| -> PyResult<_> {
            let argument = Self::request(py, request)?;
            let returned = self.callback.bind(py).call1((argument.bind(py),))?;
            Self::batch(request, &returned)
        });
        match result {
            Ok(batch) => Ok(batch),
            Err(error) => {
                if let Ok(mut slot) = self.error.lock() {
                    *slot = Some(error);
                }
                Err(GanttError::Calculation {
                    message: "任务定价策略失败 / Task-pricing policy failed".into(),
                })
            }
        }
    }
}

/// Private bridge around the pinned complete-domain task-pricing algorithm.
#[pyclass(unsendable, module = "ospf_python._native")]
pub struct TaskPricingAlgorithm {
    algorithm: TaskColumnGenerationAlgorithm<BasicTaskCompilationContext, NativePricingSolver>,
    model: MetaModel<f64>,
    group: Arc<ConstraintGroup>,
}

impl TaskPricingAlgorithm {
    fn create(
        task_count: usize,
        executor_count: usize,
        max_iterations: usize,
    ) -> Result<Self, Failure> {
        if max_iterations == 0 {
            return Err(Failure::input(
                "最大迭代数必须为正 / Maximum iterations must be positive",
            ));
        }
        let mut model = MetaModel::new("task-pricing");
        let mut algorithm = TaskColumnGenerationAlgorithm::new(
            BasicTaskCompilationContext::new(task_count, executor_count, false, false),
            NativePricingSolver {
                solver: String::new(),
                time_limit: None,
                cancellation: None,
                on_progress: Mutex::new(None),
                identity: model.model_identity(),
            },
            ColumnGenerationPolicy::new().with_max_iterations(max_iterations),
        );
        algorithm.register(&mut model).map_err(gantt_failure)?;
        let group = model
            .create_constraint_group(TASK_PRICING_GROUP_ID, "task_pricing_rows")
            .map_err(Failure::from)?;
        let mut result = Self {
            algorithm,
            model,
            group,
        };
        result.rebuild_model()?;
        Ok(result)
    }

    fn rebuild_model(&mut self) -> Result<(), Failure> {
        self.model.remove_constraints_by_group_id(self.group.id);
        let mut objective = vec![0.0; self.model.num_tokens()];
        for column in &self.algorithm.context.compilation.columns {
            if !self
                .algorithm
                .context
                .compilation
                .removed_columns
                .contains(&column.index)
            {
                objective[column.x_model_index] = column.cost.solver_cost(0.0);
            }
        }
        self.model
            .set_linear_objective(objective, ObjectiveCategory::Minimum);
        for (task, terms) in self
            .algorithm
            .context
            .compilation
            .task_compilation_terms
            .iter()
            .enumerate()
        {
            self.model
                .add_linear_constraint_with_metadata(
                    terms,
                    ConstraintRelation::Equal,
                    1.0,
                    &format!("task_compilation_{task}"),
                    Some(Arc::clone(&self.group)),
                    false,
                    0,
                    None,
                )
                .map_err(Failure::from)?;
        }
        for (executor, terms) in self
            .algorithm
            .context
            .compilation
            .executor_compilation_terms
            .iter()
            .enumerate()
        {
            self.model
                .add_linear_constraint_with_metadata(
                    terms,
                    ConstraintRelation::LessEqual,
                    1.0,
                    &format!("executor_compilation_{executor}"),
                    Some(Arc::clone(&self.group)),
                    false,
                    0,
                    None,
                )
                .map_err(Failure::from)?;
        }
        Ok(())
    }

    fn validate_columns(&self, columns: &[PricingColumnInput]) -> Result<(), Failure> {
        if columns.iter().any(|(task, executor, cost)| {
            *task >= self.algorithm.context.compilation.n_tasks
                || *executor >= self.algorithm.context.compilation.n_executors
                || !cost.is_finite()
        }) {
            return Err(Failure::input(
                "任务列索引或成本非法 / Invalid task-column indices or costs",
            ));
        }
        Ok(())
    }

    fn add_initial(
        &mut self,
        columns: Vec<PricingColumnInput>,
    ) -> Result<Vec<PricingColumnInput>, Failure> {
        self.validate_columns(&columns)?;
        let columns = columns
            .into_iter()
            .map(|(task, executor, cost)| (task, executor, pricing_cost(cost)))
            .collect();
        let added = self
            .algorithm
            .add_initial_columns(columns, &mut self.model)
            .map_err(gantt_failure)?;
        self.rebuild_model()?;
        Ok(added.iter().map(pricing_column).collect())
    }

    fn add_priced(
        &mut self,
        columns: Vec<PricingColumnInput>,
    ) -> Result<Vec<PricingColumnInput>, Failure> {
        self.validate_columns(&columns)?;
        let columns = columns
            .into_iter()
            .map(|(task, executor, cost)| TaskPricingColumn {
                task_index: task,
                executor_index: executor,
                cost: pricing_cost(cost),
            })
            .collect();
        let added = self
            .algorithm
            .add_priced_columns(columns, &mut self.model)
            .map_err(gantt_failure)?;
        self.rebuild_model()?;
        Ok(added.iter().map(pricing_column).collect())
    }
}

#[pymethods]
impl TaskPricingAlgorithm {
    #[pyo3(signature = (columns))]
    fn add_columns(
        &mut self,
        columns: Vec<PricingColumnInput>,
    ) -> Transport<Vec<PricingColumnInput>> {
        transport(self.add_initial(columns))
    }

    #[pyo3(signature = (columns))]
    fn add_priced_columns(
        &mut self,
        columns: Vec<PricingColumnInput>,
    ) -> Transport<Vec<PricingColumnInput>> {
        transport(self.add_priced(columns))
    }

    #[pyo3(signature = (*, solver, time_limit=None, cancellation=None, on_progress=None))]
    fn solve_lp(
        &mut self,
        py: Python<'_>,
        solver: String,
        time_limit: Option<f64>,
        cancellation: Option<SolveHandle>,
        on_progress: Option<Py<PyAny>>,
    ) -> PyResult<Transport<PricingLpReport>> {
        if on_progress
            .as_ref()
            .is_some_and(|callback| !callback.bind(py).is_callable())
        {
            return Ok(transport(Err(Failure::input(
                "进度回调必须可调用 / Progress callback must be callable",
            ))));
        }
        self.algorithm.solver = NativePricingSolver {
            solver,
            time_limit,
            cancellation,
            on_progress: Mutex::new(on_progress),
            identity: self.model.model_identity(),
        };
        Ok(transport((|| {
            let report = self
                .algorithm
                .solve_rmp_lp_report(&self.model)
                .map_err(gantt_failure)?;
            let objective = report
                .solution
                .as_ref()
                .and_then(|solution| solution.objective_value.or(solution.objective));
            Ok((
                report.is_optimal(),
                report.has_incumbent(),
                objective,
                format!("{:?}", report.termination_reason).to_ascii_uppercase(),
                format!("{:?}", report.problem_status).to_ascii_uppercase(),
            ))
        })()))
    }

    #[pyo3(signature = (policy))]
    fn generate(&mut self, py: Python<'_>, policy: Py<PyAny>) -> Transport<PricingBatch> {
        if !policy.bind(py).is_callable() {
            return transport(Err(Failure::input(
                "定价策略必须可调用 / Pricing policy must be callable",
            )));
        }
        let policy = PythonTaskPricingPolicy {
            callback: policy,
            error: Mutex::new(None),
        };
        let result = self.algorithm.generate_task_batch(
            &self.model,
            TaskPricingDomain::unslotted(
                self.algorithm.context.compilation.n_tasks,
                self.algorithm.context.compilation.n_executors,
            ),
            &policy,
        );
        let error = policy.error.lock().ok().and_then(|mut slot| slot.take());
        if let Some(error) = error {
            return transport(Err(Failure::binding(
                "ILLEGAL_ARGUMENT",
                format!("任务定价策略失败 / Task-pricing policy failed: {error}"),
            )));
        }
        transport(result.map_err(gantt_failure).map(|batch| {
            (
                batch
                    .columns
                    .iter()
                    .map(|column| {
                        (
                            column.task_index,
                            column.executor_index,
                            column.cost.solver_cost(0.0),
                        )
                    })
                    .collect(),
                completion_name(batch.completion).into(),
                batch.scope.as_ref().is_some_and(|scope| scope.global),
                batch.no_improving_columns,
                batch.children.len(),
            )
        }))
    }

    fn certified_lower_bound(&self) -> Transport<Option<f64>> {
        transport(
            self.algorithm
                .certified_lower_bound(&self.model)
                .map_err(gantt_failure),
        )
    }

    fn completion(&self) -> Option<&'static str> {
        self.algorithm.pricing_completion().map(completion_name)
    }
}

/// Create the private complete-domain task-pricing bridge.
#[pyfunction(signature = (*, task_count, executor_count, max_iterations=100))]
pub(crate) fn _create_task_pricing_algorithm(
    task_count: usize,
    executor_count: usize,
    max_iterations: usize,
) -> Transport<TaskPricingAlgorithm> {
    transport(TaskPricingAlgorithm::create(
        task_count,
        executor_count,
        max_iterations,
    ))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn delegates_to_the_pinned_algorithm_and_keeps_nonzero_task_duals() {
        let prices = extract(
            3,
            vec![0.0, -2.5, 4.0],
            HashMap::from([
                ("task_compilation_0".into(), 0),
                ("task_compilation_1".into(), 1),
                ("task_compilation_2".into(), 2),
            ]),
        );

        assert_eq!(prices, BTreeMap::from([(1, -2.5), (2, 4.0)]));
    }

    #[test]
    fn ignores_non_task_rows_and_out_of_range_indices() {
        let prices = extract(
            2,
            vec![7.0, 3.0],
            HashMap::from([
                ("cap_0".into(), 0),
                ("task_compilation_0".into(), 2),
                ("task_compilation_1".into(), 1),
            ]),
        );

        assert_eq!(prices, BTreeMap::from([(1, 3.0)]));
    }

    #[test]
    fn reduced_cost_uses_all_rows_and_strict_tolerance() {
        let result = improving_columns(
            vec![
                (
                    "improve".into(),
                    1.0,
                    BTreeMap::from([("task".into(), 1.0), ("capacity".into(), 2.0)]),
                ),
                (
                    "boundary".into(),
                    2.5,
                    BTreeMap::from([("task".into(), 1.0)]),
                ),
            ],
            HashMap::from([("task".into(), 2.5), ("capacity".into(), 0.25)]),
            0.5,
        )
        .unwrap();

        assert_eq!(
            result,
            BTreeMap::from([("boundary".into(), false), ("improve".into(), true)])
        );
    }

    #[test]
    fn reduced_cost_rejects_missing_duals_and_invalid_tolerance() {
        let missing = improving_columns(
            vec![(
                "column".into(),
                1.0,
                BTreeMap::from([("missing".into(), 1.0)]),
            )],
            HashMap::new(),
            0.0,
        );
        assert_eq!(missing.unwrap_err().category, "ILLEGAL_ARGUMENT");
        assert!(improving_columns(Vec::new(), HashMap::new(), f64::NAN).is_err());
        assert!(improving_columns(Vec::new(), HashMap::new(), -1.0).is_err());
    }
}
