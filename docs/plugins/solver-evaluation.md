# Solver Plugin Evaluation

## Current Status

| Solver | Status | License | Notes |
|--------|--------|---------|-------|
| Gurobi | ✅ Implemented | Commercial | Full support via gurobipy |
| SCIP | ✅ Implemented | Academic | Full support via pyscipopt |
| COPT | ✅ Implemented | Commercial | License required |
| MindOPT | ✅ Implemented | Commercial | License required |
| MockSolver | ✅ Implemented | N/A | For testing |

## Evaluation Candidates

### CPLEX (IBM)
- **Status:** Not implemented
- **License:** Commercial
- **Python SDK:** `cplex` package
- **Priority:** Medium (industry standard)
- **Complexity:** Medium (similar to Gurobi API)

### Hexaly (ex LocalSolver)
- **Status:** Not implemented
- **License:** Commercial
- **Python SDK:** `hexaly` package
- **Priority:** Low (metaheuristic solver)
- **Complexity:** High (different paradigm)

### Lingo (LINDO Systems)
- **Status:** Not implemented
- **License:** Commercial
- **Python SDK:** Limited
- **Priority:** Low
- **Complexity:** High

### Mosek
- **Status:** Not implemented
- **License:** Commercial/Academic
- **Python SDK:** `mosek` package
- **Priority:** Medium (strong for conic optimization)
- **Complexity:** Medium

## Recommendation

Focus on CPLEX and Mosek as they are industry standards with good Python SDKs. Hexaly and Lingo are lower priority due to limited Python support.

## Implementation Pattern

Each solver plugin follows the same pattern:
1. `ospf_python/core/solver/{solver}/{solver}_solver.py` — base class
2. `ospf_python/core/solver/{solver}/{solver}_linear_solver.py` — LP/MILP
3. `ospf_python/core/solver/{solver}/{solver}_quadratic_solver.py` — QP
4. `ospf_python/core/solver/{solver}/{solver}_config.py` — configuration
