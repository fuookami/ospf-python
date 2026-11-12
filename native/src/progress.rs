//! Python 回调只接收脱离模型的只读快照。 / Python callbacks receive detached, read-only snapshots only.

use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Arc, Mutex};

use ospf_rust_core::error::{CoreError, Result};
use ospf_rust_core::solver::{SolveProgressReporter, SolveProgressSnapshot};
use pyo3::prelude::*;

static NEXT_ATTEMPT: AtomicU64 = AtomicU64::new(1);

#[pyclass(frozen, get_all, module = "ospf_python._native")]
pub struct SolveProgress {
    pub model_identity: u64,
    pub attempt_identity: u64,
    pub native_attempt_id: Option<String>,
    pub source: &'static str,
    pub stage: &'static str,
    pub stage_path: Vec<String>,
    pub stage_progress: Option<f64>,
    pub overall_progress: Option<f64>,
    pub elapsed_nanoseconds: u128,
    pub objective_value: Option<f64>,
    pub best_bound: Option<f64>,
    pub relative_gap: Option<f64>,
    pub terminal: bool,
    pub initial_objective_value: Option<f64>,
    pub incumbent_solution: Option<Vec<f64>>,
    pub objective_direction: Option<String>,
    pub iterations: Option<usize>,
    pub node_count: Option<usize>,
}

pub struct ProgressBridge {
    callback: Mutex<Option<Py<PyAny>>>,
    model_identity: u64,
    attempt_identity: u64,
    first_error: Mutex<Option<String>>,
}

pub struct CallbackLease(pub Option<Arc<ProgressBridge>>);

impl Drop for CallbackLease {
    fn drop(&mut self) {
        if let Some(bridge) = &self.0 {
            // 即使 backend 延长观察者生命周期，也不能延长 Python callback 的作用域。 / Backend observer retention must not retain Python callbacks.
            Python::attach(|_| {
                let callback = bridge
                    .callback
                    .lock()
                    .unwrap_or_else(|error| error.into_inner())
                    .take();
                drop(callback);
            });
        }
    }
}

impl ProgressBridge {
    pub fn new(callback: Py<PyAny>, model_identity: u64) -> Arc<Self> {
        Arc::new(Self {
            callback: Mutex::new(Some(callback)),
            model_identity,
            attempt_identity: NEXT_ATTEMPT.fetch_add(1, Ordering::Relaxed),
            first_error: Mutex::new(None),
        })
    }

    pub fn failure(&self) -> Option<CoreError> {
        self.first_error
            .lock()
            .unwrap_or_else(|error| error.into_inner())
            .as_ref()
            .map(|message| CoreError::callback_error(message.clone()))
    }

    pub fn emit(&self, mut event: SolveProgress) -> Result<()> {
        if let Some(error) = self.failure() {
            return Err(error);
        }
        event.model_identity = self.model_identity;
        event.attempt_identity = self.attempt_identity;
        // 无模型互斥锁或取消事实锁跨越 Python 调用。 / No model/cancellation mutex is held across Python calls.
        let result = Python::attach(|py| -> PyResult<Option<String>> {
            let callback = self
                .callback
                .lock()
                .unwrap_or_else(|error| error.into_inner())
                .as_ref()
                .map(|callback| callback.clone_ref(py));
            let Some(callback) = callback else {
                return Ok(Some("回调作用域已结束 / Callback scope has ended".into()));
            };
            let event = Py::new(py, event)?;
            let returned = callback.bind(py).call1((event,))?;
            if returned.is_none() {
                Ok(None)
            } else {
                returned.extract::<String>().map(Some)
            }
        });
        let message = match result {
            Ok(None) => return Ok(()),
            Ok(Some(message)) => message,
            Err(error) => format!("Python 回调失败 / Python callback failed: {error}"),
        };
        self.first_error
            .lock()
            .unwrap_or_else(|error| error.into_inner())
            .get_or_insert(message.clone());
        Err(CoreError::callback_error(message))
    }

    pub fn reporter(self: &Arc<Self>) -> SolveProgressReporter {
        let bridge = Arc::clone(self);
        Arc::new(move |snapshot| bridge.emit(SolveProgress::from(snapshot)))
    }
}

impl From<&SolveProgressSnapshot> for SolveProgress {
    fn from(snapshot: &SolveProgressSnapshot) -> Self {
        Self {
            model_identity: 0,
            attempt_identity: 0,
            native_attempt_id: Some(snapshot.attempt_id.clone()),
            source: "reporter",
            stage: snapshot.stage.stable_name(),
            stage_path: snapshot.stage_path.clone(),
            stage_progress: snapshot.stage_progress.as_known(),
            overall_progress: snapshot.overall_progress.as_known(),
            elapsed_nanoseconds: snapshot.elapsed.as_nanos(),
            objective_value: snapshot.objective_value,
            best_bound: snapshot.best_bound,
            relative_gap: snapshot.relative_gap,
            terminal: snapshot.terminal,
            initial_objective_value: None,
            incumbent_solution: None,
            objective_direction: None,
            iterations: None,
            node_count: None,
        }
    }
}

// 两个后端的只读遥测字段同构，逐字段保留而不计算新的数学结论。 / Preserve isomorphic backend telemetry without new mathematical conclusions.
#[cfg(any(
    feature = "scip",
    feature = "gurobi10",
    feature = "gurobi11",
    feature = "gurobi12"
))]
macro_rules! telemetry_snapshot {
    ($snapshot:ty) => {
        impl From<&$snapshot> for SolveProgress {
            fn from(snapshot: &$snapshot) -> Self {
                Self {
                    model_identity: 0,
                    attempt_identity: 0,
                    native_attempt_id: None,
                    source: "backend",
                    stage: "solving",
                    stage_path: vec!["solver".into(), "solving".into()],
                    stage_progress: None,
                    overall_progress: None,
                    elapsed_nanoseconds: snapshot.solve_time.as_nanos(),
                    objective_value: snapshot.objective_value,
                    best_bound: snapshot.best_bound,
                    relative_gap: snapshot.mip_gap,
                    terminal: false,
                    initial_objective_value: snapshot.initial_objective_value,
                    incumbent_solution: snapshot.incumbent_solution.clone(),
                    objective_direction: Some(format!("{:?}", snapshot.objective_category)),
                    iterations: snapshot.iterations,
                    node_count: snapshot.node_count,
                }
            }
        }
    };
}

#[cfg(feature = "scip")]
telemetry_snapshot!(ospf_rust_core_plugin_scip::SCIPTelemetryStatus);
#[cfg(any(feature = "gurobi10", feature = "gurobi11", feature = "gurobi12"))]
telemetry_snapshot!(ospf_rust_core_plugin_gurobi::GurobiTelemetryStatus);
