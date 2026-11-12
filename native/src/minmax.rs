//! 通过固定 Rust 排序保留 Python 的比较协议。 / Preserve Python comparison protocols through pinned Rust ordering.

use std::cell::{Cell, RefCell};
use std::cmp::Ordering;

use ospf_rust_math::ordinary::minmax;
use pyo3::prelude::*;
use pyo3::types::{PyInt, PyList, PyTuple};

use crate::public_integer::{IntegerOps, IntegerRange, integer_range};

#[derive(Default)]
struct PairState {
    order: Cell<Option<Ordering>>,
    error: RefCell<Option<PyErr>>,
}

struct Compared<'a, 'py> {
    value: &'a Bound<'py, PyAny>,
    left: bool,
    minimum: bool,
    state: &'a PairState,
}

impl PartialEq for Compared<'_, '_> {
    fn eq(&self, other: &Self) -> bool {
        std::ptr::eq(self.state, other.state) && self.left == other.left
    }
}

impl PartialOrd for Compared<'_, '_> {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        if !std::ptr::eq(self.state, other.state) {
            return None;
        }
        if self.left == other.left {
            return Some(Ordering::Equal);
        }
        let order = match self.state.order.get() {
            Some(order) => order,
            None => {
                let (left, right) = if self.left {
                    (self.value, other.value)
                } else {
                    (other.value, self.value)
                };
                // 缓存单次 Python 比较，使位置排序一致且保留原有调用顺序。 / Cache one Python comparison for consistent slot ordering and original call order.
                let before = match if self.minimum {
                    right.lt(left).map(|less| !less)
                } else {
                    right.gt(left)
                } {
                    Ok(value) => value,
                    Err(error) => {
                        *self.state.error.borrow_mut() = Some(error);
                        return None;
                    }
                };
                let order = if before {
                    Ordering::Less
                } else {
                    Ordering::Greater
                };
                self.state.order.set(Some(order));
                order
            }
        };
        Some(if self.left { order } else { order.reverse() })
    }
}

fn select_right<'py>(
    left: &Bound<'py, PyAny>,
    right: &Bound<'py, PyAny>,
    minimum: bool,
) -> PyResult<bool> {
    let state = PairState::default();
    let (first, second) = minmax(
        Compared {
            value: left,
            left: true,
            minimum,
            state: &state,
        },
        Compared {
            value: right,
            left: false,
            minimum,
            state: &state,
        },
    );
    if let Some(error) = state.error.borrow_mut().take() {
        return Err(error);
    }
    Ok(!if minimum { first.left } else { second.left })
}

#[derive(Clone, Copy)]
struct SmallCandidate {
    index: usize,
    value: i64,
}

impl PartialEq for SmallCandidate {
    fn eq(&self, other: &Self) -> bool {
        self.value == other.value
    }
}

impl PartialOrd for SmallCandidate {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        self.value.partial_cmp(&other.value)
    }
}

fn select_small_int_list(
    py: Python<'_>,
    list: &Bound<'_, PyList>,
    minimum: bool,
) -> PyResult<Option<usize>> {
    let length = list.len();
    // 小列表直接走原迭代协议，避免快路径分派抵销固定调用成本。
    // Keep short lists on the original iteration protocol so fast-path dispatch does not dominate fixed call cost.
    if length < 64 {
        return Ok(None);
    }
    let pointer = unsafe { pyo3::ffi::PyList_GET_ITEM(list.as_ptr(), 0) };
    let first = unsafe { Bound::ref_from_ptr(py, &pointer) };
    if !first.is_exact_instance_of::<PyInt>() {
        return Ok(None);
    }
    let IntegerRange::Small(value) = integer_range(first)? else {
        return Ok(None);
    };
    let mut best = SmallCandidate { index: 0, value };
    for index in 1..length {
        // 只读取精确 list 的借用槽位；任何非内置小整数都重跑原协议。
        // Read only exact-list borrowed slots; rerun the original protocol for any non-small builtin integer.
        let pointer =
            unsafe { pyo3::ffi::PyList_GET_ITEM(list.as_ptr(), index as pyo3::ffi::Py_ssize_t) };
        let item = unsafe { Bound::ref_from_ptr(py, &pointer) };
        if !item.is_exact_instance_of::<PyInt>() {
            return Ok(None);
        }
        let IntegerRange::Small(value) = integer_range(item)? else {
            return Ok(None);
        };
        let candidate = SmallCandidate { index, value };
        let (low, high) = minmax(best, candidate);
        best = if minimum { low } else { high };
    }
    Ok(Some(best.index))
}

/// 用户替换的函数仍是显式扩展钩子。 / User-replaced functions remain explicit extension hooks.
#[pyfunction]
#[pyo3(signature = (*, left, right, callable, minimum, ops))]
pub(crate) fn _minmax_pair<'py>(
    left: &Bound<'py, PyAny>,
    right: &Bound<'py, PyAny>,
    callable: &Bound<'py, PyAny>,
    minimum: bool,
    ops: PyRef<'py, IntegerOps>,
) -> PyResult<Bound<'py, PyAny>> {
    if ops.is_or_current_builtin(callable, minimum)? {
        Ok(if select_right(left, right, minimum)? {
            right
        } else {
            left
        }
        .clone())
    } else {
        callable.call1((left, right))
    }
}

#[pyfunction]
#[pyo3(signature = (*, items, callable, minimum, ops))]
pub(crate) fn _ordinary_extreme<'py>(
    py: Python<'py>,
    items: &Bound<'py, PyAny>,
    callable: &Bound<'py, PyAny>,
    minimum: bool,
    ops: PyRef<'py, IntegerOps>,
) -> PyResult<Bound<'py, PyAny>> {
    if !ops.is_or_current_builtin(callable, minimum)? {
        return callable.call1((items,));
    }
    if items.is_exact_instance_of::<PyList>()
        && let Ok(list) = items.cast::<PyList>()
        && let Some(index) = select_small_int_list(py, list, minimum)?
    {
        return list.get_item(index);
    }
    let mut iterator = items.try_iter()?;
    let Some(first) = iterator.next() else {
        // 空迭代仅委托解释器生成本版本的错误文案，不计算极值。 / Let the interpreter produce its version-specific empty-input error; no extrema are computed.
        return callable.call1((PyTuple::empty(py),));
    };
    let mut best = first?;
    // 与内置极值一样同时持有当前值和比较键。 / Retain both the current value and its comparison key, like the builtin extrema.
    let mut best_key = best.clone();
    for item in iterator {
        let item = item?;
        let key = item.clone();
        if select_right(&best_key, &key, minimum)? {
            drop(best_key);
            best = item;
            best_key = key;
        }
    }
    drop(best_key);
    Ok(best)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn selects_original_python_objects_through_upstream_minmax() {
        Python::initialize();
        Python::attach(|py| {
            let left = 3_i32.into_pyobject(py).unwrap().into_any();
            let right = 5_i32.into_pyobject(py).unwrap().into_any();
            assert!(!select_right(&left, &right, true).unwrap());
            assert!(select_right(&left, &right, false).unwrap());
            assert!(!select_right(&left, &left, true).unwrap());
        });
    }

    #[test]
    fn pair_order_is_consistent_with_its_slot_identity() {
        Python::initialize();
        Python::attach(|py| {
            let value = 3_i32.into_pyobject(py).unwrap().into_any();
            let state = PairState::default();
            let left = Compared {
                value: &value,
                left: true,
                minimum: true,
                state: &state,
            };
            let right = Compared {
                value: &value,
                left: false,
                minimum: true,
                state: &state,
            };
            assert!(left == left);
            assert!(left != right);
            assert_eq!(left.partial_cmp(&right), Some(Ordering::Less));
            assert_eq!(right.partial_cmp(&left), Some(Ordering::Greater));
            assert!(left <= right);
            assert!(right > left);
        });
    }
}
