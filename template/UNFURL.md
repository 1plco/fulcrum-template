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

4. Check `functions/` logic and see if they still match `sop.md`
5. Check persistence requirements again and see if any database migrations are needed. And then see which functions need updates to use the internal-db.

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

## Step 2.5: Create and Apply Database Migrations (Before Functions)

**If functions need persistent storage, create AND APPLY migrations FIRST.**

This step is MANDATORY before Step 3 when:
- Functions need to persist state across executions
- Functions need to cache expensive computations
- The SOP mentions storing, caching, or remembering data

### Migration Workflow

1. Check `env.md` for `FULCRUM_INTERNAL_DB_RW` availability
2. Review `resources/INTERNAL_DB.md` for existing tables
3. Create migration file in `migrations/` with `CREATE TABLE IF NOT EXISTS` statements
4. **APPLY the migration immediately** by running the migration script

**CRITICAL**: Do NOT just create migration files - you MUST execute them. The internal database must be fully operational after unfurl completes. Run the migration script to apply all schema changes before proceeding to Step 3.

```bash
# Apply migrations
uv run python migrations/001_initial.py
```

Or apply directly in Python:
```python
import os
import duckdb

token = os.environ["FULCRUM_INTERNAL_DB_RW"]
db_name = os.environ["FULCRUM_INTERNAL_DB_NAME"]
conn = duckdb.connect(f"md:{db_name}?motherduck_token={token}")

# Execute CREATE TABLE statements
conn.execute("""
    CREATE TABLE IF NOT EXISTS your_table (
        id INTEGER PRIMARY KEY,
        ...
    )
""")
conn.close()
```

See `skills/internal-db/SKILL.md` for migration patterns.

## Step 3: Generate Functions

**Before implementing**: Check if any skills in `skills/` can help. Read skill descriptions in SKILL.md frontmatter to find relevant capabilities.

**Before writing code that interacts with external data:**
1. **Database schemas** - If querying databases, read `resources/RESOURCES.md` to verify table structures, column names, and data types
2. **Template files** - If reading/writing template files (Excel templates, Word documents, etc.) in `resources/` or `input/`, examine their actual format and structure first to ensure compatibility

**MANDATORY: Use Real Data Only**

Check `env.md` for available API keys, then use skills to fetch real data:
- `browser-use` for web data
- `sql` for external databases
- `internal-db` for persistent storage
- Files from `input/` or `resources/`

**PROHIBITED:** Hardcoded sample values, fabricated data, simulated API responses.

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

Before implementing, check available resources:
1. **`resources/RESOURCES.md`** - File resources and external database schemas
2. **`resources/INTERNAL_DB.md`** - Internal database tables
3. **`env.md`** - Environment variables and API keys

### Using Resources

- **File resources**: Read from `resources/{resource-name}/` directories
- **SQL databases**: Use connection string from env vars; see `skills/sql/SKILL.md`
- **Internal DB**: Use `FULCRUM_INTERNAL_DB_RW` env var; see `skills/internal-db/SKILL.md` for migration patterns and dry-run testing

**Note:** Check `resources/INTERNAL_DB.md` before creating tables. Server auto-generates schema docs after unfurl.

## Completion Checklist

**The unfurl is NOT complete until ALL of these conditions are met:**

1. ✅ All validation commands pass (ruff format, ruff check, ty check, pytest)
2. ✅ All functions are fully implemented (no stubs, no `NotImplementedError`)
3. ✅ **Internal database is operational** - migrations have been APPLIED, not just created
4. ✅ All tests pass with mocked external services

**Internal Database Requirement**: If any function uses the internal database, verify the tables exist by running a test query after applying migrations. The database must be in a working state - ticket execution will fail if functions try to query non-existent tables.
