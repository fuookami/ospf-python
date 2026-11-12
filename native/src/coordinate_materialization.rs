//! 共享坐标采样与输出布局发布，由固定上游迭代器和 builder 接管。 / Shared coordinate sampling and output layout publication via pinned upstream iterators and builders.

use num_bigint::BigInt;
use num_traits::ToPrimitive;
use ospf_rust_multiarray::{
    AbstractShape, AccessOrder, DynShape, MultiArrayBuilder, ShapeAccessOrderExt, StorageOrder,
};
use pyo3::prelude::*;
use pyo3::types::{PyInt, PyList, PyTuple};

use crate::failure::{Failure, Transport, transport};

#[pyclass(frozen, module = "ospf_python._native")]
pub struct CoordinatePlan {
    shape: Option<DynShape>,
    count: usize,
}

fn reserve_indices(count: usize) -> Result<Vec<usize>, Failure> {
    let mut values = Vec::new();
    values.try_reserve_exact(count).map_err(|_| {
        Failure::binding(
            "APPLICATION_ERROR",
            "无法分配布局索引 / Unable to allocate layout indices",
        )
    })?;
    Ok(values)
}

#[pyfunction]
pub fn _create_coordinate_plan(dims: Vec<BigInt>) -> Transport<CoordinatePlan> {
    transport((|| {
        // 保留旧坐标迭代器的非正维度为空规则，不把空形状与 rank-zero 混淆。 / Preserve nonpositive-axis emptiness without confusing it with rank zero.
        if dims.iter().any(|dim| *dim <= BigInt::from(0)) {
            return Ok(CoordinatePlan {
                shape: None,
                count: 0,
            });
        }
        let mut count = 1_usize;
        let dims = dims.into_iter().map(|dim| {
            let dim = dim.to_usize().ok_or_else(|| Failure::binding("OVERFLOW", "坐标维度超出原生容量 / Coordinate dimension exceeds native capacity"))?;
            count = count.checked_mul(dim).filter(|size| *size <= isize::MAX as usize / std::mem::size_of::<usize>()).ok_or_else(|| Failure::binding("OVERFLOW", "坐标槽位数超出原生容量 / Coordinate slot count exceeds native capacity"))?;
            Ok(dim)
        }).collect::<Result<Vec<_>, Failure>>()?;
        Ok(CoordinatePlan {
            shape: Some(DynShape::new(dims)),
            count,
        })
    })())
}

/// 内置形状源的探测结果：`strides` 已按 plan 的维度顺序解析，`data` 是提前取出的存储。
/// Probe result for a builtin shape source: `strides` in plan order, `data` hoisted.
struct BuiltinSource<'py> {
    strides: Vec<usize>,
    data: Bound<'py, PyAny>,
}

/// 判断 `owner._shape` 是否可安全地走 native 快路径。
/// Decide whether `owner._shape` may take the native fast path.
///
/// 四条同时成立才返回 `Some`：
/// 1. `owner._shape` 的**精确类型**是 `ospf_python.multiarray.shape` 里的 `Shape1..Shape4`/`DynShape`；
/// 2. 它的 `dims` 与本次 plan 的 `shape` 逐项相等；
/// 3. 它的 `strides()` 是精确非负整数；
/// 4. 反转后的 `strides()` 与调用方传入的 `strides` 逐项相等。
///
/// All four must hold; otherwise the original Python protocol path runs unchanged.
fn builtin_owner<'py>(
    py: Python<'py>,
    owner: &Bound<'py, PyAny>,
    shape: &DynShape,
    native_strides: &Option<Vec<usize>>,
) -> PyResult<Option<BuiltinSource<'py>>> {
    let Some(given) = native_strides else {
        return Ok(None);
    };
    let owner_shape = owner.getattr(pyo3::intern!(py, "_shape"))?;
    let module = py.import(pyo3::intern!(py, "ospf_python.multiarray.shape"))?;
    let exact = [
        "Shape1", "Shape2", "Shape3", "Shape4", "DynShape",
    ]
    .into_iter()
    .filter_map(|name| module.getattr(name).ok())
    .any(|class| owner_shape.get_type().is(&class));
    if !exact {
        return Ok(None);
    }
    let dims = owner_shape.getattr(pyo3::intern!(py, "dims"))?;
    let dims = dims.extract::<Vec<usize>>()?;
    if dims.len() != shape.dimension() || !(0..shape.dimension()).all(|axis| dims[axis] == shape.shape()[axis]) {
        return Ok(None);
    }
    let strides = owner_shape.call_method0(pyo3::intern!(py, "strides"))?;
    let strides = strides.extract::<Vec<usize>>()?;
    let reversed = strides.iter().rev().copied().collect::<Vec<_>>();
    if reversed.len() != given.len() || !reversed.iter().copied().eq(given.iter().copied()) {
        return Ok(None);
    }
    let data = owner.getattr(pyo3::intern!(py, "_data"))?;
    Ok(Some(BuiltinSource {
        strides,
        data,
    }))
}

/// `destination`/`_data` 的**精确类型**是否为 `numpy.ndarray`。
/// Whether the value's EXACT type is `numpy.ndarray` (subclasses keep the per-element path).
fn is_ndarray(py: Python<'_>, value: &Bound<'_, PyAny>) -> PyResult<bool> {
    let Ok(numpy) = py.import(pyo3::intern!(py, "numpy")) else {
        return Ok(false);
    };
    let Ok(ndarray) = numpy.getattr(pyo3::intern!(py, "ndarray")) else {
        return Ok(false);
    };
    Ok(value.get_type().is(&ndarray))
}

#[pymethods]
impl CoordinatePlan {
    #[pyo3(signature = (*, owner, strides, destination))]
    fn transpose_into(
        &self,
        py: Python<'_>,
        owner: &Bound<'_, PyAny>,
        strides: &Bound<'_, PyTuple>,
        destination: &Bound<'_, PyAny>,
    ) -> PyResult<Transport<Py<PyTuple>>> {
        let Some(shape) = &self.shape else {
            return Ok(transport(Ok(PyTuple::empty(py).unbind())));
        };
        let reversed_dims = (0..shape.dimension())
            .rev()
            .map(|axis| shape.shape()[axis])
            .collect::<Vec<_>>();
        // 只有精确整数且与上游偏移完全相等时才使用上游索引，不能吞掉自定义数值协议。 / Use upstream indexing only for exact integers equal to upstream offsets; never suppress custom numeric protocols.
        let native_strides = strides
            .iter()
            .map(|stride| {
                if stride.is_exact_instance_of::<PyInt>() {
                    stride.extract::<usize>().ok()
                } else {
                    None
                }
            })
            .collect::<Option<Vec<_>>>();
        let target: Option<DynShape> = [StorageOrder::RowMajor, StorageOrder::ColumnMajor]
            .into_iter()
            .map(|order| DynShape::new_with_order(reversed_dims.clone(), order))
            .find(|candidate| {
                native_strides.as_ref().is_some_and(|strides| {
                    strides.len() == candidate.dimension()
                        && strides
                            .iter()
                            .copied()
                            .eq((0..candidate.dimension()).map(|axis| candidate.offsets()[axis]))
                })
            });
        // 快路径：仅当 `owner._shape` 的**精确类型**是本模块族的形状类、且它的 `dims`/`strides`
        // 与本次调用的 plan/`strides` 完全一致时，才允许在 native 侧直算扁平索引并把 `_data` 提前读取。
        // 判据是「精确类 + 数值一致」，不是「isinstance」——子类可能重写 `flat_index`。
        // Fast path: only when `owner._shape` is EXACTLY one of this module's shape classes and its
        // dims/strides match the plan and the given strides; then the flat index is computable here
        // and `_data` may be hoisted. The test is exact class plus value equality, not isinstance,
        // because a subclass could override `flat_index`.
        let builtin = builtin_owner(py, owner, shape, &native_strides)?;
        // 批量缓冲分支：快路径 + 标准目标布局 + 双方都是 numpy ndarray 时，
        // 用一次 take + 一次 fancy-index 赋值取代逐元素的 get_item/set_item。
        // Bulk branch: under the fast path with a standard target layout and both sides being
        // numpy ndarrays, one take plus one fancy-index assignment replaces the per-element
        // get_item/set_item pair.
        if let Some(source) = &builtin {
            if let Some(target) = &target {
                // 小数组不走批量：2×3 只有 6 个元素，两个 Vec 分配 + 两次 PyList +
                // take + fancy-index + PyTuple 的固定开销可能高于 6 次逐元素 set_item。
                // 阈值 256 让「批量省下的每元素成本」明显超过它的固定开销。
                // Small arrays keep the element loop: the bulk path's fixed cost (two Vec
                // allocations, two PyList, take, fancy-index, PyTuple) can exceed six
                // per-element set_item calls. The 256 threshold makes the saving dominate.
                if self.count >= 256
                    && is_ndarray(py, &source.data)?
                    && is_ndarray(py, destination)?
                {
                    let mut old_offsets = Vec::with_capacity(self.count);
                    let mut new_offsets = Vec::with_capacity(self.count);
                    for (ordinal, indices) in shape.indices().enumerate() {
                        if ordinal.is_multiple_of(4096) {
                            py.check_signals()?;
                        }
                        let mut offset = 0_usize;
                        for (stride, index) in source.strides.iter().zip(indices.iter()) {
                            offset += stride * index;
                        }
                        old_offsets.push(offset);
                        let reversed = indices.iter().copied().rev().collect::<Vec<_>>();
                        match target.index_of(&reversed) {
                            Ok(position) => new_offsets.push(position),
                            Err(_) => {
                                return Ok(transport(Err(Failure::binding(
                                    "APPLICATION_ERROR",
                                    "上游转置索引不一致 / Inconsistent upstream transpose index",
                                ))));
                            }
                        }
                    }
                    let offsets = PyList::new(py, &old_offsets)?;
                    let values = source
                        .data
                        .call_method1(pyo3::intern!(py, "take"), (offsets,))?;
                    let targets = PyList::new(py, &new_offsets)?;
                    destination.set_item(targets, values)?;
                    let tail = PyTuple::new(
                        py,
                        [
                            old_offsets
                                .last()
                                .copied()
                                .unwrap_or(0)
                                .into_pyobject(py)?
                                .into_any(),
                            new_offsets
                                .last()
                                .copied()
                                .unwrap_or(0)
                                .into_pyobject(py)?
                                .into_any(),
                        ],
                    )?;
                    return Ok(transport(Ok(tail.unbind())));
                }
            }
        }
        let mut old_flat = None;
        let mut new_flat = None;
        for (ordinal, indices) in shape.indices().enumerate() {
            if ordinal.is_multiple_of(4096) {
                py.check_signals()?;
            }
            let next_old = match &builtin {
                Some(source) => {
                    let mut offset = 0_usize;
                    for (stride, index) in source.strides.iter().zip(indices.iter()) {
                        offset += stride * index;
                    }
                    offset.into_pyobject(py)?.into_any()
                }
                None => owner
                    .getattr(pyo3::intern!(py, "_shape"))?
                    .getattr(pyo3::intern!(py, "flat_index"))?
                    .call(PyTuple::new(py, &indices)?, None)?,
            };
            old_flat = Some(next_old);
            let reversed = indices.iter().copied().rev().collect::<Vec<_>>();
            let next_new = if let Some(target) = &target {
                let offset = match target.index_of(&reversed) {
                    Ok(offset) => offset,
                    Err(_) => {
                        return Ok(transport(Err(Failure::binding(
                            "APPLICATION_ERROR",
                            "上游转置索引不一致 / Inconsistent upstream transpose index",
                        ))));
                    }
                };
                offset.into_pyobject(py)?.into_any()
            } else {
                // 外部有符号/截短步长按原乘加顺序执行 Python 数值协议。 / External signed/truncated strides retain Python multiplication/addition order.
                let mut offset = 0_usize.into_pyobject(py)?.into_any();
                for (stride, index) in strides.iter().zip(&reversed) {
                    offset = offset.add(stride.mul(*index)?)?;
                }
                offset
            };
            new_flat = Some(next_new);
            // old_flat 回调可替换存储；必须在目标索引协议完成后重新读取。
            // 快路径下 `flat_index` 是纯函数（内置形状类），所以 `_data` 可以提前读取。
            // old_flat callbacks can replace storage; resolve it after destination-index protocols.
            // Under the fast path `flat_index` is pure, so `_data` may be hoisted.
            let value = match &builtin {
                Some(source) => source.data.get_item(old_flat.as_ref().unwrap())?,
                None => owner
                    .getattr(pyo3::intern!(py, "_data"))?
                    .get_item(old_flat.as_ref().unwrap())?,
            };
            destination.set_item(new_flat.as_ref().unwrap(), value)?;
        }
        // 最后两个外部索引保活到 Python 结果构造之后，与原局部变量生命周期一致。 / Retain the final external keys until after Python result construction, matching legacy locals.
        let tail = old_flat.into_iter().chain(new_flat).collect::<Vec<_>>();
        Ok(transport(Ok(PyTuple::new(py, tail)?.unbind())))
    }

    fn sample(&self, py: Python<'_>, owner: &Bound<'_, PyAny>) -> PyResult<Py<PyList>> {
        let values = PyList::empty(py);
        if let Some(shape) = &self.shape {
            for (position, indices) in shape.indices().enumerate() {
                if position.is_multiple_of(4096) {
                    py.check_signals()?;
                }
                // 逐次解析 get，保留覆盖、重入和后续源修改；不缓存 owner 或源叶。 / Resolve get on every visit, preserving overrides, reentrancy and later source writes; retain no owner or source leaves.
                let arguments = PyTuple::new(py, indices)?;
                let value = owner
                    .getattr(pyo3::intern!(py, "get"))?
                    .call(arguments, None)?;
                values.append(value)?;
            }
        }
        Ok(values.unbind())
    }

    #[pyo3(signature = (*, column_major, indexer=None))]
    fn permutation(
        &self,
        py: Python<'_>,
        column_major: bool,
        indexer: Option<&Bound<'_, PyAny>>,
    ) -> PyResult<Transport<Option<Vec<usize>>>> {
        let Some(shape) = &self.shape else {
            return Ok(transport(Ok(None)));
        };
        let permutation = if let Some(indexer) = indexer {
            let mut result = match reserve_indices(self.count) {
                Ok(values) => values,
                Err(error) => return Ok(transport(Err(error))),
            };
            result.resize(self.count, usize::MAX);
            for (ordinal, indices) in shape.indices().enumerate() {
                if ordinal.is_multiple_of(4096) {
                    py.check_signals()?;
                }
                let mut offset = indexer
                    .call(PyTuple::new(py, indices)?, None)?
                    .extract::<BigInt>()?;
                if offset < BigInt::from(0) {
                    offset += self.count;
                }
                let Some(offset) = offset.to_usize().filter(|offset| *offset < self.count) else {
                    return Ok(transport(Err(Failure::input(
                        "自定义布局索引越界 / Custom layout index is out of range",
                    ))));
                };
                if result[offset] != usize::MAX {
                    return Ok(transport(Err(Failure::input(
                        "自定义布局必须是一一对应的稠密映射 / Custom layout must be a bijective dense mapping",
                    ))));
                }
                result[offset] = ordinal;
            }
            result
        } else if !column_major {
            return Ok(transport(Ok(None)));
        } else {
            let mut values = match reserve_indices(self.count) {
                Ok(values) => values,
                Err(error) => return Ok(transport(Err(error))),
            };
            values.extend(0..self.count);
            let target: DynShape = DynShape::new_with_order(
                (0..shape.dimension())
                    .map(|axis| shape.shape()[axis])
                    .collect::<Vec<usize>>(),
                StorageOrder::ColumnMajor,
            );
            // 上游 builder 将逻辑 C-order ordinal 转为目标物理布局；绑定不实现坐标公式。 / The upstream builder converts logical C-order ordinals into target physical layout; no coordinate formula in the binding.
            MultiArrayBuilder::from_list_with_order(target, values, AccessOrder::RowMajor)
                .as_slice()
                .to_vec()
        };
        if permutation.iter().copied().eq(0..self.count) {
            Ok(transport(Ok(None)))
        } else {
            Ok(transport(Ok(Some(permutation))))
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use pyo3::types::PyDict;

    #[test]
    fn transpose_uses_pinned_target_and_keeps_final_keys() {
        Python::initialize();
        Python::attach(|py| {
            let plan = _create_coordinate_plan(vec![2.into(), 2.into()]).0.unwrap();
            let scope = PyDict::new(py);
            py.run(c"class Shape:\n def flat_index(self, i, j):\n  return i*2+j\nclass Source:\n _shape = Shape()\n _data = [1,2,3,4]\nsource = Source()\noutput = [None]*4", Some(&scope), None).unwrap();
            let output = scope.get_item("output").unwrap().unwrap();
            let result = plan
                .transpose_into(
                    py,
                    &scope.get_item("source").unwrap().unwrap(),
                    &PyTuple::new(py, [1, 2]).unwrap(),
                    &output,
                )
                .unwrap();
            assert_eq!(output.extract::<Vec<usize>>().unwrap(), vec![1, 2, 3, 4]);
            assert_eq!(
                result.0.unwrap().extract::<(usize, usize)>(py).unwrap(),
                (3, 3)
            );
        });
    }

    #[test]
    fn transpose_preserves_signed_external_stride_and_live_reads() {
        Python::initialize();
        Python::attach(|py| {
            let plan = _create_coordinate_plan(vec![2.into(), 3.into()]).0.unwrap();
            let scope = PyDict::new(py);
            py.run(c"class Shape:\n def flat_index(self, i, j):\n  source._data = [5,4,3,2,1,0]\n  return i*3+j\nclass Source:\n _shape = Shape()\n _data = [0]*6\nsource = Source()\noutput = [None]*6", Some(&scope), None).unwrap();
            let output = scope.get_item("output").unwrap().unwrap();
            let result = plan
                .transpose_into(
                    py,
                    &scope.get_item("source").unwrap().unwrap(),
                    &PyTuple::new(py, [-1, 3]).unwrap(),
                    &output,
                )
                .unwrap();
            assert!(result.1.is_none());
            assert_eq!(
                output.extract::<Vec<usize>>().unwrap(),
                vec![5, 0, 1, 2, 3, 4]
            );
        });
    }

    #[test]
    fn pinned_builder_publishes_column_layout_after_c_order_sampling() {
        Python::initialize();
        Python::attach(|py| {
            let plan = _create_coordinate_plan(vec![2.into(), 3.into()]).0.unwrap();
            let scope = PyDict::new(py);
            py.run(
                c"class Source:\n def get(self, i, j):\n  return i * 3 + j\nsource = Source()",
                Some(&scope),
                None,
            )
            .unwrap();
            let output = plan
                .sample(py, &scope.get_item("source").unwrap().unwrap())
                .unwrap();
            assert_eq!(
                output.extract::<Vec<usize>>(py).unwrap(),
                vec![0, 1, 2, 3, 4, 5]
            );
            assert_eq!(
                plan.permutation(py, true, None)
                    .unwrap()
                    .0
                    .unwrap()
                    .unwrap(),
                vec![0, 3, 1, 4, 2, 5]
            );
            assert!(
                plan.permutation(py, false, None)
                    .unwrap()
                    .0
                    .unwrap()
                    .is_none()
            );
        });
    }

    #[test]
    fn custom_negative_indices_and_duplicate_validation() {
        Python::initialize();
        Python::attach(|py| {
            let plan = _create_coordinate_plan(vec![3.into()]).0.unwrap();
            let scope = PyDict::new(py);
            py.run(
                c"negative = lambda i: -1-i\nduplicate = lambda i: 0",
                Some(&scope),
                None,
            )
            .unwrap();
            let negative = scope.get_item("negative").unwrap().unwrap();
            assert_eq!(
                plan.permutation(py, false, Some(&negative))
                    .unwrap()
                    .0
                    .unwrap()
                    .unwrap(),
                vec![2, 1, 0]
            );
            let duplicate = scope.get_item("duplicate").unwrap().unwrap();
            assert_eq!(
                plan.permutation(py, false, Some(&duplicate))
                    .unwrap()
                    .1
                    .unwrap()
                    .category,
                "ILLEGAL_ARGUMENT"
            );
        });
    }

    #[test]
    fn zero_axis_precedes_capacity_but_rank_zero_has_one_slot() {
        assert_eq!(_create_coordinate_plan(vec![]).0.unwrap().count, 1);
        assert_eq!(
            _create_coordinate_plan(vec![BigInt::from(1) << 100, 0.into()])
                .0
                .unwrap()
                .count,
            0
        );
        assert_eq!(
            _create_coordinate_plan(vec![BigInt::from(1) << 100, 2.into()])
                .1
                .unwrap()
                .category,
            "OVERFLOW"
        );
    }
}
