"""中转节点带宽约束 / Transfer node bandwidth constraint.

确保中转节点的总通过带宽不超过其处理能力。
Ensures that a transfer node's total throughput bandwidth
does not exceed its processing capacity.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TransferNodeViolation:
    """中转节点违反记录 / Transfer node violation record.

    记录一个中转节点的带宽超限信息。
    Records bandwidth excess information for a transfer node.

    Attributes:
        node_id: 节点标识 / Node identifier.
        total_throughput: 总通过带宽 / Total throughput bandwidth.
        max_bandwidth: 最大带宽处理能力 /
            Maximum bandwidth processing capacity.
        excess: 超出量 / Excess amount.
    """

    node_id: str = ""
    """节点标识 / Node identifier."""

    total_throughput: float = 0.0
    """总通过带宽 / Total throughput bandwidth."""

    max_bandwidth: float = 0.0
    """最大带宽处理能力 / Maximum bandwidth processing capacity."""

    excess: float = 0.0
    """超出量 / Excess amount."""


@dataclass(frozen=True)
class TransferNodeBandwidthConstraint:
    """中转节点带宽约束 / Transfer node bandwidth constraint.

    验证中转节点的总通过带宽不超过其处理能力。遍历所有
    中转节点，汇总经过该节点的带宽分配并与限制比较。
    Validates that each transfer node's total throughput does not
    exceed its processing capacity. Iterates over all transfer
    nodes, aggregating bandwidth allocations passing through
    each node and comparing against limits.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
    """

    constraint_name_prefix: str = "transfer_node"
    """约束名称前缀 / Constraint name prefix."""

    def check_nodes(
        self,
        *,
        transfer_nodes: dict[str, float],
        node_throughputs: dict[str, float],
    ) -> tuple[TransferNodeViolation, ...]:
        """检查所有中转节点的带宽约束。

        Check bandwidth constraints for all transfer nodes.

        Args:
            transfer_nodes: 中转节点标识到最大带宽的映射。
                / Transfer node-to-max-bandwidth mapping.
            node_throughputs: 节点标识到总通过带宽的映射。
                / Node-to-total-throughput mapping.

        Returns:
            违反记录元组。/ Tuple of violation records.
        """
        violations: list[TransferNodeViolation] = []
        for node_id, max_bw in transfer_nodes.items():
            if max_bw <= 0.0:
                continue
            throughput = node_throughputs.get(node_id, 0.0)
            if throughput > max_bw:
                violations.append(
                    TransferNodeViolation(
                        node_id=node_id,
                        total_throughput=throughput,
                        max_bandwidth=max_bw,
                        excess=throughput - max_bw,
                    )
                )
        return tuple(violations)

    def is_feasible(
        self,
        *,
        transfer_nodes: dict[str, float],
        node_throughputs: dict[str, float],
    ) -> bool:
        """检查中转节点约束是否可行。

        Check whether transfer node constraints are feasible.

        Args:
            transfer_nodes: 中转节点标识到最大带宽的映射。
                / Transfer node-to-max-bandwidth mapping.
            node_throughputs: 节点标识到总通过带宽的映射。
                / Node-to-total-throughput mapping.

        Returns:
            所有中转节点的带宽均在限制内时返回 True。
            True if all transfer node bandwidths are within limits.
        """
        return (
            len(
                self.check_nodes(
                    transfer_nodes=transfer_nodes,
                    node_throughputs=node_throughputs,
                )
            )
            == 0
        )

    def compute_throughput(
        self,
        node_id: str,
        routing_paths: tuple[tuple[str, ...], ...],
        service_demands: dict[str, float],
    ) -> float:
        """计算指定节点的总通过带宽。

        Compute total throughput bandwidth for a specific node.

        Args:
            node_id: 节点标识。/ Node identifier.
            routing_paths: 路由路径列表，每条路径为节点序列。
                / Routing path list, each path is a node sequence.
            service_demands: 服务标识到需求的映射。
                / Service-to-demand mapping.

        Returns:
            总通过带宽值。/ Total throughput bandwidth value.
        """
        total = 0.0
        for svc_id, path in zip(service_demands.keys(), routing_paths, strict=False):
            if node_id in path:
                total += service_demands.get(svc_id, 0.0)
        return total

    def constraint_name(
        self,
        node_id: str,
    ) -> str:
        """生成约束名称。

        Generate constraint name.

        Args:
            node_id: 节点标识。/ Node identifier.

        Returns:
            约束名称字符串。/ Constraint name string.
        """
        return f"{self.constraint_name_prefix}_{node_id}"
