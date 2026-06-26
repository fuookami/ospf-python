"""Node assignment constraint — 节点流守恒约束。

确保每个中间节点的流入量等于流出量，源节点和目标节点
满足需求量约束。
Ensures flow conservation at each intermediate node, with
source and target nodes satisfying demand constraints.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..aggregation import RouteAggregation


@dataclass(frozen=True)
class FlowBalance:
    """流守恒状态 / Flow balance status.

    Attributes:
        node: 节点标识 / Node identifier.
        inflow: 流入量 / Inflow amount.
        outflow: 流出量 / Outflow amount.
        imbalance: 不平衡量（正表示流入多） / Imbalance (positive = excess inflow).
        is_balanced: 是否平衡 / Whether balanced.
    """

    node: str
    inflow: float
    outflow: float
    imbalance: float
    is_balanced: bool


@dataclass(frozen=True)
class NodeAssignmentConstraint:
    """节点流守恒约束 / Node flow conservation constraint.

    生成节点级流守恒约束数据。对每个已分配路由的服务，
    在路径上每个中间节点处检查流入等于流出。
    Generates node-level flow conservation constraint data.
    For each assigned service route, verifies inflow equals
    outflow at every intermediate node on the path.

    Attributes:
        constraint_name_prefix: 约束名称前缀 /
            Constraint name prefix.
        tolerance: 浮点容差 / Floating-point tolerance.
    """

    constraint_name_prefix: str = "flow_conservation"
    tolerance: float = 1e-9

    def build_constraints(
        self,
        aggregation: RouteAggregation,
    ) -> tuple[FlowBalance, ...]:
        """构建流守恒约束列表。

        Build the list of flow conservation constraints.

        统计每个节点在所有已分配路径中的流入量和流出量，
        验证中间节点是否平衡。
        Counts inflow and outflow at each node across all
        assigned paths, verifying intermediate node balance.

        Args:
            aggregation: 路由聚合 / Route aggregation.

        Returns:
            流守恒状态元组 / Tuple of flow balance statuses.
        """
        inflow: dict[str, float] = {}
        outflow: dict[str, float] = {}

        for assignment in aggregation.assignments:
            edges = assignment.edge_sequence()
            service = aggregation.get_service(assignment.service_id)
            demand = service.demand if service else 1.0

            for src, tgt in edges:
                outflow[src] = outflow.get(src, 0.0) + demand
                inflow[tgt] = inflow.get(tgt, 0.0) + demand

        graph = aggregation.graph
        results: list[FlowBalance] = []
        for node in graph.nodes:
            node_in = inflow.get(node, 0.0)
            node_out = outflow.get(node, 0.0)
            imbalance = node_in - node_out

            # 源节点和目标节点允许不平衡（它们是流量的产生/消耗点）
            # Source and target nodes are allowed to be imbalanced
            is_source = any(
                a.path[0] == node for a in aggregation.assignments if a.path
            )
            is_target = any(
                a.path[-1] == node for a in aggregation.assignments if a.path
            )

            if is_source and not is_target:
                # 源节点：净流出应等于总需求
                # Source: net outflow should equal total demand
                is_balanced = imbalance <= self.tolerance
            elif is_target and not is_source:
                # 目标节点：净流入应等于总需求
                # Target: net inflow should equal total demand
                is_balanced = imbalance >= -self.tolerance
            elif is_source and is_target:
                # 同时是源和目标，检查各自服务的净流量
                # Both source and target, check per-service net flow
                is_balanced = True
            else:
                # 中间节点：流入应等于流出
                # Intermediate: inflow should equal outflow
                is_balanced = abs(imbalance) <= self.tolerance

            results.append(
                FlowBalance(
                    node=node,
                    inflow=node_in,
                    outflow=node_out,
                    imbalance=imbalance,
                    is_balanced=is_balanced,
                )
            )

        return tuple(results)

    def constraint_name(self, node: str) -> str:
        """生成约束名称。

        Generate the constraint name.

        Args:
            node: 节点标识 / Node identifier.

        Returns:
            约束名称字符串 / Constraint name string.
        """
        return f"{self.constraint_name_prefix}_{node}"

    def is_feasible(self, aggregation: RouteAggregation) -> bool:
        """检查流守恒约束是否可行。

        Check whether flow conservation constraints are feasible.

        Args:
            aggregation: 路由聚合 / Route aggregation.

        Returns:
            若所有节点流守恒均满足则返回 True。
            True if all node flow conservation constraints are satisfied.
        """
        return all(fb.is_balanced for fb in self.build_constraints(aggregation))

    def violations(
        self,
        aggregation: RouteAggregation,
    ) -> tuple[FlowBalance, ...]:
        """获取所有违反流守恒的节点。

        Get all nodes that violate flow conservation.

        Args:
            aggregation: 路由聚合 / Route aggregation.

        Returns:
            违反约束的流守恒状态元组。
            Tuple of flow balance statuses violating constraints.
        """
        return tuple(
            fb for fb in self.build_constraints(aggregation) if not fb.is_balanced
        )
