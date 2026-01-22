# Unfurl Instructions

Generate Python code from `sop.md`.

## Planning Loop (max 10 iterations)

1. **Hypothesis** - Read sop.md, propose example request that triggers SOP flow
2. **Explore** - Read all /skills, /resources, /models, /functions, /migrations
3. **Plan** - Plan implementation of library to execute sop.md, including migrations
4. **Critique** - Think of a request that would NOT work; if found, loop back with that request

## Execution Loop (until all validation passes)

1. **Write** - Generate /models, /functions, /migrations, /tests
2. **Validate** - Run ruff format, ruff check --fix, ty check, pytest
3. **Verify Real Data** - Scan code for fake/placeholder data (see below)
4. **Refine** - Fix any issues and repeat

## Real Data Verification (CRITICAL)

After writing code, verify NO fake data exists:

### Prohibited Patterns (scan for these):
- Hardcoded names: "John Doe", "Jane Smith", "Acme Corp", "Test User"
- Fake addresses: "123 Main St", "456 Oak Ave", "1234567890"
- Fake emails: "test@example.com", "user@test.com", "foo@bar.com"
- Placeholder patterns: "TODO", "FIXME", "XXX", "placeholder", "sample", "dummy"
- Hardcoded return values that should come from real sources

### Required Data Sources:
Every function that processes data MUST obtain it from:
- `input/` directory (files to process)
- `resources/` directory (reference data, templates)
- Skills (browser-use, sql, internal-db, phonic, mapbox, claude)
- Environment variables (API keys for external services)

### Verification Command:
```bash
# Check for fake data patterns in functions
grep -rE "John Doe|Jane Smith|123 Main|test@example|placeholder|TODO|FIXME" functions/ models/
# Should return empty - any matches require fixing
```

## Generate Models

For each data model needed, create `models/{snake_case(name)}.py`:

```python
from pydantic import BaseModel, Field

class {name}(BaseModel):
    """{description}"""
    {field.name}: {field.type} = Field(description="{field.description}")
    # Add "| None" if optional
```

Add export to `models/__init__.py`.

## Create and Apply Database Migrations (Before Functions)

**If functions need persistent storage, create AND APPLY migrations FIRST.**

This step is MANDATORY when:
- Functions need to persist state across executions
- Functions need to cache expensive computations
- The SOP mentions storing, caching, or remembering data

### Migration Workflow

1. Check `env.md` for `FULCRUM_INTERNAL_DB_RW` availability
2. Review `resources/INTERNAL_DB.md` for existing tables
3. Create migration file in `migrations/` with `CREATE TABLE IF NOT EXISTS` statements
4. **APPLY the migration immediately** by running the migration script

**CRITICAL**: Do NOT just create migration files - you MUST execute them. The internal database must be fully operational after unfurl completes.

```bash
# Apply migrations
uv run python migrations/001_initial.py
```

See `skills/internal-db/SKILL.md` for migration patterns.

## Generate Functions

**Before implementing**: Check if any skills in `skills/` can help. Read skill descriptions in SKILL.md frontmatter to find relevant capabilities.

**Before writing code that interacts with external data:**
1. **Database schemas** - If querying databases, read `resources/RESOURCES.md` to verify table structures, column names, and data types
2. **Template files** - If reading/writing template files in `resources/` or `input/`, examine their actual format first

**MANDATORY: Use Real Data Only**

Check `env.md` for available API keys, then use skills to fetch real data:
- `browser-use` for web data
- `sql` for external databases
- `internal-db` for persistent storage
- Files from `input/` or `resources/`

**PROHIBITED:** Hardcoded sample values, fabricated data, simulated API responses.

For each function, create `functions/{name}.py` with a **complete working implementation**:

```python
"""
{description}

SOP Reference:
> {quoted text from sop.md that this function implements}
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
    # IMPLEMENT THE FULL LOGIC HERE
    ...
```

**IMPORTANT**: Do NOT write stubs or `raise NotImplementedError()`. Write the complete, working implementation.

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

For complex skills with decision trees or multiple approaches, use extended thinking (ultrathink) to plan.

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

## Generate Tests

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

**IMPORTANT**: Write real assertions that verify the function implements the SOP correctly.

**IMPORTANT**: Tests MUST mock dispatch and all external side effects (API calls, DB writes, phone calls, browser tasks). Do not emit real dispatches or call external services in tests.

## Validate (Recursive)

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

## README.md Requirements (for ticket agent discovery)

Generate/update README.md with:

### Available Functions
| Function | Purpose | SOP Section |
|----------|---------|-------------|
| function_name | Brief description | "Quoted text from sop.md" |

### Data Models
List all models with their fields and purposes.

### Database Tables
List any internal-db tables created by migrations.

## Resources Integration

Before implementing, check available resources:
1. **`resources/RESOURCES.md`** - File resources and external database schemas
2. **`resources/INTERNAL_DB.md`** - Internal database tables
3. **`env.md`** - Environment variables and API keys

### Using Resources

- **File resources**: Read from `resources/{resource-name}/` directories
- **SQL databases**: Use connection string from env vars; see `skills/sql/SKILL.md`
- **Internal DB**: Use `FULCRUM_INTERNAL_DB_RW` env var; see `skills/internal-db/SKILL.md`

**Note:** Check `resources/INTERNAL_DB.md` before creating tables. Server auto-generates schema docs after unfurl.

## Completion Checklist

**The unfurl is NOT complete until ALL of these conditions are met:**

- [ ] All validation commands pass (ruff format, ruff check, ty check, pytest)
- [ ] All functions fully implemented (no stubs, no NotImplementedError)
- [ ] Migrations APPLIED (not just created)
- [ ] Real data verification passes (no fake data patterns found)
- [ ] README.md documents all functions with SOP mappings
