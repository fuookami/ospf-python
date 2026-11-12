//! 结构化失败传输，不按消息猜测错误。 / Structured failure transport without text classification.

use ospf_rust_base::error::ErrorCode;
use ospf_rust_core::error::{CoreError, ModelError, SolverError, VariableError};
use pyo3::class::gc::{PyTraverseError, PyVisit};
use pyo3::prelude::*;

#[pyclass(frozen, get_all, module = "ospf_python._native")]
#[derive(Clone, Debug)]
pub struct Failure {
    pub category: &'static str,
    pub source: &'static str,
    pub rust_code: Option<u8>,
    pub error_class: &'static str,
    pub message: String,
}

pub type Transport<T> = (Option<T>, Option<Failure>);

pub fn transport<T>(result: Result<T, Failure>) -> Transport<T> {
    match result {
        Ok(value) => (Some(value), None),
        Err(error) => (None, Some(error)),
    }
}

pub fn transport_unit(result: Result<(), Failure>) -> Transport<()> {
    // PyO3 将 Rust unit 转为 ()；这里的 Python 合同要求 None。 / PyO3 maps Rust unit to (); this Python contract requires None.
    (None, result.err())
}

/// 复用既有 Python Result 工厂，不保留调用载荷。 / Reuse existing Python Result factories without retaining call payloads.
pub(crate) struct ResultPublication {
    success: Py<PyAny>,
    failure: Py<PyAny>,
    missing_message: &'static str,
}

fn call_one<'py>(
    callable: &Bound<'py, PyAny>,
    argument: &Bound<'py, PyAny>,
) -> PyResult<Bound<'py, PyAny>> {
    let args = [argument.as_ptr()];
    // SAFETY: the argument is a live borrowed reference; Vectorcall returns one owned reference and reports Python errors normally.
    unsafe {
        Bound::from_owned_ptr_or_err(
            callable.py(),
            pyo3::ffi::PyObject_Vectorcall(
                callable.as_ptr(),
                args.as_ptr(),
                1,
                std::ptr::null_mut(),
            ),
        )
    }
}

impl ResultPublication {
    pub(crate) fn new(
        success: Py<PyAny>,
        failure: Py<PyAny>,
        missing_message: &'static str,
    ) -> Self {
        Self {
            success,
            failure,
            missing_message,
        }
    }

    pub(crate) fn publish(
        &self,
        py: Python<'_>,
        payload: Transport<Py<PyAny>>,
    ) -> PyResult<Py<PyAny>> {
        match payload {
            (Some(value), None) => Ok(call_one(self.success.bind(py), value.bind(py))?.unbind()),
            (_, Some(failure)) => {
                let failure = failure.into_pyobject(py)?.into_any();
                Ok(call_one(self.failure.bind(py), &failure)?.unbind())
            }
            _ => Ok(self
                .failure
                .bind(py)
                .call1((Failure::binding("APPLICATION_ERROR", self.missing_message),))?
                .unbind()),
        }
    }

    pub(crate) fn traverse(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        visit.call(&self.success)?;
        visit.call(&self.failure)
    }
}

impl Failure {
    pub fn binding(category: &'static str, message: impl Into<String>) -> Self {
        Self {
            category,
            source: "ospf-python-native",
            rust_code: None,
            error_class: "BOUNDARY",
            message: message.into(),
        }
    }

    pub fn input(message: impl Into<String>) -> Self {
        let mut failure = Self::binding("ILLEGAL_ARGUMENT", message);
        failure.rust_code = Some(ErrorCode::IllegalArgument.to_u8());
        failure
    }
}

impl From<CoreError> for Failure {
    fn from(error: CoreError) -> Self {
        use CoreError as C;
        use ModelError as M;
        use SolverError as S;
        use VariableError as V;
        let (category, rust_code) = match &error {
            C::Variable(V::NotFound(_)) => ("NOT_FOUND", None),
            C::Variable(V::AlreadyExists(_) | V::NameConflict(_)) => ("ALREADY_EXIST", None),
            C::Variable(V::InvalidRange { .. } | V::InvalidValue { .. }) => {
                ("ILLEGAL_ARGUMENT", None)
            }
            C::Model(M::NotInitialized) => ("NOT_INITIALIZED", None),
            C::Model(M::AlreadySolved | M::MissingObjective | M::SymbolNotRegistered(_)) => {
                ("FAILED_PRECONDITION", None)
            }
            C::Model(_) => ("MODEL_BUILD_FAILED", None),
            C::Solver(S::NotAvailable(_)) => ("SOLVER_NOT_AVAILABLE", None),
            C::Solver(S::Cancelled(_) | S::Interrupted(_)) => ("CANCELLED", None),
            C::Solver(S::InvalidInput(_) | S::NonFinite(_)) => ("ILLEGAL_ARGUMENT", None),
            C::Solver(S::Parsing(_)) => ("PARSING_FAILED", None),
            C::Solver(S::NoSolution | S::Unbounded | S::Infeasible | S::InfeasibleOrUnbounded) => {
                ("NO_SOLUTION", None)
            }
            C::Solver(S::Overflow(_)) => ("OVERFLOW", None),
            C::Solver(S::UnsupportedValueType(_)) | C::NotImplemented(_) => ("NOT_SUPPORTED", None),
            C::Solver(S::Timeout(_)) => ("TIMEOUT", None),
            C::Solver(S::LicenseError(_)) => ("PERMISSION_DENIED", None),
            C::Solver(_) => ("SOLVE_FAILED", None),
            C::SolverNotFound(_) => ("SOLVER_NOT_AVAILABLE", Some(ErrorCode::SolverNotFound)),
            C::SolverEnvironmentLost(_) => {
                ("UNAVAILABLE", Some(ErrorCode::OREngineEnvironmentLost))
            }
            C::SolverSolving(_) => ("SOLVE_FAILED", Some(ErrorCode::OREngineSolvingException)),
            C::SolverModeling(_) => (
                "MODEL_BUILD_FAILED",
                Some(ErrorCode::OREngineModelingException),
            ),
            C::SolverTerminated(_) => ("ABORTED", Some(ErrorCode::OREngineTerminated)),
            C::Internal(_) => ("APPLICATION_ERROR", None),
        };
        Self {
            category,
            source: "ospf-rust-core",
            rust_code: rust_code.map(ErrorCode::to_u8),
            error_class: error.solver_error_class_code(),
            message: format!("Rust 操作失败 / Rust operation failed: {error}"),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ospf_rust_base::error::ErrorPosition;
    use ospf_rust_core::error::{
        SolverEnvironmentLostError, SolverModelingError, SolverNotFoundError, SolverSolvingError,
        SolverTerminatedError,
    };
    use ospf_rust_core::variable::VariableId;

    #[test]
    fn unit_transport_uses_none_and_keeps_failure() {
        let (value, failure) = transport_unit(Ok(()));
        assert!(value.is_none() && failure.is_none());
        let (value, failure) = transport_unit(Err(Failure::input("失败 / Failure")));
        assert!(value.is_none());
        assert_eq!(failure.unwrap().category, "ILLEGAL_ARGUMENT");
    }

    #[test]
    fn publication_preserves_unit_values_and_failure_priority() {
        Python::initialize();
        Python::attach(|py| {
            let publication = ResultPublication::new(
                py.eval(c"lambda value: ('ok', value)", None, None)
                    .unwrap()
                    .unbind(),
                py.eval(c"lambda error: (error.category, error.message)", None, None)
                    .unwrap()
                    .unbind(),
                "缺失结果 / Missing result",
            );
            let result = publication.publish(py, transport(Ok(py.None()))).unwrap();
            assert_eq!(
                result.extract::<(String, Option<usize>)>(py).unwrap(),
                ("ok".into(), None)
            );
            for value in [None, Some(py.None())] {
                let result = publication
                    .publish(py, (value, Some(Failure::input("失败 / Failure"))))
                    .unwrap();
                assert_eq!(
                    result.extract::<(String, String)>(py).unwrap(),
                    ("ILLEGAL_ARGUMENT".into(), "失败 / Failure".into())
                );
            }
            let result = publication.publish(py, (None, None)).unwrap();
            assert_eq!(
                result.extract::<(String, String)>(py).unwrap(),
                (
                    "APPLICATION_ERROR".into(),
                    "缺失结果 / Missing result".into()
                )
            );
        });
    }

    #[test]
    fn semantic_mapping_never_invents_a_core_numeric_code() {
        let error = Failure::from(CoreError::Variable(VariableError::NameConflict("x".into())));
        assert_eq!(error.category, "ALREADY_EXIST");
        assert_eq!(error.rust_code, None);
        assert_eq!(error.error_class, "INPUT");
        let error = Failure::from(CoreError::solver_environment("missing library"));
        assert_eq!(error.category, "UNAVAILABLE");
        assert_eq!(error.rust_code, Some(0x24));
    }

    #[test]
    fn every_core_error_variant_has_the_documented_mapping() {
        use std::time::Duration;

        let cases = vec![
            (
                CoreError::Variable(VariableError::NotFound(VariableId::standalone(0))),
                "NOT_FOUND",
                None,
                "INPUT",
            ),
            (
                CoreError::Variable(VariableError::AlreadyExists(VariableId::standalone(0))),
                "ALREADY_EXIST",
                None,
                "INPUT",
            ),
            (
                CoreError::Variable(VariableError::InvalidRange {
                    lower: Some(1.0),
                    upper: Some(0.0),
                }),
                "ILLEGAL_ARGUMENT",
                None,
                "INPUT",
            ),
            (
                CoreError::Variable(VariableError::InvalidValue {
                    var_id: VariableId::standalone(0),
                    value: f64::NAN,
                }),
                "ILLEGAL_ARGUMENT",
                None,
                "INPUT",
            ),
            (
                CoreError::Variable(VariableError::NameConflict("x".into())),
                "ALREADY_EXIST",
                None,
                "INPUT",
            ),
            (
                CoreError::Model(ModelError::NotInitialized),
                "NOT_INITIALIZED",
                None,
                "MODELING",
            ),
            (
                CoreError::Model(ModelError::AlreadySolved),
                "FAILED_PRECONDITION",
                None,
                "MODELING",
            ),
            (
                CoreError::Model(ModelError::MissingObjective),
                "FAILED_PRECONDITION",
                None,
                "MODELING",
            ),
            (
                CoreError::Model(ModelError::SymbolNotRegistered("x".into())),
                "FAILED_PRECONDITION",
                None,
                "MODELING",
            ),
            (
                CoreError::Model(ModelError::ConstraintConflict("x".into())),
                "MODEL_BUILD_FAILED",
                None,
                "MODELING",
            ),
            (
                CoreError::Model(ModelError::InvalidConstraint("x".into())),
                "MODEL_BUILD_FAILED",
                None,
                "MODELING",
            ),
            (
                CoreError::Model(ModelError::ConstraintProgramming("x".into())),
                "MODEL_BUILD_FAILED",
                None,
                "MODELING",
            ),
            (
                CoreError::Solver(SolverError::NotAvailable("x".into())),
                "SOLVER_NOT_AVAILABLE",
                None,
                "ENVIRONMENT",
            ),
            (
                CoreError::Solver(SolverError::SolveFailed("x".into())),
                "SOLVE_FAILED",
                None,
                "BACKEND",
            ),
            (
                CoreError::Solver(SolverError::Cancelled("x".into())),
                "CANCELLED",
                None,
                "TERMINAL_PROJECTION",
            ),
            (
                CoreError::Solver(SolverError::Interrupted("x".into())),
                "CANCELLED",
                None,
                "TERMINAL_PROJECTION",
            ),
            (
                CoreError::Solver(SolverError::InvalidInput("x".into())),
                "ILLEGAL_ARGUMENT",
                None,
                "INPUT",
            ),
            (
                CoreError::Solver(SolverError::Callback("x".into())),
                "SOLVE_FAILED",
                None,
                "CALLBACK",
            ),
            (
                CoreError::Solver(SolverError::Parsing("x".into())),
                "PARSING_FAILED",
                None,
                "PARSING",
            ),
            (
                CoreError::Solver(SolverError::ContractViolation("x".into())),
                "SOLVE_FAILED",
                None,
                "INTERNAL_CONTRACT",
            ),
            (
                CoreError::Solver(SolverError::NoSolution),
                "NO_SOLUTION",
                None,
                "TERMINAL_PROJECTION",
            ),
            (
                CoreError::Solver(SolverError::Unbounded),
                "NO_SOLUTION",
                None,
                "TERMINAL_PROJECTION",
            ),
            (
                CoreError::Solver(SolverError::Infeasible),
                "NO_SOLUTION",
                None,
                "TERMINAL_PROJECTION",
            ),
            (
                CoreError::Solver(SolverError::InfeasibleOrUnbounded),
                "NO_SOLUTION",
                None,
                "TERMINAL_PROJECTION",
            ),
            (
                CoreError::Solver(SolverError::NumericalError("x".into())),
                "SOLVE_FAILED",
                None,
                "NUMERICAL",
            ),
            (
                CoreError::Solver(SolverError::PrecisionLoss("x".into())),
                "SOLVE_FAILED",
                None,
                "NUMERICAL",
            ),
            (
                CoreError::Solver(SolverError::Overflow("x".into())),
                "OVERFLOW",
                None,
                "NUMERICAL",
            ),
            (
                CoreError::Solver(SolverError::NonFinite("x".into())),
                "ILLEGAL_ARGUMENT",
                None,
                "NUMERICAL",
            ),
            (
                CoreError::Solver(SolverError::UnsupportedValueType("x".into())),
                "NOT_SUPPORTED",
                None,
                "UNSUPPORTED",
            ),
            (
                CoreError::Solver(SolverError::Timeout(Duration::from_secs(1))),
                "TIMEOUT",
                None,
                "TERMINAL_PROJECTION",
            ),
            (
                CoreError::Solver(SolverError::LicenseError("x".into())),
                "PERMISSION_DENIED",
                None,
                "LICENSE",
            ),
            (
                CoreError::SolverNotFound(SolverNotFoundError::new("x")),
                "SOLVER_NOT_AVAILABLE",
                Some(0x23),
                "ENVIRONMENT",
            ),
            (
                CoreError::SolverEnvironmentLost(SolverEnvironmentLostError::new("x")),
                "UNAVAILABLE",
                Some(0x24),
                "ENVIRONMENT",
            ),
            (
                CoreError::SolverSolving(SolverSolvingError::new("x")),
                "SOLVE_FAILED",
                Some(0x27),
                "BACKEND",
            ),
            (
                CoreError::SolverModeling(SolverModelingError::new("x")),
                "MODEL_BUILD_FAILED",
                Some(0x26),
                "MODELING",
            ),
            (
                CoreError::SolverTerminated(SolverTerminatedError {
                    position: ErrorPosition {
                        file: file!(),
                        line: line!(),
                    },
                }),
                "ABORTED",
                Some(0x28),
                "TERMINAL_PROJECTION",
            ),
            (
                CoreError::NotImplemented("x".into()),
                "NOT_SUPPORTED",
                None,
                "UNSUPPORTED",
            ),
            (
                CoreError::Internal("x".into()),
                "APPLICATION_ERROR",
                None,
                "INTERNAL_CONTRACT",
            ),
        ];

        for (error, category, rust_code, error_class) in cases {
            let failure = Failure::from(error);
            assert_eq!(failure.category, category);
            assert_eq!(failure.rust_code, rust_code);
            assert_eq!(failure.error_class, error_class);
            assert_eq!(failure.source, "ospf-rust-core");
            assert!(
                failure
                    .message
                    .starts_with("Rust 操作失败 / Rust operation failed:")
            );
        }
    }
}
