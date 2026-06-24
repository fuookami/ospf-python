"""值类型 / Value types.

定义远程求解域的值类型。
Defines value types for the remote solver domain.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SolverEndpoint:
    """求解器端点 / Solver endpoint.

    描述远程求解器的网络端点。
    Describes the network endpoint of a remote solver.

    Attributes:
        host: 主机地址 / The host address.
        port: 端口号 / The port number.
        protocol: 通信协议 / The communication protocol.
    """

    host: str
    port: int
    protocol: str = "https"


@dataclass(frozen=True)
class SolverCapability:
    """求解器能力 / Solver capability.

    描述远程求解器支持的功能。
    Describes capabilities supported by a remote solver.

    Attributes:
        solver_type: 求解器类型 / The solver type.
        supports_integer: 是否支持整数 / Whether integers are supported.
        supports_quadratic: 是否支持二次项 / Whether quadratic terms are supported.
        max_variables: 最大变量数 / Maximum number of variables.
    """

    solver_type: str
    supports_integer: bool = False
    supports_quadratic: bool = False
    max_variables: int = 0
