//! 形状、精确数组和对象存储委托固定上游。 / Delegate shapes, exact arrays and object storage to the pinned upstream.

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::ToPrimitive;
use numpy::npyffi::{NPY_ORDER, PY_ARRAY_API, PyArray_Dims};
use numpy::{PyUntypedArray, PyUntypedArrayMethods};
use ospf_rust_base::error::Error;
use ospf_rust_multiarray::{
    AbstractShape, AccessOrder, DummyIndex, DynShape, IndexCalculationError,
    MultiArray as RustMultiArray, MultiArrayBuilder, MultiArrayView as RustMultiArrayView,
    Shape1 as RustShape1, ShapeAccessOrderExt, StorageOrder,
};
use pyo3::class::basic::CompareOp;
use pyo3::class::gc::{PyTraverseError, PyVisit};
use pyo3::exceptions::{PyException, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{
    PyBool, PyBytes, PyComplex, PyFloat, PyInt, PyList, PySlice, PyString, PyTuple, PyType,
};
use std::collections::HashSet;
use std::sync::Mutex;
use std::sync::atomic::{AtomicBool, Ordering};

use crate::failure::{Failure, ResultPublication, Transport, transport, transport_unit};
use crate::numeric::Rational;
use crate::numeric_array::RationalArray;
use crate::shape_metadata::{DenseShapeError, dense_shape, fixed_shape};

pub(crate) mod iterator;

fn order(column_major: bool) -> StorageOrder {
    if column_major {
        StorageOrder::ColumnMajor
    } else {
        StorageOrder::RowMajor
    }
}

fn access(column_major: bool) -> AccessOrder {
    AccessOrder::from_storage_order(order(column_major))
}

fn nested_capacity<T>(size: usize) -> Result<Vec<T>, Failure> {
    if size
        .checked_mul(std::mem::size_of::<T>())
        .is_none_or(|bytes| bytes > isize::MAX as usize)
    {
        return Err(Failure::binding(
            "OVERFLOW",
            "嵌套输入存储字节数超出原生容量 / Nested input storage bytes exceed native capacity",
        ));
    }
    let mut values = Vec::new();
    values.try_reserve_exact(size).map_err(|_| {
        let mut failure = Failure::binding(
            "APPLICATION_ERROR",
            "无法分配嵌套输入存储 / Unable to allocate nested input storage",
        );
        failure.error_class = "RESOURCE";
        failure
    })?;
    Ok(values)
}

fn nested_values(data: &Bound<'_, PyAny>, shape: &Shape) -> Result<Vec<Py<PyAny>>, Failure> {
    let mut output = nested_capacity(shape.size())?;
    let rank = shape.value.dimension();
    let depth = rank.checked_add(1).ok_or_else(|| {
        Failure::binding(
            "OVERFLOW",
            "嵌套层数超限 / Nested depth exceeds native capacity",
        )
    })?;
    let mut frames = nested_capacity(depth)?;
    frames.push((data.clone(), 0_usize));
    // shape 限定结构深度；叶保持不透明，显式栈避免递归或用户序列协议。 / Shape bounds structural depth; opaque leaves and an explicit stack avoid recursion and user sequence protocols.
    while let Some(axis) = frames.len().checked_sub(1) {
        let (node, next) = &mut frames[axis];
        if axis == rank {
            output.push(node.clone().unbind());
            frames.pop();
            continue;
        }
        let expected = shape.value.shape()[axis];
        if *next == 0 {
            if !node.is_exact_instance_of::<PyList>() && !node.is_exact_instance_of::<PyTuple>() {
                return Err(Failure::input(format!(
                    "第 {axis} 轴需要内置 list/tuple / Axis {axis} requires a built-in list/tuple"
                )));
            }
            if node.len().ok() != Some(expected) {
                return Err(Failure::input(format!(
                    "第 {axis} 轴长度应为 {expected} / Axis {axis} length must be {expected}"
                )));
            }
        }
        if *next == expected {
            frames.pop();
            continue;
        }
        let item = node.get_item(*next).map_err(|_| {
            Failure::input("嵌套输入在读取时失效 / Nested input became invalid during reading")
        })?;
        *next += 1;
        frames.push((item, 0));
    }
    Ok(output)
}

fn pickle_error(error: Failure) -> PyErr {
    PyValueError::new_err(error.message)
}

fn pickle_shape(metadata: (u32, Vec<BigInt>, bool)) -> PyResult<Shape> {
    let (version, dims, column_major) = metadata;
    if version != 1 {
        return Err(PyValueError::new_err(
            "不支持的数组 pickle 版本 / Unsupported array pickle version",
        ));
    }
    Shape::create(dims, column_major).map_err(pickle_error)
}

#[pyfunction]
pub fn _unpickle_shape(metadata: (u32, Vec<BigInt>, bool)) -> PyResult<Shape> {
    pickle_shape(metadata)
}

#[pyfunction]
pub fn _unpickle_multiarray(metadata: (u32, Vec<BigInt>, bool)) -> PyResult<MultiArray> {
    Ok(MultiArray {
        shape: pickle_shape(metadata)?,
        value: Mutex::new(None),
        restore_pending: AtomicBool::new(true),
    })
}

#[pyfunction]
pub fn _unpickle_mutable_multiarray(
    metadata: (u32, Vec<BigInt>, bool),
) -> PyResult<MutableMultiArray> {
    Ok(MutableMultiArray {
        inner: _unpickle_multiarray(metadata)?,
    })
}

#[pyfunction]
pub fn _unpickle_multiarray_view(
    metadata: (u32, Vec<BigInt>, bool, Vec<BigInt>, Vec<BigInt>),
) -> PyResult<MultiArrayView> {
    let (version, source_dims, column_major, offsets, dims) = metadata;
    let source = pickle_shape((version, source_dims, column_major))?;
    let shape = Shape::create(dims, column_major).map_err(pickle_error)?;
    MultiArrayView::create(&source, offsets, &shape).map_err(pickle_error)
}

fn callback_failure(message: &str) -> Failure {
    let mut failure = Failure::binding("APPLICATION_ERROR", message);
    failure.error_class = "CALLBACK";
    failure
}

fn reversed_shape(shape: &Shape) -> Shape {
    let mut dims = shape.dims();
    dims.reverse();
    Shape {
        value: DynShape::new_with_order(dims, order(!shape.column_major())),
    }
}

fn mapped_value(
    py: Python<'_>,
    callback: &Bound<'_, PyAny>,
    item: Py<PyAny>,
) -> PyResult<Result<Py<PyAny>, Failure>> {
    match callback
        .call1((item,))
        .and_then(|returned| returned.extract::<(bool, Py<PyAny>)>())
    {
        Ok((true, value)) => Ok(Ok(value)),
        Ok((false, _)) => Ok(Err(callback_failure(
            "数组回调失败 / Array callback failed",
        ))),
        Err(error) if error.is_instance_of::<PyException>(py) => Ok(Err(callback_failure(
            "数组回调传输失败 / Array callback transport failed",
        ))),
        Err(error) => Err(error),
    }
}

fn map_snapshot(
    py: Python<'_>,
    values: Vec<Py<PyAny>>,
    source_shape: &Shape,
    callback: &Bound<'_, PyAny>,
    column_major: bool,
    output_shape: Option<&Shape>,
) -> PyResult<Transport<MultiArray>> {
    let shape = output_shape.unwrap_or(source_shape);
    let mut output = Vec::new();
    // 所有源引用均已快照并解锁；Python 回调及输出清理不持有存储锁。 / Source references are snapshotted and unlocked before callbacks or output cleanup.
    for item in values {
        let returned = match mapped_value(py, callback, item)? {
            Ok(value) => value,
            Err(error) => return Ok(transport(Err(error))),
        };
        if output_shape.is_some() {
            let value = returned.bind(py);
            if !value.is_exact_instance_of::<PyList>() {
                return Ok(transport(Err(callback_failure(
                    "扁平映射传输需要内置 list / Flat-map transport requires a built-in list",
                ))));
            }
            let values = value.cast::<PyList>()?;
            if values.len() > shape.value.len() - output.len() {
                return Ok(transport(Err(Failure::input(
                    "映射输出超过指定形状 / Mapped output exceeds the specified shape",
                ))));
            }
            output.extend(values.iter().map(Bound::unbind));
        } else {
            output.push(returned);
        }
    }
    Ok(transport(MultiArray::create(
        output,
        shape.clone(),
        column_major,
    )))
}

fn reduce_snapshot(
    py: Python<'_>,
    values: Vec<Py<PyAny>>,
    callback: &Bound<'_, PyAny>,
) -> PyResult<Transport<Py<PyAny>>> {
    let mut items = values.into_iter();
    let Some(mut accumulated) = items.next() else {
        return Ok(transport(Err(Failure::binding(
            "FAILED_PRECONDITION",
            "归约需要至少一个元素 / Reduction requires at least one element",
        ))));
    };
    // 仅编排 Python 二元操作；源遍历已由上游完成并快照，所有回调/引用清理均不持锁。 / Only orchestrate Python binary operations on the upstream traversal snapshot, without storage locks.
    for item in items {
        let pair = (accumulated, item).into_pyobject(py)?.into_any().unbind();
        accumulated = match mapped_value(py, callback, pair)? {
            Ok(value) => value,
            Err(error) => return Ok(transport(Err(error))),
        };
    }
    Ok(transport(Ok(accumulated)))
}

fn storage_snapshot(
    py: Python<'_>,
    value: &RustMultiArray<Py<PyAny>, DynShape>,
    region: Option<&MultiArrayView>,
    column_major: bool,
    limit: usize,
) -> Vec<Py<PyAny>> {
    match region {
        None if value.storage_order() == order(column_major) => {
            // 访问顺序就是物理顺序时，使用上游公开连续存储，避免重复坐标换算。 / When access matches storage order, use upstream public contiguous storage without repeated coordinate conversion.
            value
                .as_slice()
                .iter()
                .take(limit)
                .map(|item| item.clone_ref(py))
                .collect()
        }
        None => value
            .iter_with_order(access(column_major))
            .take(limit)
            .map(|item| item.clone_ref(py))
            .collect(),
        Some(region) => {
            let ranges = region
                .offsets
                .iter()
                .zip(region.shape.dims())
                .map(|(offset, dim)| {
                    DummyIndex::Range(Box::new(*offset as isize..(*offset + dim) as isize))
                })
                .collect();
            let view: RustMultiArrayView<'_, Py<PyAny>, DynShape> =
                RustMultiArrayView::new_by_dummy(value, &ranges);
            view.iter_with_order(access(column_major))
                .take(limit)
                .map(|item| item.clone_ref(py))
                .collect()
        }
    }
}

fn checked_snapshot(values: Vec<Py<PyAny>>, shape: &Shape) -> Result<Vec<Py<PyAny>>, Failure> {
    if values.len() != shape.size() {
        return Err(Failure::binding(
            "APPLICATION_ERROR",
            "Rust 数组快照长度不匹配 / Rust array snapshot length mismatch",
        ));
    }
    Ok(values)
}

fn operand_shape<'a>(source: &'a MultiArray, region: Option<&'a MultiArrayView>) -> &'a Shape {
    region.map_or(&source.shape, |region| &region.shape)
}

// 同一次比较持有的两侧引用快照。 / Operand reference snapshots held by one comparison.
type ReferenceSnapshotPair = (Vec<Py<PyAny>>, Vec<Py<PyAny>>);

fn comparison_snapshots(
    py: Python<'_>,
    left: &MultiArray,
    right: &MultiArray,
    left_region: Option<&MultiArrayView>,
    right_region: Option<&MultiArrayView>,
) -> Result<ReferenceSnapshotPair, Failure> {
    if let Some(region) = left_region {
        region.check_source(&left.shape)?;
    }
    if let Some(region) = right_region {
        region.check_source(&right.shape)?;
    }
    let (left_values, right_values) = if std::ptr::eq(left, right) {
        let guard = left.value.lock().unwrap_or_else(|error| error.into_inner());
        let value = guard.as_ref().ok_or_else(MultiArray::cleared)?;
        // 同源两侧必须来自同一槽位版本；不持锁执行比较或释放快照。 / Same-source operands share one slot version; compare and release snapshots only after unlocking.
        let snapshots = (
            storage_snapshot(py, value, left_region, false, usize::MAX),
            storage_snapshot(py, value, right_region, false, usize::MAX),
        );
        drop(guard);
        snapshots
    } else {
        let snapshot = |source: &MultiArray, region: Option<&MultiArrayView>| match region {
            Some(region) => source.region_snapshot(py, region, false),
            None => source.snapshot(py, false),
        };
        (snapshot(left, left_region)?, snapshot(right, right_region)?)
    };
    Ok((
        checked_snapshot(left_values, operand_shape(left, left_region))?,
        checked_snapshot(right_values, operand_shape(right, right_region))?,
    ))
}

enum ReferenceStorage<'py> {
    Immutable(PyRef<'py, MultiArray>),
    Mutable(PyRef<'py, MutableMultiArray>),
}

impl ReferenceStorage<'_> {
    fn inner(&self) -> &MultiArray {
        match self {
            Self::Immutable(source) => source,
            Self::Mutable(source) => &source.inner,
        }
    }
}

fn reference_storage<'py>(value: &Bound<'py, PyAny>) -> Result<ReferenceStorage<'py>, Failure> {
    if let Ok(source) = value.extract::<PyRef<'py, MultiArray>>() {
        return Ok(ReferenceStorage::Immutable(source));
    }
    if let Ok(source) = value.extract::<PyRef<'py, MutableMultiArray>>() {
        return Ok(ReferenceStorage::Mutable(source));
    }
    Err(Failure::input(
        "比较需要原生引用数组 / Comparison requires native reference arrays",
    ))
}

fn builtin_equality_leaf(value: &Bound<'_, PyAny>) -> bool {
    value.is_exact_instance_of::<PyInt>()
        || value.is_exact_instance_of::<PyFloat>()
        || value.is_exact_instance_of::<PyBool>()
        || value.is_none()
        || value.is_exact_instance_of::<PyString>()
        || value.is_exact_instance_of::<PyBytes>()
        || value.is_exact_instance_of::<PyComplex>()
}

#[pyfunction]
#[pyo3(signature = (*, left, right, callback, left_region=None, right_region=None, builtin_equality=false))]
pub fn _compare_reference_arrays(
    py: Python<'_>,
    left: &Bound<'_, PyAny>,
    right: &Bound<'_, PyAny>,
    callback: &Bound<'_, PyAny>,
    left_region: Option<&MultiArrayView>,
    right_region: Option<&MultiArrayView>,
    builtin_equality: bool,
) -> PyResult<Transport<bool>> {
    if !callback.is_callable() {
        return Ok(transport(Err(Failure::input(
            "元素比较器必须可调用 / Element comparator must be callable",
        ))));
    }
    let (left, right) = match (reference_storage(left), reference_storage(right)) {
        (Ok(left), Ok(right)) => (left, right),
        (Err(error), _) | (_, Err(error)) => return Ok(transport(Err(error))),
    };
    let (left_values, right_values) =
        match comparison_snapshots(py, left.inner(), right.inner(), left_region, right_region) {
            Ok(values) => values,
            Err(error) => return Ok(transport(Err(error))),
        };
    if operand_shape(left.inner(), left_region).dims()
        != operand_shape(right.inner(), right_region).dims()
    {
        return Ok(transport(Ok(false)));
    }
    for (index, (left, right)) in left_values.into_iter().zip(right_values).enumerate() {
        if builtin_equality
            && builtin_equality_leaf(left.bind(py))
            && builtin_equality_leaf(right.bind(py))
            && (left.bind(py).is_exact_instance_of::<PyBytes>()
                == right.bind(py).is_exact_instance_of::<PyBytes>())
        {
            // 仅精确内置类型走 CPython 值协议，不用带 identity shortcut 的 RichCompareBool。 / Exact builtins use CPython value comparison, not RichCompareBool's identity shortcut.
            let equal = left.bind(py).rich_compare(right.bind(py), CompareOp::Eq)?;
            if !equal.extract::<bool>()? {
                return Ok(transport(Ok(false)));
            }
            continue;
        }
        let pair = (index, left, right).into_pyobject(py)?.into_any().unbind();
        let result = match mapped_value(py, callback, pair)? {
            Ok(value) => value,
            Err(error) => return Ok(transport(Err(error))),
        };
        if !result.bind(py).is_exact_instance_of::<PyBool>() {
            return Ok(transport(Err(callback_failure(
                "比较回调需要 bool / Comparison callback requires bool",
            ))));
        }
        if !result.bind(py).extract::<bool>()? {
            return Ok(transport(Ok(false)));
        }
    }
    Ok(transport(Ok(true)))
}

// 保留 Python Unicode（包括孤立代理码），不把用户字符串有损转换为 Rust UTF-8。 / Preserve Python Unicode, including lone surrogates, without lossy Rust UTF-8 conversion.
struct DescriptionText<'py> {
    parts: Vec<Bound<'py, PyString>>,
    length: usize,
    limit: usize,
    truncated: bool,
}

impl<'py> DescriptionText<'py> {
    fn new(limit: usize) -> Self {
        Self {
            parts: Vec::new(),
            length: 0,
            limit,
            truncated: false,
        }
    }

    fn remaining(&self) -> usize {
        self.limit - self.length
    }

    fn push(&mut self, py: Python<'py>, text: &Bound<'py, PyString>) -> PyResult<bool> {
        let length = text.len()?;
        if length > self.remaining() {
            self.parts.push(
                text.get_item(PySlice::new(py, 0, self.remaining() as isize, 1))?
                    .cast_into::<PyString>()?,
            );
            self.length = self.limit;
            self.truncated = true;
            return Ok(false);
        }
        self.parts.push(text.clone());
        self.length += length;
        Ok(true)
    }

    fn append(&mut self, py: Python<'py>, text: &str) -> PyResult<bool> {
        self.push(py, &PyString::new(py, text))
    }

    fn tuple(
        &mut self,
        py: Python<'py>,
        values: impl ExactSizeIterator<Item = usize>,
    ) -> PyResult<bool> {
        let length = values.len();
        if !self.append(py, "(")? {
            return Ok(false);
        }
        for (index, value) in values.enumerate() {
            if (index != 0 && !self.append(py, ", ")?) || !self.append(py, &value.to_string())? {
                return Ok(false);
            }
        }
        if length == 1 && !self.append(py, ",")? {
            return Ok(false);
        }
        self.append(py, ")")
    }

    fn header(
        &mut self,
        py: Python<'py>,
        shape: &Shape,
        region: Option<&MultiArrayView>,
    ) -> PyResult<bool> {
        if !self.append(py, "Array(shape=")?
            || !self.tuple(
                py,
                (0..shape.value.dimension()).map(|axis| shape.value.shape()[axis]),
            )?
            || !self.append(py, ", storage_order=")?
            || !self.append(
                py,
                if shape.column_major() {
                    "COLUMN_MAJOR"
                } else {
                    "ROW_MAJOR"
                },
            )?
            || !self.append(py, ", offsets=")?
        {
            return Ok(false);
        }
        let complete = match region {
            Some(region) => self.tuple(py, region.offsets.iter().copied())?,
            None => self.append(py, "None")?,
        };
        Ok(complete && self.append(py, ", access_order=ROW_MAJOR, data=[")?)
    }

    fn finish(self, py: Python<'py>) -> PyResult<Py<PyAny>> {
        let text = PyString::new(py, "").call_method1("join", (PyList::new(py, self.parts)?,))?;
        if self.truncated {
            return Ok(text
                .get_item(PySlice::new(py, 0, (self.limit - 3) as isize, 1))?
                .call_method1("__add__", ("...",))?
                .unbind());
        }
        Ok(text.unbind())
    }
}

fn description_snapshot(
    py: Python<'_>,
    source: &MultiArray,
    region: Option<&MultiArrayView>,
    limit: usize,
) -> Result<Vec<Py<PyAny>>, Failure> {
    if let Some(region) = region {
        region.check_source(&source.shape)?;
    }
    let guard = source
        .value
        .lock()
        .unwrap_or_else(|error| error.into_inner());
    let value = guard.as_ref().ok_or_else(MultiArray::cleared)?;
    let values = storage_snapshot(py, value, region, false, limit);
    drop(guard);
    if values.len() != limit.min(operand_shape(source, region).size()) {
        return Err(Failure::binding(
            "APPLICATION_ERROR",
            "描述快照长度不匹配 / Description snapshot length mismatch",
        ));
    }
    Ok(values)
}

#[pyfunction]
#[pyo3(signature = (*, source, callback, max_items, max_chars, region=None))]
pub fn _describe_reference_array(
    py: Python<'_>,
    source: &Bound<'_, PyAny>,
    callback: &Bound<'_, PyAny>,
    max_items: usize,
    max_chars: usize,
    region: Option<&MultiArrayView>,
) -> PyResult<Transport<Py<PyAny>>> {
    if !callback.is_callable() || max_chars < 3 || max_chars > isize::MAX as usize {
        return Ok(transport(Err(Failure::input(
            "描述需要可调用格式器和至少三个字符的容量 / Description requires a callable formatter and a capacity of at least three characters",
        ))));
    }
    let source = match reference_storage(source) {
        Ok(source) => source,
        Err(error) => return Ok(transport(Err(error))),
    };
    let shape = operand_shape(source.inner(), region);
    let mut text = DescriptionText::new(max_chars);
    text.header(py, shape, region)?;
    let limit = max_items.min(text.remaining());
    // 仅获取可能显示的逻辑前缀；即使只显示元数据，仍在回调前验证源和区域。 / Snapshot only a displayable logical prefix; validate source and region even for metadata-only output.
    let values = match description_snapshot(py, source.inner(), region, limit) {
        Ok(values) => values,
        Err(error) => return Ok(transport(Err(error))),
    };
    if text.truncated {
        return Ok(transport(Ok(text.finish(py)?)));
    }
    let count = values.len();
    for (index, value) in values.into_iter().enumerate() {
        if index != 0 && !text.append(py, ", ")? {
            break;
        }
        if text.remaining() == 0 {
            text.truncated = true;
            break;
        }
        let formatted = match mapped_value(py, callback, value)? {
            Ok(value) => value,
            Err(error) => return Ok(transport(Err(error))),
        };
        if !formatted.bind(py).is_exact_instance_of::<PyString>() {
            return Ok(transport(Err(callback_failure(
                "描述格式器需要内置 str / Description formatter requires a built-in str",
            ))));
        }
        if !text.push(py, formatted.bind(py).cast::<PyString>()?)? {
            break;
        }
    }
    if !text.truncated {
        if count < shape.size() {
            if count != 0 {
                text.append(py, ", ")?;
            }
            if !text.truncated {
                text.append(py, "...")?;
            }
        }
        if !text.truncated {
            text.append(py, "])")?;
        }
    }
    Ok(transport(Ok(text.finish(py)?)))
}

fn nest_snapshot(
    py: Python<'_>,
    mut values: Vec<Py<PyAny>>,
    shape: &Shape,
) -> PyResult<Transport<Py<PyAny>>> {
    if values.len() != shape.value.len() {
        return Ok(transport(Err(Failure::binding(
            "APPLICATION_ERROR",
            "嵌套输出的快照长度不匹配 / Nested output snapshot length mismatch",
        ))));
    }
    // 上游行遍历已确定坐标顺序；这里只构建 Python 协议容器，不重排元素。 / Upstream row traversal supplies coordinate order; only build Python protocol containers here.
    for width in shape.dims().into_iter().rev() {
        let mut items = values.into_iter();
        let count = items.len() / width;
        let mut groups = Vec::with_capacity(count);
        for _ in 0..count {
            groups.push(
                PyList::new(py, items.by_ref().take(width))?
                    .into_any()
                    .unbind(),
            );
        }
        values = groups;
    }
    Ok(transport(values.pop().ok_or_else(|| {
        Failure::binding(
            "APPLICATION_ERROR",
            "嵌套输出缺少根值 / Nested output lacks a root value",
        )
    })))
}

fn range_failure() -> Failure {
    Failure::binding(
        "OUT_OF_RANGE",
        "索引超出形状范围 / Index outside shape bounds",
    )
}

fn dense_shape_failure(error: DenseShapeError) -> Failure {
    match error {
        DenseShapeError::Dimension => {
            Failure::input("维度必须为正的机器整数 / Dimensions must be positive machine integers")
        }
        DenseShapeError::Size => Failure::binding("OVERFLOW", "形状大小溢出 / Shape size overflow"),
    }
}

fn index_failure(error: IndexCalculationError) -> Failure {
    Failure {
        category: match &error {
            IndexCalculationError::DimensionMismatching(_) => "ILLEGAL_ARGUMENT",
            IndexCalculationError::OutOfShape(_) => "OUT_OF_RANGE",
        },
        source: "ospf-rust-multiarray",
        rust_code: Some(error.code().to_u8()),
        error_class: "INPUT",
        message: format!("数组索引失败 / Array indexing failed: {error}"),
    }
}

fn validated_fixed_items<'py>(
    value: &'py Bound<'py, PyAny>,
) -> Result<&'py Bound<'py, PyTuple>, Failure> {
    if !value.is_exact_instance_of::<PyTuple>() {
        return Err(Failure::input(
            "索引必须为整数 tuple / Indices must be an integer tuple",
        ));
    }
    let value = value
        .cast::<PyTuple>()
        .map_err(|_| Failure::input("索引必须为整数 tuple / Indices must be an integer tuple"))?;
    for item in value.iter() {
        if !item.is_instance_of::<PyInt>() || item.is_instance_of::<PyBool>() {
            return Err(Failure::input(
                "索引必须为整数 tuple / Indices must be an integer tuple",
            ));
        }
    }
    Ok(value)
}

fn checked_fixed_coordinates<const N: usize>(
    value: &Bound<'_, PyTuple>,
) -> Result<[usize; N], Failure> {
    if value.len() != N {
        return Err(Failure::input("索引维数不匹配 / Index dimension mismatch"));
    }
    let mut coordinates = [0usize; N];
    for (position, item) in value.iter().enumerate() {
        coordinates[position] = item.extract::<usize>().map_err(|_| range_failure())?;
    }
    Ok(coordinates)
}

fn checked_fixed_dimension<'py>(value: Bound<'py, PyAny>) -> Result<Bound<'py, PyInt>, Failure> {
    if !value.is_instance_of::<PyInt>() || value.is_instance_of::<PyBool>() {
        return Err(Failure::input(
            "维度必须为整数 tuple / Dimensions must be an integer tuple",
        ));
    }
    value
        .cast_into::<PyInt>()
        .map_err(|_| Failure::input("维度必须为整数 tuple / Dimensions must be an integer tuple"))
}

fn fixed_dimension_value(value: &Bound<'_, PyInt>) -> Result<usize, Failure> {
    value.extract::<usize>().map_err(|_| {
        Failure::input("维度必须为正的机器整数 / Dimensions must be positive machine integers")
    })
}

enum FixedDimensions<'py> {
    D1([Bound<'py, PyInt>; 1]),
    D2([Bound<'py, PyInt>; 2]),
    D3([Bound<'py, PyInt>; 3]),
    D4([Bound<'py, PyInt>; 4]),
}

impl FixedDimensions<'_> {
    fn locate(
        &self,
        indices: &Bound<'_, PyTuple>,
        column_major: bool,
    ) -> Result<(usize, usize), Failure> {
        match self {
            Self::D1([d0]) => {
                let dims = [fixed_dimension_value(d0)?];
                locate_fixed_shape(dims, indices, column_major)
            }
            Self::D2([d0, d1]) => {
                let dims = [fixed_dimension_value(d0)?, fixed_dimension_value(d1)?];
                locate_fixed_shape(dims, indices, column_major)
            }
            Self::D3([d0, d1, d2]) => {
                let dims = [
                    fixed_dimension_value(d0)?,
                    fixed_dimension_value(d1)?,
                    fixed_dimension_value(d2)?,
                ];
                locate_fixed_shape(dims, indices, column_major)
            }
            Self::D4([d0, d1, d2, d3]) => {
                let dims = [
                    fixed_dimension_value(d0)?,
                    fixed_dimension_value(d1)?,
                    fixed_dimension_value(d2)?,
                    fixed_dimension_value(d3)?,
                ];
                locate_fixed_shape(dims, indices, column_major)
            }
        }
    }
}

fn locate_fixed_shape<const N: usize>(
    dims: [usize; N],
    indices: &Bound<'_, PyTuple>,
    column_major: bool,
) -> Result<(usize, usize), Failure> {
    let shape = fixed_shape(dims, column_major).map_err(dense_shape_failure)?;
    let coordinates = checked_fixed_coordinates::<N>(indices)?;
    let offset = shape.index_of(&coordinates).map_err(index_failure)?;
    Ok((offset, shape.len()))
}

fn checked_bigint_tuple(
    value: &Bound<'_, PyTuple>,
    message: &'static str,
) -> Result<Vec<BigInt>, Failure> {
    let mut output = Vec::new();
    output.try_reserve_exact(value.len()).map_err(|_| {
        let mut failure = Failure::binding(
            "APPLICATION_ERROR",
            "无法分配整数元组存储 / Unable to allocate integer tuple storage",
        );
        failure.error_class = "RESOURCE";
        failure
    })?;
    for item in value.iter() {
        if !item.is_instance_of::<PyInt>() || item.is_instance_of::<PyBool>() {
            return Err(Failure::input(message));
        }
        output.push(
            item.extract::<BigInt>()
                .map_err(|_| Failure::input(message))?,
        );
    }
    Ok(output)
}

#[pyclass(frozen, module = "ospf_python._native")]
#[derive(Clone)]
pub struct Shape {
    value: DynShape,
}

impl Shape {
    fn create(dims: Vec<BigInt>, column_major: bool) -> Result<Self, Failure> {
        Self::from_dense(dims.iter().map(BigInt::to_usize), column_major)
    }

    fn from_dense(
        dims: impl IntoIterator<Item = Option<usize>>,
        column_major: bool,
    ) -> Result<Self, Failure> {
        Ok(Self {
            value: dense_shape(dims, column_major).map_err(|error| match error {
                DenseShapeError::Dimension => Failure::input(
                    "维度必须为正的机器整数 / Dimensions must be positive machine integers",
                ),
                DenseShapeError::Size => {
                    Failure::binding("OVERFLOW", "形状大小溢出 / Shape size overflow")
                }
            })?,
        })
    }

    fn checked_index(&self, indices: Vec<BigInt>) -> Result<usize, Failure> {
        if indices.len() != self.value.dimension() {
            return Err(Failure::input("索引维数不匹配 / Index dimension mismatch"));
        }
        let indices = indices
            .into_iter()
            .map(|index| index.to_usize().ok_or_else(range_failure))
            .collect::<Result<Vec<_>, _>>()?;
        self.value.index_of(&indices).map_err(index_failure)
    }

    fn checked_vector(&self, index: BigInt) -> Result<Vec<usize>, Failure> {
        // vector_of 本身不校验线性范围；先检查再委托。 / vector_of does not check linear bounds itself.
        let index = index
            .to_usize()
            .filter(|index| *index < self.value.len())
            .ok_or_else(range_failure)?;
        self.value.vector_of(index).map_err(index_failure)
    }
}

#[pymethods]
impl Shape {
    fn __reduce__(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        let restore = py
            .import("ospf_python._native")?
            .getattr("_unpickle_shape")?;
        Ok((restore, ((1u32, self.dims(), self.column_major()),))
            .into_pyobject(py)?
            .into_any()
            .unbind())
    }

    #[getter]
    fn dims(&self) -> Vec<usize> {
        (0..self.value.dimension())
            .map(|i| self.value.shape()[i])
            .collect()
    }

    #[getter]
    fn size(&self) -> usize {
        self.value.len()
    }

    #[getter]
    fn column_major(&self) -> bool {
        self.value.storage_order() == StorageOrder::ColumnMajor
    }

    fn strides(&self) -> Vec<usize> {
        (0..self.value.dimension())
            .map(|i| self.value.offsets()[i])
            .collect()
    }

    fn index_of(&self, py: Python<'_>, indices: Vec<BigInt>) -> Transport<usize> {
        transport(py.detach(|| self.checked_index(indices)))
    }

    fn vector_of(&self, py: Python<'_>, index: BigInt) -> Transport<Vec<usize>> {
        transport(py.detach(|| self.checked_vector(index)))
    }

    fn indices_of(&self, py: Python<'_>, vectors: Vec<Vec<BigInt>>) -> Transport<Vec<usize>> {
        transport(py.detach(|| {
            vectors
                .into_iter()
                .map(|vector| self.checked_index(vector))
                .collect()
        }))
    }
}

#[pyclass(frozen, module = "ospf_python._native")]
pub struct RationalMultiArray {
    value: RustMultiArray<BigRational, DynShape>,
}

#[pyclass(frozen, module = "ospf_python._native")]
pub struct MultiArray {
    shape: Shape,
    value: Mutex<Option<RustMultiArray<Py<PyAny>, DynShape>>>,
    restore_pending: AtomicBool,
}

impl MultiArray {
    fn full(shape: Shape, value: &Bound<'_, PyAny>) -> Result<Self, Failure> {
        let size = shape.value.len();
        if size
            .checked_mul(std::mem::size_of::<Py<PyAny>>())
            .is_none_or(|bytes| bytes > isize::MAX as usize)
        {
            return Err(Failure::binding(
                "OVERFLOW",
                "填充存储字节数超出原生容量 / Filled storage bytes exceed native capacity",
            ));
        }
        let mut values = Vec::new();
        values.try_reserve_exact(size).map_err(|_| {
            let mut failure = Failure::binding(
                "APPLICATION_ERROR",
                "无法分配填充存储 / Unable to allocate filled storage",
            );
            failure.error_class = "RESOURCE";
            failure
        })?;
        // 仅构造逐槽强引用，按存储顺序交给上游直接接管；不执行元素协议或复制元素。 / Build per-slot strong references for upstream buffer adoption, without invoking protocols or copying elements.
        values.resize_with(size, || value.clone().unbind());
        let column_major = shape.column_major();
        Self::create(values, shape, column_major)
    }

    fn create(values: Vec<Py<PyAny>>, shape: Shape, column_major: bool) -> Result<Self, Failure> {
        if values.len() != shape.value.len() {
            return Err(Failure::input(
                "元素数与形状不匹配 / Element count does not match shape",
            ));
        }
        let value = MultiArrayBuilder::from_list_with_order(
            shape.value.clone(),
            values,
            access(column_major),
        );
        Ok(Self {
            shape,
            value: Mutex::new(Some(value)),
            restore_pending: AtomicBool::new(false),
        })
    }

    fn pickle_reduction(&self, py: Python<'_>, mutable: bool) -> PyResult<Py<PyAny>> {
        let values = self
            .snapshot(py, self.shape.column_major())
            .map_err(pickle_error)?;
        let restore = py.import("ospf_python._native")?.getattr(if mutable {
            "_unpickle_mutable_multiarray"
        } else {
            "_unpickle_multiarray"
        })?;
        // 元数据先构造空壳；pickle/deepcopy 的 memo 在恢复元素前登记句柄，保留回边。 / Memoize the metadata-only shell before restoring element state, preserving back edges.
        Ok((
            restore,
            ((1u32, self.shape.dims(), self.shape.column_major()),),
            values,
        )
            .into_pyobject(py)?
            .into_any()
            .unbind())
    }

    fn restore_state(&self, state: &Bound<'_, PyAny>) -> PyResult<()> {
        if !state.is_exact_instance_of::<PyList>() {
            return Err(PyValueError::new_err(
                "数组 pickle 状态必须为内置 list / Array pickle state must be a built-in list",
            ));
        }
        let items = state.cast::<PyList>()?;
        if items.len() != self.shape.size() {
            return Err(PyValueError::new_err(
                "数组 pickle 元素数不匹配 / Array pickle element count mismatch",
            ));
        }
        let values = items.iter().map(Bound::unbind).collect();
        let restored = Self::create(values, self.shape.clone(), self.shape.column_major())
            .map_err(pickle_error)?;
        let restored_value = restored
            .value
            .into_inner()
            .unwrap_or_else(|error| error.into_inner());
        {
            let mut guard = self.value.lock().unwrap_or_else(|error| error.into_inner());
            if !self.restore_pending.load(Ordering::Relaxed) {
                // 已发布/GC 清理的容器不能借协议再次初始化。 / Published or GC-cleared storage cannot be reinitialized through the protocol.
                return Err(PyValueError::new_err(
                    "数组 pickle 状态已终结 / Array pickle state is already finalized",
                ));
            }
            *guard = restored_value;
            self.restore_pending.store(false, Ordering::Relaxed);
        }
        Ok(())
    }

    fn cleared() -> Failure {
        Failure::binding(
            "FAILED_PRECONDITION",
            "数组已由垃圾回收清理 / Array has been cleared by garbage collection",
        )
    }

    fn snapshot(&self, py: Python<'_>, column_major: bool) -> Result<Vec<Py<PyAny>>, Failure> {
        // 锁内仅借用和增加引用，不执行 Python 或释放 GIL。 / Only borrow and incref under the lock; no Python calls or GIL release.
        let guard = self.value.lock().unwrap_or_else(|error| error.into_inner());
        let value = guard.as_ref().ok_or_else(Self::cleared)?;
        let values = storage_snapshot(py, value, None, column_major, usize::MAX);
        drop(guard);
        checked_snapshot(values, &self.shape)
    }

    fn region_snapshot(
        &self,
        py: Python<'_>,
        region: &MultiArrayView,
        column_major: bool,
    ) -> Result<Vec<Py<PyAny>>, Failure> {
        region.check_source(&self.shape)?;
        let guard = self.value.lock().unwrap_or_else(|error| error.into_inner());
        let value = guard.as_ref().ok_or_else(Self::cleared)?;
        let values = storage_snapshot(py, value, Some(region), column_major, usize::MAX);
        drop(guard);
        checked_snapshot(values, &region.shape)
    }
}

#[pymethods]
impl MultiArray {
    fn __reduce__(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        self.pickle_reduction(py, false)
    }

    fn __setstate__(&self, state: &Bound<'_, PyAny>) -> PyResult<()> {
        self.restore_state(state)
    }

    #[getter]
    fn shape(&self) -> Shape {
        self.shape.clone()
    }

    fn at(&self, py: Python<'_>, indices: Vec<BigInt>) -> Transport<Py<PyAny>> {
        transport((|| {
            let index = self.shape.checked_index(indices)?;
            let guard = self.value.lock().unwrap_or_else(|error| error.into_inner());
            let value = guard.as_ref().ok_or_else(Self::cleared)?;
            Ok(value[index].clone_ref(py))
        })())
    }

    /// 按完整坐标批量读取，供公共 `at_many` 原样保留。 / Batch read by complete coordinates, so the public `at_many` can be preserved verbatim.
    ///
    /// 与 `set_many` 不同，读取允许重复坐标：重复读不是错误。
    /// Unlike `set_many`, repeated coordinates are allowed here; reading twice is not an error.
    fn at_many(&self, py: Python<'_>, indices: Vec<Vec<BigInt>>) -> Transport<Vec<Py<PyAny>>> {
        transport((|| {
            let indexes = indices
                .into_iter()
                .map(|coordinate| self.shape.checked_index(coordinate))
                .collect::<Result<Vec<_>, Failure>>()?;
            let guard = self.value.lock().unwrap_or_else(|error| error.into_inner());
            let value = guard.as_ref().ok_or_else(Self::cleared)?;
            Ok(indexes
                .into_iter()
                .map(|index| value[index].clone_ref(py))
                .collect())
        })())
    }

    /// 旧 `get` 的绑定侧等价物，按原始 Python 顺序返回叶值。
    /// Binding-side equivalent of the legacy `get`, returning the leaf in the original Python order.
    fn get(&self, py: Python<'_>, indices: Vec<BigInt>) -> Transport<Py<PyAny>> {
        self.at(py, indices)
    }

    fn flatten(&self, py: Python<'_>, column_major: bool) -> Transport<Vec<Py<PyAny>>> {
        transport(self.snapshot(py, column_major))
    }

    fn to_storage_order(&self, py: Python<'_>, column_major: bool) -> Transport<Self> {
        transport((|| {
            let shape = Shape {
                value: DynShape::new_with_order(self.shape.dims(), order(column_major)),
            };
            Self::create(self.snapshot(py, column_major)?, shape, column_major)
        })())
    }

    fn reshape(&self, py: Python<'_>, shape: &Shape) -> Transport<Self> {
        transport((|| {
            if self.shape.value.len() != shape.value.len() {
                return Err(Failure::input(
                    "重塑必须保持元素数 / Reshape must preserve element count",
                ));
            }
            if self.shape.value.storage_order() != shape.value.storage_order() {
                return Err(Failure::input(
                    "重塑不能隐式变更存储顺序 / Reshape cannot implicitly change storage order",
                ));
            }
            Self::create(
                self.snapshot(py, self.shape.column_major())?,
                shape.clone(),
                shape.column_major(),
            )
        })())
    }

    fn transpose(&self, py: Python<'_>) -> Transport<Self> {
        let shape = reversed_shape(&self.shape);
        // 反转轴并翻转布局保持物理序列；由上游 builder 直接接管。 / Reversing axes and layout preserves physical order for the upstream builder.
        transport(
            self.snapshot(py, self.shape.column_major())
                .and_then(|values| Self::create(values, shape.clone(), shape.column_major())),
        )
    }

    #[pyo3(signature = (*, callback, column_major, output_shape=None))]
    fn mapped(
        &self,
        py: Python<'_>,
        callback: &Bound<'_, PyAny>,
        column_major: bool,
        output_shape: Option<&Shape>,
    ) -> PyResult<Transport<Self>> {
        match self.snapshot(py, column_major) {
            Ok(values) => map_snapshot(
                py,
                values,
                &self.shape,
                callback,
                column_major,
                output_shape,
            ),
            Err(error) => Ok(transport(Err(error))),
        }
    }

    #[pyo3(signature = (*, indices, callback, region=None))]
    fn mapped_at(
        &self,
        py: Python<'_>,
        indices: Vec<BigInt>,
        callback: &Bound<'_, PyAny>,
        region: Option<&MultiArrayView>,
    ) -> PyResult<Transport<Py<PyAny>>> {
        // 受检读取仅克隆一个槽位；返回后锁已释放，才调用用户函数。 / Checked reads clone one slot and release the lock before calling Python.
        let input = match region {
            Some(region) => self.region_at(py, region, indices),
            None => self.at(py, indices),
        };
        match input {
            (_, Some(error)) => Ok(transport(Err(error))),
            (Some(item), None) => Ok(transport(mapped_value(py, callback, item)?)),
            (None, None) => Ok(transport(Err(Failure::binding(
                "APPLICATION_ERROR",
                "原生读取缺少成功值 / Native read lacks a success value",
            )))),
        }
    }

    #[pyo3(signature = (*, callback, column_major, region=None))]
    fn reduced(
        &self,
        py: Python<'_>,
        callback: &Bound<'_, PyAny>,
        column_major: bool,
        region: Option<&MultiArrayView>,
    ) -> PyResult<Transport<Py<PyAny>>> {
        let snapshot = match region {
            Some(region) => self.region_snapshot(py, region, column_major),
            None => self.snapshot(py, column_major),
        };
        match snapshot {
            Ok(values) => reduce_snapshot(py, values, callback),
            Err(error) => Ok(transport(Err(error))),
        }
    }

    #[pyo3(signature = (*, region=None))]
    fn to_list(
        &self,
        py: Python<'_>,
        region: Option<&MultiArrayView>,
    ) -> PyResult<Transport<Py<PyAny>>> {
        let (snapshot, shape) = match region {
            Some(region) => (self.region_snapshot(py, region, false), &region.shape),
            None => (self.snapshot(py, false), &self.shape),
        };
        match snapshot {
            Ok(values) => nest_snapshot(py, values, shape),
            Err(error) => Ok(transport(Err(error))),
        }
    }

    fn region_at(
        &self,
        py: Python<'_>,
        region: &MultiArrayView,
        indices: Vec<BigInt>,
    ) -> Transport<Py<PyAny>> {
        transport((|| {
            let index = region.source_index(&self.shape, indices)?;
            let guard = self.value.lock().unwrap_or_else(|error| error.into_inner());
            let value = guard.as_ref().ok_or_else(Self::cleared)?;
            Ok(value[index].clone_ref(py))
        })())
    }

    fn region_flatten(
        &self,
        py: Python<'_>,
        region: &MultiArrayView,
        column_major: bool,
    ) -> Transport<Vec<Py<PyAny>>> {
        transport(self.region_snapshot(py, region, column_major))
    }

    fn region_materialize(&self, py: Python<'_>, region: &MultiArrayView) -> Transport<Self> {
        transport(
            self.region_snapshot(py, region, region.shape.column_major())
                .and_then(|values| {
                    Self::create(values, region.shape.clone(), region.shape.column_major())
                }),
        )
    }

    fn region_transpose(&self, py: Python<'_>, region: &MultiArrayView) -> Transport<Self> {
        let shape = reversed_shape(&region.shape);
        transport(
            self.region_snapshot(py, region, region.shape.column_major())
                .and_then(|values| Self::create(values, shape.clone(), shape.column_major())),
        )
    }

    #[pyo3(signature = (*, region, callback, column_major, output_shape=None))]
    fn region_mapped(
        &self,
        py: Python<'_>,
        region: &MultiArrayView,
        callback: &Bound<'_, PyAny>,
        column_major: bool,
        output_shape: Option<&Shape>,
    ) -> PyResult<Transport<Self>> {
        match self.region_snapshot(py, region, column_major) {
            Ok(values) => map_snapshot(
                py,
                values,
                &region.shape,
                callback,
                column_major,
                output_shape,
            ),
            Err(error) => Ok(transport(Err(error))),
        }
    }

    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        let guard = self.value.lock().unwrap_or_else(|error| error.into_inner());
        if let Some(value) = guard.as_ref() {
            // 每个存储槽都是真实强引用，重复元素也须逐次访问。 / Visit each owned slot, including duplicate references.
            for index in 0..self.shape.value.len() {
                visit.call(&value[index])?;
            }
        }
        Ok(())
    }

    fn __clear__(&self) {
        let value = {
            let mut guard = self.value.lock().unwrap_or_else(|error| error.into_inner());
            self.restore_pending.store(false, Ordering::Relaxed);
            guard.take()
        };
        // 先发布已清理状态并解锁，再触发可能重入的 Python 析构。 / Publish cleared state and unlock before potentially reentrant Python destruction.
        drop(value);
    }
}

#[pyfunction]
#[pyo3(signature = (*, values, shape, column_major))]
pub fn _create_multiarray(
    values: Vec<Py<PyAny>>,
    shape: &Shape,
    column_major: bool,
) -> Transport<MultiArray> {
    transport(MultiArray::create(values, shape.clone(), column_major))
}

#[pyfunction]
#[pyo3(signature = (*, shape, value))]
pub fn _full_multiarray(shape: &Shape, value: &Bound<'_, PyAny>) -> Transport<MultiArray> {
    transport(MultiArray::full(shape.clone(), value))
}

#[pyfunction]
#[pyo3(signature = (*, data, shape))]
pub fn _multiarray_from_nested(data: &Bound<'_, PyAny>, shape: &Shape) -> Transport<MultiArray> {
    transport(
        nested_values(data, shape)
            .and_then(|values| MultiArray::create(values, shape.clone(), false)),
    )
}

#[pyfunction]
#[pyo3(signature = (*, data, shape))]
pub fn _mutable_multiarray_from_nested(
    data: &Bound<'_, PyAny>,
    shape: &Shape,
) -> Transport<MutableMultiArray> {
    transport(nested_values(data, shape).and_then(|values| {
        MultiArray::create(values, shape.clone(), false).map(|inner| MutableMultiArray { inner })
    }))
}

#[pyclass(frozen, module = "ospf_python._native")]
pub struct MutableMultiArray {
    inner: MultiArray,
}

impl MutableMultiArray {
    fn replace(&self, updates: Vec<(usize, Py<PyAny>)>) -> Result<(), Failure> {
        let mut old_values = Vec::with_capacity(updates.len());
        {
            let mut guard = self
                .inner
                .value
                .lock()
                .unwrap_or_else(|error| error.into_inner());
            let value = guard.as_mut().ok_or_else(MultiArray::cleared)?;
            for (index, item) in updates {
                old_values.push(std::mem::replace(&mut value[index], item));
            }
        }
        // 整批发布后解锁再 decref；元素析构可以读取或继续写入。 / Publish the whole batch and unlock before decref; destructors may read or write again.
        drop(old_values);
        Ok(())
    }
}

#[pymethods]
impl MutableMultiArray {
    fn __reduce__(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        self.inner.pickle_reduction(py, true)
    }

    fn __setstate__(&self, state: &Bound<'_, PyAny>) -> PyResult<()> {
        self.inner.restore_state(state)
    }

    #[getter]
    fn shape(&self) -> Shape {
        self.inner.shape()
    }

    fn at(&self, py: Python<'_>, indices: Vec<BigInt>) -> Transport<Py<PyAny>> {
        self.inner.at(py, indices)
    }

    fn flatten(&self, py: Python<'_>, column_major: bool) -> Transport<Vec<Py<PyAny>>> {
        self.inner.flatten(py, column_major)
    }

    fn set_many(&self, updates: Vec<(Vec<BigInt>, Py<PyAny>)>) -> Transport<()> {
        transport_unit((|| {
            let mut seen = HashSet::with_capacity(updates.len());
            let updates = updates.into_iter().map(|(indices, item)| {
                let index = self.inner.shape.checked_index(indices)?;
                if !seen.insert(index) {
                    return Err(Failure::input("批次不能重复写入同一坐标 / Batch cannot write the same coordinate twice"));
                }
                Ok((index, item))
            }).collect::<Result<Vec<_>, Failure>>()?;
            self.replace(updates)
        })())
    }

    fn to_immutable(&self, py: Python<'_>) -> Transport<MultiArray> {
        transport(
            self.inner
                .snapshot(py, self.inner.shape.column_major())
                .and_then(|values| {
                    MultiArray::create(
                        values,
                        self.inner.shape.clone(),
                        self.inner.shape.column_major(),
                    )
                }),
        )
    }

    fn transpose(&self, py: Python<'_>) -> Transport<MultiArray> {
        self.inner.transpose(py)
    }

    #[pyo3(signature = (*, callback, column_major, output_shape=None))]
    fn mapped(
        &self,
        py: Python<'_>,
        callback: &Bound<'_, PyAny>,
        column_major: bool,
        output_shape: Option<&Shape>,
    ) -> PyResult<Transport<MultiArray>> {
        self.inner.mapped(py, callback, column_major, output_shape)
    }

    fn region_at(
        &self,
        py: Python<'_>,
        region: &MultiArrayView,
        indices: Vec<BigInt>,
    ) -> Transport<Py<PyAny>> {
        self.inner.region_at(py, region, indices)
    }

    #[pyo3(signature = (*, indices, callback, region=None))]
    fn mapped_at(
        &self,
        py: Python<'_>,
        indices: Vec<BigInt>,
        callback: &Bound<'_, PyAny>,
        region: Option<&MultiArrayView>,
    ) -> PyResult<Transport<Py<PyAny>>> {
        self.inner.mapped_at(py, indices, callback, region)
    }

    #[pyo3(signature = (*, callback, column_major, region=None))]
    fn reduced(
        &self,
        py: Python<'_>,
        callback: &Bound<'_, PyAny>,
        column_major: bool,
        region: Option<&MultiArrayView>,
    ) -> PyResult<Transport<Py<PyAny>>> {
        self.inner.reduced(py, callback, column_major, region)
    }

    #[pyo3(signature = (*, region=None))]
    fn to_list(
        &self,
        py: Python<'_>,
        region: Option<&MultiArrayView>,
    ) -> PyResult<Transport<Py<PyAny>>> {
        self.inner.to_list(py, region)
    }

    fn region_flatten(
        &self,
        py: Python<'_>,
        region: &MultiArrayView,
        column_major: bool,
    ) -> Transport<Vec<Py<PyAny>>> {
        self.inner.region_flatten(py, region, column_major)
    }

    fn region_materialize(&self, py: Python<'_>, region: &MultiArrayView) -> Transport<MultiArray> {
        self.inner.region_materialize(py, region)
    }

    fn region_transpose(&self, py: Python<'_>, region: &MultiArrayView) -> Transport<MultiArray> {
        self.inner.region_transpose(py, region)
    }

    #[pyo3(signature = (*, region, callback, column_major, output_shape=None))]
    fn region_mapped(
        &self,
        py: Python<'_>,
        region: &MultiArrayView,
        callback: &Bound<'_, PyAny>,
        column_major: bool,
        output_shape: Option<&Shape>,
    ) -> PyResult<Transport<MultiArray>> {
        self.inner
            .region_mapped(py, region, callback, column_major, output_shape)
    }

    fn region_set_many(
        &self,
        region: &MultiArrayView,
        updates: Vec<(Vec<BigInt>, Py<PyAny>)>,
    ) -> Transport<()> {
        transport_unit((|| {
            let mut seen = HashSet::with_capacity(updates.len());
            let updates = updates.into_iter().map(|(indices, item)| {
                let index = region.source_index(&self.inner.shape, indices)?;
                if !seen.insert(index) {
                    return Err(Failure::input("批次不能重复写入同一坐标 / Batch cannot write the same coordinate twice"));
                }
                Ok((index, item))
            }).collect::<Result<Vec<_>, Failure>>()?;
            self.replace(updates)
        })())
    }

    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        self.inner.__traverse__(visit)
    }

    fn __clear__(&self) {
        self.inner.__clear__();
    }
}

#[pyclass(frozen, module = "ospf_python._native")]
#[derive(Clone)]
pub struct MultiArrayView {
    source_shape: Shape,
    shape: Shape,
    offsets: Vec<usize>,
}

pub(crate) struct ViewCopyPlan {
    region: MultiArrayView,
}

pub(crate) struct ViewCopyDescriptor {
    pub(crate) start: usize,
    pub(crate) dims: Vec<usize>,
    pub(crate) strides: Vec<usize>,
    pub(crate) size: usize,
}

impl ViewCopyPlan {
    #[cfg(test)]
    pub(crate) fn create(
        dims: Vec<BigInt>,
        offsets: Vec<BigInt>,
        column_major: bool,
    ) -> Result<Self, Failure> {
        let source = Shape::create(dims, column_major)?;
        Ok(Self {
            region: MultiArrayView::with_extent(&source, Some(offsets), None)?,
        })
    }

    pub(crate) fn from_dense(
        dims: Vec<usize>,
        offsets: Vec<usize>,
        column_major: bool,
    ) -> Result<Self, Failure> {
        Ok(Self {
            region: MultiArrayView::with_dense_extent(
                Shape::from_dense(dims.into_iter().map(Some), column_major)?,
                offsets,
            )?,
        })
    }

    pub(crate) fn dims(&self) -> Vec<usize> {
        self.region.shape.dims()
    }

    pub(crate) fn source_size(&self) -> usize {
        self.region.source_shape.size()
    }

    pub(crate) fn identity(&self) -> bool {
        self.region.offsets.iter().all(|offset| *offset == 0)
    }

    pub(crate) fn descriptor(&self) -> Result<ViewCopyDescriptor, Failure> {
        let target = &self.region.shape.value;
        let source = &self.region.source_shape.value;
        let start = source
            .index_of(&self.region.offsets)
            .map_err(index_failure)?;
        let mut axes = (0..target.dimension())
            .filter(|axis| target.shape()[*axis] > 1)
            .collect::<Vec<_>>();
        // 按固定 Rust 的目标步长排序，只发布存储描述符，不重写线性索引公式。
        // Order axes by pinned Rust target strides, publishing storage metadata rather than another linear-index formula.
        axes.sort_unstable_by_key(|axis| std::cmp::Reverse(target.offsets()[*axis]));
        let (dims, strides) = if axes.is_empty() {
            (vec![1], vec![1])
        } else {
            (
                axes.iter().map(|axis| target.shape()[*axis]).collect(),
                axes.iter().map(|axis| source.offsets()[*axis]).collect(),
            )
        };
        Ok(ViewCopyDescriptor {
            start,
            dims,
            strides,
            size: target.len(),
        })
    }

    pub(crate) fn gather(
        &self,
        py: Python<'_>,
        indexer: Option<&Bound<'_, PyAny>>,
    ) -> PyResult<Transport<Vec<usize>>> {
        let mut output = match nested_capacity(self.region.shape.size()) {
            Ok(values) => values,
            Err(error) => return Ok(transport(Err(error))),
        };
        // 本次计划已冻结并检查范围；只投影上游产生的坐标，不逐槽重复 BigInt/源形状验证。
        // This immutable plan is already range-checked; project upstream coordinates without per-slot BigInt/source-shape revalidation.
        for (ordinal, mut indices) in self
            .region
            .shape
            .value
            .indices_with_order(access(self.region.shape.column_major()))
            .enumerate()
        {
            if ordinal.is_multiple_of(4096) {
                py.check_signals()?;
            }
            let offset = if let Some(indexer) = indexer {
                let arguments = PyTuple::new(
                    py,
                    indices
                        .into_iter()
                        .zip(&self.region.offsets)
                        .map(|(index, offset)| index + offset),
                )?;
                let offset = indexer.call(arguments, None)?;
                if offset.is_instance_of::<PyBool>() {
                    return Ok(transport(Err(Failure::input(
                        "布局索引不能是 bool / Layout indices must not be bool",
                    ))));
                }
                // SAFETY: 标准整数协议返回拥有的引用，不读取原始缓冲指针。 / Standard integer protocol returns an owned reference without reading raw buffer pointers.
                let mut offset = unsafe {
                    Bound::from_owned_ptr_or_err(py, pyo3::ffi::PyNumber_Index(offset.as_ptr()))
                }?
                .extract::<BigInt>()?;
                if offset < BigInt::from(0) {
                    offset += self.source_size();
                }
                match offset
                    .to_usize()
                    .filter(|offset| *offset < self.source_size())
                {
                    Some(offset) => offset,
                    None => return Ok(transport(Err(range_failure()))),
                }
            } else {
                for (index, offset) in indices.iter_mut().zip(&self.region.offsets) {
                    *index += offset;
                }
                match self.region.source_shape.value.index_of(&indices) {
                    Ok(offset) => offset,
                    Err(error) => return Ok(transport(Err(index_failure(error)))),
                }
            };
            output.push(offset);
        }
        Ok(transport(Ok(output)))
    }
}

impl MultiArrayView {
    fn with_extent(
        source: &Shape,
        offsets: Option<Vec<BigInt>>,
        shape: Option<&Shape>,
    ) -> Result<Self, Failure> {
        let offsets = offsets.unwrap_or_else(|| vec![0.into(); source.value.dimension()]);
        if let Some(shape) = shape {
            return Self::create(source, offsets, shape);
        }
        if offsets.len() != source.value.dimension() {
            return Err(Failure::input(
                "偏移维数必须匹配源 / Offset rank must match the source",
            ));
        }
        Self::with_dense_extent(
            source.clone(),
            offsets
                .into_iter()
                .map(|offset| offset.to_usize().ok_or_else(range_failure))
                .collect::<Result<_, _>>()?,
        )
    }

    fn with_dense_extent(source: Shape, offsets: Vec<usize>) -> Result<Self, Failure> {
        if offsets.len() != source.value.dimension() {
            return Err(Failure::input(
                "偏移维数必须匹配源 / Offset rank must match the source",
            ));
        }
        // 仅计算受检剩余范围；形状、步长及索引仍交固定上游。 / Derive checked remaining extents only; pinned upstream owns shapes, strides and indexing.
        let shape = if offsets.iter().all(|offset| *offset == 0) {
            source.clone()
        } else {
            Shape::from_dense(
                source
                    .dims()
                    .into_iter()
                    .zip(&offsets)
                    .map(|(dim, offset)| {
                        dim.checked_sub(*offset).filter(|remaining| *remaining > 0)
                    }),
                source.column_major(),
            )
            .map_err(|_| range_failure())?
        };
        Ok(Self {
            source_shape: source,
            shape,
            offsets,
        })
    }

    fn create(source: &Shape, offsets: Vec<BigInt>, shape: &Shape) -> Result<Self, Failure> {
        if offsets.len() != source.value.dimension()
            || shape.value.dimension() != source.value.dimension()
            || source.column_major() != shape.column_major()
        {
            return Err(Failure::input(
                "视图维数和存储顺序必须匹配源 / View rank and storage order must match the source",
            ));
        }
        let offsets = offsets
            .into_iter()
            .zip(source.dims())
            .zip(shape.dims())
            .map(|((offset, source_dim), dim)| {
                let offset = offset.to_usize().ok_or_else(range_failure)?;
                if dim > source_dim || offset > source_dim - dim {
                    return Err(range_failure());
                }
                Ok(offset)
            })
            .collect::<Result<Vec<_>, _>>()?;
        Ok(Self {
            source_shape: source.clone(),
            shape: shape.clone(),
            offsets,
        })
    }

    fn check_source(&self, source: &Shape) -> Result<(), Failure> {
        if self.source_shape.dims() != source.dims()
            || self.source_shape.column_major() != source.column_major()
        {
            return Err(Failure::input(
                "视图源形状不匹配 / View source shape mismatch",
            ));
        }
        Ok(())
    }

    fn source_index(&self, source: &Shape, indices: Vec<BigInt>) -> Result<usize, Failure> {
        self.check_source(source)?;
        self.shape.checked_index(indices.clone())?;
        // 仅投影受检坐标；步长及线性索引仍由上游 Shape 计算。 / Project checked coordinates only; upstream Shape computes strides and offsets.
        source.checked_index(
            indices
                .into_iter()
                .zip(&self.offsets)
                .map(|(index, offset)| index + BigInt::from(*offset))
                .collect(),
        )
    }
}

#[pymethods]
impl MultiArrayView {
    fn __reduce__(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        let restore = py
            .import("ospf_python._native")?
            .getattr("_unpickle_multiarray_view")?;
        let metadata = (
            1u32,
            self.source_shape.dims(),
            self.source_shape.column_major(),
            self.offsets.clone(),
            self.shape.dims(),
        );
        Ok((restore, (metadata,))
            .into_pyobject(py)?
            .into_any()
            .unbind())
    }

    #[getter]
    fn shape(&self) -> Shape {
        self.shape.clone()
    }

    #[pyo3(signature = (offsets=None, shape=None))]
    fn subview(&self, offsets: Option<Vec<BigInt>>, shape: Option<&Shape>) -> Transport<Self> {
        transport(
            Self::with_extent(&self.shape, offsets, shape).map(|relative| Self {
                source_shape: self.source_shape.clone(),
                shape: relative.shape,
                offsets: relative
                    .offsets
                    .into_iter()
                    .zip(&self.offsets)
                    .map(|(local, base)| local + base)
                    .collect(),
            }),
        )
    }
}

#[pyfunction]
#[pyo3(signature = (*, values, shape, column_major))]
pub fn _create_mutable_multiarray(
    values: Vec<Py<PyAny>>,
    shape: &Shape,
    column_major: bool,
) -> Transport<MutableMultiArray> {
    transport(
        MultiArray::create(values, shape.clone(), column_major)
            .map(|inner| MutableMultiArray { inner }),
    )
}

#[pyfunction]
#[pyo3(signature = (*, shape, value))]
pub fn _full_mutable_multiarray(
    shape: &Shape,
    value: &Bound<'_, PyAny>,
) -> Transport<MutableMultiArray> {
    transport(MultiArray::full(shape.clone(), value).map(|inner| MutableMultiArray { inner }))
}

#[pyfunction]
#[pyo3(signature = (*, source_shape, offsets=None, shape=None))]
pub fn _create_multiarray_view(
    source_shape: &Shape,
    offsets: Option<Vec<BigInt>>,
    shape: Option<&Shape>,
) -> Transport<MultiArrayView> {
    transport(MultiArrayView::with_extent(source_shape, offsets, shape))
}

impl RationalMultiArray {
    fn create(values: &RationalArray, shape: &Shape, column_major: bool) -> Result<Self, Failure> {
        if values.values.len() != shape.value.len() {
            return Err(Failure::input(
                "元素数与形状不匹配 / Element count does not match shape",
            ));
        }
        Ok(Self {
            value: MultiArrayBuilder::from_list_with_order(
                shape.value.clone(),
                values.values.clone(),
                access(column_major),
            ),
        })
    }

    fn reshape_value(&self, shape: &Shape) -> Result<Self, Failure> {
        if self.value.shape.len() != shape.value.len() {
            return Err(Failure::input(
                "重塑必须保持元素数 / Reshape must preserve element count",
            ));
        }
        if self.value.storage_order() != shape.value.storage_order() {
            return Err(Failure::input(
                "重塑不能隐式变更存储顺序 / Reshape cannot implicitly change storage order",
            ));
        }
        Ok(Self {
            value: self.value.reshape(shape.value.clone()),
        })
    }
}

#[pymethods]
impl RationalMultiArray {
    #[getter]
    fn shape(&self) -> Shape {
        Shape {
            value: self.value.shape.clone(),
        }
    }

    fn at(&self, py: Python<'_>, indices: Vec<BigInt>) -> Transport<Rational> {
        transport(py.detach(|| {
            let shape = self.shape();
            let index = shape.checked_index(indices)?;
            Ok(Rational {
                value: self.value[index].clone(),
            })
        }))
    }

    fn flatten(&self, py: Python<'_>, column_major: bool) -> RationalArray {
        py.detach(|| RationalArray {
            values: self.value.flatten(access(column_major)),
        })
    }

    fn to_storage_order(&self, py: Python<'_>, column_major: bool) -> Self {
        py.detach(|| Self {
            value: self.value.to_storage_order(order(column_major)),
        })
    }

    fn reshape(&self, py: Python<'_>, shape: &Shape) -> Transport<Self> {
        transport(py.detach(|| self.reshape_value(shape)))
    }
}

#[pyfunction]
#[pyo3(signature = (*, dims, column_major))]
pub fn _create_shape(py: Python<'_>, dims: Vec<BigInt>, column_major: bool) -> Transport<Shape> {
    transport(py.detach(|| Shape::create(dims, column_major)))
}

#[pyfunction]
#[pyo3(signature = (*, dims, column_major, indices))]
pub fn _checked_shared_offset(
    py: Python<'_>,
    dims: &Bound<'_, PyTuple>,
    column_major: bool,
    indices: &Bound<'_, PyTuple>,
) -> Transport<(usize, usize)> {
    let dims = match checked_bigint_tuple(
        dims,
        "维度必须为整数 tuple / Dimensions must be an integer tuple",
    ) {
        Ok(dims) => dims,
        Err(error) => return transport(Err(error)),
    };
    let indices = match checked_bigint_tuple(
        indices,
        "索引必须为整数 tuple / Indices must be an integer tuple",
    ) {
        Ok(indices) => indices,
        Err(error) => return transport(Err(error)),
    };
    // 当前元数据、完整坐标校验和大小发布在一次原生调用内完成。 / Validate current metadata, full coordinates and size in one native call.
    transport(py.detach(move || {
        let shape = Shape::create(dims, column_major)?;
        let offset = shape.checked_index(indices)?;
        Ok((offset, shape.value.len()))
    }))
}

/// 只持协议类型、布局常量和 Result 工厂；每次操作重新读取 owner 元数据。 / Retain only protocol types, layout constants and Result factories; reread owner metadata on every operation.
#[pyclass(
    name = "_SharedAccess",
    frozen,
    weakref,
    module = "ospf_python._native"
)]
pub struct SharedAccess {
    shape_types: Py<PyTuple>,
    row_major: Py<PyAny>,
    column_major: Py<PyAny>,
    ndarray_type: Py<PyType>,
    scalar_type: Py<PyType>,
    publication: ResultPublication,
}

impl SharedAccess {
    fn standard_shape_rank(
        &self,
        py: Python<'_>,
        shape: &Bound<'_, PyAny>,
    ) -> (bool, Option<usize>) {
        let shape_type = shape.get_type();
        for (position, kind) in self.shape_types.bind(py).iter().enumerate() {
            if shape_type.is(&kind) {
                // 前四项与 Python 侧 Shape1-4 顺序一致。 / The first four entries mirror Python Shape1-4 order.
                return (true, (position < 4).then_some(position + 1));
            }
        }
        (false, None)
    }

    fn fixed_dimensions<'py>(
        &self,
        py: Python<'py>,
        shape: &Bound<'py, PyAny>,
        rank: usize,
    ) -> PyResult<Result<FixedDimensions<'py>, Failure>> {
        macro_rules! dimension {
            ($name:literal) => {
                match checked_fixed_dimension(shape.getattr(pyo3::intern!(py, $name))?) {
                    Ok(value) => value,
                    Err(failure) => return Ok(Err(failure)),
                }
            };
        }
        Ok(Ok(match rank {
            1 => FixedDimensions::D1([dimension!("d0")]),
            2 => FixedDimensions::D2([dimension!("d0"), dimension!("d1")]),
            3 => FixedDimensions::D3([dimension!("d0"), dimension!("d1"), dimension!("d2")]),
            4 => FixedDimensions::D4([
                dimension!("d0"),
                dimension!("d1"),
                dimension!("d2"),
                dimension!("d3"),
            ]),
            _ => {
                return Ok(Err(Failure::binding(
                    "APPLICATION_ERROR",
                    "不支持的固定形状维数 / Unsupported fixed shape rank",
                )));
            }
        }))
    }

    fn locate<'py>(
        &self,
        py: Python<'py>,
        owner: &Bound<'py, PyAny>,
        indices: &Bound<'py, PyAny>,
        standard_layout: &Bound<'py, PyAny>,
    ) -> PyResult<Transport<(Bound<'py, PyAny>, usize)>> {
        if !standard_layout.is_exact_instance_of::<PyBool>() {
            return Ok(transport(Err(Failure::input(
                "standard_layout 必须为 bool / standard_layout must be bool",
            ))));
        }
        let standard_layout = match standard_layout.extract::<bool>() {
            Ok(value) => value,
            Err(_) => {
                return Ok(transport(Err(Failure::input(
                    "standard_layout 必须为 bool / standard_layout must be bool",
                ))));
            }
        };
        let shape = owner.getattr(pyo3::intern!(py, "_shape"))?;
        let (is_standard_shape, fixed_rank) = self.standard_shape_rank(py, &shape);
        if !is_standard_shape && !standard_layout {
            return Ok(transport(Err(Failure::input(
                "自定义形状必须显式确认标准布局 / Custom shapes require explicit standard-layout confirmation",
            ))));
        }
        let fixed_dimensions = match fixed_rank {
            Some(rank) => match self.fixed_dimensions(py, &shape, rank)? {
                Ok(dimensions) => Some(dimensions),
                Err(failure) => return Ok(transport(Err(failure))),
            },
            None => None,
        };
        let dynamic_dimensions = if fixed_dimensions.is_none() {
            let dims = shape.getattr(pyo3::intern!(py, "dims"))?;
            if !dims.is_exact_instance_of::<PyTuple>() {
                return Ok(transport(Err(Failure::input(
                    "维度必须为整数 tuple / Dimensions must be an integer tuple",
                ))));
            }
            match checked_bigint_tuple(
                dims.cast::<PyTuple>()?,
                "维度必须为整数 tuple / Dimensions must be an integer tuple",
            ) {
                Ok(dims) => Some(dims),
                Err(failure) => return Ok(transport(Err(failure))),
            }
        } else {
            None
        };
        let fixed_indices = if fixed_dimensions.is_some() {
            match validated_fixed_items(indices) {
                Ok(indices) => Some(indices),
                Err(failure) => return Ok(transport(Err(failure))),
            }
        } else {
            None
        };
        let dynamic_indices = if fixed_dimensions.is_none() {
            if !indices.is_exact_instance_of::<PyTuple>() {
                return Ok(transport(Err(Failure::input(
                    "索引必须为整数 tuple / Indices must be an integer tuple",
                ))));
            }
            match checked_bigint_tuple(
                indices.cast::<PyTuple>()?,
                "索引必须为整数 tuple / Indices must be an integer tuple",
            ) {
                Ok(indices) => Some(indices),
                Err(failure) => return Ok(transport(Err(failure))),
            }
        } else {
            None
        };
        let storage_order = shape.getattr(pyo3::intern!(py, "storage_order"))?;
        let column_major = if storage_order.is(self.column_major.bind(py)) {
            true
        } else if storage_order.is(self.row_major.bind(py)) {
            false
        } else {
            return Ok(transport(Err(Failure::input(
                "需要存储顺序 / Storage order required",
            ))));
        };
        let location = match (
            fixed_dimensions,
            fixed_indices,
            dynamic_dimensions,
            dynamic_indices,
        ) {
            (Some(dimensions), Some(indices), None, None) => {
                dimensions.locate(indices, column_major)
            }
            (None, None, Some(dims), Some(indices)) => {
                Shape::create(dims, column_major).and_then(|shape| {
                    shape
                        .checked_index(indices)
                        .map(|offset| (offset, shape.value.len()))
                })
            }
            _ => Err(Failure::binding(
                "APPLICATION_ERROR",
                "共享形状协议不一致 / Shared shape protocol mismatch",
            )),
        };
        let (offset, size) = match location {
            Ok(location) => location,
            Err(failure) => return Ok(transport(Err(failure))),
        };
        let data = owner.getattr(pyo3::intern!(py, "_data"))?;
        if !data.get_type().is_subclass(self.ndarray_type.bind(py))? {
            return Ok(transport(Err(Failure::input(
                "共享存储必须为 ndarray / Shared storage must be an ndarray",
            ))));
        }
        let ndim = data
            .getattr(pyo3::intern!(py, "ndim"))?
            .extract::<usize>()?;
        let data_size = data
            .getattr(pyo3::intern!(py, "size"))?
            .extract::<usize>()?;
        if ndim != 1 || data_size != size {
            return Ok(transport(Err(Failure::input(
                "共享存储必须是一维且与形状大小一致 / Shared storage must be one-dimensional and match the shape size",
            ))));
        }
        Ok(transport(Ok((data, offset))))
    }
}

#[pymethods]
impl SharedAccess {
    #[new]
    #[pyo3(signature = (
        *,
        shape_types,
        row_major,
        column_major,
        ndarray_type,
        scalar_type,
        success,
        failure
    ))]
    fn new(
        shape_types: Py<PyTuple>,
        row_major: Py<PyAny>,
        column_major: Py<PyAny>,
        ndarray_type: Py<PyType>,
        scalar_type: Py<PyType>,
        success: Py<PyAny>,
        failure: Py<PyAny>,
    ) -> Self {
        Self {
            shape_types,
            row_major,
            column_major,
            ndarray_type,
            scalar_type,
            publication: ResultPublication::new(
                success,
                failure,
                "缺少共享访问结果 / Missing shared access result",
            ),
        }
    }

    #[pyo3(signature = (*, owner, indices, standard_layout))]
    fn read(
        &self,
        py: Python<'_>,
        owner: &Bound<'_, PyAny>,
        indices: &Bound<'_, PyAny>,
        standard_layout: &Bound<'_, PyAny>,
    ) -> PyResult<Py<PyAny>> {
        let (location, failure) = self.locate(py, owner, indices, standard_layout)?;
        let payload = match (location, failure) {
            (Some((data, offset)), None) => {
                let leaf = data.get_item(offset)?;
                let leaf = if leaf.get_type().is_subclass(self.scalar_type.bind(py))? {
                    leaf.call_method0(pyo3::intern!(py, "item"))?
                } else {
                    leaf
                };
                transport(Ok(leaf.unbind()))
            }
            (_, Some(failure)) => transport(Err(failure)),
            _ => transport(Err(Failure::binding(
                "APPLICATION_ERROR",
                "缺少共享读取位置 / Missing shared read location",
            ))),
        };
        self.publication.publish(py, payload)
    }

    #[pyo3(signature = (*, owner, indices, value, standard_layout))]
    fn write(
        &self,
        py: Python<'_>,
        owner: &Bound<'_, PyAny>,
        indices: &Bound<'_, PyAny>,
        value: &Bound<'_, PyAny>,
        standard_layout: &Bound<'_, PyAny>,
    ) -> PyResult<Py<PyAny>> {
        let (location, failure) = self.locate(py, owner, indices, standard_layout)?;
        let payload = match (location, failure) {
            (Some((data, offset)), None) => {
                data.set_item(offset, value)?;
                transport(Ok(py.None()))
            }
            (_, Some(failure)) => transport(Err(failure)),
            _ => transport(Err(Failure::binding(
                "APPLICATION_ERROR",
                "缺少共享写入位置 / Missing shared write location",
            ))),
        };
        self.publication.publish(py, payload)
    }

    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        visit.call(&self.shape_types)?;
        visit.call(&self.row_major)?;
        visit.call(&self.column_major)?;
        visit.call(&self.ndarray_type)?;
        visit.call(&self.scalar_type)?;
        self.publication.traverse(visit)
    }
}

/// 存储重塑只改变元数据；不构造假叶或截断/补值。 / Storage reshape changes metadata only, without dummy leaves, truncation or filling.
#[pyfunction]
#[pyo3(signature = (*, count, dims))]
pub fn _reshape_storage_shape(count: BigInt, dims: Vec<BigInt>) -> Transport<Vec<usize>> {
    transport((|| {
        if dims.iter().any(|dim| *dim > BigInt::from(isize::MAX)) {
            return Err(Failure::binding(
                "OVERFLOW",
                "重塑维度超出原生容量 / Reshape dimension exceeds native capacity",
            ));
        }
        let count = count
            .to_usize()
            .filter(|count| *count <= isize::MAX as usize)
            .ok_or_else(|| {
                Failure::binding(
                    "OVERFLOW",
                    "存储大小超出原生容量 / Storage size exceeds native capacity",
                )
            })?;
        let target = Shape::create(dims, false)?;
        if target.size() != count {
            return Err(Failure::input(
                "重塑必须保持实际存储元素数 / Reshape must preserve actual storage element count",
            ));
        }
        Ok(vec![target.size()])
    })())
}

#[cfg(test)]
thread_local! {
    static FLATTEN_PLAN_COUNT: std::cell::Cell<usize> = const { std::cell::Cell::new(0) };
}

fn pinned_flatten_length(count: usize) -> usize {
    #[cfg(test)]
    FLATTEN_PLAN_COUNT.with(|calls| calls.set(calls.get() + 1));
    RustShape1::<StorageOrder>::new_with(count).len()
}

/// 仅发布一维元数据，超大正计数不承诺上游索引容量。 / Publish one-dimensional metadata; huge positive counts do not promise upstream indexing capacity.
#[pyfunction]
pub fn _flatten_storage_shape(count: BigInt) -> Transport<Vec<BigInt>> {
    transport((|| {
        if count <= BigInt::from(0) {
            return Err(Failure::input(
                "展平形状大小必须为正 / Flatten shape size must be positive",
            ));
        }
        if let Some(count) = count
            .to_usize()
            .filter(|count| *count <= isize::MAX as usize)
        {
            Ok(vec![BigInt::from(pinned_flatten_length(count))])
        } else {
            // 旧公共稀疏元数据可大于真实缓冲，不为这次复制分配虚构槽。 / Legacy sparse metadata can exceed the real buffer; never allocate fictitious slots for this copy.
            Ok(vec![count])
        }
    })())
}

/// 由 NumPy 自身复制任意 dtype，不借用或解码叶。 / Let NumPy copy any dtype without borrowing or decoding leaves.
pub(crate) fn copy_storage<'py>(data: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
    if data.is_exact_instance_of::<PyUntypedArray>() {
        let array = data.cast::<PyUntypedArray>()?;
        // SAFETY: 附着解释器内的已验证 ndarray；新引用由 Bound 接管，错误保留 NumPy 原异常。 / Attached interpreter, checked ndarray; Bound owns the new reference and retains NumPy errors.
        unsafe {
            Bound::from_owned_ptr_or_err(
                data.py(),
                PY_ARRAY_API.PyArray_NewCopy(
                    data.py(),
                    array.as_array_ptr(),
                    NPY_ORDER::NPY_CORDER,
                ),
            )
        }
    } else {
        data.call_method0(pyo3::intern!(data.py(), "copy"))
    }
}

fn call_two<'py>(
    callable: &Bound<'py, PyAny>,
    left: &Bound<'py, PyAny>,
    right: &Bound<'py, PyAny>,
) -> PyResult<Bound<'py, PyAny>> {
    let args = [left.as_ptr(), right.as_ptr()];
    // SAFETY: both arguments are live borrowed references; Vectorcall owns the returned reference and reports Python errors normally.
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

fn call_zero<'py>(callable: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
    // SAFETY: no positional or keyword arguments are passed; Vectorcall owns the returned reference and reports Python errors normally.
    unsafe {
        Bound::from_owned_ptr_or_err(
            callable.py(),
            pyo3::ffi::PyObject_Vectorcall(
                callable.as_ptr(),
                std::ptr::null(),
                0,
                std::ptr::null_mut(),
            ),
        )
    }
}

fn call_shape_keyword<'py>(
    shape_type: &Bound<'py, PyAny>,
    dims: &Bound<'py, PyAny>,
    keyword: &Bound<'py, PyTuple>,
) -> PyResult<Bound<'py, PyAny>> {
    let args = [dims.as_ptr()];
    // SAFETY: the keyword value and name tuple outlive Vectorcall; no positional arguments are passed.
    unsafe {
        Bound::from_owned_ptr_or_err(
            shape_type.py(),
            pyo3::ffi::PyObject_Vectorcall(shape_type.as_ptr(), args.as_ptr(), 0, keyword.as_ptr()),
        )
    }
}

/// 只更改未发布独立副本的 rank，不调整元素数量。 / Change only the rank of an unpublished independent copy, never its element count.
/// `target` 是否为 `types[1..]` 中某个**内置形状类**的精确实例。
///
/// `types` 由 Python 侧一次传入（`(ndarray, DynShape, Shape1..Shape4)`），
/// 所以这里只做类型指针比较，**不 import、不 getattr**——与每次调用重新解析模块相比没有额外开销。
///
/// 此前守卫要求「等于 `types[1]`（只有 `DynShape`）」，导致用户直接传 `Shape2` 作 reshape 目标时
/// 退化 **1.38 倍**（实测 7,693 vs 5,569 ns）。`Shape1`..`Shape4` 与 `DynShape` 的 `dims`
/// 都是纯 tuple 且都不重写它，所以对快路径等价。
///
/// Exact instance of one of the builtin shape classes listed in `types[1..]`. Only pointer
/// comparisons — no import, no getattr. The old guard required equality with `types[1]`
/// (`DynShape` only), so passing `Shape2` as the reshape target degraded by 1.38x.
fn is_builtin_shape(target: &Bound<'_, PyAny>, types: &Bound<'_, PyTuple>) -> PyResult<bool> {
    for index in 1..types.len() {
        let Ok(class) = types.get_item(index) else {
            continue;
        };
        if target.get_type().is(&class) {
            return Ok(true);
        }
    }
    Ok(false)
}

fn flatten_copied_header(data: &Bound<'_, PyAny>, count: usize) -> PyResult<()> {
    let array = data.cast::<PyUntypedArray>()?;
    if array.ndim() == 1 {
        return Ok(());
    }
    let mut count = count as isize;
    let mut dims = PyArray_Dims {
        ptr: &mut count,
        len: 1,
    };
    // SAFETY: 仅接收本模块 NewCopy 刚创建、未暴露的 C-order 缓冲；数量已验证相同，无别名或 Rust 借用。 / Only a fresh unpublished C-order NewCopy buffer with the same validated count, no aliases or Rust borrows.
    let result = unsafe {
        Bound::from_owned_ptr_or_err(
            data.py(),
            PY_ARRAY_API.PyArray_Resize(
                data.py(),
                array.as_array_ptr(),
                &mut dims,
                0,
                NPY_ORDER::NPY_CORDER,
            ),
        )
    }?;
    drop(result);
    Ok(())
}

fn check_flatten_count(count: &Bound<'_, PyAny>) -> PyResult<Result<(), Failure>> {
    if count.is_exact_instance_of::<PyInt>() {
        if let Ok(size) = count.extract::<isize>() {
            if size <= 0 {
                return Ok(Err(Failure::input(
                    "展平形状大小必须为正 / Flatten shape size must be positive",
                )));
            }
            // 仅当上游长度一致时保留原 Python 整数身份。 / Retain Python integer identity only when the upstream length agrees.
            if pinned_flatten_length(size as usize) != size as usize {
                return Ok(Err(Failure::binding(
                    "DATA_LOSS",
                    "上游展平长度不一致 / Upstream flattened length differs",
                )));
            }
        } else {
            let value = count.extract::<BigInt>()?;
            if value <= BigInt::from(0) {
                return Ok(Err(Failure::input(
                    "展平形状大小必须为正 / Flatten shape size must be positive",
                )));
            }
        }
    } else {
        let value = count.extract::<BigInt>()?;
        let (planned, failure) = _flatten_storage_shape(value.clone());
        if let Some(failure) = failure {
            return Ok(Err(failure));
        }
        if planned.as_deref() != Some(std::slice::from_ref(&value)) {
            return Ok(Err(Failure::binding(
                "DATA_LOSS",
                "上游展平长度不一致 / Upstream flattened length differs",
            )));
        }
    }
    Ok(Ok(()))
}

fn flatten_shape_for_count<'py>(
    py: Python<'py>,
    count: &Bound<'py, PyAny>,
    shape_type: &Bound<'py, PyAny>,
    keyword: &Bound<'py, PyTuple>,
) -> PyResult<Result<Bound<'py, PyAny>, Failure>> {
    if let Err(failure) = check_flatten_count(count)? {
        return Ok(Err(failure));
    }
    let dims = PyTuple::new(py, [count])?;
    Ok(Ok(call_shape_keyword(shape_type, &dims, keyword)?))
}

/// 固定形状规划与外部复制协议，不镜像 NumPy 载荷。 / Pinned shape planning and external copy protocols without mirroring NumPy payloads.
#[pyfunction]
#[pyo3(signature = (*, owner, target, flatten, types, resolve))]
pub fn _transform_storage(
    py: Python<'_>,
    owner: &Bound<'_, PyAny>,
    target: &Bound<'_, PyAny>,
    flatten: bool,
    types: &Bound<'_, PyTuple>,
    resolve: &Bound<'_, PyAny>,
) -> PyResult<Transport<Py<PyAny>>> {
    let array_type = types.get_item(0)?;
    let shape_type = types.get_item(1)?;
    let shape_keyword = PyTuple::new(py, ["dims"])?;
    if flatten {
        let count = owner.getattr(pyo3::intern!(py, "size"))?;
        let shape = match flatten_shape_for_count(py, &count, &shape_type, &shape_keyword)? {
            Ok(shape) => shape,
            Err(failure) => return Ok(transport(Err(failure))),
        };
        let constructor = call_zero(resolve)?;
        let data = copy_storage(&owner.getattr(pyo3::intern!(py, "_data"))?)?;
        let value = call_two(&constructor, &shape, &data);
        drop(constructor);
        drop(data);
        return Ok(transport(Ok(value?.unbind())));
    }
    let data = owner.getattr(pyo3::intern!(py, "_data"))?;
    if data.get_type().is(&array_type)
        && data.is_exact_instance_of::<PyUntypedArray>()
        && is_builtin_shape(target, &types)?
    {
        let dims = target
            .getattr(pyo3::intern!(py, "dims"))?
            .extract::<Vec<BigInt>>()?;
        let count = BigInt::from(data.cast::<PyUntypedArray>()?.len());
        let (dims, failure) = _reshape_storage_shape(count, dims);
        if let Some(failure) = failure {
            return Ok(transport(Err(failure)));
        }
        let Some(dims) = dims else {
            return Ok(transport(Err(Failure::binding(
                "APPLICATION_ERROR",
                "缺少重塑元数据 / Missing reshape metadata",
            ))));
        };
        let constructor = call_zero(resolve)?;
        let copied = copy_storage(&data)?;
        flatten_copied_header(&copied, dims[0])?;
        drop(data);
        let value = call_two(&constructor, target, &copied);
        drop(constructor);
        drop(copied);
        return Ok(transport(Ok(value?.unbind())));
    }
    let reshape = data.getattr(pyo3::intern!(py, "reshape"))?;
    // 自定义存储/shape 保留完整外部协议，不是默认算法 fallback。 / Custom storage/shape retain complete external protocols, not a default-algorithm fallback.
    drop(data);
    let shaped = reshape.call1((target.getattr(pyo3::intern!(py, "dims"))?,))?;
    drop(reshape);
    let new_data = shaped.call_method0(pyo3::intern!(py, "flatten"))?;
    drop(shaped);
    let constructor = call_zero(resolve)?;
    let copied = new_data.call_method0(pyo3::intern!(py, "copy"))?;
    let value = constructor.call1((target, &copied));
    drop(constructor);
    drop(copied);
    Ok(transport(Ok(value?.unbind())))
}

fn flatten_value_with_shape(
    py: Python<'_>,
    owner: &Bound<'_, PyAny>,
    shape: &Bound<'_, PyAny>,
    resolve: &Bound<'_, PyAny>,
) -> PyResult<Py<PyAny>> {
    let constructor = call_zero(resolve)?;
    let data = copy_storage(&owner.getattr(pyo3::intern!(py, "_data"))?)?;
    let value = call_two(&constructor, shape, &data);
    drop(constructor);
    drop(data);
    Ok(value?.unbind())
}

fn flatten_with_shape(
    py: Python<'_>,
    owner: &Bound<'_, PyAny>,
    shape: &Bound<'_, PyAny>,
    resolve: &Bound<'_, PyAny>,
) -> PyResult<Transport<Py<PyAny>>> {
    Ok(transport(Ok(flatten_value_with_shape(
        py, owner, shape, resolve,
    )?)))
}

/// 仅复用协议类型和结果工厂，不保存数组、shape 实例或载荷。 / Reuse protocol types and result factories only, never arrays, shape instances or payloads.
#[pyclass(
    name = "_StorageTransform",
    frozen,
    weakref,
    module = "ospf_python._native"
)]
pub struct StorageTransform {
    types: Py<PyTuple>,
    shape_keyword: Py<PyTuple>,
    publication: ResultPublication,
}

#[pymethods]
impl StorageTransform {
    #[new]
    #[pyo3(signature = (*, types, success, failure))]
    fn new(
        py: Python<'_>,
        types: Py<PyTuple>,
        success: Py<PyAny>,
        failure: Py<PyAny>,
    ) -> PyResult<Self> {
        Ok(Self {
            types,
            shape_keyword: PyTuple::new(py, ["dims"])?.unbind(),
            publication: ResultPublication::new(
                success,
                failure,
                "缺少存储变换结果 / Missing storage transform result",
            ),
        })
    }

    fn flatten(
        &self,
        py: Python<'_>,
        owner: &Bound<'_, PyAny>,
        resolve: &Bound<'_, PyAny>,
    ) -> PyResult<Py<PyAny>> {
        let count = owner.getattr(pyo3::intern!(py, "size"))?;
        let shape_type = self.types.bind(py).get_item(1)?;
        let shape =
            match flatten_shape_for_count(py, &count, &shape_type, self.shape_keyword.bind(py))? {
                Ok(shape) => shape,
                Err(failure) => return self.publication.publish(py, transport(Err(failure))),
            };
        let payload = flatten_with_shape(py, owner, &shape, resolve)?;
        self.publication.publish(py, payload)
    }

    fn flatten_value(
        &self,
        py: Python<'_>,
        owner: &Bound<'_, PyAny>,
        shape: &Bound<'_, PyAny>,
        resolve: &Bound<'_, PyAny>,
    ) -> PyResult<Py<PyAny>> {
        flatten_value_with_shape(py, owner, shape, resolve)
    }

    fn flatten_value_result(
        &self,
        py: Python<'_>,
        owner: &Bound<'_, PyAny>,
        shape: &Bound<'_, PyAny>,
        resolve: &Bound<'_, PyAny>,
    ) -> PyResult<Py<PyAny>> {
        let payload = flatten_with_shape(py, owner, shape, resolve)?;
        self.publication.publish(py, payload)
    }

    fn flatten_value_result_checked(
        &self,
        py: Python<'_>,
        owner: &Bound<'_, PyAny>,
        count: &Bound<'_, PyAny>,
        shape: &Bound<'_, PyAny>,
        resolve: &Bound<'_, PyAny>,
    ) -> PyResult<Py<PyAny>> {
        if let Err(failure) = check_flatten_count(count)? {
            return self.publication.publish(py, transport(Err(failure)));
        }
        let payload = flatten_with_shape(py, owner, shape, resolve)?;
        self.publication.publish(py, payload)
    }

    #[pyo3(signature = (owner, count, resolve, *, shape_resolve=None))]
    fn flatten_counted(
        &self,
        py: Python<'_>,
        owner: &Bound<'_, PyAny>,
        count: &Bound<'_, PyAny>,
        resolve: &Bound<'_, PyAny>,
        shape_resolve: Option<&Bound<'_, PyAny>>,
    ) -> PyResult<Py<PyAny>> {
        let shape_type = match shape_resolve {
            Some(shape_resolve) => call_zero(shape_resolve)?,
            None => self.types.bind(py).get_item(1)?,
        };
        let shape = flatten_shape_for_count(py, count, &shape_type, self.shape_keyword.bind(py));
        drop(shape_type);
        let shape = match shape? {
            Ok(shape) => shape,
            Err(failure) => return self.publication.publish(py, transport(Err(failure))),
        };
        let payload = flatten_with_shape(py, owner, &shape, resolve)?;
        self.publication.publish(py, payload)
    }

    #[pyo3(signature = (*, owner, target, precopy, resolve))]
    fn reshape(
        &self,
        py: Python<'_>,
        owner: &Bound<'_, PyAny>,
        target: &Bound<'_, PyAny>,
        precopy: bool,
        resolve: &Bound<'_, PyAny>,
    ) -> PyResult<Py<PyAny>> {
        if precopy {
            // 与 Python 调用表达式一致，先解析 callable 再求值参数。 / Like Python call expressions, resolve the callable before evaluating arguments.
            let constructor = call_zero(resolve)?;
            // 快路径：当 `resolve()` 返回的正是**注册的不可变数组类型**、存储是精确 ndarray、
            // 目标是精确形状类时，中间那次「复制 + 构造」是不可观察的，可以省掉。
            // 不这样做时可变 reshape 会做两次复制两次构造（先 copy+construct，再 `.reshape()`
            // 又走一次 copy+construct），而冻结的 legacy 参考只做一次——那正是负载下 1.16 的来源。
            // Fast path: when `resolve()` returns the registered immutable array type, the storage is
            // an exact ndarray and the target is the exact shape type, the intermediate copy+construct
            // is unobservable and can be dropped. Without this, a mutable reshape copies and constructs
            // twice while the frozen legacy reference does it once — the source of the 1.16 under load.
            if constructor.is(&self.types.bind(py).get_item(0)?) {
                let data = owner.getattr(pyo3::intern!(py, "_data"))?;
                let target_is_shape = target
                    .get_type()
                    .is(&self.types.bind(py).get_item(1)?);
                if data.is_exact_instance_of::<PyUntypedArray>() && target_is_shape {
                    drop(data);
                    drop(constructor);
                    let payload =
                        _transform_storage(py, owner, target, false, self.types.bind(py), resolve)?;
                    return self.publication.publish(py, payload);
                }
                drop(data);
            }
            let shape = owner.getattr(pyo3::intern!(py, "_shape"))?;
            let data = copy_storage(&owner.getattr(pyo3::intern!(py, "_data"))?)?;
            let temporary = call_two(&constructor, &shape, &data);
            // CALL 按 callable、shape、data 顺序清理，早于后续方法分派。 / CALL releases callable, shape and data in order, before subsequent method dispatch.
            drop(constructor);
            drop(shape);
            drop(data);
            let temporary = temporary?;
            // 临时对象可能覆盖 reshape；返回其外层 Result，不重复包装或拆包。 / The temporary can override reshape; return its outer Result without wrapping or unwrapping it.
            return Ok(temporary
                .call_method1(pyo3::intern!(py, "reshape"), (target,))?
                .unbind());
        }
        let payload = _transform_storage(py, owner, target, false, self.types.bind(py), resolve)?;
        self.publication.publish(py, payload)
    }

    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        visit.call(&self.types)?;
        self.publication.traverse(visit)
    }
}

#[pyfunction]
#[pyo3(signature = (*, values, shape, column_major))]
pub fn _create_rational_multiarray(
    py: Python<'_>,
    values: &RationalArray,
    shape: &Shape,
    column_major: bool,
) -> Transport<RationalMultiArray> {
    transport(py.detach(|| RationalMultiArray::create(values, shape, column_major)))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn storage_reshape_plans_actual_count_without_truncation_or_fill() {
        assert_eq!(
            _reshape_storage_shape(6.into(), vec![3.into(), 2.into()])
                .0
                .unwrap(),
            vec![6]
        );
        for dims in [vec![2.into()], vec![8.into()]] {
            assert_eq!(
                _reshape_storage_shape(6.into(), dims).1.unwrap().category,
                "ILLEGAL_ARGUMENT"
            );
        }
        assert_eq!(_reshape_storage_shape(1.into(), vec![]).0.unwrap(), vec![1]);
        assert_eq!(
            _reshape_storage_shape(2.into(), vec![BigInt::from(1) << 100])
                .1
                .unwrap()
                .category,
            "OVERFLOW"
        );
    }

    #[test]
    fn flatten_metadata_does_not_allocate_sparse_payload() {
        let huge: BigInt = BigInt::from(1) << 200;
        assert_eq!(_flatten_storage_shape(huge.clone()).0.unwrap(), vec![huge]);
        assert_eq!(
            _flatten_storage_shape(6.into()).0.unwrap(),
            vec![BigInt::from(6)]
        );
        assert_eq!(
            _flatten_storage_shape(0.into()).1.unwrap().category,
            "ILLEGAL_ARGUMENT"
        );
    }

    #[test]
    fn ordinary_flatten_metadata_uses_pinned_shape_before_python_factory() {
        Python::initialize();
        Python::attach(|py| {
            let factory = py.eval(c"lambda *, dims: dims", None, None).unwrap();
            let keyword = PyTuple::new(py, ["dims"]).unwrap();
            let count = 10_000usize.into_pyobject(py).unwrap().into_any();
            let before = FLATTEN_PLAN_COUNT.with(|calls| calls.get());
            let dims = flatten_shape_for_count(py, &count, &factory, &keyword)
                .unwrap()
                .unwrap();
            let dims = dims.cast::<PyTuple>().unwrap();
            assert!(dims.get_item(0).unwrap().is(&count));
            assert_eq!(FLATTEN_PLAN_COUNT.with(|calls| calls.get()), before + 1);

            let huge = py.eval(c"1 << 200", None, None).unwrap();
            let dims = flatten_shape_for_count(py, &huge, &factory, &keyword)
                .unwrap()
                .unwrap();
            assert!(
                dims.cast::<PyTuple>()
                    .unwrap()
                    .get_item(0)
                    .unwrap()
                    .is(&huge)
            );
            assert_eq!(FLATTEN_PLAN_COUNT.with(|calls| calls.get()), before + 1);

            let boolean = py.eval(c"True", None, None).unwrap();
            let dims = flatten_shape_for_count(py, &boolean, &factory, &keyword)
                .unwrap()
                .unwrap();
            assert!(
                dims.cast::<PyTuple>()
                    .unwrap()
                    .get_item(0)
                    .unwrap()
                    .is(&boolean)
            );
            assert_eq!(FLATTEN_PLAN_COUNT.with(|calls| calls.get()), before + 2);
        });
    }

    #[test]
    fn checked_flatten_value_uses_pinned_shape_before_publication() {
        Python::initialize();
        Python::attach(|py| {
            let count = 10_000usize.into_pyobject(py).unwrap().into_any();
            let before = FLATTEN_PLAN_COUNT.with(|calls| calls.get());
            assert!(check_flatten_count(&count).unwrap().is_ok());
            assert_eq!(FLATTEN_PLAN_COUNT.with(|calls| calls.get()), before + 1);

            let zero = 0usize.into_pyobject(py).unwrap().into_any();
            let failure = check_flatten_count(&zero).unwrap().unwrap_err();
            assert_eq!(failure.category, "ILLEGAL_ARGUMENT");
        });
    }

    #[test]
    fn description_prefix_checks_lifecycle_even_without_displayed_items() {
        Python::initialize();
        Python::attach(|py| {
            let shape = Shape::create(vec![2.into(), 3.into()], true).unwrap();
            let value = py.None().into_bound(py);
            let source = MultiArray::full(shape.clone(), &value).unwrap();
            let region_shape = Shape::create(vec![1.into(), 2.into()], true).unwrap();
            let region =
                MultiArrayView::create(&shape, vec![1.into(), 1.into()], &region_shape).unwrap();
            assert!(
                description_snapshot(py, &source, Some(&region), 0)
                    .unwrap()
                    .is_empty()
            );
            assert_eq!(
                description_snapshot(py, &source, Some(&region), 1)
                    .unwrap()
                    .len(),
                1
            );
            assert_eq!(
                description_snapshot(py, &source, Some(&region), 10)
                    .unwrap()
                    .len(),
                2
            );
            source.__clear__();
            assert_eq!(
                description_snapshot(py, &source, Some(&region), 0)
                    .unwrap_err()
                    .category,
                "FAILED_PRECONDITION"
            );
        });
    }

    #[test]
    fn comparison_pair_snapshots_validate_regions_and_cleared_lifecycle() {
        Python::initialize();
        Python::attach(|py| {
            let shape = Shape::create(vec![2.into(), 3.into()], false).unwrap();
            let value = py.None().into_bound(py);
            let source = MultiArray::full(shape.clone(), &value).unwrap();
            let region_shape = Shape::create(vec![1.into(), 2.into()], false).unwrap();
            let left =
                MultiArrayView::create(&shape, vec![0.into(), 1.into()], &region_shape).unwrap();
            let right =
                MultiArrayView::create(&shape, vec![1.into(), 1.into()], &region_shape).unwrap();
            let (left_values, right_values) =
                comparison_snapshots(py, &source, &source, Some(&left), Some(&right)).unwrap();
            assert_eq!(left_values.len(), 2);
            assert_eq!(right_values.len(), 2);
            assert!(
                left_values
                    .iter()
                    .chain(&right_values)
                    .all(|item| item.bind(py).is(&value))
            );
            assert!(checked_snapshot(vec![], &region_shape).is_err());
            source.__clear__();
            assert_eq!(
                comparison_snapshots(py, &source, &source, Some(&left), Some(&right))
                    .unwrap_err()
                    .category,
                "FAILED_PRECONDITION"
            );
        });
    }

    #[test]
    fn nested_input_is_shape_bounded_iterative_and_capacity_checked() {
        Python::initialize();
        Python::attach(|py| {
            let leaf = PyList::empty(py).into_any();
            let scalar = Shape::create(vec![], false).unwrap();
            let array =
                MultiArray::create(nested_values(&leaf, &scalar).unwrap(), scalar, false).unwrap();
            assert!(array.snapshot(py, false).unwrap()[0].bind(py).is(&leaf));
            let huge = Shape::create(vec![BigInt::from(isize::MAX)], false).unwrap();
            assert_eq!(
                nested_values(&leaf, &huge).unwrap_err().category,
                "OVERFLOW"
            );
            let shape = Shape::create(vec![2.into(), 2.into()], true).unwrap();
            let row = PyList::new(py, [&leaf, &leaf]).unwrap();
            let data = PyTuple::new(py, [&row, &row]).unwrap().into_any();
            let values = nested_values(&data, &shape).unwrap();
            assert_eq!(values.len(), 4);
            assert!(values.iter().all(|value| value.bind(py).is(&leaf)));
            let wrong = Shape::create(vec![2.into(), 3.into()], false).unwrap();
            assert_eq!(
                nested_values(&data, &wrong).unwrap_err().category,
                "ILLEGAL_ARGUMENT"
            );
        });
    }

    #[test]
    fn pickle_restore_is_atomic_one_shot_and_clear_is_terminal() {
        Python::initialize();
        Python::attach(|py| {
            let pending = _unpickle_multiarray((1, vec![2.into()], false)).unwrap();
            assert!(pending.snapshot(py, false).is_err());
            assert!(pending.pickle_reduction(py, false).is_err());
            assert!(
                pending
                    .restore_state(&PyList::empty(py).into_any())
                    .is_err()
            );
            let state = PyList::new(py, [py.None(), py.None()]).unwrap().into_any();
            pending.restore_state(&state).unwrap();
            assert_eq!(pending.snapshot(py, false).unwrap().len(), 2);
            assert!(pending.restore_state(&state).is_err());
            pending.__clear__();
            assert!(pending.restore_state(&state).is_err());
            let pending = _unpickle_multiarray((1, vec![2.into()], false)).unwrap();
            pending.__clear__();
            assert!(pending.restore_state(&state).is_err());
        });
    }

    #[test]
    fn filled_storage_checks_byte_capacity_and_retains_scalar_leaf() {
        Python::initialize();
        Python::attach(|py| {
            let value = PyList::empty(py).into_any();
            let huge = Shape::create(vec![BigInt::from(isize::MAX)], false).unwrap();
            let error = MultiArray::full(huge, &value).err().unwrap();
            assert_eq!(error.category, "OVERFLOW");
            let scalar = Shape::create(vec![], true).unwrap();
            let array = MultiArray::full(scalar, &value).unwrap();
            let snapshot = array.snapshot(py, false).unwrap();
            assert_eq!(snapshot.len(), 1);
            assert!(snapshot[0].bind(py).is(&value));
        });
    }

    #[test]
    fn reversed_axes_preserve_physical_offsets_and_invert_layout() {
        for column_major in [false, true] {
            for dims in [vec![], vec![1], vec![2, 3], vec![2, 1, 3, 4]] {
                let shape = Shape::create(
                    dims.iter().copied().map(BigInt::from).collect(),
                    column_major,
                )
                .unwrap();
                let transposed = reversed_shape(&shape);
                assert_eq!(transposed.column_major(), !column_major);
                assert_eq!(reversed_shape(&transposed).dims(), dims);
                for index in 0..shape.size() {
                    let mut vector = shape.checked_vector(index.into()).unwrap();
                    vector.reverse();
                    assert_eq!(
                        transposed
                            .checked_index(vector.into_iter().map(BigInt::from).collect())
                            .unwrap(),
                        index
                    );
                }
            }
        }
    }

    #[test]
    fn cleared_arrays_reject_mapping_without_calling_python() {
        Python::initialize();
        Python::attach(|py| {
            let scope = pyo3::types::PyDict::new(py);
            py.run(
                c"def callback(value):\n raise AssertionError('must not call cleared storage')",
                Some(&scope),
                None,
            )
            .unwrap();
            let callback = scope.get_item("callback").unwrap().unwrap();
            let shape = Shape::create(vec![1.into()], false).unwrap();
            let region = MultiArrayView::create(&shape, vec![0.into()], &shape).unwrap();
            let array = MultiArray::create(vec![py.None()], shape, false).unwrap();
            array.__clear__();
            for region in [None, Some(&region)] {
                assert_eq!(
                    array
                        .mapped_at(py, vec![0.into()], &callback, region)
                        .unwrap()
                        .1
                        .unwrap()
                        .category,
                    "FAILED_PRECONDITION"
                );
                assert_eq!(
                    array
                        .reduced(py, &callback, false, region)
                        .unwrap()
                        .1
                        .unwrap()
                        .category,
                    "FAILED_PRECONDITION"
                );
                assert_eq!(
                    array.to_list(py, region).unwrap().1.unwrap().category,
                    "FAILED_PRECONDITION"
                );
            }
            assert_eq!(
                array
                    .mapped(py, &callback, false, None)
                    .unwrap()
                    .1
                    .unwrap()
                    .category,
                "FAILED_PRECONDITION"
            );
            assert_eq!(
                array
                    .region_mapped(py, &region, &callback, true, None)
                    .unwrap()
                    .1
                    .unwrap()
                    .category,
                "FAILED_PRECONDITION"
            );
            assert!(array.transpose(py).1.is_some());
            assert!(array.region_transpose(py, &region).1.is_some());
        });
    }

    #[test]
    fn protocol_conversion_and_fold_guard_invalid_internal_snapshots() {
        Python::initialize();
        Python::attach(|py| {
            let scalar = Shape::create(vec![], true).unwrap();
            let (value, error) = nest_snapshot(py, vec![py.None()], &scalar).unwrap();
            assert!(error.is_none());
            assert!(value.unwrap().bind(py).is_none());
            assert_eq!(
                nest_snapshot(py, vec![], &scalar)
                    .unwrap()
                    .1
                    .unwrap()
                    .category,
                "APPLICATION_ERROR"
            );
            assert_eq!(
                reduce_snapshot(py, vec![], py.None().bind(py))
                    .unwrap()
                    .1
                    .unwrap()
                    .category,
                "FAILED_PRECONDITION"
            );
        });
    }

    #[test]
    fn shape_guards_unchecked_upstream_operations() {
        assert!(Shape::create(vec![0.into()], false).is_err());
        assert!(Shape::create(vec![BigInt::from(isize::MAX), 2.into()], false).is_err());
        let scalar = Shape::create(vec![], true).unwrap();
        assert_eq!(scalar.value.len(), 1);
        assert_eq!(
            scalar.checked_vector(0.into()).unwrap(),
            Vec::<usize>::new()
        );
        assert!(scalar.checked_vector(1.into()).is_err());
        assert_eq!(scalar.checked_index(vec![]).unwrap(), 0);
        assert!(scalar.checked_index(vec![0.into()]).is_err());
    }

    #[test]
    fn storage_conversion_and_reshape_use_upstream_values() {
        let shape = Shape::create(vec![2.into(), 3.into()], true).unwrap();
        let values = RationalArray {
            values: (0..6)
                .map(|i| BigRational::from_integer(i.into()))
                .collect(),
        };
        let array = RationalMultiArray::create(&values, &shape, false).unwrap();
        assert_eq!(array.value[1], values.values[3]);
        assert_eq!(array.value.flatten(AccessOrder::RowMajor), values.values);
        let wrong = Shape::create(vec![5.into()], true).unwrap();
        assert!(array.reshape_value(&wrong).is_err());
        let wrong_order = Shape::create(vec![6.into()], false).unwrap();
        assert!(array.reshape_value(&wrong_order).is_err());
        assert!(RationalMultiArray::create(&values, &wrong, false).is_err());
    }

    #[test]
    fn clearing_releases_lock_before_python_destructor_reenters() {
        Python::initialize();
        Python::attach(|py| {
            let scope = pyo3::types::PyDict::new(py);
            py.run(
                c"class Item:\n def __del__(self):\n  results.append(array.at([0])[1].category)\nresults = []\nitem = Item()",
                Some(&scope),
                None,
            )
            .unwrap();
            let item = scope.get_item("item").unwrap().unwrap().unbind();
            scope.del_item("item").unwrap();
            let shape = Shape::create(vec![1.into()], false).unwrap();
            let array = Py::new(
                py,
                MultiArray::create(vec![item], shape.clone(), false).unwrap(),
            )
            .unwrap();
            scope.set_item("array", &array).unwrap();
            array.borrow(py).__clear__();
            let results: Vec<String> = scope
                .get_item("results")
                .unwrap()
                .unwrap()
                .extract()
                .unwrap();
            assert_eq!(results, ["FAILED_PRECONDITION"]);
            assert!(array.borrow(py).flatten(py, false).1.is_some());
            assert!(array.borrow(py).reshape(py, &shape).1.is_some());
            assert!(array.borrow(py).to_storage_order(py, true).1.is_some());
            array.borrow(py).__clear__();
            scope.clear();
        });
    }

    #[test]
    fn region_boundaries_and_nested_projection_are_checked() {
        let source = Shape::create(vec![4.into(), 5.into()], true).unwrap();
        let shape = Shape::create(vec![3.into(), 4.into()], true).unwrap();
        let region = MultiArrayView::create(&source, vec![1.into(), 1.into()], &shape).unwrap();
        assert_eq!(
            region
                .source_index(&source, vec![2.into(), 3.into()])
                .unwrap(),
            19
        );
        assert!(
            region
                .source_index(&source, vec![3.into(), 0.into()])
                .is_err()
        );
        let inner = Shape::create(vec![2.into(), 2.into()], true).unwrap();
        let subview = region
            .subview(Some(vec![1.into(), 2.into()]), Some(&inner))
            .0
            .unwrap();
        assert_eq!(subview.offsets, [2, 3]);
        assert_eq!(
            subview
                .source_index(&source, vec![1.into(), 1.into()])
                .unwrap(),
            19
        );
        assert!(MultiArrayView::create(&source, vec![2.into(), 1.into()], &shape).is_err());
        assert!(
            MultiArrayView::create(&source, vec![BigInt::from(isize::MAX), 0.into()], &shape)
                .is_err()
        );
    }

    #[test]
    fn remaining_region_checks_rank_bounds_layout_and_nested_origin() {
        for column_major in [false, true] {
            let source = Shape::create(vec![4.into(), 5.into()], column_major).unwrap();
            let full = MultiArrayView::with_extent(&source, None, None).unwrap();
            assert_eq!(full.shape.dims(), [4, 5]);
            let region =
                MultiArrayView::with_extent(&source, Some(vec![1.into(), 2.into()]), None).unwrap();
            assert_eq!(region.shape.dims(), [3, 3]);
            assert_eq!(region.shape.column_major(), column_major);
            let subview = region
                .subview(Some(vec![2.into(), 1.into()]), None)
                .0
                .unwrap();
            assert_eq!(subview.shape.dims(), [1, 2]);
            assert_eq!(subview.offsets, [3, 3]);
            assert_eq!(
                subview
                    .source_index(&source, vec![0.into(), 1.into()])
                    .unwrap(),
                source.checked_index(vec![3.into(), 4.into()]).unwrap()
            );
            for offsets in [
                vec![],
                vec![0.into()],
                vec![4.into(), 0.into()],
                vec![(-1).into(), 0.into()],
                vec![BigInt::from(1u128 << 100), 0.into()],
            ] {
                assert!(MultiArrayView::with_extent(&source, Some(offsets), None).is_err());
            }
        }
        let scalar = Shape::create(vec![], true).unwrap();
        assert_eq!(
            MultiArrayView::with_extent(&scalar, None, None)
                .unwrap()
                .shape
                .size(),
            1
        );
    }

    #[test]
    fn clearing_mutable_storage_allows_reentrant_failed_reads_and_writes() {
        Python::initialize();
        Python::attach(|py| {
            let scope = pyo3::types::PyDict::new(py);
            py.run(
                c"class Item:\n def __del__(self):\n  results.append(array.at([0])[1].category)\n  results.append(array.set_many([([0], None)])[1].category)\nresults = []\nitem = Item()",
                Some(&scope), None,
            ).unwrap();
            let item = scope.get_item("item").unwrap().unwrap().unbind();
            scope.del_item("item").unwrap();
            let shape = Shape::create(vec![1.into()], false).unwrap();
            let array = Py::new(
                py,
                MutableMultiArray {
                    inner: MultiArray::create(vec![item], shape, false).unwrap(),
                },
            )
            .unwrap();
            scope.set_item("array", &array).unwrap();
            array.borrow(py).__clear__();
            let results: Vec<String> = scope
                .get_item("results")
                .unwrap()
                .unwrap()
                .extract()
                .unwrap();
            assert_eq!(results, ["FAILED_PRECONDITION", "FAILED_PRECONDITION"]);
            assert!(array.borrow(py).to_immutable(py).1.is_some());
            array.borrow(py).__clear__();
            scope.clear();
        });
    }
}
