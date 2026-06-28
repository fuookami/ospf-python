# Framework API Reference

Domain frameworks for optimization problems.

## bpp1d — 1D Bin Packing

Pack items into bins minimizing the number of bins.

```python
from ospf_python.framework.bpp1d.domain.item.model.item import Item
from ospf_python.framework.bpp1d.domain.item.model.bin import Bin
from ospf_python.framework.bpp1d.domain.solution.service.bin_packer import BinPacker
from ospf_python.framework.bpp1d.domain.constraint.model.constraint import Constraint
from ospf_python.framework.bpp1d.domain.constraint.service.constraint_checker import ConstraintChecker
from ospf_python.framework.bpp1d.application.bpp1d_application_service import Bpp1dApplicationService
```

### Key Classes

| Class | Description |
|-------|-------------|
| `Item` | Item with width and height |
| `Bin` | Bin with capacity |
| `BinPacker` | FFD bin packing algorithm |
| `Constraint` | Capacity constraint |
| `ConstraintChecker` | Validates constraints |
| `Bpp1dApplicationService` | Application-level service |

## bpp2d — 2D Bin Packing

Place rectangles and circles into containers.

```python
from ospf_python.framework.bpp2d.domain.item.model.rectangle import Rectangle
from ospf_python.framework.bpp2d.domain.item.model.circle import Circle
from ospf_python.framework.bpp2d.domain.service.geometric_packer import GeometricPacker
from ospf_python.framework.bpp2d.domain.constraint.model.weight_constraint import WeightConstraint
from ospf_python.framework.bpp2d.domain.constraint.model.geometric_constraint import GeometricConstraint
```

### Key Classes

| Class | Description |
|-------|-------------|
| `Rectangle` | Rectangular item |
| `Circle` | Circular item |
| `GeometricPacker` | Places items in containers |
| `WeightConstraint` | Weight capacity constraint |
| `GeometricConstraint` | Non-overlap constraint |

## bpp3d — 3D Bin Packing

Column generation algorithm for 3D packing.

```python
from ospf_python.framework.bpp3d.application.service.column_generation_algorithm import ColumnGenerationAlgorithm
from ospf_python.framework.bpp3d.domain.item.model.item import Item3D
from ospf_python.framework.bpp3d.domain.item.model.bin import Bin3D
```

## csp1d — 1D Cutting Stock

Optimize 1D material cutting to minimize waste.

```python
from ospf_python.framework.csp1d.domain.material.model.material import Material
from ospf_python.framework.csp1d.domain.material.model.production import Production
from ospf_python.framework.csp1d.domain.material.material_context import MaterialContext
from ospf_python.framework.csp1d.domain.cutting_plan_generation.service.costar_filler import CostarFiller
```

### Key Classes

| Class | Description |
|-------|-------------|
| `Material` | Raw material with width/length |
| `Production` | Production demand |
| `MaterialContext` | Material domain context |
| `CostarFiller` | Co-star filling algorithm |

## csp2d — 2D Cutting Stock

Generate guillotine cutting plans for 2D sheets.

```python
from ospf_python.framework.csp2d.domain.material.model.sheet import Sheet
from ospf_python.framework.csp2d.domain.product.model.demand import Demand
from ospf_python.framework.csp2d.domain.product.model.shape import Shape
from ospf_python.framework.csp2d.domain.service.cutting_plan_generator import CuttingPlanGenerator
from ospf_python.framework.csp2d.domain.service.material_optimizer import MaterialOptimizer
```

### Key Classes

| Class | Description |
|-------|-------------|
| `Sheet` | Raw sheet material |
| `Shape` | Product shape |
| `Demand` | Demand for a shape |
| `CuttingPlanGenerator` | Generates cutting plans |
| `MaterialOptimizer` | Optimizes material usage |

## gantt_scheduling — Gantt Chart Scheduling

Resource-constrained scheduling with Gantt chart output.

```python
from ospf_python.framework.gantt_scheduling.application.service.task.task_application_service import TaskApplicationService
from ospf_python.framework.gantt_scheduling.application.service.bunch.bunch_application_service import BunchApplicationService
from ospf_python.framework.gantt_scheduling.application.model.gantt_problem import GanttProblem
from ospf_python.framework.gantt_scheduling.application.model.gantt_solution import GanttSolution
```

### Key Classes

| Class | Description |
|-------|-------------|
| `GanttProblem` | Problem definition |
| `GanttSolution` | Solution with schedule |
| `TaskApplicationService` | Task-level service |
| `BunchApplicationService` | Bunch-level service |

## network_scheduling — Network Scheduling

Shortest path and max flow optimization on networks.

```python
from ospf_python.framework.network_scheduling.domain.node.model.node import Node
from ospf_python.framework.network_scheduling.domain.node.model.node_type import NodeType
from ospf_python.framework.network_scheduling.domain.edge.model.edge import Edge
from ospf_python.framework.network_scheduling.domain.flow.model.demand import Demand
from ospf_python.framework.network_scheduling.domain.service.shortest_path import ShortestPath
from ospf_python.framework.network_scheduling.domain.service.flow_optimizer import FlowOptimizer
```

### Key Classes

| Class | Description |
|-------|-------------|
| `Node` | Network node (SOURCE, TRANSIT, SINK) |
| `Edge` | Network edge with cost |
| `Demand` | Flow demand |
| `ShortestPath` | Dijkstra shortest path |
| `FlowOptimizer` | Max flow optimization |
