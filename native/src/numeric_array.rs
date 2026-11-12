//! 批量边界仅编排固定版数学运算，不构造逐元素 Python 对象。 / Batch orchestration without per-element Python objects.

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{ToPrimitive, Zero};
use ospf_rust_math::operator::{AddRef, DivRef, MulRef, SubRef};
use pyo3::prelude::*;

use crate::failure::{Failure, Transport, transport};
use crate::numeric::Rational;

#[pyclass(frozen, module = "ospf_python._native")]
pub struct RationalArray {
    pub(crate) values: Vec<BigRational>,
}

impl RationalArray {
    fn create(inputs: Vec<(BigInt, BigInt)>) -> Result<Self, Failure> {
        let values = inputs
            .into_iter()
            .enumerate()
            .map(|(index, (numerator, denominator))| {
                Rational::create(numerator, denominator)
                    .map(|value| value.value)
                    .map_err(|mut error| {
                        error.message.push_str(&format!("; 索引 / index: {index}"));
                        error
                    })
            })
            .collect::<Result<_, _>>()?;
        Ok(Self { values })
    }

    fn same_length(&self, other: &Self) -> Result<(), Failure> {
        if self.values.len() != other.values.len() {
            return Err(Failure::input(format!(
                "数组长度不匹配 / Array length mismatch: {} != {}",
                self.values.len(),
                other.values.len()
            )));
        }
        Ok(())
    }

    fn binary(
        &self,
        other: &Self,
        operation: fn(&BigRational, &BigRational) -> BigRational,
    ) -> Result<Self, Failure> {
        self.same_length(other)?;
        Ok(Self {
            values: self
                .values
                .iter()
                .zip(&other.values)
                .map(|(a, b)| operation(a, b))
                .collect(),
        })
    }

    fn sum_value(&self) -> Rational {
        Rational {
            value: self.values.iter().fold(BigRational::zero(), |acc, value| {
                BigRational::add_ref(&acc, value)
            }),
        }
    }

    fn dot_value(&self, other: &Self) -> Result<Rational, Failure> {
        self.same_length(other)?;
        Ok(Rational {
            value: self
                .values
                .iter()
                .zip(&other.values)
                .fold(BigRational::zero(), |acc, (a, b)| {
                    BigRational::add_ref(&acc, &BigRational::mul_ref(a, b))
                }),
        })
    }
}

#[pymethods]
impl RationalArray {
    fn __len__(&self) -> usize {
        self.values.len()
    }

    fn as_integer_ratios(&self, py: Python<'_>) -> Vec<(BigInt, BigInt)> {
        py.detach(|| {
            self.values
                .iter()
                .map(|value| (value.numer().clone(), value.denom().clone()))
                .collect()
        })
    }

    fn at(&self, py: Python<'_>, index: BigInt) -> Transport<Rational> {
        transport(py.detach(|| {
            index
                .to_usize()
                .and_then(|index| self.values.get(index))
                .cloned()
                .map(|value| Rational { value })
                .ok_or_else(|| {
                    Failure::binding(
                        "OUT_OF_RANGE",
                        "索引超出数组范围 / Index outside array bounds",
                    )
                })
        }))
    }

    fn sum(&self, py: Python<'_>) -> Rational {
        py.detach(|| self.sum_value())
    }

    fn dot(&self, py: Python<'_>, other: &Self) -> Transport<Rational> {
        transport(py.detach(|| self.dot_value(other)))
    }

    fn add(&self, py: Python<'_>, other: &Self) -> Transport<Self> {
        transport(py.detach(|| self.binary(other, BigRational::add_ref)))
    }

    fn subtract(&self, py: Python<'_>, other: &Self) -> Transport<Self> {
        transport(py.detach(|| self.binary(other, BigRational::sub_ref)))
    }

    fn multiply(&self, py: Python<'_>, other: &Self) -> Transport<Self> {
        transport(py.detach(|| self.binary(other, BigRational::mul_ref)))
    }

    fn divide(&self, py: Python<'_>, other: &Self) -> Transport<Self> {
        transport(py.detach(|| {
            self.same_length(other)?;
            if let Some(index) = other.values.iter().position(Zero::is_zero) {
                return Err(Failure::input(format!(
                    "除数不能为零 / Divisor must not be zero; 索引 / index: {index}"
                )));
            }
            self.binary(other, BigRational::div_ref)
        }))
    }
}

#[pyfunction]
pub fn _create_rational_array(
    py: Python<'_>,
    inputs: Vec<(BigInt, BigInt)>,
) -> Transport<RationalArray> {
    transport(py.detach(|| RationalArray::create(inputs)))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn empty_reductions_have_exact_zero_identity() {
        let values = RationalArray::create(vec![]).unwrap();
        assert!(values.sum_value().value.is_zero());
        assert!(values.dot_value(&values).unwrap().value.is_zero());
    }

    #[test]
    fn construction_and_length_fail_without_partial_output() {
        let error = RationalArray::create(vec![(1.into(), 2.into()), (3.into(), 0.into())])
            .err()
            .unwrap();
        assert!(error.message.contains("index: 1"));
        let a = RationalArray::create(vec![(1.into(), 2.into())]).unwrap();
        let b = RationalArray::create(vec![]).unwrap();
        assert!(a.dot_value(&b).is_err());
        assert!(a.binary(&b, BigRational::add_ref).is_err());
        assert_eq!(a.sum_value().value, BigRational::new(1.into(), 2.into()));
    }
}
