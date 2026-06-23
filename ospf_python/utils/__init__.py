"""ospf-python utilities.

Provides error handling, Result pattern, and functional primitives.
"""

from ospf_python.utils.error import (
    Err,
    Error,
    ErrorCode,
    ExErr,
    LazyErr,
)
from ospf_python.utils.functional import (
    compose,
    constant,
    curry,
    flip,
    identity,
    ignore,
    tap,
)
from ospf_python.utils.result import (
    ExResult,
    Failed,
    Fatal,
    Ok,
    Result,
    Ret,
    Try,
    Warn,
    failed,
    fatal,
    ok,
    pipe,
    run,
    warn,
)

__all__ = [
    # Error types
    "Error",
    "ErrorCode",
    "Err",
    "ExErr",
    "LazyErr",
    # Result types
    "Result",
    "Ok",
    "Failed",
    "Fatal",
    "ExResult",
    "Warn",
    "Try",
    "Ret",
    # Result factory functions
    "ok",
    "failed",
    "fatal",
    "warn",
    # Result combinators
    "run",
    "pipe",
    # Functional primitives
    "identity",
    "constant",
    "compose",
    "curry",
    "flip",
    "tap",
    "ignore",
]
