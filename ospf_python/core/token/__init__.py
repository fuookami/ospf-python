"""Core token module.

Provides token system for model elements.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, unique
from typing import TypeVar

T = TypeVar("T")


@unique
class TokenType(Enum):
    """Token type.

    Token 类型。
    """

    VARIABLE = "variable"
    CONSTRAINT = "constraint"
    OBJECTIVE = "objective"
    EXPRESSION = "expression"


@dataclass(frozen=True, slots=True)
class Token:
    """Token for identifying model elements.

    用于标识模型元素的 Token。
    """

    name: str
    token_type: TokenType
    index: int = -1

    def __repr__(self) -> str:
        """String representation."""
        return f"Token({self.name}, {self.token_type.value}, {self.index})"


@dataclass(frozen=True, slots=True)
class VariableToken(Token):
    """Token for variables.

    变量 Token。
    """

    token_type: TokenType = TokenType.VARIABLE


@dataclass(frozen=True, slots=True)
class ConstraintToken(Token):
    """Token for constraints.

    约束 Token。
    """

    token_type: TokenType = TokenType.CONSTRAINT


@dataclass(frozen=True, slots=True)
class ObjectiveToken(Token):
    """Token for objectives.

    目标 Token。
    """

    token_type: TokenType = TokenType.OBJECTIVE


def variable_token(name: str, index: int = -1) -> VariableToken:
    """Create a variable token."""
    return VariableToken(name, TokenType.VARIABLE, index)


def constraint_token(name: str, index: int = -1) -> ConstraintToken:
    """Create a constraint token."""
    return ConstraintToken(name, TokenType.CONSTRAINT, index)


def objective_token(name: str, index: int = -1) -> ObjectiveToken:
    """Create an objective token."""
    return ObjectiveToken(name, TokenType.OBJECTIVE, index)
