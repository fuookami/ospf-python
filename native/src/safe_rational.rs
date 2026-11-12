//! 保留上游有理数算术，避免其递归顺序比较。 / Keep upstream rational arithmetic without recursive ordering.

use std::cmp::Ordering;
use std::ops::{Add, Div, Mul, Neg, Sub};

use num_rational::BigRational;
use num_traits::{FromPrimitive, One, Signed, ToPrimitive, Zero};
use ospf_rust_core::model::LinearModelValue;
use ospf_rust_core::solver::{SolveValue, SolveValueConversionPolicy};
use ospf_rust_quantities::unit::UnitConversionValue;

use crate::numeric::compare_rationals;

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct SafeRational(pub(crate) BigRational);

impl UnitConversionValue for SafeRational {
    fn from_decimal(value: &bigdecimal::BigDecimal) -> Option<Self> {
        BigRational::from_decimal(value).map(Self)
    }
}

impl PartialOrd for SafeRational {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for SafeRational {
    fn cmp(&self, other: &Self) -> Ordering {
        compare_rationals(&self.0, &other.0)
    }
}

impl Add for SafeRational {
    type Output = Self;

    fn add(self, other: Self) -> Self {
        Self(self.0 + other.0)
    }
}

impl Sub for SafeRational {
    type Output = Self;

    fn sub(self, other: Self) -> Self {
        Self(self.0 - other.0)
    }
}

impl Mul for SafeRational {
    type Output = Self;

    fn mul(self, other: Self) -> Self {
        Self(self.0 * other.0)
    }
}

impl Div for SafeRational {
    type Output = Self;

    fn div(self, other: Self) -> Self {
        Self(self.0 / other.0)
    }
}

impl Neg for SafeRational {
    type Output = Self;

    fn neg(self) -> Self {
        Self(-self.0)
    }
}

impl Zero for SafeRational {
    fn zero() -> Self {
        Self(BigRational::zero())
    }

    fn is_zero(&self) -> bool {
        self.0.is_zero()
    }
}

impl One for SafeRational {
    fn one() -> Self {
        Self(BigRational::one())
    }
}

impl FromPrimitive for SafeRational {
    fn from_i64(value: i64) -> Option<Self> {
        BigRational::from_i64(value).map(Self)
    }

    fn from_u64(value: u64) -> Option<Self> {
        BigRational::from_u64(value).map(Self)
    }

    fn from_i128(value: i128) -> Option<Self> {
        BigRational::from_i128(value).map(Self)
    }

    fn from_u128(value: u128) -> Option<Self> {
        BigRational::from_u128(value).map(Self)
    }

    fn from_f64(value: f64) -> Option<Self> {
        BigRational::from_float(value).map(Self)
    }
}

impl ToPrimitive for SafeRational {
    fn to_i64(&self) -> Option<i64> {
        self.0.to_i64()
    }

    fn to_u64(&self) -> Option<u64> {
        self.0.to_u64()
    }

    fn to_i128(&self) -> Option<i128> {
        self.0.to_i128()
    }

    fn to_u128(&self) -> Option<u128> {
        self.0.to_u128()
    }

    fn to_f64(&self) -> Option<f64> {
        self.0.to_f64()
    }
}

impl LinearModelValue for SafeRational {
    fn is_finite_value(&self) -> bool {
        true
    }

    fn is_integral_value(&self, tolerance: &Self) -> bool {
        let fraction = (&self.0 - BigRational::from_integer(self.0.to_integer())).abs();
        compare_rationals(&fraction, &tolerance.0) != Ordering::Greater
            || compare_rationals(&(BigRational::one() - fraction), &tolerance.0)
                != Ordering::Greater
    }
}

impl SolveValue for SafeRational {
    fn type_name() -> &'static str {
        <BigRational as SolveValue>::type_name()
    }

    fn from_f64_with_policy(
        value: f64,
        policy: SolveValueConversionPolicy,
    ) -> ospf_rust_core::error::Result<Self> {
        BigRational::from_f64_with_policy(value, policy).map(Self)
    }

    fn to_f64_with_policy(
        &self,
        policy: SolveValueConversionPolicy,
    ) -> ospf_rust_core::error::Result<f64> {
        self.0.to_f64_with_policy(policy)
    }

    fn to_nonnegative_integral_upper_bound(&self) -> ospf_rust_core::error::Result<i64> {
        self.0.to_nonnegative_integral_upper_bound()
    }
}

#[cfg(test)]
mod tests {
    use num_bigint::BigInt;

    use super::*;

    #[test]
    fn deep_order_and_integrality_use_constant_stack_comparisons() {
        let (mut a, mut b) = (BigInt::from(0), BigInt::from(1));
        for _ in 0..16384 {
            (a, b) = (b.clone(), a + b);
        }
        let left = SafeRational(BigRational::new(a.clone(), b.clone()));
        let right = SafeRational(BigRational::new(b.clone(), a + b));
        assert_eq!(left.cmp(&right), compare_rationals(&left.0, &right.0));
        let tolerance = SafeRational(BigRational::new(1.into(), 10.into()));
        assert!(
            SafeRational(BigRational::new((-19).into(), 10.into())).is_integral_value(&tolerance)
        );
        assert!(
            !SafeRational(BigRational::new((-18).into(), 10.into())).is_integral_value(&tolerance)
        );
    }

    #[test]
    fn strict_backend_conversion_keeps_upstream_policy() {
        let exact = SafeRational::from_f64(0.1).unwrap();
        assert_eq!(
            exact
                .to_f64_with_policy(SolveValueConversionPolicy::Strict)
                .unwrap(),
            0.1
        );
        let decimal = SafeRational(BigRational::new(1.into(), 10.into()));
        assert!(
            decimal
                .to_f64_with_policy(SolveValueConversionPolicy::Strict)
                .is_err()
        );
    }
}
