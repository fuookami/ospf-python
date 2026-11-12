//! 稠密元数据的唯一容量检查边界。 / One capacity-validation boundary for dense metadata.

use ospf_rust_multiarray::{AbstractShape, DynShape, Shape, StorageOrder};

#[cfg(test)]
thread_local! {
    static UPSTREAM_SHAPE_COUNT: std::cell::Cell<usize> = const { std::cell::Cell::new(0) };
    static UPSTREAM_INDEX_COUNT: std::cell::Cell<usize> = const { std::cell::Cell::new(0) };
}

#[cfg(test)]
pub(crate) fn upstream_shape_count() -> usize {
    UPSTREAM_SHAPE_COUNT.with(std::cell::Cell::get)
}

#[cfg(test)]
pub(crate) fn upstream_index_count() -> usize {
    UPSTREAM_INDEX_COUNT.with(std::cell::Cell::get)
}

#[derive(Debug, PartialEq)]
pub(crate) enum DenseShapeError {
    Dimension,
    Size,
}

fn checked_axis(size: &mut usize, dim: Option<usize>) -> Result<usize, DenseShapeError> {
    let dim = dim
        .filter(|dim| *dim > 0)
        .ok_or(DenseShapeError::Dimension)?;
    // 上游不检查乘积；也必须满足 Python 长度协议。 / Upstream products are unchecked; also respect Python's length protocol.
    *size = size
        .checked_mul(dim)
        .filter(|size| *size <= isize::MAX as usize)
        .ok_or(DenseShapeError::Size)?;
    Ok(dim)
}

pub(crate) fn validate_dense_dimensions(
    dims: impl IntoIterator<Item = Option<usize>>,
) -> Result<(), DenseShapeError> {
    let mut size = 1;
    for dim in dims {
        checked_axis(&mut size, dim)?;
    }
    Ok(())
}

pub(crate) fn dense_shape(
    dims: impl IntoIterator<Item = Option<usize>>,
    column_major: bool,
) -> Result<DynShape, DenseShapeError> {
    let mut size = 1usize;
    let dims = dims
        .into_iter()
        .map(|dim| checked_axis(&mut size, dim))
        .collect::<Result<Vec<_>, _>>()?;
    #[cfg(test)]
    UPSTREAM_SHAPE_COUNT.with(|count| count.set(count.get() + 1));
    Ok(DynShape::new_with_order(
        dims,
        if column_major {
            StorageOrder::ColumnMajor
        } else {
            StorageOrder::RowMajor
        },
    ))
}

pub(crate) fn fixed_shape_size<const N: usize>(dims: [usize; N]) -> Result<usize, DenseShapeError> {
    let mut size = 1;
    for dim in dims {
        checked_axis(&mut size, Some(dim))?;
    }
    #[cfg(test)]
    UPSTREAM_SHAPE_COUNT.with(|count| count.set(count.get() + 1));
    Ok(Shape::<N>::new(dims).len())
}

pub(crate) fn fixed_shape<const N: usize>(
    dims: [usize; N],
    column_major: bool,
) -> Result<Shape<N>, DenseShapeError> {
    validate_dense_dimensions(dims.into_iter().map(Some))?;
    #[cfg(test)]
    UPSTREAM_SHAPE_COUNT.with(|count| count.set(count.get() + 1));
    Ok(Shape::<N>::new_with_order(
        dims,
        if column_major {
            StorageOrder::ColumnMajor
        } else {
            StorageOrder::RowMajor
        },
    ))
}

pub(crate) fn fixed_shape_offsets<const N: usize>(
    dims: [usize; N],
    column_major: bool,
) -> Result<([usize; N], usize), DenseShapeError> {
    let shape = fixed_shape(dims, column_major)?;
    Ok((
        std::array::from_fn(|axis| shape.offsets()[axis]),
        shape.len(),
    ))
}

pub(crate) fn fixed_shape_index<const N: usize>(
    dims: [usize; N],
    coordinates: [usize; N],
    column_major: bool,
) -> Option<([usize; N], usize, usize)> {
    if dims
        .iter()
        .zip(coordinates)
        .any(|(dim, index)| index >= *dim)
    {
        return None;
    }
    let shape = fixed_shape(dims, column_major).ok()?;
    #[cfg(test)]
    UPSTREAM_INDEX_COUNT.with(|count| count.set(count.get() + 1));
    let index = shape.index_of(&coordinates).ok()?;
    Some((
        std::array::from_fn(|axis| shape.offsets()[axis]),
        shape.len(),
        index,
    ))
}

#[cfg(test)]
mod tests {
    use super::*;
    use ospf_rust_multiarray::AbstractShape;

    #[test]
    fn validates_before_entering_upstream_and_preserves_layout() {
        for (column, expected) in [(false, [12, 4, 1]), (true, [1, 2, 6])] {
            let shape = dense_shape([Some(2), Some(3), Some(4)], column).unwrap();
            assert_eq!(shape.len(), 24);
            for (axis, offset) in expected.into_iter().enumerate() {
                assert_eq!(shape.offsets()[axis], offset);
            }
        }
        assert_eq!(dense_shape([], false).unwrap().len(), 1);
        assert!(matches!(
            dense_shape([Some(0)], false),
            Err(DenseShapeError::Dimension)
        ));
        assert!(matches!(
            dense_shape([None], false),
            Err(DenseShapeError::Dimension)
        ));
        assert!(matches!(
            dense_shape([Some(isize::MAX as usize), Some(2)], false),
            Err(DenseShapeError::Size)
        ));
    }

    #[test]
    fn fixed_shape_size_uses_the_same_capacity_guard() {
        assert_eq!(fixed_shape_size([2, 3]).unwrap(), 6);
        assert_eq!(fixed_shape_size([2, 3, 4]).unwrap(), 24);
        assert_eq!(fixed_shape_size([2, 3, 4, 5]).unwrap(), 120);
        assert_eq!(fixed_shape_size([0, 3]), Err(DenseShapeError::Dimension));
        assert_eq!(
            fixed_shape_size([isize::MAX as usize, 2]),
            Err(DenseShapeError::Size)
        );
    }

    #[test]
    fn fixed_shape_offsets_use_the_same_guard_and_layout() {
        assert_eq!(
            fixed_shape_offsets([2, 3, 4, 1], false),
            Ok(([12, 4, 1, 1], 24))
        );
        assert_eq!(
            fixed_shape_offsets([2, 3, 4, 1], true),
            Ok(([1, 2, 6, 24], 24))
        );
        assert_eq!(
            fixed_shape_offsets([0, 1, 1, 1], false),
            Err(DenseShapeError::Dimension)
        );
        assert_eq!(
            fixed_shape_offsets([isize::MAX as usize, 2], false),
            Err(DenseShapeError::Size)
        );
    }

    #[test]
    fn fixed_shape_index_checks_bounds_and_uses_upstream() {
        let before = upstream_index_count();
        assert_eq!(fixed_shape_index([], [], false), Some(([], 1, 0)));
        assert_eq!(
            fixed_shape_index([2, 3, 4], [1, 2, 3], false),
            Some(([12, 4, 1], 24, 23))
        );
        assert_eq!(
            fixed_shape_index([2, 3, 4], [1, 2, 3], true),
            Some(([1, 2, 6], 24, 23))
        );
        assert_eq!(fixed_shape_index([2, 3], [2, 0], false), None);
        assert_eq!(fixed_shape_index([0, 3], [0, 0], false), None);
        assert_eq!(
            fixed_shape_index([isize::MAX as usize, 2], [0, 0], false),
            None
        );
        assert_eq!(upstream_index_count(), before + 3);
    }

    #[test]
    fn first_failure_does_not_consume_later_metadata() {
        let mut reads = 0;
        let result = dense_shape(
            [Some(isize::MAX as usize), Some(2), Some(0)]
                .into_iter()
                .inspect(|_| reads += 1),
            false,
        );
        assert!(matches!(result, Err(DenseShapeError::Size)));
        assert_eq!(reads, 2);
        let mut values = [Some(isize::MAX as usize), Some(2), Some(0)].into_iter();
        assert!(matches!(
            dense_shape(&mut values, false),
            Err(DenseShapeError::Size)
        ));
        assert_eq!(values.next(), Some(Some(0)));
    }
}
