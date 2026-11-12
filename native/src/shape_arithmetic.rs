//! 公开形状的计算边界，不缓存另一份元数据。 / Public shape arithmetic without a second metadata cache.

use num_bigint::BigInt;
use num_traits::ToPrimitive;
use ospf_rust_multiarray::{AbstractShape, DynShape};
use pyo3::class::basic::CompareOp;
use pyo3::class::gc::{PyTraverseError, PyVisit};
use pyo3::exceptions::{PyOverflowError, PyRuntimeError, PyStopIteration, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyInt, PyIterator, PyList, PyTuple};
use std::sync::Mutex;

use crate::shape_metadata::{
    dense_shape as checked_dense_shape, fixed_shape_index, fixed_shape_offsets, fixed_shape_size,
    validate_dense_dimensions,
};

fn integer_tuple<'a, 'py>(value: &'a Bound<'py, PyAny>) -> Option<&'a Bound<'py, PyTuple>> {
    if !value.is_exact_instance_of::<PyTuple>() {
        return None;
    }
    let values = value.cast::<PyTuple>().ok()?;
    values
        .iter()
        .all(|item| item.is_exact_instance_of::<PyInt>())
        .then_some(values)
}

fn dense_shape(dims: &[BigInt], column_major: bool) -> Option<DynShape> {
    checked_dense_shape(dims.iter().map(BigInt::to_usize), column_major).ok()
}

fn tuple_dense_size(dims: &Bound<'_, PyTuple>) -> Option<usize> {
    validate_dense_dimensions(dims.iter().map(|dim| dim.extract::<usize>().ok())).ok()?;
    let mut batch = [0; 4];
    let mut count = 0;
    for dim in dims.iter() {
        if count == batch.len() {
            // 固定形状组合上游长度，避免动态 offsets 的按 rank 分配。 / Compose upstream fixed-shape lengths without rank-sized dynamic offsets.
            batch[0] = fixed_shape_size(batch).ok()?;
            count = 1;
        }
        batch[count] = dim.extract::<usize>().ok()?;
        count += 1;
    }
    match count {
        0 => fixed_shape_size([]),
        1 => fixed_shape_size([batch[0]]),
        2 => fixed_shape_size([batch[0], batch[1]]),
        3 => fixed_shape_size([batch[0], batch[1], batch[2]]),
        4 => fixed_shape_size(batch),
        _ => unreachable!(),
    }
    .ok()
}

fn tuple_dense_strides(
    py: Python<'_>,
    dims: &Bound<'_, PyTuple>,
    column_major: bool,
) -> PyResult<Option<Py<PyAny>>> {
    if validate_dense_dimensions(dims.iter().map(|dim| dim.extract::<usize>().ok())).is_err() {
        return Ok(None);
    }
    let rank = dims.len();
    // 新 tuple 未暴露；失败时保留 Python 分配异常。 / The new tuple is private; retain Python allocation errors.
    let output =
        unsafe { Bound::from_owned_ptr_or_err(py, pyo3::ffi::PyTuple_New(rank as isize))? };
    let mut base = 1usize;
    for chunk in 0..rank.div_ceil(4) {
        let (start, end) = if column_major {
            let start = chunk * 4;
            (start, (start + 4).min(rank))
        } else {
            let end = rank - chunk * 4;
            (end.saturating_sub(4), end)
        };
        let mut batch = [1usize; 4];
        for (axis, slot) in batch.iter_mut().take(end - start).enumerate() {
            *slot = dims.get_item(start + axis)?.extract::<usize>()?;
        }
        let (offsets, len) = fixed_shape_offsets(batch, column_major).map_err(|_| {
            PyValueError::new_err("形状容量校验失败 / Shape capacity validation failed")
        })?;
        for (axis, offset) in offsets.into_iter().take(end - start).enumerate() {
            // SAFETY: 已验证的机器整数仅用于构造新引用；输出 tuple 尚未共享，索引唯一且在界内。 / Checked machine integers create owned references; the tuple is private and each index is unique and in bounds.
            unsafe {
                let value = Bound::from_owned_ptr_or_err(
                    py,
                    pyo3::ffi::PyLong_FromUnsignedLongLong((base * offset) as u64),
                )?;
                if pyo3::ffi::PyTuple_SetItem(
                    output.as_ptr(),
                    (start + axis) as isize,
                    value.into_ptr(),
                ) != 0
                {
                    return Err(PyErr::fetch(py));
                }
            }
        }
        base *= len;
    }
    Ok(Some(output.unbind()))
}

fn tuple_dense_index(
    dims: &Bound<'_, PyTuple>,
    strides: &Bound<'_, PyTuple>,
    indices: &Bound<'_, PyTuple>,
    column_major: bool,
) -> PyResult<Option<usize>> {
    if validate_dense_dimensions(dims.iter().map(|dim| dim.extract::<usize>().ok())).is_err() {
        return Ok(None);
    }
    let rank = dims.len();
    if rank == 0 {
        return Ok(fixed_shape_index([], [], column_major).map(|(_, _, index)| index));
    }
    let mut base = 1usize;
    let mut index = 0usize;
    // 组合上游固定形状索引，避免随 rank 增长的分配。 / Compose upstream fixed-shape indices without rank-sized allocations.
    for chunk in 0..rank.div_ceil(4) {
        let (start, end) = if column_major {
            let start = chunk * 4;
            (start, (start + 4).min(rank))
        } else {
            let end = rank - chunk * 4;
            (end.saturating_sub(4), end)
        };
        let mut batch = [1usize; 4];
        let mut coordinates = [0usize; 4];
        let mut given_strides = [0usize; 4];
        for axis in 0..end - start {
            batch[axis] = dims.get_item(start + axis)?.extract::<usize>()?;
            let Ok(coordinate) = indices.get_item(start + axis)?.extract::<usize>() else {
                return Ok(None);
            };
            let Ok(stride) = strides.get_item(start + axis)?.extract::<usize>() else {
                return Ok(None);
            };
            coordinates[axis] = coordinate;
            given_strides[axis] = stride;
        }
        let Some((offsets, len, partial)) = fixed_shape_index(batch, coordinates, column_major)
        else {
            return Ok(None);
        };
        if (0..end - start).any(|axis| given_strides[axis] != base * offsets[axis]) {
            return Ok(None);
        }
        index += base * partial;
        base *= len;
    }
    Ok(Some(index))
}

fn tuple_bounded_index(
    strides: &Bound<'_, PyTuple>,
    indices: &Bound<'_, PyTuple>,
) -> PyResult<Option<i128>> {
    let py = strides.py();
    let extract = |value: Bound<'_, PyAny>| match value.extract::<i128>() {
        Ok(value) => Ok(Some(value)),
        Err(error) if error.is_instance_of::<PyOverflowError>(py) => Ok(None),
        Err(error) => Err(error),
    };
    let mut total = 0i128;
    for (stride, index) in strides.iter().zip(indices.iter()) {
        let Some(stride) = extract(stride)? else {
            return Ok(None);
        };
        let Some(index) = extract(index)? else {
            return Ok(None);
        };
        let Some(next) = stride
            .checked_mul(index)
            .and_then(|term| total.checked_add(term))
        else {
            return Ok(None);
        };
        total = next;
    }
    Ok(Some(total))
}

fn product(py: Python<'_>, dims: &[BigInt]) -> PyResult<Py<PyAny>> {
    if let Some(shape) = dense_shape(dims, false) {
        return Ok(shape.len().into_pyobject(py)?.into_any().unbind());
    }
    // 稀疏元数据无需可寻址的稠密缓冲；不截断为 usize。 / Sparse metadata needs no addressable dense buffer; never truncate it to usize.
    Ok(dims
        .iter()
        .product::<BigInt>()
        .into_pyobject(py)?
        .into_any()
        .unbind())
}

fn integer_product(py: Python<'_>, dims: &[Bound<'_, PyAny>]) -> PyResult<Py<PyAny>> {
    let mut machine = 1usize;
    let mut fits_machine = true;
    for dim in dims {
        match dim.extract::<usize>() {
            Ok(value) => match machine.checked_mul(value) {
                Some(next) => machine = next,
                None => {
                    fits_machine = false;
                    break;
                }
            },
            Err(_) => {
                fits_machine = false;
                break;
            }
        }
    }
    if fits_machine {
        return Ok(machine.into_pyobject(py)?.into_any().unbind());
    }
    let exact = dims
        .iter()
        .map(|dim| dim.extract::<BigInt>())
        .collect::<PyResult<Vec<_>>>()?;
    product(py, &exact)
}

/// 保留固定字段的左结合乘法及动态维度的原地乘法协议。 / Preserve fixed-field left multiplication and dynamic in-place multiplication.
#[pyfunction]
pub fn _shape_size(
    py: Python<'_>,
    owner: &Bound<'_, PyAny>,
    rank: Option<usize>,
) -> PyResult<Py<PyAny>> {
    if let Some(rank) = rank {
        if !(2..=4).contains(&rank) {
            return Err(PyValueError::new_err(
                "固定形状计算仅接受2至4轴 / Fixed shape arithmetic requires two to four axes",
            ));
        }
        let names = ["d0", "d1", "d2", "d3"];
        let mut seen: [Option<Bound<'_, PyAny>>; 4] = std::array::from_fn(|_| None);
        let mut machine_dims = [0; 4];
        let mut machine = 1usize;
        let mut machine_mode = true;
        let mut exact: Vec<Bound<'_, PyAny>> = Vec::new();
        let mut first = None;
        let mut accumulated: Option<Bound<'_, PyAny>> = None;
        for (index, name) in names.iter().take(rank).enumerate() {
            let dim = owner.getattr(*name)?;
            if machine_mode {
                if dim.is_exact_instance_of::<PyInt>()
                    && let Ok(value) = dim.extract::<usize>()
                    && let Some(next) = machine.checked_mul(value)
                {
                    machine = next;
                    seen[index] = Some(dim);
                    machine_dims[index] = value;
                    continue;
                }
                machine_mode = false;
                exact.extend(seen[..index].iter_mut().filter_map(Option::take));
                first = exact.first().cloned();
            }
            accumulated = match accumulated {
                Some(value) => Some(value.mul(&dim)?),
                None if dim.is_exact_instance_of::<PyInt>() => {
                    first = if exact.is_empty() {
                        Some(dim.clone())
                    } else {
                        None
                    };
                    exact.push(dim);
                    None
                }
                None if exact.is_empty() => Some(dim),
                None => {
                    let value = first
                        .take()
                        .map_or_else(|| integer_product(py, &exact), |value| Ok(value.unbind()))?;
                    Some(value.bind(py).mul(&dim)?)
                }
            };
        }
        if machine_mode {
            let planned = match rank {
                2 => fixed_shape_size([machine_dims[0], machine_dims[1]]),
                3 => fixed_shape_size([machine_dims[0], machine_dims[1], machine_dims[2]]),
                4 => fixed_shape_size(machine_dims),
                _ => unreachable!(),
            };
            if let Ok(size) = planned {
                return Ok(size.into_pyobject(py)?.into_any().unbind());
            }
            return Ok(machine.into_pyobject(py)?.into_any().unbind());
        }
        return match accumulated {
            Some(value) => Ok(value.unbind()),
            None => integer_product(py, &exact),
        };
    }
    let dims = owner.getattr(pyo3::intern!(py, "dims"))?;
    if let Some(dims) = integer_tuple(&dims)
        && let Some(size) = tuple_dense_size(dims)
    {
        return Ok(size.into_pyobject(py)?.into_any().unbind());
    }
    // 非稠密整数沿用 Python 数值协议以恢复分配失败。 / Use Python numeric slots for non-dense integers to recover allocation failures.
    let mut accumulated = 1usize.into_pyobject(py)?.into_any();
    let mut previous = py.None().into_bound(py);
    let iterator = dims.try_iter()?;
    drop(dims);
    for dim in iterator {
        // for 的旧循环变量在取得下一项之后才释放。 / The old for-loop variable is released only after obtaining the next item.
        drop(std::mem::replace(&mut previous, dim?));
        // SAFETY: 两个附着解释器内的强引用，仅执行 CPython 数值协议；新引用交给 Bound。 / Two owned attached-interpreter references, CPython numeric protocol only; Bound owns the new reference.
        accumulated = unsafe {
            Bound::from_owned_ptr_or_err(
                py,
                pyo3::ffi::PyNumber_InPlaceMultiply(accumulated.as_ptr(), previous.as_ptr()),
            )?
        };
    }
    Ok(accumulated.unbind())
}

#[pyfunction]
#[pyo3(signature = (*, dims, storage_order, row_major))]
pub fn _shape_strides(
    py: Python<'_>,
    dims: &Bound<'_, PyAny>,
    storage_order: &Bound<'_, PyAny>,
    row_major: &Bound<'_, PyAny>,
) -> PyResult<Py<PyAny>> {
    let rank = dims.len()?;
    if rank == 0 {
        return Ok(PyTuple::empty(py).into_any().unbind());
    }
    let column_major = !storage_order
        .rich_compare(row_major, CompareOp::Eq)?
        .is_truthy()?;
    if let Some(dims) = integer_tuple(dims) {
        if let Some(strides) = tuple_dense_strides(py, dims, column_major)? {
            return Ok(strides);
        }
        let dims = dims.extract::<Vec<BigInt>>()?;
        let mut strides = vec![BigInt::from(1); rank];
        if column_major {
            for axis in 1..rank {
                strides[axis] = &strides[axis - 1] * &dims[axis - 1];
            }
        } else {
            for axis in (0..rank - 1).rev() {
                strides[axis] = &strides[axis + 1] * &dims[axis + 1];
            }
        }
        return Ok(PyTuple::new(py, strides)?.into_any().unbind());
    }
    // 自定义数值/序列保留原乘法顺序，未使用的端轴不读取。 / Preserve custom numeric/sequence multiplication order; do not read the unused end axis.
    let strides = PyList::new(py, std::iter::repeat_n(0, rank))?;
    strides.set_item(if column_major { 0 } else { rank - 1 }, 1)?;
    if column_major {
        for axis in 1..rank {
            let value = strides.get_item(axis - 1)?.mul(dims.get_item(axis - 1)?)?;
            strides.set_item(axis, value)?;
        }
    } else {
        for axis in (0..rank - 1).rev() {
            let value = strides.get_item(axis + 1)?.mul(dims.get_item(axis + 1)?)?;
            strides.set_item(axis, value)?;
        }
    }
    Ok(PyTuple::new(py, strides.iter())?.into_any().unbind())
}

fn generator_error(py: Python<'_>, error: PyErr) -> PyErr {
    if error.is_instance_of::<PyStopIteration>(py) {
        let converted = PyRuntimeError::new_err(
            "生成器内部抛出 StopIteration / generator raised StopIteration",
        );
        if let Err(context_error) = converted.value(py).setattr("__context__", error.value(py)) {
            return context_error;
        }
        converted.set_cause(py, Some(error));
        converted
    } else {
        error
    }
}

struct TermsState {
    iterator: Option<Py<PyIterator>>,
    left: Option<Py<PyAny>>,
    right: Option<Py<PyAny>>,
    busy: bool,
}

#[pyclass(frozen, module = "ospf_python._native")]
struct ShapeTerms {
    state: Mutex<TermsState>,
}

impl ShapeTerms {
    fn finish(&self, result: PyResult<Option<Py<PyAny>>>) -> PyResult<Option<Py<PyAny>>> {
        let released = {
            let mut state = self.state.lock().unwrap_or_else(|error| error.into_inner());
            state.busy = false;
            if matches!(&result, Ok(Some(_))) {
                (None, None, None)
            } else {
                (state.iterator.take(), state.left.take(), state.right.take())
            }
        };
        // 先销毁 for 迭代器，再按局部变量顺序释放；析构不持锁。 / Release the for iterator before local operands, with no lock during destruction.
        drop(released);
        result
    }
}

#[pymethods]
impl ShapeTerms {
    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__(&self, py: Python<'_>) -> PyResult<Option<Py<PyAny>>> {
        let iterator = {
            let mut state = self.state.lock().unwrap_or_else(|error| error.into_inner());
            if state.busy {
                return Err(PyValueError::new_err(
                    "生成器正在执行 / generator already executing",
                ));
            }
            let Some(iterator) = &state.iterator else {
                return Ok(None);
            };
            let iterator = iterator.clone_ref(py);
            state.busy = true;
            iterator
        };
        let pair = iterator.bind(py).clone().next();
        drop(iterator);
        let result = (|| {
            let Some(pair) = pair else { return Ok(None) };
            let pair = pair?;
            let (left, right) = pair.extract::<(Py<PyAny>, Py<PyAny>)>()?;
            drop(pair);
            // 保留上一组 s/i 到新 pair 完成，再按 UNPACK/STORE 顺序替换。 / Retain old s/i until the next pair is complete, then replace in UNPACK/STORE order.
            let old_left = {
                let mut state = self.state.lock().unwrap_or_else(|error| error.into_inner());
                state.left.replace(left.clone_ref(py))
            };
            drop(old_left);
            let old_right = {
                let mut state = self.state.lock().unwrap_or_else(|error| error.into_inner());
                state.right.replace(right.clone_ref(py))
            };
            drop(old_right);
            let value = left.bind(py).mul(right.bind(py)).map(Bound::unbind);
            drop(left);
            drop(right);
            value.map(Some)
        })();
        self.finish(result.map_err(|error| generator_error(py, error)))
    }

    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        let state = self.state.lock().unwrap_or_else(|error| error.into_inner());
        visit.call(&state.iterator)?;
        visit.call(&state.left)?;
        visit.call(&state.right)
    }

    fn __clear__(&self) {
        let released = {
            let mut state = self.state.lock().unwrap_or_else(|error| error.into_inner());
            (state.iterator.take(), state.left.take(), state.right.take())
        };
        drop(released);
    }
}

#[pyfunction]
#[pyo3(signature = (*, dims, strides, indices))]
pub fn _shape_flat_index(
    py: Python<'_>,
    dims: &Bound<'_, PyAny>,
    strides: &Bound<'_, PyAny>,
    indices: &Bound<'_, PyAny>,
) -> PyResult<Py<PyAny>> {
    if let (Some(strides), Some(indices)) = (integer_tuple(strides), integer_tuple(indices)) {
        if let Some(dims) = integer_tuple(dims)
            && strides.len() == dims.len()
            && indices.len() == dims.len()
        {
            // 单位轴可能让行布局首步长也为1，末轴及末步长可消歧。 / Unit axes can also give row-major a first stride of one; the last dimension and stride disambiguate.
            let column_major = strides.len() > 1
                && strides.get_item(0)?.extract::<usize>().ok() == Some(1)
                && (strides.get_item(strides.len() - 1)?.extract::<usize>().ok() != Some(1)
                    || dims.get_item(dims.len() - 1)?.extract::<usize>().ok() != Some(1));
            if let Some(index) = tuple_dense_index(dims, strides, indices, column_major)? {
                // SAFETY: 受检机器整数构造新引用，分配失败保留 Python 异常。 / A checked machine integer creates an owned reference; retain Python allocation errors.
                return unsafe {
                    Ok(Bound::from_owned_ptr_or_err(
                        py,
                        pyo3::ffi::PyLong_FromUnsignedLongLong(index as u64),
                    )?
                    .unbind())
                };
            }
        }
        if let Some(value) = tuple_bounded_index(strides, indices)? {
            let bytes = value.to_le_bytes();
            // SAFETY: 完整初始化的二补码仅在持有 GIL 的调用中读取，输出拥有引用。 / Fully initialized two's-complement bytes are read only during the GIL-held call; the result is owned.
            return unsafe {
                Ok(Bound::from_owned_ptr_or_err(
                    py,
                    pyo3::ffi::PyLong_FromNativeBytes(
                        bytes.as_ptr().cast(),
                        bytes.len(),
                        pyo3::ffi::Py_ASNATIVEBYTES_LITTLE_ENDIAN,
                    ),
                )?
                .unbind())
            };
        }
        // shortcut: BigInt 运算和转换仍可能因分配失败终止，待上游支持可恢复分配后替换。 / BigInt operations and conversions may still abort on OOM; replace when upstream allocation is recoverable.
        let mut value = BigInt::ZERO;
        for (stride, index) in strides.iter().zip(indices.iter()) {
            value += stride.extract::<BigInt>()? * index.extract::<BigInt>()?;
        }
        return Ok(value.into_pyobject(py)?.into_any().unbind());
    }
    let builtins = py.import("builtins")?;
    let sum = builtins.getattr("sum")?;
    let kwargs = PyDict::new(py);
    kwargs.set_item("strict", false)?;
    let pairs = builtins
        .getattr("zip")?
        .call((strides, indices), Some(&kwargs))?
        .cast_into::<PyIterator>()?;
    let products = Py::new(
        py,
        ShapeTerms {
            state: Mutex::new(TermsState {
                iterator: Some(pairs.unbind()),
                left: None,
                right: None,
                busy: false,
            }),
        },
    )?;
    // sum 保持 CPython 的补偿浮点算法，不以普通 Rust/Python 加法替代。 / Keep CPython sum's compensated floating algorithm, not ordinary Rust/Python addition.
    Ok(sum.call1((products,))?.unbind())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::shape_metadata::{upstream_index_count, upstream_shape_count};

    #[test]
    fn dense_fixed_size_uses_upstream_shape() {
        Python::initialize();
        Python::attach(|py| {
            let owner = py
                .import("types")
                .unwrap()
                .getattr("SimpleNamespace")
                .unwrap()
                .call0()
                .unwrap();
            for (axis, value) in [2usize, 3, 4, 5].into_iter().enumerate() {
                owner.setattr(format!("d{axis}"), value).unwrap();
            }
            for (rank, expected) in [(2, 6), (3, 24), (4, 120)] {
                let before = upstream_shape_count();
                let actual = _shape_size(py, &owner, Some(rank)).unwrap();
                assert_eq!(actual.extract::<usize>(py).unwrap(), expected);
                assert_eq!(upstream_shape_count(), before + 1);
            }
            for value in [0i128, -1, isize::MAX as i128, isize::MAX as i128 + 1] {
                owner.setattr("d0", value).unwrap();
                let before = upstream_shape_count();
                let actual = _shape_size(py, &owner, Some(2)).unwrap();
                assert_eq!(actual.extract::<i128>(py).unwrap(), value * 3);
                assert_eq!(upstream_shape_count(), before);
            }
        });
    }

    #[test]
    fn dense_dynamic_size_uses_upstream_shape_but_sparse_size_does_not() {
        Python::initialize();
        Python::attach(|py| {
            let owner = py
                .import("types")
                .unwrap()
                .getattr("SimpleNamespace")
                .unwrap()
                .call0()
                .unwrap();
            for (dims, expected) in [(vec![], 1), (vec![7], 7), (vec![2, 3, 4], 24)] {
                owner
                    .setattr("dims", PyTuple::new(py, dims).unwrap())
                    .unwrap();
                let before = upstream_shape_count();
                let actual = _shape_size(py, &owner, None).unwrap();
                assert_eq!(actual.extract::<usize>(py).unwrap(), expected);
                assert_eq!(upstream_shape_count(), before + 1);
            }
            owner
                .setattr("dims", PyTuple::new(py, [2, 3, 1, 2, 1, 5, 1, 7]).unwrap())
                .unwrap();
            let before = upstream_shape_count();
            let actual = _shape_size(py, &owner, None).unwrap();
            assert_eq!(actual.extract::<usize>(py).unwrap(), 420);
            assert_eq!(upstream_shape_count(), before + 3);
            for dims in [
                vec![0i128, 3],
                vec![-1, 3],
                vec![isize::MAX as i128, 2],
                vec![1, 1, 1, 1, 1, 0],
            ] {
                owner
                    .setattr("dims", PyTuple::new(py, &dims).unwrap())
                    .unwrap();
                let before = upstream_shape_count();
                let actual = _shape_size(py, &owner, None).unwrap();
                assert_eq!(
                    actual.extract::<i128>(py).unwrap(),
                    dims.iter().product::<i128>()
                );
                assert_eq!(upstream_shape_count(), before);
            }
        });
    }

    #[test]
    fn dense_dynamic_strides_compose_upstream_fixed_shapes() {
        Python::initialize();
        Python::attach(|py| {
            let dims = PyTuple::new(py, [2usize, 1, 3, 1, 5, 1, 7, 1, 11]).unwrap();
            let row = pyo3::types::PyString::new(py, "row");
            for (order, expected) in [
                ("row", [1155, 1155, 385, 385, 77, 77, 11, 11, 1]),
                ("column", [1, 2, 2, 6, 6, 30, 30, 210, 210]),
            ] {
                let order = pyo3::types::PyString::new(py, order);
                let before = upstream_shape_count();
                let actual = _shape_strides(py, dims.as_any(), order.as_any(), row.as_any())
                    .unwrap()
                    .extract::<Vec<usize>>(py)
                    .unwrap();
                assert_eq!(actual, expected);
                assert_eq!(upstream_shape_count(), before + 3);
            }
        });
    }

    #[test]
    fn dense_dynamic_index_composes_upstream_fixed_shapes() {
        Python::initialize();
        Python::attach(|py| {
            let dims = PyTuple::new(py, [2usize, 1, 3, 1, 5, 1, 7, 1, 11]).unwrap();
            let indices = PyTuple::new(py, [1usize, 0, 2, 0, 4, 0, 6, 0, 10]).unwrap();
            for strides in [
                [1155usize, 1155, 385, 385, 77, 77, 11, 11, 1],
                [1usize, 2, 2, 6, 6, 30, 30, 210, 210],
            ] {
                let strides = PyTuple::new(py, strides).unwrap();
                let before = upstream_index_count();
                let actual =
                    _shape_flat_index(py, dims.as_any(), strides.as_any(), indices.as_any())
                        .unwrap();
                assert_eq!(actual.extract::<usize>(py).unwrap(), 2309);
                assert_eq!(upstream_index_count(), before + 3);
            }
            let empty = PyTuple::empty(py);
            let before = upstream_index_count();
            let actual =
                _shape_flat_index(py, empty.as_any(), empty.as_any(), empty.as_any()).unwrap();
            assert_eq!(actual.extract::<usize>(py).unwrap(), 0);
            assert_eq!(upstream_index_count(), before + 1);
        });
    }

    #[test]
    fn dense_guard_precedes_upstream_and_keeps_layout() {
        let dims = [2.into(), 3.into(), 4.into()];
        for (column, expected) in [(false, [12, 4, 1]), (true, [1, 2, 6])] {
            let shape = dense_shape(&dims, column).unwrap();
            assert_eq!(shape.len(), 24);
            for (axis, offset) in expected.into_iter().enumerate() {
                assert_eq!(shape.offsets()[axis], offset);
            }
            assert_eq!(shape.index_of(&vec![1, 2, 3]).unwrap(), 23);
        }
        assert!(dense_shape(&[0.into(), 3.into()], false).is_none());
        assert!(dense_shape(&[(-1).into()], false).is_none());
        assert!(dense_shape(&[BigInt::from(1) << 200], false).is_none());
        assert!(dense_shape(&[isize::MAX.into(), 2.into()], false).is_none());
        assert_eq!(dense_shape(&[], false).unwrap().len(), 1);
    }

    #[test]
    fn sparse_product_is_exact_without_a_dense_allocation() {
        Python::initialize();
        Python::attach(|py| {
            let big: BigInt = BigInt::from(1) << 200;
            let value = product(py, &[big.clone(), 3.into(), 5.into()]).unwrap();
            assert_eq!(value.extract::<BigInt>(py).unwrap(), big * 15);
        });
    }

    #[test]
    fn dynamic_product_preserves_unbounded_integers() {
        Python::initialize();
        Python::attach(|py| {
            let owner = py
                .import("types")
                .unwrap()
                .getattr("SimpleNamespace")
                .unwrap()
                .call0()
                .unwrap();
            let machine = PyTuple::new(py, [2usize, 3, 4]).unwrap();
            owner.setattr("dims", machine).unwrap();
            assert_eq!(
                _shape_size(py, &owner, None)
                    .unwrap()
                    .extract::<usize>(py)
                    .unwrap(),
                24
            );

            let big: BigInt = BigInt::from(1) << 200;
            let sparse = PyTuple::new(
                py,
                [
                    big.clone().into_pyobject(py).unwrap().into_any(),
                    BigInt::from(3).into_pyobject(py).unwrap().into_any(),
                ],
            )
            .unwrap();
            owner.setattr("dims", sparse).unwrap();
            assert_eq!(
                _shape_size(py, &owner, None)
                    .unwrap()
                    .extract::<BigInt>(py)
                    .unwrap(),
                big * 3
            );

            let boundary = PyTuple::new(py, [isize::MAX as usize, 2]).unwrap();
            owner.setattr("dims", boundary).unwrap();
            assert_eq!(
                _shape_size(py, &owner, None)
                    .unwrap()
                    .extract::<BigInt>(py)
                    .unwrap(),
                BigInt::from(isize::MAX) * 2
            );
        });
    }
}
