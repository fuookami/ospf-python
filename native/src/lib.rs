//! Python 原生边界；不重复实现 OSPF 内核。 / Python boundary without a second OSPF kernel.

use ospf_rust_base::error::ErrorCode;
use pyo3::prelude::*;
use std::collections::BTreeMap;

mod bpp1d;
mod bpp1d_extension;
mod bpp1d_pool;
mod chaotic;
mod chaotic_system;
mod combinatorics;
mod control;
mod coordinate_materialization;
mod dual;
mod elementary_operators;
mod failure;
mod fractal;
mod gantt_activity;
mod gantt_task;
mod integer_power;
mod logarithm;
mod minmax;
mod model;
mod multiarray;
mod numeric;
mod numeric_array;
mod owner;
mod prime_sieve;
mod progress;
mod projection;
mod public_floating;
mod public_integer;
mod public_rational;
mod quantities;
mod quantity_arithmetic;
mod quantity_callback;
mod quantity_duration;
mod quantity_ordering;
mod safe_rational;
mod selection;
mod shape_arithmetic;
mod shape_metadata;
mod shared_access;
mod shared_iteration;
mod shared_mapping;
mod shared_nested;
mod shared_reduce;
mod shared_view;
mod solve;
mod trivalent;

const OSPF_RUST_REVISION: &str = "74e8b38ba283d1cf97fb7647559d9ddf579fc7de";

fn compiled_solvers() -> Vec<&'static str> {
    [
        (cfg!(feature = "scip"), "scip"),
        (cfg!(feature = "gurobi10"), "gurobi10"),
        (cfg!(feature = "gurobi11"), "gurobi11"),
        (cfg!(feature = "gurobi12"), "gurobi12"),
    ]
    .into_iter()
    .filter_map(|(enabled, name)| enabled.then_some(name))
    .collect()
}

/// 查询编译期身份，不启动求解器或申请许可证。 / Inspect build identity without solver/license access.
#[pyfunction]
fn build_info() -> BTreeMap<&'static str, String> {
    BTreeMap::from([
        ("binding_version", env!("CARGO_PKG_VERSION").into()),
        ("rust_revision", OSPF_RUST_REVISION.into()),
        ("required_toolchain", "nightly-2026-08-01".into()),
        ("target_os", std::env::consts::OS.into()),
        ("target_arch", std::env::consts::ARCH.into()),
        ("native_solvers", compiled_solvers().join(",")),
    ])
}

/// 验证边界成功/失败传输，不将业务失败抛为异常。 / Exercise value/error transport without business exceptions.
#[pyfunction]
fn _checked_nonnegative(value: i64) -> (Option<i64>, Option<(u8, &'static str)>) {
    if value < 0 {
        (
            None,
            Some((
                ErrorCode::IllegalArgument.to_u8(),
                "值不能为负数 / Value must be nonnegative",
            )),
        )
    } else {
        (Some(value), None)
    }
}

/// 创建 Rust 所有者并以数据返回基础设施失败。 / Create an owner, returning infrastructure failures as data.
#[pyfunction]
fn _create_model(py: Python<'_>, name: String) -> failure::Transport<model::Model> {
    failure::transport(py.detach(|| model::Model::create(name)))
}

/// 注册私有扩展；公共领域 API 由 Python 门面负责。 / Register the private extension behind public facades.
#[pymodule]
fn _native(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add("__version__", env!("CARGO_PKG_VERSION"))?;
    module.add_function(wrap_pyfunction!(build_info, module)?)?;
    module.add_function(wrap_pyfunction!(
        quantity_arithmetic::_quantity_arithmetic,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(
        quantity_duration::_quantity_duration_from,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(
        quantity_duration::_quantity_to_timedelta,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(
        quantity_callback::_convert_quantity_callback,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(
        quantity_callback::_convert_quantity_dispatched,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(
        quantity_ordering::_quantity_extreme,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(
        quantity_ordering::_quantity_contains,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(_checked_nonnegative, module)?)?;
    module.add_function(wrap_pyfunction!(_create_model, module)?)?;
    module.add_function(wrap_pyfunction!(bpp1d::_create_bpp1d_context, module)?)?;
    module.add_function(wrap_pyfunction!(gantt_activity::_solve_activity, module)?)?;
    module.add_function(wrap_pyfunction!(gantt_task::_task_shadow_prices, module)?)?;
    module.add_function(wrap_pyfunction!(
        gantt_task::_create_task_pricing_algorithm,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(
        gantt_task::_task_improving_columns,
        module
    )?)?;
    module.add_class::<gantt_task::TaskPricingAlgorithm>()?;
    module.add_class::<bpp1d::Bpp1dContext>()?;
    module.add_class::<bpp1d_pool::Bpp1dPool>()?;
    module.add_class::<public_integer::IntegerOps>()?;
    module.add_class::<public_integer::IntegerFacade>()?;
    module.add_class::<public_floating::FloatingOps>()?;
    module.add(
        "_public_floating",
        Py::new(
            module.py(),
            public_floating::FloatingOps::create(module.py())?,
        )?,
    )?;
    module.add(
        "_public_integer",
        Py::new(
            module.py(),
            public_integer::IntegerOps::create(module.py())?,
        )?,
    )?;
    module.add_function(wrap_pyfunction!(combinatorics::_cross, module)?)?;
    module.add_function(wrap_pyfunction!(chaotic::_logistic_float64_step, module)?)?;
    module.add_function(wrap_pyfunction!(
        chaotic_system::_chaotic_system_step,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(minmax::_minmax_pair, module)?)?;
    module.add_function(wrap_pyfunction!(minmax::_ordinary_extreme, module)?)?;
    module.add_function(wrap_pyfunction!(selection::_selection, module)?)?;
    module.add_function(wrap_pyfunction!(prime_sieve::_primes_up_to, module)?)?;
    module.add_function(wrap_pyfunction!(integer_power::_pow_int, module)?)?;
    module.add_function(wrap_pyfunction!(logarithm::_log_base, module)?)?;
    module.add_function(wrap_pyfunction!(
        elementary_operators::_elementary_operator,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(fractal::_fractal_escape_time, module)?)?;
    module.add_function(wrap_pyfunction!(trivalent::_trivalent, module)?)?;
    module.add_function(wrap_pyfunction!(shape_arithmetic::_shape_size, module)?)?;
    module.add_function(wrap_pyfunction!(shape_arithmetic::_shape_strides, module)?)?;
    module.add_function(wrap_pyfunction!(
        shape_arithmetic::_shape_flat_index,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(
        coordinate_materialization::_create_coordinate_plan,
        module
    )?)?;
    module.add_class::<coordinate_materialization::CoordinatePlan>()?;
    module.add_function(wrap_pyfunction!(shared_mapping::_map_shared_array, module)?)?;
    module.add_function(wrap_pyfunction!(
        shared_reduce::_reduce_shared_array,
        module
    )?)?;
    module.add_class::<shared_iteration::SharedArrayIterator>()?;
    module.add_function(wrap_pyfunction!(shared_access::_read_shared_array, module)?)?;
    module.add_class::<multiarray::SharedAccess>()?;
    module.add_function(wrap_pyfunction!(
        shared_nested::_nested_shared_array,
        module
    )?)?;
    module.add_class::<shared_nested::SharedNested>()?;
    module.add_function(wrap_pyfunction!(
        shared_view::_materialize_shared_view,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(
        shared_iteration::_iterate_shared_array,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(numeric::_create_rational, module)?)?;
    module.add_function(wrap_pyfunction!(numeric::_rational_from_json, module)?)?;
    module.add_function(wrap_pyfunction!(numeric::_restore_rational, module)?)?;
    module.add_function(wrap_pyfunction!(
        quantities::_restore_quantity_unit,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(
        public_rational::_public_rational_normalize,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(
        public_rational::_public_rational_binary,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(
        public_rational::_public_rational_negated,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(
        public_rational::_public_rational_less,
        module
    )?)?;
    module.add_class::<numeric::Rational>()?;
    module.add_class::<quantities::QuantityUnit>()?;
    module.add_function(wrap_pyfunction!(quantities::_create_quantity_unit, module)?)?;
    module.add_function(wrap_pyfunction!(
        quantities::_create_quantity_unit_encoded,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(
        quantities::_quantity_unit_from_json,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(
        numeric_array::_create_rational_array,
        module
    )?)?;
    module.add_class::<numeric_array::RationalArray>()?;
    module.add_function(wrap_pyfunction!(multiarray::_create_shape, module)?)?;
    module.add_function(wrap_pyfunction!(
        multiarray::_checked_shared_offset,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(
        multiarray::_create_rational_multiarray,
        module
    )?)?;
    module.add_class::<multiarray::Shape>()?;
    module.add_function(wrap_pyfunction!(
        multiarray::_reshape_storage_shape,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(
        multiarray::_flatten_storage_shape,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(multiarray::_transform_storage, module)?)?;
    module.add_class::<multiarray::StorageTransform>()?;
    module.add_class::<shared_view::SharedView>()?;
    module.add_class::<multiarray::RationalMultiArray>()?;
    module.add_function(wrap_pyfunction!(multiarray::_create_multiarray, module)?)?;
    module.add_function(wrap_pyfunction!(
        multiarray::_compare_reference_arrays,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(
        multiarray::_describe_reference_array,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(multiarray::_full_multiarray, module)?)?;
    module.add_function(wrap_pyfunction!(
        multiarray::_multiarray_from_nested,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(
        multiarray::_mutable_multiarray_from_nested,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(
        multiarray::_full_mutable_multiarray,
        module
    )?)?;
    module.add_class::<multiarray::MultiArray>()?;
    module.add_function(wrap_pyfunction!(
        multiarray::_create_mutable_multiarray,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(
        multiarray::_create_multiarray_view,
        module
    )?)?;
    module.add_class::<multiarray::MutableMultiArray>()?;
    module.add_class::<multiarray::MultiArrayView>()?;
    module.add_class::<multiarray::iterator::MultiArrayIterator>()?;
    module.add_function(wrap_pyfunction!(
        multiarray::iterator::_create_reference_iterator,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(multiarray::_unpickle_shape, module)?)?;
    module.add_function(wrap_pyfunction!(multiarray::_unpickle_multiarray, module)?)?;
    module.add_function(wrap_pyfunction!(
        multiarray::_unpickle_mutable_multiarray,
        module
    )?)?;
    module.add_function(wrap_pyfunction!(
        multiarray::_unpickle_multiarray_view,
        module
    )?)?;
    module.add_class::<failure::Failure>()?;
    module.add_class::<model::VariableHandle>()?;
    module.add_class::<model::ConstraintHandle>()?;
    module.add_class::<dual::DualCertificate>()?;
    module.add_class::<model::Model>()?;
    module.add_class::<projection::Projection>()?;
    module.add_class::<projection::PricingRequest>()?;
    module.add_class::<projection::PricingBound>()?;
    module.add_class::<projection::ProjectionSolution>()?;
    module.add_class::<control::SolveHandle>()?;
    module.add_class::<control::CancellationRecord>()?;
    module.add_class::<progress::SolveProgress>()?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::_checked_nonnegative;

    #[test]
    fn nonnegative_values_preserve_i64_domain() {
        assert_eq!(_checked_nonnegative(0), (Some(0), None));
        assert_eq!(_checked_nonnegative(i64::MAX), (Some(i64::MAX), None));
    }

    #[test]
    fn negative_values_keep_rust_error_identity() {
        let (value, error) = _checked_nonnegative(i64::MIN);
        assert!(value.is_none());
        assert_eq!(error.map(|detail| detail.0), Some(0x34));
    }
}
