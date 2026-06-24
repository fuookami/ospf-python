"""物理量定义。/ Physical quantity definitions.

包含物理量、值域、极值工具和时长扩展。
Contains quantity, value range, min/max utilities,
and duration extensions.
"""

from ospf_python.quantities.quantity.duration_extensions import (
    from_hours as from_hours,
)
from ospf_python.quantities.quantity.duration_extensions import (
    from_minutes as from_minutes,
)
from ospf_python.quantities.quantity.duration_extensions import (
    to_timedelta as to_timedelta,
)
from ospf_python.quantities.quantity.min_max import (
    max_quantity as max_quantity,
)
from ospf_python.quantities.quantity.min_max import (
    min_quantity as min_quantity,
)
from ospf_python.quantities.quantity.quantity import (
    Quantity as Quantity,
)
from ospf_python.quantities.quantity.value_range import (
    QuantityValueRange as QuantityValueRange,
)
