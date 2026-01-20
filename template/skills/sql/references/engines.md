# Database Engine Reference

Engine-specific connection patterns and quirks for SQLAlchemy 2.0+.

## PostgreSQL

**Driver**: `psycopg` (psycopg3)

**Connection String**:
```
postgresql+psycopg://user:password@host:5432/database
```

**With Schema**:
```python
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql+psycopg://user:password@host:5432/database",
    connect_args={"options": "-csearch_path=my_schema"}
)
```

**SSL Connection**:
```python
engine = create_engine(
    "postgresql+psycopg://user:password@host:5432/database?sslmode=require"
)
```

**Notes**:
- Default port: 5432
- Supports `RETURNING` clause for INSERT/UPDATE/DELETE
- Use `::type` for explicit type casting

---

## MySQL

**Driver**: `pymysql`

**Connection String**:
```
mysql+pymysql://user:password@host:3306/database
```

**With Charset**:
```python
engine = create_engine(
    "mysql+pymysql://user:password@host:3306/database?charset=utf8mb4"
)
```

**Notes**:
- Default port: 3306
- Use `charset=utf8mb4` for full Unicode support
- `RETURNING` not supported; use `SELECT LAST_INSERT_ID()` after INSERT
- Case sensitivity depends on server configuration

---

## SQLite

**Driver**: Built-in Python `sqlite3`

**Connection String**:
```
sqlite:///path/to/database.db
```

**In-Memory**:
```
sqlite:///:memory:
```

**Relative Path**:
```python
from pathlib import Path

db_path = Path(__file__).parent / "data.db"
engine = create_engine(f"sqlite:///{db_path}")
```

**Notes**:
- No port or host (file-based or in-memory)
- Limited concurrent write support
- Use `check_same_thread=False` for multi-threaded access:
  ```python
  engine = create_engine("sqlite:///db.sqlite", connect_args={"check_same_thread": False})
  ```

---

## SQL Server (MSSQL)

**Driver**: `pyodbc`

**Connection String**:
```
mssql+pyodbc://user:password@host:1433/database?driver=ODBC+Driver+18+for+SQL+Server
```

**Trusted Connection (Windows)**:
```
mssql+pyodbc://@host/database?driver=ODBC+Driver+18+for+SQL+Server&trusted_connection=yes
```

**With Encryption**:
```python
engine = create_engine(
    "mssql+pyodbc://user:password@host:1433/database"
    "?driver=ODBC+Driver+18+for+SQL+Server"
    "&encrypt=yes"
    "&TrustServerCertificate=yes"
)
```

**Notes**:
- Default port: 1433
- Requires ODBC driver installed on system
- Use `TOP n` instead of `LIMIT n` for limiting rows
- Schema qualification: `schema.table_name`

---

## Common Patterns

### Connection Pooling

```python
engine = create_engine(
    os.environ["DATABASE_URL"],
    pool_size=5,           # Number of connections to keep
    max_overflow=10,       # Extra connections when pool is full
    pool_timeout=30,       # Seconds to wait for connection
    pool_recycle=1800      # Recycle connections after 30 minutes
)
```

### Echo SQL (Debugging)

```python
engine = create_engine(os.environ["DATABASE_URL"], echo=True)
```

### Dispose Connections

```python
# Clean up all connections (useful at end of script)
engine.dispose()
```
