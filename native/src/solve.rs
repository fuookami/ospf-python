//! 将运行时控制传给同一次 Rust 求解。 / Forward runtime controls to the same Rust solve attempt.

use std::sync::Arc;

use ospf_rust_core::model::MetaModel;
use ospf_rust_core::model::intermediate::LinearTriadModel;
#[cfg(any(
    feature = "scip",
    feature = "gurobi10",
    feature = "gurobi11",
    feature = "gurobi12"
))]
use ospf_rust_core::solver::LinearSolver;
use ospf_rust_core::solver::SolveReport;
use pyo3::prelude::*;

use crate::control::SolveHandle;
use crate::dual::DualCertificate;
use crate::failure::Failure;
use crate::progress::{CallbackLease, ProgressBridge};

pub struct SolveRequest {
    pub solver: String,
    pub time_limit: Option<f64>,
    pub cancellation: Option<SolveHandle>,
    pub on_progress: Option<Py<PyAny>>,
}

pub fn solve(model: &MetaModel<f64>, request: SolveRequest) -> Result<String, Failure> {
    serialize(&execute(model, request, None)?)
}

pub fn solve_compiled(
    model: &MetaModel<f64>,
    request: SolveRequest,
    provenance: Arc<u8>,
    generation: u64,
) -> Result<(String, Option<DualCertificate>, Option<Failure>), Failure> {
    solve_compiled_snapshot(model, request, provenance, generation, false)
}

pub fn solve_relaxed_compiled(
    model: &MetaModel<f64>,
    request: SolveRequest,
    provenance: Arc<u8>,
    generation: u64,
) -> Result<(String, Option<DualCertificate>, Option<Failure>), Failure> {
    solve_compiled_snapshot(model, request, provenance, generation, true)
}

fn solve_compiled_snapshot(
    model: &MetaModel<f64>,
    request: SolveRequest,
    provenance: Arc<u8>,
    generation: u64,
    relaxed: bool,
) -> Result<(String, Option<DualCertificate>, Option<Failure>), Failure> {
    let snapshot = model.linear_model_snapshot().map_err(Failure::from)?;
    if snapshot.rows.len() != model.num_constraints()
        || snapshot.variables.len() != model.num_tokens()
    {
        return Err(Failure::binding(
            "NOT_SUPPORTED",
            "仅支持直接线性行与变量 / Only direct linear rows and variables are supported",
        ));
    }
    let compiled_snapshot = if relaxed {
        let mut snapshot = snapshot.clone();
        for state in &mut snapshot.variables {
            *state = state.relaxed().map_err(Failure::from)?;
        }
        snapshot
    } else {
        snapshot.clone()
    };
    let compilation = compiled_snapshot.compile_flt64().map_err(Failure::from)?;
    let cancellation = request.cancellation.clone();
    let report = execute(model, request, Some(&compilation.model))?;
    let cancelled = cancellation
        .as_ref()
        .is_some_and(|handle| handle.inner().cancellation_preceded_completion());
    let certificate = crate::dual::issue(
        &compiled_snapshot,
        &compilation,
        &report,
        provenance,
        generation,
        cancelled,
    );
    let raw = serialize(&report)?;
    Ok(match certificate {
        Ok(certificate) => (raw, Some(certificate), None),
        Err(error) => (raw, None, Some(error)),
    })
}

pub(crate) fn execute(
    model: &MetaModel<f64>,
    request: SolveRequest,
    compiled: Option<&LinearTriadModel>,
) -> Result<SolveReport<f64>, Failure> {
    let target = match compiled {
        Some(compiled) => SolveTarget::Compiled(compiled),
        None => SolveTarget::Source(model),
    };
    execute_inner(model.model_identity(), request, target)
}

pub(crate) fn execute_compiled(
    model_identity: u64,
    request: SolveRequest,
    compiled: &LinearTriadModel,
) -> Result<SolveReport<f64>, Failure> {
    execute_inner(model_identity, request, SolveTarget::Compiled(compiled))
}

#[cfg_attr(
    not(any(
        feature = "scip",
        feature = "gurobi10",
        feature = "gurobi11",
        feature = "gurobi12"
    )),
    allow(dead_code)
)]
enum SolveTarget<'a> {
    Source(&'a MetaModel<f64>),
    Compiled(&'a LinearTriadModel),
}

fn execute_inner(
    model_identity: u64,
    request: SolveRequest,
    target: SolveTarget<'_>,
) -> Result<SolveReport<f64>, Failure> {
    let time_limit = request
        .time_limit
        .map(|seconds| {
            if !seconds.is_finite() || seconds <= 0.0 {
                return Err(Failure::input(
                    "时间限制必须有限且为正 / Time limit must be finite and positive",
                ));
            }
            let duration = std::time::Duration::try_from_secs_f64(seconds)
                .map_err(|_| Failure::input("无效时间限制 / Invalid time limit"))?;
            if duration.is_zero() {
                return Err(Failure::input(
                    "时间限制过小，无法表示 / Time limit too small to represent",
                ));
            }
            Ok(duration)
        })
        .transpose()?;
    if !crate::compiled_solvers().contains(&request.solver.as_str()) {
        let known = ["scip", "gurobi10", "gurobi11", "gurobi12"].contains(&request.solver.as_str());
        return Err(Failure::binding(
            if known {
                "SOLVER_NOT_AVAILABLE"
            } else {
                "NOT_SUPPORTED"
            },
            format!(
                "后端未编译或不受支持 / Backend not compiled or unsupported: {}",
                request.solver
            ),
        ));
    }
    if matches!(target, SolveTarget::Compiled(_))
        && request.solver == "scip"
        && time_limit.is_some()
    {
        return Err(Failure::binding(
            "NOT_SUPPORTED",
            "SCIP 编译模型的时限尚未验证 / SCIP compiled-model time limits are not validated",
        ));
    }
    let _attempt = request
        .cancellation
        .as_ref()
        .map(SolveHandle::begin)
        .transpose()?;
    let bridge = request
        .on_progress
        .map(|callback| ProgressBridge::new(callback, model_identity));
    let _callbacks = CallbackLease(bridge.clone());
    let reporter = bridge.as_ref().map(ProgressBridge::reporter);
    let options = ospf_rust_core::solver::SolveOptions {
        time_limit,
        cancellation_handle: request.cancellation.as_ref().map(SolveHandle::inner),
        progress_reporter: reporter.as_ref(),
        ..Default::default()
    };
    let result = run_solver(&target, &request.solver, &options, bridge.as_ref());
    if let Some(error) = bridge.as_ref().and_then(|bridge| bridge.failure()) {
        return Err(Failure::from(error));
    }
    let report = result?;
    report.validate().map_err(Failure::from)?;
    Ok(report)
}

pub(crate) fn serialize(report: &SolveReport<f64>) -> Result<String, Failure> {
    serde_json::to_string(&report).map_err(|error| {
        Failure::binding(
            "DATA_LOSS",
            format!("报告序列化失败 / Report serialization failed: {error}"),
        )
    })
}

fn run_solver(
    target: &SolveTarget<'_>,
    solver: &str,
    options: &ospf_rust_core::solver::SolveOptions<'_>,
    bridge: Option<&Arc<ProgressBridge>>,
) -> Result<ospf_rust_core::solver::SolveReport<f64>, Failure> {
    let _ = (target, options, bridge);
    // 上游报告读取后端配置；同一时限也须作为单次选项传入。 / Upstream reports read the backend config; pass the same limit as a per-solve option too.
    let time_limit = options.time_limit.map(|limit| limit.as_secs_f64());
    let _ = time_limit;
    match solver {
        #[cfg(feature = "scip")]
        "scip" => {
            use ospf_rust_core_plugin_scip::{
                SCIPConfig, SCIPSolver, SCIPTelemetryCallback, SCIPTelemetryStatus,
            };
            let telemetry_callback = bridge.map(|bridge| {
                let bridge = Arc::clone(bridge);
                Arc::new(move |snapshot: &SCIPTelemetryStatus| bridge.emit(snapshot.into()))
                    as SCIPTelemetryCallback
            });
            let config = SCIPConfig {
                output_flag: false,
                time_limit,
                telemetry_callback,
                ..Default::default()
            };
            let solver = SCIPSolver::with_config(config);
            match target {
                SolveTarget::Compiled(compiled) => {
                    solver.solve_linear_report_with_options(compiled, options)
                }
                SolveTarget::Source(model) => model.solve_report_with_options(&solver, options),
            }
            .map_err(Failure::from)
        }
        #[cfg(any(feature = "gurobi10", feature = "gurobi11", feature = "gurobi12"))]
        name if crate::compiled_solvers().contains(&name) && name.starts_with("gurobi") => {
            use ospf_rust_core_plugin_gurobi::{
                GurobiConfig, GurobiSolver, GurobiTelemetryCallback, GurobiTelemetryStatus,
            };
            let telemetry_callback = bridge.map(|bridge| {
                let bridge = Arc::clone(bridge);
                Arc::new(move |snapshot: &GurobiTelemetryStatus| bridge.emit(snapshot.into()))
                    as GurobiTelemetryCallback
            });
            let config = GurobiConfig {
                output_flag: false,
                time_limit,
                telemetry_callback,
                ..Default::default()
            };
            let solver = GurobiSolver::with_config(config);
            match target {
                SolveTarget::Compiled(compiled) => {
                    solver.solve_linear_report_with_options(compiled, options)
                }
                SolveTarget::Source(model) => model.solve_report_with_options(&solver, options),
            }
            .map_err(Failure::from)
        }
        _ => Err(Failure::binding(
            "SOLVER_NOT_AVAILABLE",
            "未编译后端 / Backend not compiled",
        )),
    }
}
