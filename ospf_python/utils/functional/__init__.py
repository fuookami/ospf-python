# ospf_python.utils.functional

from ospf_python.utils.functional.boolean import all_of, any_of, none_of
from ospf_python.utils.functional.collection import (
    chunked,
    distinct_by,
    flatten,
    sum_of,
    zip_with_next,
)
from ospf_python.utils.functional.condition import Condition, ListFindResult
from ospf_python.utils.functional.date_time_range import (
    DateTimeRange,
    contains,
    overlaps,
)
from ospf_python.utils.functional.either import Either, Left, Right
from ospf_python.utils.functional.eq import Eq, PartialEq
from ospf_python.utils.functional.list import (
    first_or_none,
    last_or_none,
    max_by_or_none,
    min_by_or_none,
    single_or_none,
)
from ospf_python.utils.functional.map import (
    filter_keys,
    filter_values,
    map_keys,
    map_values,
    merge,
)
from ospf_python.utils.functional.min_max import clamp, ensure_max, ensure_min
from ospf_python.utils.functional.nullable import also_not_none, let_not_none
from ospf_python.utils.functional.ord import Ord, Order, PartialOrd
from ospf_python.utils.functional.predicate import and_then, negate, or_else
from ospf_python.utils.functional.quadruple import Quadruple
from ospf_python.utils.functional.result import (
    ExResult,
    Failed,
    Fatal,
    Ok,
    Result,
    Success,
    Warn,
)
from ospf_python.utils.functional.variant import (
    V3V1,
    V3V2,
    V3V3,
    V4V1,
    V4V2,
    V4V3,
    V4V4,
    V2Left,
    V2Right,
    Variant2,
    Variant3,
    Variant4,
)

__all__ = [
    # boolean
    "all_of",
    "any_of",
    "none_of",
    # condition
    "Condition",
    "ListFindResult",
    # either
    "Either",
    "Left",
    "Right",
    # eq
    "Eq",
    "PartialEq",
    # ord
    "Ord",
    "Order",
    "PartialOrd",
    # quadruple
    "Quadruple",
    # result
    "ExResult",
    "Failed",
    "Fatal",
    "Ok",
    "Result",
    "Success",
    "Warn",
    # variant
    "Variant2",
    "Variant3",
    "Variant4",
    "V2Left",
    "V2Right",
    "V3V1",
    "V3V2",
    "V3V3",
    "V4V1",
    "V4V2",
    "V4V3",
    "V4V4",
    # collection
    "flatten",
    "distinct_by",
    "chunked",
    "zip_with_next",
    "sum_of",
    # date_time_range
    "DateTimeRange",
    "contains",
    "overlaps",
    # list
    "first_or_none",
    "last_or_none",
    "single_or_none",
    "min_by_or_none",
    "max_by_or_none",
    # map
    "map_values",
    "map_keys",
    "filter_keys",
    "filter_values",
    "merge",
    # min_max
    "clamp",
    "ensure_min",
    "ensure_max",
    # nullable
    "let_not_none",
    "also_not_none",
    # predicate
    "negate",
    "and_then",
    "or_else",
]
