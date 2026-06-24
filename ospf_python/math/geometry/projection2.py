"""二维投影工具。

2D projection utilities.
"""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.math.geometry.point import Point


@dataclass(frozen=True)
class Projection2:
    """二维投影结果。

    2D projection result.

    Attributes:
        point: 投影点。/ Projected point.
        parameter: 投影参数 t。/ Projection parameter t.
    """

    point: Point
    parameter: float

    @staticmethod
    def onto_line(
        *,
        point: Point,
        line_start: Point,
        line_end: Point,
    ) -> Projection2:
        """将点投影到线段上。

        Project a point onto a line segment.

        Args:
            point: 待投影的点。/ Point to project.
            line_start: 线段起点。/ Line start.
            line_end: 线段终点。/ Line end.

        Returns:
            投影结果。/ Projection result.
        """
        dx = line_end.x - line_start.x
        dy = line_end.y - line_start.y
        len_sq = dx * dx + dy * dy
        if len_sq == 0.0:
            return Projection2(point=line_start, parameter=0.0)
        px = point.x - line_start.x
        py = point.y - line_start.y
        t = (px * dx + py * dy) / len_sq
        t_clamped = max(0.0, min(1.0, t))
        proj = Point(
            x=line_start.x + t_clamped * dx,
            y=line_start.y + t_clamped * dy,
        )
        return Projection2(point=proj, parameter=t_clamped)
