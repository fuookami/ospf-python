"""几何图元模块。

Geometry primitives module.
"""

from ospf_python.math.geometry.axis2 import Axis2
from ospf_python.math.geometry.axis3 import Axis3
from ospf_python.math.geometry.axis_permutation2 import AxisPermutation2
from ospf_python.math.geometry.axis_permutation3 import AxisPermutation3
from ospf_python.math.geometry.axis_plane3 import AxisPlane3
from ospf_python.math.geometry.box2 import Box2
from ospf_python.math.geometry.box3 import Box3
from ospf_python.math.geometry.circle import Circle
from ospf_python.math.geometry.cuboid3 import Cuboid3
from ospf_python.math.geometry.cuboid3_view import Cuboid3View
from ospf_python.math.geometry.cylinder3 import Cylinder3
from ospf_python.math.geometry.dimension import Dimension
from ospf_python.math.geometry.distance import (
    distance,
    distance3,
    distance_squared,
    manhattan_distance,
)
from ospf_python.math.geometry.edge import Edge
from ospf_python.math.geometry.placement2 import Placement2
from ospf_python.math.geometry.placement3 import Placement3
from ospf_python.math.geometry.plane_frame3 import PlaneFrame3
from ospf_python.math.geometry.point import Point, Point3
from ospf_python.math.geometry.projection2 import Projection2
from ospf_python.math.geometry.quadrilateral import Quadrilateral
from ospf_python.math.geometry.quantity_ops import QuantityOps
from ospf_python.math.geometry.rectangle import Rectangle
from ospf_python.math.geometry.shape3 import Shape3
from ospf_python.math.geometry.triangle import Triangle
from ospf_python.math.geometry.triangulation import triangulate
from ospf_python.math.geometry.vector import Vector

__all__ = [
    "Axis2",
    "Axis3",
    "AxisPermutation2",
    "AxisPermutation3",
    "AxisPlane3",
    "Box2",
    "Box3",
    "Circle",
    "Cuboid3",
    "Cuboid3View",
    "Cylinder3",
    "Dimension",
    "Edge",
    "Placement2",
    "Placement3",
    "PlaneFrame3",
    "Point",
    "Point3",
    "Projection2",
    "Quadrilateral",
    "QuantityOps",
    "Rectangle",
    "Shape3",
    "Triangle",
    "Vector",
    "distance",
    "distance3",
    "distance_squared",
    "manhattan_distance",
    "triangulate",
]
