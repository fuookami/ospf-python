//! 公共 view 的复制协议和受检区域发布。 / Public view copy protocols and checked region publication.

use num_bigint::BigInt;
use numpy::npyffi::{_PyArray_GET_ITEM_DATA, NPY_ORDER, PY_ARRAY_API, PyArray_Dims};
use numpy::{PyArrayDescrMethods, PyUntypedArray, PyUntypedArrayMethods};
use pyo3::class::gc::{PyTraverseError, PyVisit};
use pyo3::prelude::*;
use pyo3::types::{PyBool, PyDict, PyInt, PyTuple};

use crate::failure::{Failure, ResultPublication, Transport, transport};
use crate::multiarray::{ViewCopyDescriptor, ViewCopyPlan, copy_storage};

fn append_integer(
    value: &Bound<'_, PyAny>,
    dimensions: bool,
    size: &mut usize,
    output: Option<&mut Vec<usize>>,
) -> PyResult<Option<Failure>> {
    let py = value.py();
    if value.is_instance_of::<PyBool>() {
        return Ok(Some(Failure::input(
            "视图元数据不能是 bool / View metadata must not be bool",
        )));
    }
    let integer = if value.is_exact_instance_of::<PyInt>() {
        match value.extract::<usize>() {
            Ok(integer) => integer,
            Err(_) => return Ok(Some(integer_failure(value, dimensions)?)),
        }
    } else {
        // SAFETY: 标准整数协议返回拥有的 Python 整数引用。 / The standard integer protocol returns an owned Python integer reference.
        let indexed =
            unsafe { Bound::from_owned_ptr_or_err(py, pyo3::ffi::PyNumber_Index(value.as_ptr())) }?;
        match indexed.extract::<usize>() {
            Ok(integer) => integer,
            Err(_) => return Ok(Some(integer_failure(&indexed, dimensions)?)),
        }
    };
    if dimensions {
        if integer == 0 {
            return Ok(Some(Failure::input(
                "视图源维度必须为正 / View source dimensions must be positive",
            )));
        }
        let next = size.checked_mul(integer);
        let Some(next) = next.filter(|next| *next <= isize::MAX as usize) else {
            return Ok(Some(Failure::binding(
                "OVERFLOW",
                "视图源大小超出原生容量 / View source size exceeds native capacity",
            )));
        };
        *size = next;
    }
    if let Some(output) = output {
        output.push(integer);
    }
    Ok(None)
}

fn integer_failure(value: &Bound<'_, PyAny>, dimensions: bool) -> PyResult<Failure> {
    Ok(if !dimensions {
        Failure::binding(
            "OUT_OF_RANGE",
            "视图偏移超出范围 / View offset is out of range",
        )
    } else if value.extract::<BigInt>()? <= BigInt::from(0) {
        Failure::input("视图源维度必须为正 / View source dimensions must be positive")
    } else {
        Failure::binding(
            "OVERFLOW",
            "视图源大小超出原生容量 / View source size exceeds native capacity",
        )
    })
}

fn integers(input: &Bound<'_, PyAny>, dimensions: bool) -> PyResult<Transport<Vec<usize>>> {
    let mut output = Vec::new();
    let mut size = 1usize;
    if input.is_exact_instance_of::<PyTuple>() {
        for value in input.cast::<PyTuple>()?.iter() {
            if let Some(error) = append_integer(&value, dimensions, &mut size, Some(&mut output))? {
                return Ok(transport(Err(error)));
            }
        }
    } else {
        for value in input.try_iter()? {
            if let Some(error) = append_integer(&value?, dimensions, &mut size, Some(&mut output))?
            {
                return Ok(transport(Err(error)));
            }
        }
    }
    Ok(transport(Ok(output)))
}

fn call_two<'py>(
    callable: &Bound<'py, PyAny>,
    left: &Bound<'py, PyAny>,
    right: &Bound<'py, PyAny>,
) -> PyResult<Bound<'py, PyAny>> {
    let args = [left.as_ptr(), right.as_ptr()];
    // SAFETY: Both arguments are live borrowed references; Vectorcall owns the returned reference and reports Python errors normally.
    unsafe {
        Bound::from_owned_ptr_or_err(
            callable.py(),
            pyo3::ffi::PyObject_Vectorcall(
                callable.as_ptr(),
                args.as_ptr(),
                2,
                std::ptr::null_mut(),
            ),
        )
    }
}

fn exact_zero_pair(value: &Bound<'_, PyAny>) -> PyResult<bool> {
    if !value.is_exact_instance_of::<PyTuple>() {
        return Ok(false);
    }
    let tuple = value.cast::<PyTuple>()?;
    if tuple.len() != 2 {
        return Ok(false);
    }
    for item in tuple.iter() {
        if !item.is_exact_instance_of::<PyInt>() || item.extract::<usize>().ok() != Some(0) {
            return Ok(false);
        }
    }
    Ok(true)
}

fn copy_standard_region<'py>(
    array: &Bound<'py, PyUntypedArray>,
    descriptor: &ViewCopyDescriptor,
) -> PyResult<Option<Bound<'py, PyAny>>> {
    let py = array.py();
    let mut output_dims = array
        .shape()
        .iter()
        .map(|dim| *dim as isize)
        .collect::<Vec<_>>();
    output_dims[0] = descriptor.size as isize;
    let dtype = array.dtype();
    if array.shape().contains(&0) || dtype.itemsize() == 0 {
        // SAFETY: NumPy 自行分配空载荷/零字节 dtype，维度来自受检 Rust 区域和真实存储轴。
        // NumPy allocates the empty/zero-byte payload itself; dimensions come from the checked Rust region and actual storage axes.
        return unsafe {
            Bound::from_owned_ptr_or_err(
                py,
                PY_ARRAY_API.PyArray_NewFromDescr(
                    py,
                    numpy::npyffi::get_type_object(py, numpy::npyffi::NpyTypes::PyArray_Type),
                    dtype.into_dtype_ptr(),
                    output_dims.len() as i32,
                    output_dims.as_mut_ptr(),
                    std::ptr::null_mut(),
                    std::ptr::null_mut(),
                    0,
                    std::ptr::null_mut(),
                ),
            )
            .map(Some)
        };
    }
    if descriptor.dims.len() + array.ndim() - 1 > 64 {
        return Ok(None);
    }
    let Some(start) = (descriptor.start as isize).checked_mul(array.strides()[0]) else {
        return Ok(None);
    };
    let mut dims = descriptor
        .dims
        .iter()
        .map(|dim| *dim as isize)
        .collect::<Vec<_>>();
    dims.extend_from_slice(&output_dims[1..]);
    let strides = descriptor
        .strides
        .iter()
        .map(|stride| (*stride as isize).checked_mul(array.strides()[0]))
        .collect::<Option<Vec<_>>>();
    let Some(mut strides) = strides else {
        return Ok(None);
    };
    strides.extend_from_slice(&array.strides()[1..]);
    // SAFETY: 不解引用或写入元素指针。受检区域提供槽起点/维度/步长，真实 ndarray 提供字节步长。
    // Only transfer a storage pointer to NumPy, never dereference/write leaves: checked Rust supplies slot start/dims/strides and the actual ndarray supplies byte strides.
    // array 强引用与 view.base 在整个 dtype 感知复制期间保活源；NewFromDescr 接管 dtype 引用。
    // The strong array reference and view.base retain storage throughout dtype-aware copying; NewFromDescr steals the descriptor reference.
    let view = unsafe {
        let data = (*_PyArray_GET_ITEM_DATA(array.as_array_ptr()))
            .data
            .wrapping_offset(start);
        Bound::from_owned_ptr_or_err(
            py,
            PY_ARRAY_API.PyArray_NewFromDescr(
                py,
                numpy::npyffi::get_type_object(py, numpy::npyffi::NpyTypes::PyArray_Type),
                dtype.into_dtype_ptr(),
                dims.len() as i32,
                dims.as_mut_ptr(),
                strides.as_mut_ptr(),
                data.cast(),
                0,
                std::ptr::null_mut(),
            ),
        )?
        .cast_into::<PyUntypedArray>()?
    };
    // SAFETY: NumPy 接管新增的 base 强引用，临时 view 不拥有借用的数据。 / NumPy steals the new base reference; the temporary view never owns borrowed data.
    if unsafe {
        PY_ARRAY_API.PyArray_SetBaseObject(py, view.as_array_ptr(), array.clone().into_ptr())
    } < 0
    {
        return Err(PyErr::fetch(py));
    }
    // SAFETY: view/base 均保活；所有复制、对象增减引用及 dtype 处理由 NumPy 自己完成。
    // Both view and base are alive; NumPy alone copies storage, maintains object references and handles dtype protocols.
    let output = unsafe {
        Bound::from_owned_ptr_or_err(
            py,
            PY_ARRAY_API.PyArray_NewCopy(py, view.as_array_ptr(), NPY_ORDER::NPY_CORDER),
        )?
        .cast_into::<PyUntypedArray>()?
    };
    if output
        .shape()
        .iter()
        .map(|dim| *dim as isize)
        .ne(output_dims.iter().copied())
    {
        let mut shape = PyArray_Dims {
            ptr: output_dims.as_mut_ptr(),
            len: output_dims.len() as i32,
        };
        // SAFETY: 仅调整本次新建未发布 C-order 副本的 header，元素数量不变，不持有 Rust 数据借用。
        // Only adjust the fresh unpublished C-order copy's header, with unchanged element count and no Rust data borrow.
        unsafe {
            Bound::from_owned_ptr_or_err(
                py,
                PY_ARRAY_API.PyArray_Resize(
                    py,
                    output.as_array_ptr(),
                    &mut shape,
                    0,
                    NPY_ORDER::NPY_CORDER,
                ),
            )?;
        }
    }
    Ok(Some(output.into_any()))
}

#[pyfunction]
#[pyo3(signature = (*, owner, shape_types, row_major, column_major, make_shape, resolve))]
pub fn _materialize_shared_view(
    py: Python<'_>,
    owner: &Bound<'_, PyAny>,
    shape_types: &Bound<'_, PyTuple>,
    row_major: &Bound<'_, PyAny>,
    column_major: &Bound<'_, PyAny>,
    make_shape: &Bound<'_, PyAny>,
    resolve: &Bound<'_, PyAny>,
) -> PyResult<Transport<Py<PyAny>>> {
    // 与旧表达式一致：复制完成后捕获构造器，再读取当前 source.shape。
    // Match the legacy expression: finish copying, capture the constructor, then read current source.shape.
    let copied = copy_storage(
        &owner
            .getattr(pyo3::intern!(py, "_source"))?
            .getattr(pyo3::intern!(py, "_data"))?,
    )?;
    let constructor = resolve.call0()?;
    let source = owner.getattr(pyo3::intern!(py, "_source"))?;
    let shape = source.getattr(pyo3::intern!(py, "shape"))?;
    // Shape2 的零偏移区域只需验证两个字段、布局和偏移，避免构造通用 dims/offset 向量。
    // A Shape2 identity region needs only its two fields, layout and offsets; avoid the generic dims/offset vectors.
    let shape2 = shape_types.len() > 1 && shape.get_type().is(&shape_types.get_item(1)?);
    let fast_offsets = if shape2 {
        Some(owner.getattr(pyo3::intern!(py, "_offsets"))?)
    } else {
        None
    };
    if let Some(offsets) = fast_offsets.as_ref()
        && exact_zero_pair(offsets)?
    {
        let mut size = 1usize;
        let d0 = shape.getattr(pyo3::intern!(py, "d0"))?;
        let d1 = shape.getattr(pyo3::intern!(py, "d1"))?;
        for value in [&d0, &d1] {
            if let Some(error) = append_integer(value, true, &mut size, None)? {
                return Ok(transport(Err(error)));
            }
        }
        let order = shape.getattr(pyo3::intern!(py, "storage_order"))?;
        if !order.is(row_major) && !order.is(column_major) {
            return Ok(transport(Err(Failure::input(
                "视图存储顺序无效 / Invalid view storage order",
            ))));
        }
        return Ok(transport(Ok(
            call_two(&constructor, &shape, &copied)?.unbind()
        )));
    }
    let (dims, error) = integers(&shape.getattr(pyo3::intern!(py, "dims"))?, true)?;
    if let Some(error) = error {
        return Ok(transport(Err(error)));
    }
    let order = shape.getattr(pyo3::intern!(py, "storage_order"))?;
    let column = if order.is(row_major) {
        false
    } else if order.is(column_major) {
        true
    } else {
        return Ok(transport(Err(Failure::input(
            "视图存储顺序无效 / Invalid view storage order",
        ))));
    };
    let offsets = match fast_offsets {
        Some(offsets) => offsets,
        None => owner.getattr(pyo3::intern!(py, "_offsets"))?,
    };
    if !offsets.is_exact_instance_of::<PyTuple>() {
        return Ok(transport(Err(Failure::input(
            "视图偏移必须为整数 tuple / View offsets must be an integer tuple",
        ))));
    }
    let (offsets, error) = integers(&offsets, false)?;
    if let Some(error) = error {
        return Ok(transport(Err(error)));
    }
    let dims = dims.unwrap();
    let offsets = offsets.unwrap();
    // 元数据已逐项检查；恒等区域不需要分配未使用的稠密形状/步长。
    // Metadata is already checked item by item; identity regions need no unused dense shapes or strides.
    if dims.len() == offsets.len() && offsets.iter().all(|offset| *offset == 0) {
        return Ok(transport(Ok(
            call_two(&constructor, &shape, &copied)?.unbind()
        )));
    }
    let plan = match ViewCopyPlan::from_dense(dims, offsets, column) {
        Ok(plan) => plan,
        Err(error) => return Ok(transport(Err(error))),
    };
    debug_assert!(!plan.identity());
    if copied.len()? != plan.source_size() {
        return Ok(transport(Err(Failure::input(
            "复制存储第一轴与源形状不匹配 / Copied storage axis zero does not match the source shape",
        ))));
    }
    let indexer = if shape_types.iter().any(|kind| shape.get_type().is(&kind)) {
        None
    } else {
        Some(shape.getattr(pyo3::intern!(py, "flat_index"))?)
    };
    let mut result_shape = None;
    if indexer.is_none() && copied.is_exact_instance_of::<PyUntypedArray>() {
        let descriptor = match plan.descriptor() {
            Ok(descriptor) => descriptor,
            Err(error) => return Ok(transport(Err(error))),
        };
        result_shape = Some(call_two(
            make_shape,
            PyTuple::new(py, plan.dims())?.as_any(),
            &order,
        )?);
        py.check_signals()?;
        let array = copied.cast::<PyUntypedArray>()?;
        // 工厂和 signal handler 均可改变外部 copy 返回的存储；交付描述符前重新检查。
        // Factories and signal handlers can mutate externally returned copy storage; recheck before handing off its descriptor.
        if array.shape().first().copied() != Some(plan.source_size()) {
            return Ok(transport(Err(Failure::input(
                "形状工厂使复制存储失效 / Shape factory invalidated copied storage",
            ))));
        }
        if let Some(selected) = copy_standard_region(array, &descriptor)? {
            return Ok(transport(Ok(call_two(
                &constructor,
                &result_shape.unwrap(),
                &selected,
            )?
            .unbind())));
        }
    }
    let (indices, error) = plan.gather(py, indexer.as_ref())?;
    if let Some(error) = error {
        return Ok(transport(Err(error)));
    }
    let result_shape = match result_shape {
        Some(shape) => shape,
        None => call_two(make_shape, PyTuple::new(py, plan.dims())?.as_any(), &order)?,
    };
    let kwargs = PyDict::new(py);
    kwargs.set_item("axis", 0)?;
    // 目标坐标/排列已由固定 Rust 决定；take 仅是保留 dtype/附加轴的外部存储协议。
    // Pinned Rust already determines target coordinates/order; take only adapts external storage, preserving dtype/trailing axes.
    let selected = copied.call_method(
        pyo3::intern!(py, "take"),
        (indices.unwrap(),),
        Some(&kwargs),
    )?;
    Ok(transport(Ok(call_two(
        &constructor,
        &result_shape,
        &selected,
    )?
    .unbind())))
}

/// 只持协议类型、顺序常量和 Result 工厂；不缓存 owner/shape/叶。 / Retain only protocol types, order constants and Result factories, never owners, shapes or leaves.
#[pyclass(name = "_SharedView", frozen, weakref, module = "ospf_python._native")]
pub struct SharedView {
    shape_types: Py<PyTuple>,
    row_major: Py<PyAny>,
    column_major: Py<PyAny>,
    publication: ResultPublication,
}

#[pymethods]
impl SharedView {
    #[new]
    #[pyo3(signature = (*, shape_types, row_major, column_major, success, failure))]
    fn new(
        shape_types: Py<PyTuple>,
        row_major: Py<PyAny>,
        column_major: Py<PyAny>,
        success: Py<PyAny>,
        failure: Py<PyAny>,
    ) -> Self {
        Self {
            shape_types,
            row_major,
            column_major,
            publication: ResultPublication::new(
                success,
                failure,
                "缺少普通视图物化结果 / Missing plain view materialization result",
            ),
        }
    }

    #[pyo3(signature = (owner, make_shape, resolve))]
    fn materialize(
        &self,
        py: Python<'_>,
        owner: &Bound<'_, PyAny>,
        make_shape: &Bound<'_, PyAny>,
        resolve: &Bound<'_, PyAny>,
    ) -> PyResult<Py<PyAny>> {
        let payload = _materialize_shared_view(
            py,
            owner,
            self.shape_types.bind(py),
            self.row_major.bind(py),
            self.column_major.bind(py),
            make_shape,
            resolve,
        )?;
        self.publication.publish(py, payload)
    }

    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        visit.call(&self.shape_types)?;
        visit.call(&self.row_major)?;
        visit.call(&self.column_major)?;
        self.publication.traverse(visit)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use pyo3::types::PyDict;

    #[test]
    fn checked_suffix_uses_pinned_source_and_target_layouts() {
        Python::initialize();
        Python::attach(|py| {
            for (column, expected) in [
                (false, vec![5, 6, 7, 9, 10, 11]),
                (true, vec![4, 5, 7, 8, 10, 11]),
            ] {
                let plan = ViewCopyPlan::create(
                    vec![3.into(), 4.into()],
                    vec![1.into(), 1.into()],
                    column,
                )
                .unwrap();
                assert_eq!(plan.dims(), [2, 3]);
                assert_eq!(plan.source_size(), 12);
                assert!(!plan.identity());
                assert_eq!(plan.gather(py, None).unwrap().0.unwrap(), expected);
            }
        });
    }

    #[test]
    fn custom_indices_preserve_negative_normalization_and_read_aliases() {
        Python::initialize();
        Python::attach(|py| {
            let scope = PyDict::new(py);
            py.run(
                c"negative = lambda i,j: -1-(i*4+j)\nalias = lambda i,j: 0",
                Some(&scope),
                None,
            )
            .unwrap();
            let plan =
                ViewCopyPlan::create(vec![3.into(), 4.into()], vec![1.into(), 1.into()], false)
                    .unwrap();
            assert_eq!(
                plan.gather(py, scope.get_item("negative").unwrap().as_ref())
                    .unwrap()
                    .0
                    .unwrap(),
                [6, 5, 4, 2, 1, 0]
            );
            assert_eq!(
                plan.gather(py, scope.get_item("alias").unwrap().as_ref())
                    .unwrap()
                    .0
                    .unwrap(),
                [0; 6]
            );
        });
    }

    #[test]
    fn descriptor_storage_order_matches_every_checked_region_coordinate() {
        use ospf_rust_multiarray::{DynShape, ShapeAccessOrderExt};

        Python::initialize();
        Python::attach(|py| {
            for column in [false, true] {
                for dims in [vec![], vec![3], vec![2, 3], vec![2, 1, 3], vec![2, 3, 1, 2]] {
                    let source: DynShape = DynShape::new(dims.clone());
                    for offsets in source.indices() {
                        let plan = ViewCopyPlan::from_dense(dims.clone(), offsets, column).unwrap();
                        let descriptor = plan.descriptor().unwrap();
                        let expected = plan.gather(py, None).unwrap().0.unwrap();
                        let descriptor_shape: DynShape = DynShape::new(descriptor.dims);
                        let actual = descriptor_shape
                            .indices()
                            .map(|indices| {
                                descriptor.start
                                    + indices
                                        .iter()
                                        .zip(&descriptor.strides)
                                        .map(|(index, stride)| index * stride)
                                        .sum::<usize>()
                            })
                            .collect::<Vec<_>>();
                        assert_eq!(actual, expected);
                        assert_eq!(actual.len(), descriptor.size);
                    }
                }
            }
        });
    }

    #[test]
    fn integer_metadata_rejects_bool_overflow_and_negative_offsets() {
        Python::initialize();
        Python::attach(|py| {
            assert_eq!(
                integers(&PyTuple::new(py, [true]).unwrap(), true)
                    .unwrap()
                    .1
                    .unwrap()
                    .category,
                "ILLEGAL_ARGUMENT"
            );
            assert_eq!(
                integers(&PyTuple::new(py, [BigInt::from(1) << 100]).unwrap(), true)
                    .unwrap()
                    .1
                    .unwrap()
                    .category,
                "OVERFLOW"
            );
            assert_eq!(
                integers(&PyTuple::new(py, [-1]).unwrap(), false)
                    .unwrap()
                    .1
                    .unwrap()
                    .category,
                "OUT_OF_RANGE"
            );
        });
    }
}
