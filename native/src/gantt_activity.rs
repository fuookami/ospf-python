//! 固定 Rust 的有限候选活动调度。 / Finite-candidate activity scheduling from pinned Rust.

use std::collections::BTreeMap;

use num_bigint::BigInt;
use ospf_rust_core::model::MetaModel;
use ospf_rust_framework_gantt_scheduling::GanttError;
use ospf_rust_framework_gantt_scheduling::domain::activity::{
    Activity, ActivityChoiceKey, ActivityDependency, ActivityDependencyPresence, ActivityEndpoint,
    ActivityMode, ActivityResource, ActivityResourceUse, ActivityRow, ActivitySchedulingContext,
    ActivitySchedulingProblem,
};
use ospf_rust_framework_gantt_scheduling::domain::task::SolverValueAdapter;
use ospf_rust_framework_gantt_scheduling::infrastructure::TimeRange;
use ospf_rust_quantities::{Quantity, unit::Unit};
use pyo3::prelude::*;
use time::{Duration, OffsetDateTime};

use crate::control::SolveHandle;
use crate::failure::{Failure, Transport, transport};
use crate::numeric::Rational;
use crate::quantities::QuantityUnit;
use crate::safe_rational::SafeRational;
use crate::solve::SolveRequest;

type ResourceInput = (String, Py<Rational>, Py<QuantityUnit>, Vec<(i64, i64)>);
type UseInput = (String, Py<Rational>);
type ModeInput = (String, i64, Vec<i64>, Vec<UseInput>, Py<Rational>);
type ActivityInput = (String, Vec<ModeInput>, Option<Py<Rational>>);
type DependencyInput = (String, String, i64);
type RowTerm = (String, String, i64, Py<Rational>);
type RowInput = (
    String,
    Py<QuantityUnit>,
    Vec<RowTerm>,
    Vec<UseInput>,
    Option<Py<Rational>>,
    Option<Py<Rational>>,
);
type Placement = (String, String, i64, i64);
type Schedule = (Vec<Placement>, (BigInt, BigInt), Vec<String>);
type Solved = (u64, String, Option<Schedule>, Option<Failure>);

fn gantt_error(error: GanttError) -> Failure {
    let category = match error {
        GanttError::InvalidInput { .. }
        | GanttError::InvalidTimeRange { .. }
        | GanttError::InvalidDuration { .. } => "ILLEGAL_ARGUMENT",
        GanttError::Lifecycle { .. } => "FAILED_PRECONDITION",
        GanttError::Unsupported { .. } => "NOT_SUPPORTED",
        GanttError::EmptyResult { .. } => "NO_SOLUTION",
        GanttError::Conversion { .. } | GanttError::Calculation { .. } => "APPLICATION_ERROR",
    };
    let mut failure = Failure::binding(
        category,
        format!("活动调度失败 / Activity scheduling failed: {error}"),
    );
    failure.source = "ospf-rust-framework-gantt-scheduling";
    failure
}

fn instant(nanos: i64) -> OffsetDateTime {
    OffsetDateTime::UNIX_EPOCH + Duration::nanoseconds(nanos)
}

fn range((start, end): (i64, i64)) -> TimeRange {
    TimeRange::new(instant(start), instant(end))
}

fn size_error() -> Failure {
    Failure::binding(
        "RESOURCE_EXHAUSTED",
        "活动模型估算超出预算 / Activity model estimate exceeds budget",
    )
}

fn check_budget(
    activities: &[ActivityInput],
    resources: &[ResourceInput],
    dependencies: &[DependencyInput],
    rows: &[RowInput],
    max_work: usize,
) -> Result<(), Failure> {
    let mut choices = 0usize;
    let mut uses = 0usize;
    let mut modes = 0usize;
    for (_, activity_modes, cancellation_cost) in activities {
        modes = modes
            .checked_add(activity_modes.len())
            .ok_or_else(size_error)?;
        choices = choices
            .checked_add(usize::from(cancellation_cost.is_some()))
            .ok_or_else(size_error)?;
        for (_, _, starts, mode_uses, _) in activity_modes {
            choices = choices.checked_add(starts.len()).ok_or_else(size_error)?;
            uses = uses
                .checked_add(
                    starts
                        .len()
                        .checked_mul(mode_uses.len())
                        .ok_or_else(size_error)?,
                )
                .and_then(|value| value.checked_add(mode_uses.len()))
                .ok_or_else(size_error)?;
        }
    }
    let unavailable = resources
        .iter()
        .try_fold(0usize, |sum, (_, _, _, ranges)| {
            sum.checked_add(ranges.len()).ok_or_else(size_error)
        })?;
    let events = unavailable
        .checked_add(uses)
        .and_then(|value| value.checked_mul(2))
        .and_then(|value| value.checked_add(2))
        .ok_or_else(size_error)?;
    let resource_work = resources
        .len()
        .checked_mul(events)
        .and_then(|value| value.checked_mul(choices.checked_add(1)?))
        .ok_or_else(size_error)?;
    let dependency_work = dependencies
        .len()
        .checked_mul(choices)
        .and_then(|value| value.checked_mul(choices))
        .and_then(|value| value.checked_mul(2))
        .ok_or_else(size_error)?;
    let row_terms = rows
        .iter()
        .try_fold(0usize, |sum, (_, _, terms, cancellations, _, _)| {
            sum.checked_add(terms.len())
                .and_then(|value| value.checked_add(cancellations.len()))
                .ok_or_else(size_error)
        })?;
    let row_work = rows
        .len()
        .checked_mul(choices.checked_add(1).ok_or_else(size_error)?)
        .and_then(|value| value.checked_mul(2))
        .and_then(|value| value.checked_add(row_terms.checked_mul(2)?))
        .ok_or_else(size_error)?;
    let work = resource_work
        .checked_add(dependency_work)
        .and_then(|value| value.checked_add(row_work))
        .and_then(|value| value.checked_add(choices))
        .and_then(|value| value.checked_add(modes))
        .and_then(|value| value.checked_add(uses))
        .and_then(|value| value.checked_add(activities.len()))
        .and_then(|value| value.checked_add(resources.len()))
        .and_then(|value| value.checked_add(dependencies.len()))
        .and_then(|value| value.checked_add(unavailable))
        .ok_or_else(size_error)?;
    if max_work == 0 || work > max_work {
        return Err(size_error());
    }
    Ok(())
}

fn quantity(value: &Rational, unit: &Unit) -> Quantity<SafeRational, Unit> {
    Quantity::new(SafeRational(value.value.clone()), unit.clone())
}

fn problem(
    py: Python<'_>,
    horizon: (i64, i64),
    resources: Vec<ResourceInput>,
    activities: Vec<ActivityInput>,
    dependencies: Vec<DependencyInput>,
    rows: Vec<RowInput>,
    cost_unit: &QuantityUnit,
) -> Result<ActivitySchedulingProblem<SafeRational>, Failure> {
    let mut units = BTreeMap::new();
    let mut native_resources = Vec::with_capacity(resources.len());
    for (id, capacity, unit, unavailable) in resources {
        let unit = unit.borrow(py).cloned_unit();
        if units.insert(id.clone(), unit.clone()).is_some() {
            return Err(Failure::input("资源身份重复 / Duplicate resource identity"));
        }
        native_resources.push(ActivityResource {
            id: id.into(),
            capacity: quantity(&capacity.borrow(py), &unit),
            unavailable_times: unavailable.into_iter().map(range).collect(),
            capacities: vec![],
        });
    }
    let cost_unit = cost_unit.cloned_unit();
    let mut native_activities = Vec::with_capacity(activities.len());
    for (id, modes, cancellation_cost) in activities {
        let mut native_modes = Vec::with_capacity(modes.len());
        for (mode, duration, starts, uses, cost) in modes {
            if duration < 0
                || starts
                    .iter()
                    .any(|start| start.checked_add(duration).is_none())
            {
                return Err(Failure::input(
                    "活动时长无效或时间溢出 / Invalid activity duration or time overflow",
                ));
            }
            let mut native_uses = Vec::with_capacity(uses.len());
            for (resource, amount) in uses {
                let unit = units
                    .get(&resource)
                    .ok_or_else(|| Failure::input("未知资源 / Unknown resource"))?;
                native_uses.push(ActivityResourceUse {
                    resource: resource.into(),
                    quantity: quantity(&amount.borrow(py), unit),
                    from: Duration::ZERO,
                    until: None,
                });
            }
            native_modes.push(ActivityMode {
                id: mode,
                duration: Duration::nanoseconds(duration),
                starts: starts.into_iter().map(instant).collect(),
                resources: native_uses,
                cost: quantity(&cost.borrow(py), &cost_unit),
                material_flows: vec![],
            });
        }
        native_activities.push(Activity {
            id: id.into(),
            modes: native_modes,
            cancellation_cost: cancellation_cost
                .map(|value| quantity(&value.borrow(py), &cost_unit)),
        });
    }
    let mut native_rows = Vec::with_capacity(rows.len());
    for (id, unit, terms, cancellations, lower, upper) in rows {
        let unit = unit.borrow(py).cloned_unit();
        let mut coefficients = BTreeMap::new();
        for (task, mode, start, value) in terms {
            let key = ActivityChoiceKey {
                task: task.into(),
                mode,
                start: instant(start),
            };
            if coefficients
                .insert(key, quantity(&value.borrow(py), &unit))
                .is_some()
            {
                return Err(Failure::input(
                    "活动行候选重复 / Duplicate activity row choice",
                ));
            }
        }
        let mut cancellation_coefficients = BTreeMap::new();
        for (task, value) in cancellations {
            if cancellation_coefficients
                .insert(task.into(), quantity(&value.borrow(py), &unit))
                .is_some()
            {
                return Err(Failure::input(
                    "活动行取消身份重复 / Duplicate activity row cancellation",
                ));
            }
        }
        native_rows.push(ActivityRow {
            id,
            coefficients,
            cancellation_coefficients,
            lower: lower.map(|value| quantity(&value.borrow(py), &unit)),
            upper: upper.map(|value| quantity(&value.borrow(py), &unit)),
            unit,
        });
    }
    Ok(ActivitySchedulingProblem {
        horizon: range(horizon),
        activities: native_activities,
        resources: native_resources,
        dependencies: dependencies
            .into_iter()
            .map(|(predecessor, successor, lag)| ActivityDependency {
                predecessor: predecessor.into(),
                successor: successor.into(),
                from: ActivityEndpoint::Finish,
                to: ActivityEndpoint::Start,
                minimum: Duration::nanoseconds(lag),
                maximum: None,
                presence: ActivityDependencyPresence::RequireBoth,
            })
            .collect(),
        baselines: vec![],
        executions: vec![],
        rows: native_rows,
        cost_unit,
        materials: vec![],
        material_events: vec![],
    })
}

fn exact(value: &SafeRational, actual: f64) -> Result<(), Failure> {
    let expected = Rational {
        value: value.0.clone(),
    }
    .float_value(true)?;
    if expected != actual {
        return Err(Failure::binding(
            "DATA_LOSS",
            "活动系数转换不一致 / Activity coefficient conversion mismatch",
        ));
    }
    Ok(())
}

fn solve(
    problem: ActivitySchedulingProblem<SafeRational>,
    request: SolveRequest,
) -> Result<Solved, Failure> {
    let mut context = ActivitySchedulingContext::new(
        problem,
        &SolverValueAdapter::<SafeRational>::new(),
        None,
        Default::default(),
    )
    .map_err(gantt_error)?;
    let prepared = context.aggregation().prepared();
    for choice in prepared.choices().values() {
        exact(&choice.cost.value, choice.cost.solver)?;
    }
    for cost in prepared.cancellation_costs().values() {
        exact(&cost.value, cost.solver)?;
    }
    for row in prepared.rows() {
        for value in row
            .terms
            .values()
            .chain(row.lower.iter())
            .chain(row.upper.iter())
        {
            exact(&value.value, value.solver)?;
        }
    }
    let mut model = MetaModel::<f64>::new("activity-scheduling");
    context.register(&mut model).map_err(gantt_error)?;
    let compilation = context.compile(&model).map_err(gantt_error)?;
    if compilation.objective_offset() != 0.0 {
        return Err(Failure::binding(
            "NOT_SUPPORTED",
            "活动目标常数未保留 / Activity objective offset is unsupported",
        ));
    }
    let report = crate::solve::execute(&model, request, Some(compilation.model()))?;
    let raw = crate::bpp1d::serialize_report(&report)?;
    let solution = context
        .extract_solution(&model, &compilation, &report)
        .map_err(gantt_error)
        .and_then(|schedule| {
            schedule.ok_or_else(|| {
                Failure::binding(
                    "NO_SOLUTION",
                    "报告没有可复核解 / Report has no solution to validate",
                )
            })
        })
        .and_then(|schedule| {
            let placements = schedule
                .placements
                .into_iter()
                .map(|placement| {
                    let start = i64::try_from(placement.time.start.unix_timestamp_nanos())
                        .map_err(|_| Failure::input("开始时间溢出 / Start time overflow"))?;
                    let end = i64::try_from(placement.time.end.unix_timestamp_nanos())
                        .map_err(|_| Failure::input("结束时间溢出 / End time overflow"))?;
                    Ok((
                        placement.key.task.to_string(),
                        placement.key.mode,
                        start,
                        end,
                    ))
                })
                .collect::<Result<Vec<_>, Failure>>()?;
            Ok((
                placements,
                schedule.cost.value.0.into_raw(),
                schedule
                    .cancelled
                    .into_iter()
                    .map(|id| id.to_string())
                    .collect(),
            ))
        });
    let (solution, error) = transport(solution);
    Ok((model.model_identity(), raw, solution, error))
}

#[pyfunction]
#[pyo3(signature = (*, horizon, resources, activities, dependencies, rows, cost_unit, max_work, solver, time_limit, cancellation, on_progress))]
#[allow(clippy::too_many_arguments)]
pub fn _solve_activity(
    py: Python<'_>,
    horizon: (i64, i64),
    resources: Vec<ResourceInput>,
    activities: Vec<ActivityInput>,
    dependencies: Vec<DependencyInput>,
    rows: Vec<RowInput>,
    cost_unit: &QuantityUnit,
    max_work: usize,
    solver: String,
    time_limit: Option<f64>,
    cancellation: Option<SolveHandle>,
    on_progress: Option<Py<PyAny>>,
) -> Transport<Solved> {
    let input =
        check_budget(&activities, &resources, &dependencies, &rows, max_work).and_then(|()| {
            problem(
                py,
                horizon,
                resources,
                activities,
                dependencies,
                rows,
                cost_unit,
            )
        });
    let request = SolveRequest {
        solver,
        time_limit,
        cancellation,
        on_progress,
    };
    transport(input.and_then(|input| py.detach(|| solve(input, request))))
}
