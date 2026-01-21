# Unfurl Instructions

Generate Python code from `manifest.json`.

## Manifest Schema

```json
{
  "title": "string",
  "data_models": [
    {
      "name": "ModelName",
      "description": "What this model represents",
      "fields": [
        {"name": "field_name", "type": "str", "description": "...", "optional": false}
      ]
    }
  ],
  "functions": [
    {
      "name": "function_name",
      "description": "What this function does",
      "citation": {"start": 0, "end": 100, "text": "exact text from SOP"},
      "input_model": "InputModelName",
      "output_model": "OutputModelName"
    }
  ]
}
```

## Step 1: Cleanup Stale Files

Before generating code, validate existing files against `manifest.json`:

1. Check `models/` - delete any model files not in `data_models`
2. Check `functions/` - delete any function files not in `functions`
3. Check `tests/` - delete any test files for functions no longer in manifest

Keep `__init__.py` files. Update exports in `__init__.py` to remove deleted items.

## Step 2: Generate Models

For each `data_models` entry, create `models/{snake_case(name)}.py`:

```python
from pydantic import BaseModel, Field

class {name}(BaseModel):
    """{description}"""
    {field.name}: {field.type} = Field(description="{field.description}")
    # Add "| None" if optional
```

Add export to `models/__init__.py`.

## Step 3: Generate Functions

**Before implementing**: Check if any skills in `skills/` can help. Read skill descriptions in SKILL.md frontmatter to find relevant capabilities.

**Before writing code that interacts with external data:**
1. **Database schemas** - If querying databases, read `resources/RESOURCES.md` to verify table structures, column names, and data types
2. **Template files** - If reading/writing template files (Excel templates, Word documents, etc.) in `resources/` or `input/`, examine their actual format and structure first to ensure compatibility

For each `functions` entry, create `functions/{name}.py` with a **complete working implementation**:

```python
"""
{description}

SOP Reference:
> {citation.text}
"""
from models import {input_model}, {output_model}


def {name}(data: {input_model}) -> {output_model}:
    """
    {description}

    Args:
        data: {input_model} instance

    Returns:
        {output_model}
    """
    # IMPLEMENT THE FULL LOGIC HERE based on:
    # 1. The function description
    # 2. The SOP citation text
    # 3. The input/output model fields
    ...
```

**IMPORTANT**: Do NOT write stubs or `raise NotImplementedError()`. Write the complete, working implementation that fulfills the SOP requirement described in the citation.

### File I/O Convention

When functions need to read or write files:
- Read input files from `input/` directory
- Write output files to `output/` directory
- Use `pathlib.Path` for path handling:

```python
from pathlib import Path

INPUT_DIR = Path(__file__).parent.parent / "input"
OUTPUT_DIR = Path(__file__).parent.parent / "output"
```

### Skill Integration

When implementing functions, use skills from `skills/` as reference documentation.

#### How to Use Skills

1. Read the relevant `SKILL.md` completely
2. Find code patterns matching your function's requirements
3. Adapt examples to work with your input/output models

For complex skills with decision trees or multiple approaches, use extended thinking (ultrathink) to plan: What does the skill provide? How does it map to my models? What's the implementation sequence?

Add export to `functions/__init__.py`.

### Dispatch Integration (Required)

All generated functions MUST emit dispatch events using the fulcrum-sdk. Dispatches create a user-facing timeline of progress.

**Setup:**
```python
from fulcrum_sdk._internal.dispatch import get_dispatch_client

dispatch = get_dispatch_client()
```

**Required dispatch points:**
- Start of major processing phases: `dispatch.dispatch_text("Starting invoice processing")`
- External API calls: `dispatch.dispatch_api_call("Geocoding address", service="mapbox", operation="geocode")`
- External references created: `dispatch.dispatch_external_ref("Browser task created", provider="browser-use", ref_type="task", ref_id=task_id)`
- Database operations: `dispatch.dispatch_db("Inserted records", operation="insert", table="invoices", rows=15)`
- Output model display: `dispatch.dispatch_model("Validated output", model=result)` (shows actual field values)

**Do NOT dispatch:**
- Internal file reads/writes
- Every tool call or iteration
- Debug output (use stdout instead)
- Sensitive data (credentials, PII)

See `skills/fulcrum-sdk/SKILL.md` for complete API reference.

## Step 4: Generate Tests

For each function, create `tests/test_{name}.py` with **real test cases**:

```python
from functions import {name}
from models import {input_model}, {output_model}


def test_{name}_basic():
    # Use realistic test data based on the model fields
    data = {input_model}(field1=value1, field2=value2, ...)
    result = {name}(data)
    assert isinstance(result, {output_model})
    # Assert specific expected values based on SOP logic


def test_{name}_edge_cases():
    # Test boundary conditions, edge cases
    ...
```

**IMPORTANT**: Write real assertions that verify the function implements the SOP correctly. Use concrete test values, not placeholders.

**IMPORTANT**: Tests MUST mock dispatch and all external side effects (API calls, DB writes, phone calls, browser tasks). Do not emit real dispatches or call external services in tests.

## Step 5: Validate (Recursive)

Run validation commands and fix any issues until ALL checks pass:

```bash
uv run ruff format .
uv run ruff check . --fix
uv run ty check
uv run pytest
```

**IMPORTANT**: If any validation step fails:
1. Analyze the error output carefully
2. Debug and fix the issue in the relevant file(s)
3. Re-run ALL validation commands from the beginning
4. Repeat until all 4 commands pass with zero errors

Do NOT proceed or consider the unfurl complete until:
- `ruff format` runs without changes
- `ruff check` reports no issues
- `ty check` reports no type errors
- `pytest` shows all tests passing

This is a blocking requirement. Keep iterating until success.

## Resources Integration

When implementing functions, check if project resources are available:

1. **Read `resources/RESOURCES.md`** to see available data files and database schemas
2. **Read `resources/INTERNAL_DB.md`** to see internal database tables (for persistent storage)
3. **Check `env.md`** for project-specific environment variables
4. **Use resources appropriately**:
   - File resources are in `resources/{resource-name}/` directories
   - SQL connections use env vars from secret resources
   - Internal DB uses `FULCRUM_INTERNAL_DB_RW` and `FULCRUM_INTERNAL_DB_NAME` env vars
   - Reference file resources using relative paths from project root

### Example: Using File Resources

```python
from pathlib import Path

RESOURCES_DIR = Path(__file__).parent.parent / "resources"

def process_data(data: InputModel) -> OutputModel:
    # Read from file resource
    data_file = RESOURCES_DIR / "customer-data" / "customers.csv"
    # ... process file ...
```

### Example: Using SQL Resources

```python
import os

def query_database(data: InputModel) -> OutputModel:
    conn_str = os.environ["DATABASE_URL"]  # From secret resource
    # ... query database ...
```

For complete SQL patterns, scripts, and write operation safety guidelines, see `skills/sql/SKILL.md`.

### Example: Using Internal Database

The internal database is a per-project DuckDB/MotherDuck database for persistent storage across agent runs.

#### When to Use Internal DB During Unfurl

- Storing workflow state that persists between tickets
- Caching expensive computations or API results
- Maintaining lookup tables for business logic
- Tracking execution history and audit logs

#### Creating Migrations During Unfurl

If your functions need persistent storage:

1. **Check if internal DB is available**:
   ```python
   import os

   if not os.environ.get('FULCRUM_INTERNAL_DB_RW'):
       # Skip DB setup - will be available on next run
       return
   ```

2. **Create tables idempotently** (use IF NOT EXISTS):
   ```python
   import os
   import duckdb

   def setup_internal_db():
       token = os.environ['FULCRUM_INTERNAL_DB_RW']
       db_name = os.environ['FULCRUM_INTERNAL_DB_NAME']

       conn = duckdb.connect(f"md:{db_name}?motherduck_token={token}")
       conn.execute("""
           CREATE TABLE IF NOT EXISTS workflow_state (
               id INTEGER PRIMARY KEY,
               key VARCHAR NOT NULL UNIQUE,
               value VARCHAR,
               updated_at TIMESTAMP DEFAULT now()
           )
       """)
       conn.close()
   ```

3. **Document schema in function docstrings** so the server-side introspection captures the intent.

#### Dry-Run Testing for DB Operations

**Always test DB operations before committing changes.** Use the dry-run pattern to verify queries work:

```python
def migrate_with_dry_run(conn, migration_sql: str, dry_run: bool = True):
    """Test migration before applying. Always dry-run first during unfurl."""
    try:
        conn.execute("BEGIN TRANSACTION")
        conn.execute(migration_sql)

        if dry_run:
            conn.execute("ROLLBACK")
            print("DRY RUN: Changes rolled back. Verify output before applying.")
            return {"status": "dry_run_success"}
        else:
            conn.execute("COMMIT")
            return {"status": "applied"}

    except Exception as e:
        conn.execute("ROLLBACK")
        print(f"Migration failed: {e}")
        raise
```

**Usage during unfurl:**
```python
# Step 1: Dry-run to test
result = migrate_with_dry_run(conn, "ALTER TABLE users ADD COLUMN email VARCHAR", dry_run=True)

# Step 2: If dry-run succeeds, apply for real
if result["status"] == "dry_run_success":
    migrate_with_dry_run(conn, "ALTER TABLE users ADD COLUMN email VARCHAR", dry_run=False)
```

#### Safe Migration Workflow

For schema changes, follow this workflow:

1. **Inspect current schema** using `scripts/inspect_internal_db.py`
2. **Backup existing data** (if modifying tables with data):
   ```python
   conn.execute("CREATE TABLE users_backup AS SELECT * FROM users")
   ```
3. **Dry-run migration** (wrap in transaction, rollback)
4. **Apply migration** if dry-run succeeds
5. **Verify data integrity** after migration

#### Data Preservation Tips

> **Never lose data during schema changes:**

- **Never DROP TABLE** without backing up data first
- **Use ALTER TABLE ADD COLUMN** instead of recreating tables
- **For column type changes**, use the safe pattern:
  ```python
  # Step 1: Add new column
  conn.execute("ALTER TABLE users ADD COLUMN email_new VARCHAR")

  # Step 2: Copy data with transformation
  conn.execute("UPDATE users SET email_new = LOWER(email)")

  # Step 3: Verify data copied correctly
  count = conn.execute("""
      SELECT COUNT(*) FROM users
      WHERE email_new IS NULL AND email IS NOT NULL
  """).fetchone()[0]
  assert count == 0, f"Data loss: {count} rows missing"

  # Step 4: Drop old, rename new
  conn.execute("ALTER TABLE users DROP COLUMN email")
  conn.execute("ALTER TABLE users RENAME COLUMN email_new TO email")
  ```

- **Keep migration tracking table** to know what's been applied:
  ```python
  conn.execute("""
      CREATE TABLE IF NOT EXISTS schema_migrations (
          version INTEGER PRIMARY KEY,
          name VARCHAR,
          applied_at TIMESTAMP DEFAULT now()
      )
  """)
  ```

For complete migration patterns and examples, see `skills/internal-db/references/patterns.md`.

#### Schema Documentation

After unfurl completes, the server automatically introspects the database and generates `resources/INTERNAL_DB.md` with the current schema. Subsequent ticket executions can reference this file.

**Note:** Check `resources/INTERNAL_DB.md` to see existing table schemas before creating new tables.
