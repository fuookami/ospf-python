//! 固定上游分形逃逸时间适配，不复制复数迭代算法。 / Pinned fractal escape-time adaptation without another complex-iteration implementation.

use ospf_rust_math::fractal::{FractalError, escape_time};
use ospf_rust_math::geometry::Point2;
use pyo3::prelude::*;
use pyo3::types::{PyComplex, PyComplexMethods};

use crate::failure::{Failure, Transport, transport};

fn escape_time_failure(error: FractalError) -> Failure {
    Failure::input(format!(
        "分形逃逸时间计算失败 / Fractal escape-time evaluation failed: {}",
        error.message()
    ))
}

fn evaluate(
    z_real: f64,
    z_imag: f64,
    c_real: f64,
    c_imag: f64,
    max_iterations: u64,
) -> Result<u64, Failure> {
    escape_time(
        Point2::new(z_real, z_imag),
        Point2::new(c_real, c_imag),
        max_iterations,
        2.0,
    )
    .map_err(escape_time_failure)
}

/// 在固定上游执行一次复数逃逸迭代。 / Execute one complex escape iteration in pinned upstream.
#[pyfunction]
#[pyo3(signature = (z, c, max_iterations))]
pub(crate) fn _fractal_escape_time(
    py: Python<'_>,
    z: &Bound<'_, PyComplex>,
    c: &Bound<'_, PyComplex>,
    max_iterations: u64,
) -> PyResult<Transport<u64>> {
    let z_real = z.real();
    let z_imag = z.imag();
    let c_real = c.real();
    let c_imag = c.imag();
    // Tiny calls finish well below an observable signal interval. Keep them on
    // the attaching thread to avoid two GIL transitions; long runs remain
    // cancellable and release the GIL while upstream iterates.
    let result = if max_iterations <= 4_096 {
        evaluate(z_real, z_imag, c_real, c_imag, max_iterations)
    } else {
        py.check_signals()?;
        let result = py.detach(move || evaluate(z_real, z_imag, c_real, c_imag, max_iterations));
        py.check_signals()?;
        result
    };
    Ok(transport(result))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn mandelbrot_origin_uses_pinned_escape_time() {
        assert_eq!(evaluate(0.0, 0.0, 0.0, 0.0, 64).unwrap(), 64);
    }

    #[test]
    fn julia_and_far_points_preserve_exit_semantics() {
        assert_eq!(evaluate(0.1, 0.1, -0.7, 0.27015, 200).unwrap(), 200);
        assert_eq!(evaluate(100.0, 100.0, -0.7, 0.27015, 100).unwrap(), 0);
    }

    #[test]
    fn invalid_upstream_limits_are_structured_failures() {
        let failure = evaluate(0.0, 0.0, 0.0, 0.0, 0).unwrap_err();
        assert_eq!(failure.category, "ILLEGAL_ARGUMENT");
        assert_eq!(failure.source, "ospf-python-native");
    }

    #[test]
    fn ieee_special_values_follow_pinned_comparisons() {
        assert_eq!(evaluate(f64::NAN, 0.0, 0.0, 0.0, 8).unwrap(), 8);
        assert_eq!(evaluate(f64::INFINITY, 0.0, 0.0, 0.0, 8).unwrap(), 0);
    }
}
