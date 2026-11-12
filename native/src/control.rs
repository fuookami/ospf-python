//! 单次 attempt 的共享取消事实来自 Rust。 / Rust owns the shared cancellation facts of one attempt.

use std::sync::Arc;
use std::sync::atomic::{AtomicU8, Ordering};

use ospf_rust_core::solver::{CancellationOrigin, SolveHandle as CoreHandle};
use pyo3::prelude::*;

use crate::failure::{Failure, Transport, transport};

struct Shared {
    handle: CoreHandle,
    phase: AtomicU8,
}

#[pyclass(frozen, from_py_object, module = "ospf_python._native")]
#[derive(Clone)]
pub struct SolveHandle {
    shared: Arc<Shared>,
}

#[pyclass(frozen, get_all, module = "ospf_python._native")]
pub struct CancellationRecord {
    pub origin: String,
    pub requested_at_epoch_ms: u64,
    pub reason: Option<String>,
}

pub struct AttemptLease(Arc<Shared>);

impl Drop for AttemptLease {
    fn drop(&mut self) {
        // 也覆盖建模/回调提前失败；核心若已完成，保留其更早的完成事实。 / Cover early failures without replacing core completion.
        self.0.handle.mark_completed();
        self.0.phase.store(2, Ordering::Release);
    }
}

impl SolveHandle {
    pub fn begin(&self) -> Result<AttemptLease, Failure> {
        self.shared
            .phase
            .compare_exchange(0, 1, Ordering::AcqRel, Ordering::Acquire)
            .map_err(|_| {
                Failure::binding(
                    "FAILED_PRECONDITION",
                    "取消句柄仅用于一次求解 / A solve handle is single-use",
                )
            })?;
        Ok(AttemptLease(Arc::clone(&self.shared)))
    }

    pub fn inner(&self) -> &CoreHandle {
        &self.shared.handle
    }
}

#[pymethods]
impl SolveHandle {
    #[new]
    fn new() -> Self {
        Self {
            shared: Arc::new(Shared {
                handle: CoreHandle::new(),
                phase: AtomicU8::new(0),
            }),
        }
    }

    #[getter]
    fn phase(&self) -> &'static str {
        match self.shared.phase.load(Ordering::Acquire) {
            0 => "READY",
            1 => "RUNNING",
            _ => "FINISHED",
        }
    }

    #[getter]
    fn is_cancelled(&self, py: Python<'_>) -> bool {
        py.detach(|| self.inner().is_cancelled())
    }

    #[getter]
    fn completed_at_epoch_ms(&self, py: Python<'_>) -> Option<u64> {
        py.detach(|| self.inner().completed_at_epoch_ms())
    }

    #[getter]
    fn cancellation_preceded_completion(&self, py: Python<'_>) -> bool {
        py.detach(|| self.inner().cancellation_preceded_completion())
    }

    fn cancellation(&self, py: Python<'_>) -> Option<CancellationRecord> {
        py.detach(|| {
            self.inner()
                .cancellation()
                .map(|record| CancellationRecord {
                    origin: record.origin.to_wire_code().to_owned(),
                    requested_at_epoch_ms: record.requested_at_epoch_ms,
                    reason: record.reason,
                })
        })
    }

    #[pyo3(signature = (*, origin="user", reason=None))]
    fn cancel(&self, py: Python<'_>, origin: &str, reason: Option<String>) -> Transport<bool> {
        transport(py.detach(|| {
            if origin.trim().is_empty() {
                return Err(Failure::input(
                    "取消来源不能为空 / Cancellation origin must not be empty",
                ));
            }
            Ok(self
                .inner()
                .cancel_with_reason(CancellationOrigin::from_wire_code(origin), reason))
        }))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn one_attempt_cannot_be_reused_or_shared_by_concurrent_solves() {
        let handle = SolveHandle::new();
        let lease = handle.begin().unwrap();
        assert_eq!(handle.phase(), "RUNNING");
        assert!(handle.clone().begin().is_err());
        drop(lease);
        assert_eq!(handle.phase(), "FINISHED");
        assert!(handle.begin().is_err());
        assert!(handle.inner().completed_at_epoch_ms().is_some());
    }

    #[test]
    fn late_cancellation_retains_the_core_linearization() {
        let handle = SolveHandle::new();
        drop(handle.begin().unwrap());
        assert!(handle.inner().cancel(CancellationOrigin::User));
        assert!(!handle.inner().cancellation_preceded_completion());
    }
}
