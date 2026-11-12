"""Gantt scheduling produce aggregation."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any


@dataclass(frozen=True)
class ProduceAggregation:
    """生产聚合。

    Produce aggregation: the data the produce-scope constraints read.

    **为什么需要这些字段**：本包的两个约束构建器直接读聚合的数据：

    * `ProduceOrderConstraint.build_constraints` 读 `order_pairs` 与
      `assignments_for_item(...)`（后者取 `start_time` / `end_time`）；
    * `ProduceDemandConstraint.build_constraints` 读 `item_keys` 与
      `assignments_for_item(...)`（后者取 `assignment_amount`）。

    在此之前本类只有一个 `name` 字段，所以这两个构建器对真实聚合类调用时会抛
    `AttributeError`——行为测试一直用 `_StubProduceAggregation` 替身，掩盖了这一点。
    形状对齐同包下已可用的 `CapacitySchedulingAggregation`：
    私有元组字段 + 只读访问器 + 不可变的 `with_*` 构建器。

    The two produce-scope constraint builders read `order_pairs`, `item_keys`
    and `assignments_for_item(...)` off the aggregation. This class previously
    carried only `name`, so calling them with the real type raised `AttributeError`;
    the behavioral tests used a stub and hid it. The shape mirrors the working
    `CapacitySchedulingAggregation`: private tuple fields, read-only accessors and
    immutable `with_*` builders.

    Attributes:
        name: 聚合名称 / Aggregation name.
        capacities: 容量记录 / Capacity records.
        demands: 需求记录 / Demand records.
        order_pairs: 排序对 / Order pairs.
        batch_order_pairs: 批次排序对 / Batch order pairs.
        _assignments: 分配记录（私有，经访问器读取）/
            Assignment records (private, read through accessors).
    """

    name: str = "produce_aggregation"
    capacities: tuple[Any, ...] = ()
    demands: tuple[Any, ...] = ()
    order_pairs: tuple[Any, ...] = ()
    batch_order_pairs: tuple[Any, ...] = ()
    _assignments: tuple[Any, ...] = ()
    _batch_capacities: tuple[Any, ...] = ()

    @property
    def is_valid(self) -> bool:
        """检查是否可用。/ Check if valid."""
        return bool(self.name)

    @property
    def item_keys(self) -> tuple[str, ...]:
        """获取已注册的物料项标识。/ Get registered item keys.

        按首次出现顺序去重，与 `CapacitySchedulingAggregation.work_item_keys` 同构。
        与 `batch_keys` 保持一致：**缺键（`None`）的分配不产生标识**——否则 `None`
        会被当成一个合法物料项传进 `ProduceDemandConstraint`，而那里按 `None` 查
        `assignments_for_item` 只能得到空集，凭空多出一条「零分配」的约束。

        De-duplicated in first-appearance order, mirroring `work_item_keys`.
        Consistent with `batch_keys`: assignments without the attribute contribute no
        key, so a missing key cannot surface as a phantom zero-assignment constraint.
        """
        return tuple(
            dict.fromkeys(
                getattr(a, "item_key", "")
                for a in self._assignments
                if getattr(a, "item_key", None) is not None
            )
        )

    def assignments_for_item(
        self,
        item_key: str,
    ) -> tuple[Any, ...]:
        """获取指定物料项的分配。/ Get assignments for an item."""
        return tuple(
            a for a in self._assignments if getattr(a, "item_key", None) == item_key
        )

    @property
    def assignments(self) -> tuple[Any, ...]:
        """获取全部已注册分配。/ Get every registered assignment.

        只读暴露，使调用方可以一次遍历完成分组，而不必对每个物料项调用一次
        `assignments_for_item`（那是 O(项 × 分配)）。与
        `CapacitySchedulingAggregation.assignments` 同构。

        Read-only exposure so callers can group in a single pass instead of calling
        `assignments_for_item` per item (O(items x assignments)).
        """
        return self._assignments

    def assignments_for_batch(
        self,
        batch_key: str,
    ) -> tuple[Any, ...]:
        """获取指定批次的分配。/ Get assignments for a batch."""
        return tuple(
            a for a in self._assignments if getattr(a, "batch_key", None) == batch_key
        )

    @property
    def batch_keys(self) -> tuple[str, ...]:
        """获取已注册的批次标识。/ Get registered batch keys.

        按首次出现顺序去重，与 `item_keys` 同构。
        De-duplicated in first-appearance order, mirroring `item_keys`.
        """
        return tuple(
            dict.fromkeys(
                getattr(a, "batch_key", "")
                for a in self._assignments
                if getattr(a, "batch_key", None) is not None
            )
        )

    @property
    def batch_capacities(self) -> tuple[Any, ...]:
        """获取批次容量记录。/ Get batch capacity records.

        `batch_capacities` 是本类为批次域单独持有的元组（与按物料项的 `capacities`
        分开），因为两者由不同的约束构建器读取。默认空元组，经
        `with_batch_capacity` 追加。

        Batch capacity records, held separately from the item-level `capacities`
        because different constraint builders read them. Empty by default, appended
        through `with_batch_capacity`.
        """
        return self._batch_capacities

    def total_demand_for_batch(self, batch_key: str) -> float:
        """计算指定批次的总需求。/ Compute total demand for a batch.

        累加顺序与 `sum(...)` 相同（按分配注册顺序）。
        Same summation order as `sum(...)` over the registered assignments.
        """
        total = 0.0
        for assignment in self._assignments:
            if getattr(assignment, "batch_key", None) == batch_key:
                total += getattr(assignment, "demand", 0.0)
        return total

    def _append(self, field: str, value: Any) -> ProduceAggregation:
        """在指定字段末尾追加一项，返回新副本。/ Append to one field, returning a copy.

        六个 `with_*` 都只是「某个字段追加一项、其余不变」。逐一手抄全部七个字段
        容易在加新字段时漏掉一处（本类这一轮就新增了 `_batch_capacities`，
        当时六个构造器都要改）。这里集中一次。

        All six `with_*` builders just append to one field. Hand-copying all seven
        fields each time is how a newly added field gets missed (this class gained
        `_batch_capacities` this round, and all six builders had to change); this
        keeps the copy in one place.
        """
        current = getattr(self, field)
        return replace(self, **{field: (*current, value)})

    def with_batch_capacity(
        self,
        batch_capacity: Any,
    ) -> ProduceAggregation:
        """创建包含新批次容量的聚合副本。/ Copy with a new batch capacity."""
        return self._append("_batch_capacities", batch_capacity)

    def with_assignment(
        self,
        assignment: Any,
    ) -> ProduceAggregation:
        """创建包含新分配的聚合副本。/ Copy with a new assignment."""
        return self._append("_assignments", assignment)

    def with_capacity(
        self,
        capacity: Any,
    ) -> ProduceAggregation:
        """创建包含新容量的聚合副本。/ Copy with a new capacity."""
        return self._append("capacities", capacity)

    def with_demand(
        self,
        demand: Any,
    ) -> ProduceAggregation:
        """创建包含新需求的聚合副本。/ Copy with a new demand."""
        return self._append("demands", demand)

    def with_order_pair(
        self,
        order_pair: Any,
    ) -> ProduceAggregation:
        """创建包含新排序对的聚合副本。/ Copy with a new order pair."""
        return self._append("order_pairs", order_pair)

    def with_batch_order_pair(
        self,
        batch_order_pair: Any,
    ) -> ProduceAggregation:
        """创建包含新批次排序对的聚合副本。/ Copy with a new batch order pair."""
        return self._append("batch_order_pairs", batch_order_pair)
