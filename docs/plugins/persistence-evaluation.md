# Persistence Plugin Evaluation

## Current State

Persistence plugins are now implemented in ospf-python.

### Implemented Backends

| Backend | Module | Status | Notes |
|---------|--------|--------|-------|
| SQLite | `framework.persistence.sqlite_repository` | Implemented | Built-in, no external deps, good for dev/testing |
| Redis | `framework.persistence.redis_repository` | Implemented | Fast caching layer, `redis-py` is mature |
| Base | `framework.persistence.repository` | Implemented | Abstract base class (Repository pattern) |

### Usage

```python
from ospf_python.framework.persistence.repository import Repository
from ospf_python.framework.persistence.sqlite_repository import SQLiteRepository
from ospf_python.framework.persistence.redis_repository import RedisRepository
```

## Python Ecosystem Alternatives (for future expansion)

| Kotlin Plugin | Python Alternative | Status |
|---------------|-------------------|--------|
| Kafka | `confluent-kafka` / `kafka-python` | Candidate |
| MySQL | `SQLAlchemy` + `pymysql` | Candidate |
| PostgreSQL | `SQLAlchemy` + `psycopg2` | Candidate |
| MongoDB | `pymongo` | Candidate |
| MyBatis/Ktorm | `SQLAlchemy` / `SQLModel` | Candidate |

### Recommended Architecture

```python
# Repository pattern with SQLAlchemy
from ospf_python.framework.persistence.repository import Repository

class TaskRepository(Repository[Task]):
    def find_by_id(self, task_id: str) -> Task | None: ...
    def save(self, task: Task) -> None: ...
    def delete(self, task_id: str) -> None: ...
```

### Implementation Priority

1. **SQLite** — Built-in, no external deps, good for dev/testing ✅
2. **Redis** — Fast caching layer, `redis-py` is mature ✅
3. **PostgreSQL** (via SQLAlchemy) — Production database
4. **Kafka** — Event streaming, `confluent-kafka` is production-ready

### Pydantic DTO Integration

```python
from pydantic import BaseModel

class TaskDTO(BaseModel):
    task_id: str
    name: str
    duration: float
    priority: int = 0
```

### Alembic Migrations

```bash
alembic init alembic
alembic revision --autogenerate -m "create task table"
alembic upgrade head
```
