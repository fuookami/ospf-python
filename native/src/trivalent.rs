//! 三值常量AST及枚举传输适配；逻辑求值唯一复用固定上游。 / Trivalent constant AST and enum transport; logical evaluation uses only pinned upstream.

use ospf_rust_math::Trivalent;
use ospf_rust_math::symbol::expression::{
    BooleanExpression, EmptyEvaluationContext, evaluate_boolean,
};
use pyo3::prelude::*;
use pyo3::types::PyBool;

use crate::failure::{Failure, Transport, transport};

fn decode(value: &Bound<'_, PyAny>) -> Result<Trivalent, Failure> {
    if value.is_none() {
        Ok(Trivalent::Unknown)
    } else if value.is_exact_instance_of::<PyBool>() {
        value
            .extract::<bool>()
            .map(Trivalent::from)
            .map_err(|_| Failure::input("无效三值传输 / Invalid trivalent transport"))
    } else {
        Err(Failure::input(
            "三值传输必须是bool或None / Trivalent transport must be bool or None",
        ))
    }
}

fn evaluate(operation: &str, left: Trivalent, right: Trivalent) -> Result<Option<bool>, Failure> {
    let left = BooleanExpression::constant(left);
    let expression = match operation {
        "and" => BooleanExpression::and(vec![left, BooleanExpression::constant(right)]),
        "or" => BooleanExpression::or(vec![left, BooleanExpression::constant(right)]),
        "not" if right == Trivalent::Unknown => BooleanExpression::not_expr(left),
        "bool" if right == Trivalent::Unknown => left,
        _ => {
            return Err(Failure::input(
                "无效三值操作或操作数数量 / Invalid trivalent operation or operand count",
            ));
        }
    };
    Ok(evaluate_boolean(&expression, &EmptyEvaluationContext).into())
}

/// 只接收门面已验证的有限状态，不触发外部truth/index/float协议。 / Accept only facade-validated finite states, without external truth/index/float protocols.
#[pyfunction]
#[pyo3(signature = (*, operation, left, right))]
pub(crate) fn _trivalent(
    operation: &str,
    left: &Bound<'_, PyAny>,
    right: &Bound<'_, PyAny>,
) -> Transport<Option<bool>> {
    transport(
        decode(left)
            .and_then(|left| decode(right).and_then(|right| evaluate(operation, left, right))),
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn all_binary_states_use_the_pinned_evaluator() {
        let states = [Trivalent::True, Trivalent::False, Trivalent::Unknown];
        let and = [
            [Some(true), Some(false), None],
            [Some(false), Some(false), Some(false)],
            [None, Some(false), None],
        ];
        let or = [
            [Some(true), Some(true), Some(true)],
            [Some(true), Some(false), None],
            [Some(true), None, None],
        ];
        for (i, left) in states.iter().enumerate() {
            for (j, right) in states.iter().enumerate() {
                assert_eq!(evaluate("and", *left, *right).unwrap(), and[i][j]);
                assert_eq!(evaluate("or", *left, *right).unwrap(), or[i][j]);
            }
        }
    }

    #[test]
    fn all_unary_states_and_unknown_success_are_preserved() {
        for (state, negated, optional) in [
            (Trivalent::True, Some(false), Some(true)),
            (Trivalent::False, Some(true), Some(false)),
            (Trivalent::Unknown, None, None),
        ] {
            assert_eq!(evaluate("not", state, Trivalent::Unknown).unwrap(), negated);
            assert_eq!(
                evaluate("bool", state, Trivalent::Unknown).unwrap(),
                optional
            );
        }
        assert!(
            transport(evaluate("not", Trivalent::Unknown, Trivalent::Unknown))
                .1
                .is_none()
        );
    }

    #[test]
    fn invalid_operation_and_unary_arity_are_explicit_failures() {
        for operation in ["", "xor", "NOT", "not", "bool"] {
            assert_eq!(
                evaluate(operation, Trivalent::True, Trivalent::False)
                    .unwrap_err()
                    .category,
                "ILLEGAL_ARGUMENT"
            );
        }
    }
}
