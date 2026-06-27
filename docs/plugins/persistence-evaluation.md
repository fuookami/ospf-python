# Persistence Plugin Evaluation

## Python Alternatives to Kotlin Persistence

### Current State
- No persistence plugins implemented
- Kotlin has: Kafka, Redis, MySQL, SQLite, MongoDB

### Python Ecosystem Alternatives

| Kotlin Plugin | Python Alternative | Status |
|---------------|-------------------|--------|
| Kafka | `confluent-kafka` / `kafka-python` | Recommended |
| Redis | `redis-py` | Recommended |
| MySQL | `SQLAlchemy` + `pymysql` | Recommended |
| SQLite | `sqlite3` (stdlib) / `SQLAlchemy` | Recommended |
| MongoDB | `pymongo` | Recommended |
| MyBatis/Ktorm | `SQLAlchemy` / `SQLModel` | Recommended |

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

1. **SQLite** — Built-in, no external deps, good for dev/testing
2. **Redis** — Fast caching layer, `redis-py` is mature
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
