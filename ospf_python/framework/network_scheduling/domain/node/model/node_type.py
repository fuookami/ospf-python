"""节点类型枚举 / Node type enumeration.

定义网络中节点的功能分类。
Defines functional categories for nodes in a network.
"""

from __future__ import annotations

import enum


class NodeType(enum.Enum):
    """节点类型 / Node type.

    描述网络节点在流优化中的角色。
    Describes the role of a network node in flow optimization.

    Attributes:
        value: 类型字符串标识 / Type string identifier.
    """

    SOURCE = "source"
    """源节点 / Source node.

    流的起点，仅产出流量。
    Origin of flow, only produces flow.
    """

    SINK = "sink"
    """汇节点 / Sink node.

    流的终点，仅接收流量。
    Destination of flow, only consumes flow.
    """

    TRANSIT = "transit"
    """转运节点 / Transit node.

    中间节点，流量守恒。
    Intermediate node, flow is conserved.
    """

    JUNCTION = "junction"
    """汇聚节点 / Junction node.

    多条路径的交汇点，流量守恒。
    Intersection of multiple paths, flow is conserved.
    """

    @property
    def is_terminal(self) -> bool:
        """是否为终端节点 / Whether this is a terminal node.

        源节点和汇节点为终端节点。
        Source and sink nodes are terminal nodes.

        Returns:
            是否为终端节点 / Whether terminal.
        """
        return self is NodeType.SOURCE or self is NodeType.SINK

    @property
    def can_route(self) -> bool:
        """是否可以路由 / Whether this node can route flow.

        转运节点和汇聚节点可以路由流量。
        Transit and junction nodes can route flow.

        Returns:
            是否可路由 / Whether routable.
        """
        return self is NodeType.TRANSIT or self is NodeType.JUNCTION
