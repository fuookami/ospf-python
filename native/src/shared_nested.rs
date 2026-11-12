//! 共享缓冲的 dtype 转换与上游逻辑嵌套导出。 / Dtype conversion and upstream logical nested export from shared buffers.

use num_bigint::BigInt;
use num_traits::ToPrimitive;
use numpy::npyffi::{
    _PyArray_GET_ITEM_DATA, NPY_ARRAY_WRITEABLE, NPY_ORDER, PY_ARRAY_API, PyArray_Dims,
};
use numpy::{PyArrayDescrMethods, PyUntypedArray, PyUntypedArrayMethods};
use ospf_rust_multiarray::{AbstractShape, DynShape, ShapeAccessOrderExt};
use pyo3::class::gc::{PyTraverseError, PyVisit};
use pyo3::ffi;
use pyo3::prelude::*;
use pyo3::types::{PyBool, PyInt, PyList, PySlice, PyTuple};

use crate::failure::{Failure, ResultPublication, Transport, transport};
use crate::shape_metadata::{DenseShapeError, dense_shape};

fn raw_list<'py>(py: Python<'py>, len: usize) -> PyResult<Bound<'py, PyList>> {
    // SAFETY: PyList_New returns a new owned list with all slots initialized to NULL.
    // Each caller fills every slot before the list can be observed.
    unsafe {
        Bound::from_owned_ptr_or_err(py, ffi::PyList_New(len as isize))?
            .cast_into::<PyList>()
            .map_err(Into::into)
    }
}

fn set_raw_item(list: &Bound<'_, PyList>, index: usize, value: Bound<'_, PyAny>) {
    debug_assert!(index < list.len());
    // SAFETY: index is in the freshly allocated list; PyList_SET_ITEM steals the
    // owned reference and the list is not shared while it is being populated.
    unsafe {
        ffi::PyList_SET_ITEM(list.as_ptr(), index as isize, value.into_ptr());
    }
}

fn dense_shape_failure(error: DenseShapeError) -> Failure {
    match error {
        DenseShapeError::Dimension => Failure::input(
            "嵌套输出需要正整数维度 / Nested output requires positive integer dimensions",
        ),
        DenseShapeError::Size => Failure::binding(
            "OVERFLOW",
            "嵌套输出大小超出原生容量 / Nested output size exceeds native capacity",
        ),
    }
}

fn checked_fixed_dimension(value: &Bound<'_, PyAny>) -> PyResult<Result<Option<usize>, Failure>> {
    if value.is_instance_of::<PyBool>() {
        return Ok(Err(Failure::input(
            "维度不能是 bool / Dimensions must not be bool",
        )));
    }
    if value.is_exact_instance_of::<PyInt>() {
        return Ok(match value.extract::<usize>() {
            Ok(integer) => Ok(Some(integer)),
            Err(_) => Err(Failure::binding(
                "OVERFLOW",
                "维度超出原生容量 / Dimension exceeds native capacity",
            )),
        });
    }
    // SAFETY: 标准整数协议返回一个拥有的 Python 引用，不借用缓冲。 / The standard integer protocol returns an owned Python reference, without borrowing buffers.
    let indexed = unsafe {
        Bound::from_owned_ptr_or_err(value.py(), pyo3::ffi::PyNumber_Index(value.as_ptr()))
    }?;
    match indexed.extract::<usize>() {
        Ok(integer) => Ok(Ok(Some(integer))),
        Err(_) => {
            let integer = indexed.extract::<BigInt>()?;
            if integer > BigInt::from(0) && integer.to_usize().is_none() {
                Ok(Err(Failure::binding(
                    "OVERFLOW",
                    "维度超出原生容量 / Dimension exceeds native capacity",
                )))
            } else {
                Ok(Ok(integer.to_usize()))
            }
        }
    }
}

struct FixedPlan {
    rank: usize,
    dims: [usize; 4],
    len: usize,
}

impl FixedPlan {
    fn len(&self) -> usize {
        self.len
    }
}

fn fixed_nested_plan<const N: usize>(dims: &Bound<'_, PyTuple>) -> PyResult<Transport<FixedPlan>> {
    debug_assert_eq!(dims.len(), N);
    let mut values = [0usize; 4];
    let mut protocol_error = None;
    let mut dimension_failure = None;
    let mut size = 1usize;
    // 与通用路径相同，在首个容量/协议失败点停止并保留该失败；Python 协议错误优先。
    // Match the generic path by stopping at the first capacity/protocol failure and
    // retaining it, while Python protocol exceptions take precedence.
    for (axis, value) in dims.iter().enumerate() {
        match checked_fixed_dimension(&value) {
            Ok(Ok(Some(integer))) => {
                values[axis] = integer;
                if integer == 0 {
                    dimension_failure = Some(dense_shape_failure(DenseShapeError::Dimension));
                    break;
                }
                let Some(next) = size
                    .checked_mul(integer)
                    .filter(|next| *next <= isize::MAX as usize)
                else {
                    dimension_failure = Some(Failure::binding(
                        "OVERFLOW",
                        "嵌套输出大小超出原生容量 / Nested output size exceeds native capacity",
                    ));
                    break;
                };
                size = next;
            }
            Ok(Ok(None)) => {
                dimension_failure = Some(dense_shape_failure(DenseShapeError::Dimension));
                break;
            }
            Ok(Err(error)) => {
                dimension_failure = Some(error);
                break;
            }
            Err(error) => {
                protocol_error = Some(error);
                break;
            }
        }
    }
    if let Some(error) = protocol_error {
        return Err(error);
    }
    if let Some(error) = dimension_failure {
        return Ok(transport(Err(error)));
    }
    Ok(transport(Ok(FixedPlan {
        rank: N,
        dims: values,
        len: size,
    })))
}

fn dense_nested_plan(
    py: Python<'_>,
    dims: &Bound<'_, PyAny>,
    column_major: bool,
) -> PyResult<Transport<DynShape>> {
    let mut protocol_error = None;
    let mut dimension_failure = None;
    let dimensions = dims.try_iter()?.map(|value| {
        let parsed = (|| {
            let value = value?;
            if value.is_instance_of::<PyBool>() {
                dimension_failure = Some(Failure::input(
                    "维度不能是 bool / Dimensions must not be bool",
                ));
                return Ok(None);
            }
            if value.is_exact_instance_of::<PyInt>() {
                return match value.extract::<usize>() {
                    Ok(integer) => Ok(Some(integer)),
                    Err(_) => {
                        dimension_failure = Some(Failure::binding(
                            "OVERFLOW",
                            "维度超出原生容量 / Dimension exceeds native capacity",
                        ));
                        Ok(None)
                    }
                };
            }
            // SAFETY: 标准整数协议返回一个拥有的 Python 引用，不借用缓冲。 / The standard integer protocol returns an owned Python reference, without borrowing buffers.
            let integer = unsafe {
                Bound::from_owned_ptr_or_err(py, pyo3::ffi::PyNumber_Index(value.as_ptr()))
            }?;
            let integer = integer.extract::<BigInt>()?;
            if integer > BigInt::from(0) && integer.to_usize().is_none() {
                dimension_failure = Some(Failure::binding(
                    "OVERFLOW",
                    "维度超出原生容量 / Dimension exceeds native capacity",
                ));
            }
            Ok(integer.to_usize())
        })();
        match parsed {
            Ok(value) => value,
            Err(error) => {
                protocol_error = Some(error);
                None
            }
        }
    });
    let plan = dense_shape(dimensions, column_major);
    if let Some(error) = protocol_error {
        return Err(error);
    }
    if let Some(error) = dimension_failure {
        return Ok(transport(Err(error)));
    }
    Ok(transport(plan.map_err(dense_shape_failure)))
}

fn target_view_list<'py, S: AbstractShape>(
    py: Python<'py>,
    physical: &Bound<'py, PyUntypedArray>,
    plan: &S,
) -> PyResult<Transport<Bound<'py, PyList>>> {
    debug_assert!(plan.dimension() > 1 && plan.dimension() <= 64);
    let itemsize = physical.dtype().itemsize();
    let mut shape = [0isize; 64];
    let mut strides = [0isize; 64];
    for axis in 0..plan.dimension() {
        shape[axis] = match isize::try_from(plan.shape()[axis]) {
            Ok(value) => value,
            Err(_) => {
                return Ok(transport(Err(Failure::binding(
                    "OVERFLOW",
                    "嵌套输出维度超出 NumPy 容量 / Nested-output dimension exceeds NumPy capacity",
                ))));
            }
        };
        strides[axis] = match plan.offsets()[axis]
            .checked_mul(itemsize)
            .and_then(|value| isize::try_from(value).ok())
        {
            Some(value) => value,
            None => {
                return Ok(transport(Err(Failure::binding(
                    "OVERFLOW",
                    "嵌套输出视图超出 NumPy 容量 / Nested-output view exceeds NumPy capacity",
                ))));
            }
        };
    }
    // SAFETY: physical owns a live buffer; Pinned Shape checked the dense target
    // strides against that buffer's capacity. The base object keeps it alive.
    let data_ptr = unsafe { (*_PyArray_GET_ITEM_DATA(physical.as_array_ptr().cast_const())).data };
    let flags = unsafe { (*_PyArray_GET_ITEM_DATA(physical.as_array_ptr().cast_const())).flags }
        & NPY_ARRAY_WRITEABLE;
    // SAFETY: NumPy receives one checked shape/stride map over the live ravel buffer.
    let view = unsafe {
        Bound::from_owned_ptr_or_err(
            py,
            PY_ARRAY_API.PyArray_NewFromDescr(
                py,
                numpy::npyffi::get_type_object(py, numpy::npyffi::NpyTypes::PyArray_Type),
                physical.dtype().into_dtype_ptr(),
                plan.dimension() as i32,
                shape.as_mut_ptr(),
                strides.as_mut_ptr(),
                data_ptr.cast(),
                flags,
                std::ptr::null_mut(),
            ),
        )?
        .cast_into::<PyUntypedArray>()?
    };
    // SAFETY: PyArray_SetBaseObject steals the new strong reference and rejects
    // cycles; the view is unpublished and the base outlives PyArray_ToList.
    if unsafe {
        PY_ARRAY_API.PyArray_SetBaseObject(py, view.as_array_ptr(), physical.clone().into_ptr())
    } < 0
    {
        return Err(PyErr::fetch(py));
    }
    // SAFETY: ndarray and base remain live; NumPy only serializes this checked view.
    // SAFETY: ndarray and base remain live; NumPy only serializes this checked view.
    let serialized = unsafe {
        Bound::from_owned_ptr_or_err(py, PY_ARRAY_API.PyArray_ToList(py, view.as_array_ptr()))?
    };
    let values = serialized.cast_into::<PyList>()?;
    Ok(transport(Ok(values)))
}

fn reshaped_list<'py>(
    py: Python<'py>,
    physical: &Bound<'py, PyUntypedArray>,
    plan: &FixedPlan,
    column_major: bool,
) -> PyResult<Transport<Bound<'py, PyList>>> {
    debug_assert!(plan.rank > 1 && plan.rank <= 4);
    let mut dimensions = [0isize; 64];
    for (slot, dimension) in dimensions.iter_mut().zip(plan.dims.iter()).take(plan.rank) {
        *slot = match isize::try_from(*dimension) {
            Ok(value) => value,
            Err(_) => {
                return Ok(transport(Err(Failure::binding(
                    "OVERFLOW",
                    "嵌套输出维度超出 NumPy 容量 / Nested-output dimension exceeds NumPy capacity",
                ))));
            }
        };
    }
    let mut shape = PyArray_Dims {
        ptr: dimensions.as_mut_ptr(),
        len: plan.rank as i32,
    };
    // SAFETY: physical is a live C-order input buffer and fixed Rust already checked
    // every target dimension and the total count. NumPy only changes the view shape.
    let view = unsafe {
        Bound::from_owned_ptr_or_err(
            py,
            PY_ARRAY_API.PyArray_Newshape(
                py,
                physical.as_array_ptr(),
                &mut shape,
                if column_major {
                    NPY_ORDER::NPY_FORTRANORDER
                } else {
                    NPY_ORDER::NPY_CORDER
                },
            ),
        )?
        .cast_into::<PyUntypedArray>()?
    };
    // SAFETY: ndarray and base remain live; NumPy only serializes this checked shape.
    let serialized = unsafe {
        Bound::from_owned_ptr_or_err(py, PY_ARRAY_API.PyArray_ToList(py, view.as_array_ptr()))?
    };
    let values = serialized.cast_into::<PyList>()?;
    Ok(transport(Ok(values)))
}

enum NestedPlan {
    Fixed(FixedPlan),
    Dense(DynShape),
}

impl NestedPlan {
    fn len(&self) -> usize {
        match self {
            Self::Fixed(shape) => shape.len(),
            Self::Dense(shape) => shape.len(),
        }
    }
}

#[pyfunction]
#[pyo3(signature = (*, owner, shape_types, row_major, column_major))]
pub fn _nested_shared_array(
    py: Python<'_>,
    owner: &Bound<'_, PyAny>,
    shape_types: &Bound<'_, PyTuple>,
    row_major: &Bound<'_, PyAny>,
    column_major: &Bound<'_, PyAny>,
) -> PyResult<Transport<Py<PyAny>>> {
    let data = owner.getattr(pyo3::intern!(py, "_data"))?;
    // callable 必须在形状 getter 前捕获；外部 hook 可替换 owner 的字段。 / Capture the callable before shape getters, which can replace owner fields.
    let reshape = data.getattr(pyo3::intern!(py, "reshape"))?;
    let shape = owner.getattr(pyo3::intern!(py, "_shape"))?;
    let dims = shape.getattr(pyo3::intern!(py, "dims"))?;
    let accepted_shape = shape_types.iter().any(|kind| shape.get_type().is(&kind));
    if !data.is_exact_instance_of::<PyUntypedArray>() || !accepted_shape {
        // 自定义存储/形状的 reshape/tolist 是外部扩展协议，不猜测其映射。 / Custom storage/shape reshape/tolist are external protocols; never infer their mapping.
        return Ok(transport(Ok(reshape
            .call1((&dims,))?
            .call_method0(pyo3::intern!(py, "tolist"))?
            .unbind())));
    }
    let storage_order = shape.getattr(pyo3::intern!(py, "storage_order"))?;
    let column = if storage_order.is(row_major) {
        false
    } else if storage_order.is(column_major) {
        true
    } else {
        return Ok(transport(Err(Failure::input(
            "嵌套输出存储顺序无效 / Invalid nested-output storage order",
        ))));
    };
    // 1–4 维仍读取同一个 dims，但使用栈上固定计划和目标视图，避免通用迭代、
    // 非必要 BigInt 转换及 DynShape 堆分配。
    // Ranks 1–4 still read the same dims, then use a stack-backed plan and target view,
    // avoiding generic iteration, unnecessary BigInt conversion and a heap-allocated
    // DynShape.
    let fixed_rank = if dims.is_exact_instance_of::<PyTuple>() {
        match dims.len()? {
            rank @ 1..=4 => Some(rank),
            _ => None,
        }
    } else {
        None
    };
    let plan = if let Some(rank) = fixed_rank {
        let dims = dims.cast::<PyTuple>()?;
        match rank {
            1 => {
                let (shape, error) = fixed_nested_plan::<1>(dims)?;
                if let Some(error) = error {
                    return Ok(transport(Err(error)));
                }
                let Some(shape) = shape else {
                    return Ok(transport(Err(Failure::binding(
                        "APPLICATION_ERROR",
                        "缺少嵌套输出一维计划 / Missing nested-output 1-D plan",
                    ))));
                };
                NestedPlan::Fixed(shape)
            }
            2 => {
                let (shape, error) = fixed_nested_plan::<2>(dims)?;
                if let Some(error) = error {
                    return Ok(transport(Err(error)));
                }
                let Some(shape) = shape else {
                    return Ok(transport(Err(Failure::binding(
                        "APPLICATION_ERROR",
                        "缺少嵌套输出二维计划 / Missing nested-output 2-D plan",
                    ))));
                };
                NestedPlan::Fixed(shape)
            }
            3 => {
                let (shape, error) = fixed_nested_plan::<3>(dims)?;
                if let Some(error) = error {
                    return Ok(transport(Err(error)));
                }
                let Some(shape) = shape else {
                    return Ok(transport(Err(Failure::binding(
                        "APPLICATION_ERROR",
                        "缺少嵌套输出三维计划 / Missing nested-output 3-D plan",
                    ))));
                };
                NestedPlan::Fixed(shape)
            }
            4 => {
                let (shape, error) = fixed_nested_plan::<4>(dims)?;
                if let Some(error) = error {
                    return Ok(transport(Err(error)));
                }
                let Some(shape) = shape else {
                    return Ok(transport(Err(Failure::binding(
                        "APPLICATION_ERROR",
                        "缺少嵌套输出四维计划 / Missing nested-output 4-D plan",
                    ))));
                };
                NestedPlan::Fixed(shape)
            }
            _ => {
                return Ok(transport(Err(Failure::binding(
                    "APPLICATION_ERROR",
                    "嵌套输出固定维度无效 / Invalid fixed nested-output rank",
                ))));
            }
        }
    } else {
        let (shape, error) = dense_nested_plan(py, &dims, column)?;
        if let Some(error) = error {
            return Ok(transport(Err(error)));
        }
        let Some(shape) = shape else {
            return Ok(transport(Err(Failure::binding(
                "APPLICATION_ERROR",
                "缺少嵌套输出形状计划 / Missing nested-output shape plan",
            ))));
        };
        NestedPlan::Dense(shape)
    };
    let expected_len = plan.len();
    let array = data.cast::<PyUntypedArray>()?;
    if array.len() != expected_len {
        return Ok(transport(Err(Failure::input(
            "缓冲数量与形状不匹配 / Buffer count does not match the shape",
        ))));
    }
    // 连续源本身已是 C-order 物理序列；其他源仍由 NumPy 只做一维 C-order 摄入，不传目标形状。
    // A contiguous source already is the C-order physical sequence; otherwise NumPy only ingests one dimension.
    let physical = if array.is_c_contiguous() {
        array.clone()
    } else {
        // SAFETY: 已验证、保活的真正 ndarray；这里只摄入 C-order 源存储，不传目标形状。
        // Checked live ndarray; only ingest C-order source storage here, without the target shape.
        unsafe {
            Bound::from_owned_ptr_or_err(
                py,
                PY_ARRAY_API.PyArray_Ravel(py, array.as_array_ptr(), NPY_ORDER::NPY_CORDER),
            )?
            .cast_into::<PyUntypedArray>()?
        }
    };
    if physical.len() != expected_len {
        return Ok(transport(Err(Failure::input(
            "转换期间缓冲数量变化 / Buffer count changed during conversion",
        ))));
    }
    let convert = |row: &Bound<'_, PyUntypedArray>| -> PyResult<Bound<'_, PyList>> {
        // SAFETY: ndarray 及其 base 均由 Bound 保活；NumPy 只序列化给定的一维物理切片。
        // Bound keeps the ndarray and its base alive; NumPy only serializes the given 1D physical slice.
        unsafe {
            Bound::from_owned_ptr_or_err(py, PY_ARRAY_API.PyArray_ToList(py, row.as_array_ptr()))?
                .cast_into::<PyList>()
                .map_err(Into::into)
        }
    };
    let plan = match plan {
        NestedPlan::Fixed(shape) => {
            if shape.rank == 1 {
                let values = convert(&physical)?;
                debug_assert_eq!(values.len(), shape.len());
                return Ok(transport(Ok(values.into_any().unbind())));
            }
            let (values, error) = reshaped_list(py, &physical, &shape, column)?;
            if let Some(error) = error {
                return Ok(transport(Err(error)));
            }
            let Some(values) = values else {
                return Ok(transport(Err(Failure::binding(
                    "APPLICATION_ERROR",
                    "缺少嵌套输出列表 / Missing nested-output list",
                ))));
            };
            return Ok(transport(Ok(values.into_any().unbind())));
        }
        NestedPlan::Dense(shape) => shape,
    };
    if plan.dimension() == 0 {
        return Ok(transport(Ok(convert(&physical)?.get_item(0)?.unbind())));
    }
    if plan.dimension() == 1 {
        return Ok(transport(Ok(convert(&physical)?.into_any().unbind())));
    }
    // 行主序已经与一维物理序列一致；先序列化一次再按固定 Shape 分组，
    // 比创建目标视图后让 NumPy 递归更少一层固定成本。
    // Row-major already matches the 1D physical sequence; serialize once and
    // group by the pinned Shape instead of constructing a target view.
    let row_order = if column && plan.dimension() > 64 {
        match dense_shape(
            (0..plan.dimension()).map(|axis| Some(plan.shape()[axis])),
            false,
        ) {
            Ok(shape) => Some(shape),
            Err(_) => {
                return Ok(transport(Err(Failure::binding(
                    "APPLICATION_ERROR",
                    "上游嵌套行顺序不一致 / Inconsistent upstream nested row order",
                ))));
            }
        }
    } else {
        None
    };
    let linear = plan.dimension() > 64
        && (!column
            || row_order.as_ref().is_some_and(|row| {
                (0..plan.dimension()).all(|axis| {
                    plan.shape()[axis] == 1 || plan.offsets()[axis] == row.offsets()[axis]
                })
            }));
    let group_axes;
    let mut values;
    if linear {
        values = convert(&physical)?;
        group_axes = plan.dimension();
    } else if plan.dimension() <= 64 {
        let (values, error) = target_view_list(py, &physical, &plan)?;
        if let Some(error) = error {
            return Ok(transport(Err(error)));
        }
        let Some(values) = values else {
            return Ok(transport(Err(Failure::binding(
                "APPLICATION_ERROR",
                "缺少嵌套输出列表 / Missing nested-output list",
            ))));
        };
        return Ok(transport(Ok(values.into_any().unbind())));
    } else {
        let last_axis = plan.dimension() - 1;
        let width = plan.shape()[last_axis];
        let stride = plan.offsets()[last_axis];
        let prefix = match dense_shape((0..last_axis).map(|axis| Some(plan.shape()[axis])), false) {
            Ok(shape) => shape,
            Err(_) => {
                return Ok(transport(Err(Failure::binding(
                    "APPLICATION_ERROR",
                    "上游嵌套前缀不一致 / Inconsistent upstream nested prefix",
                ))));
            }
        };
        let built = if width <= 32 {
            // 短行只把物理叶序列化一次；随后用固定 Rust 行起点直接组装目标行，
            // 避免逐叶重排、逐叶 append 以及额外的末轴分组。
            // Serialize tiny runs once, then assemble target rows directly from pinned Rust starts.
            let serialized = convert(&physical)?;
            let rows = raw_list(py, prefix.len())?;
            let mut full_indices = vec![0; plan.dimension()];
            for (ordinal, indices) in prefix.indices().enumerate() {
                if ordinal.is_multiple_of(4096) {
                    py.check_signals()?;
                }
                full_indices[..last_axis].copy_from_slice(&indices);
                let index = match plan.index_of(&full_indices) {
                    Ok(index) => index,
                    Err(_) => {
                        return Ok(transport(Err(Failure::binding(
                            "APPLICATION_ERROR",
                            "上游嵌套索引不一致 / Inconsistent upstream nested index",
                        ))));
                    }
                };
                let row = if stride == 1 {
                    let end = index
                        .checked_add(width)
                        .filter(|end| *end <= serialized.len());
                    let Some(end) = end else {
                        return Ok(transport(Err(Failure::binding(
                            "APPLICATION_ERROR",
                            "上游嵌套索引越界 / Upstream nested index exceeds storage",
                        ))));
                    };
                    serialized.get_slice(index, end)
                } else {
                    let row = raw_list(py, width)?;
                    for column_index in 0..width {
                        let leaf_index = column_index
                            .checked_mul(stride)
                            .and_then(|span| index.checked_add(span));
                        let Some(leaf_index) = leaf_index.filter(|slot| *slot < serialized.len())
                        else {
                            return Ok(transport(Err(Failure::binding(
                                "APPLICATION_ERROR",
                                "上游嵌套索引越界 / Upstream nested index exceeds storage",
                            ))));
                        };
                        // SAFETY: leaf_index was checked against the live serialized list.
                        set_raw_item(&row, column_index, unsafe {
                            serialized.get_item_unchecked(leaf_index)
                        });
                    }
                    row
                };
                set_raw_item(&rows, ordinal, row.into_any());
            }
            rows
        } else {
            let rows = raw_list(py, prefix.len())?;
            let mut full_indices = vec![0; plan.dimension()];
            for (ordinal, indices) in prefix.indices().enumerate() {
                if ordinal.is_multiple_of(4096) {
                    py.check_signals()?;
                }
                full_indices[..last_axis].copy_from_slice(&indices);
                let index = match plan.index_of(&full_indices) {
                    Ok(index) => index,
                    Err(_) => {
                        return Ok(transport(Err(Failure::binding(
                            "APPLICATION_ERROR",
                            "上游嵌套索引不一致 / Inconsistent upstream nested index",
                        ))));
                    }
                };
                let stop = (width - 1)
                    .checked_mul(stride)
                    .and_then(|span| index.checked_add(span))
                    .filter(|end| *end < physical.len())
                    .and_then(|end| end.checked_add(1));
                let Some(stop) = stop else {
                    return Ok(transport(Err(Failure::binding(
                        "APPLICATION_ERROR",
                        "上游嵌套切片越界 / Upstream nested slice exceeds storage",
                    ))));
                };
                // 起点、步长和长度都来自固定 Rust；NumPy 不接收目标轴或布局，仅执行安全的一维存储切片。
                // Pinned Rust supplies start, stride and length; NumPy receives no target axes/layout, only a safe 1D storage slice.
                let slice = PySlice::new(py, index as isize, stop as isize, stride as isize);
                let row = physical.get_item(slice)?.cast_into::<PyUntypedArray>()?;
                let row = convert(&row)?;
                if row.len() != width {
                    return Ok(transport(Err(Failure::binding(
                        "APPLICATION_ERROR",
                        "嵌套切片数量不一致 / Inconsistent nested slice count",
                    ))));
                }
                set_raw_item(&rows, ordinal, row.into_any());
            }
            rows
        };
        group_axes = last_axis;
        values = built;
    };
    // 逻辑次序已经由上游确定；这里只创建 Python 容器，标量/对象叶不再探测或拆包。
    // Upstream already determines logical order; only build Python containers, without probing or unwrapping leaves.
    for axis in (1..group_axes).rev() {
        let width = plan.shape()[axis];
        let group_count: usize = values.len() / width;
        let groups = raw_list(py, group_count)?;
        for group_index in 0..group_count {
            if group_index.is_multiple_of(4096) {
                py.check_signals()?;
            }
            let start = group_index * width;
            set_raw_item(
                &groups,
                group_index,
                values.get_slice(start, start + width).into_any(),
            );
        }
        values = groups;
    }
    Ok(transport(Ok(values.into_any().unbind())))
}

/// 只持协议配置与 Result 工厂，不缓存调用 owner/shape/叶。
/// Retain only protocol configuration and Result factories, never call owners, shapes or leaves.
#[pyclass(
    name = "_SharedNested",
    frozen,
    weakref,
    module = "ospf_python._native"
)]
pub struct SharedNested {
    shape_types: Py<PyTuple>,
    row_major: Py<PyAny>,
    column_major: Py<PyAny>,
    publication: ResultPublication,
}

#[pymethods]
impl SharedNested {
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
                "缺少嵌套导出结果 / Missing nested-export result",
            ),
        }
    }

    fn to_list(&self, py: Python<'_>, owner: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let payload = _nested_shared_array(
            py,
            owner,
            self.shape_types.bind(py),
            self.row_major.bind(py),
            self.column_major.bind(py),
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
