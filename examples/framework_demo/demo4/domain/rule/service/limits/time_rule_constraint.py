"""Time rule constraint enforcement.

时间规则约束执行 / Time rule constraint enforcement.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TimeSlotView:
    """View of a time slot for constraint checking.

    用于约束检查的时间槽视图。
    """

    slot_id: str
    start_time: float
    end_time: float
    task_count: int


@dataclass(frozen=True)
class TimeWindow:
    """An allowed time window for scheduling.

    允许的调度时间窗口。
    """

    window_start: float
    window_end: float


class TimeRuleConstraint:
    """Enforces time-based scheduling rules.

    强制执行基于时间的调度规则。
    """

    def __init__(
        self,
        *,
        min_gap: float = 0.0,
        allowed_windows: tuple[TimeWindow, ...] = (),
    ) -> None:
        self._min_gap = min_gap
        self._windows = allowed_windows

    def check(
        self,
        slots: tuple[TimeSlotView, ...],
    ) -> list[str]:
        """Validate time rules against scheduled slots.

        对已调度的时间槽验证时间规则。
        """
        violations: list[str] = []
        violations.extend(
            self._check_gaps(slots),
        )
        if self._windows:
            violations.extend(
                self._check_windows(slots),
            )
        violations.extend(
            self._check_slot_ordering(slots),
        )
        return violations

    def _check_gaps(
        self,
        slots: tuple[TimeSlotView, ...],
    ) -> list[str]:
        """Check minimum gap between consecutive slots.

        检查连续时间槽之间的最小间隔。
        """
        violations: list[str] = []
        if self._min_gap <= 0.0:
            return violations
        sorted_slots = sorted(
            slots,
            key=lambda s: s.start_time,
        )
        for left, right in zip(
            sorted_slots,
            sorted_slots[1:],
            strict=False,
        ):
            gap = right.start_time - left.end_time
            if 0 < gap < self._min_gap:
                violations.append(
                    f"Gap {gap:.1f}s between "
                    f"'{left.slot_id}' and "
                    f"'{right.slot_id}' "
                    f"(min {self._min_gap:.1f}s)"
                )
        return violations

    def _check_windows(
        self,
        slots: tuple[TimeSlotView, ...],
    ) -> list[str]:
        """Check that all slots fall within allowed windows.

        检查所有时间槽是否在允许的窗口内。
        """
        violations: list[str] = []
        for slot in slots:
            in_window = False
            for window in self._windows:
                if (
                    slot.start_time >= window.window_start
                    and slot.end_time <= window.window_end
                ):
                    in_window = True
                    break
            if not in_window:
                violations.append(
                    f"Slot '{slot.slot_id}' "
                    f"({slot.start_time:.1f}-"
                    f"{slot.end_time:.1f}) "
                    f"outside allowed windows"
                )
        return violations

    def _check_slot_ordering(
        self,
        slots: tuple[TimeSlotView, ...],
    ) -> list[str]:
        """Check that slots have valid time ordering.

        检查时间槽是否有有效的时间顺序。
        """
        violations: list[str] = []
        for slot in slots:
            if slot.start_time > slot.end_time:
                violations.append(
                    f"Slot '{slot.slot_id}' has "
                    f"start ({slot.start_time:.1f}) "
                    f"> end ({slot.end_time:.1f})"
                )
        return violations
