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

Add export to `functions/__init__.py`.

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
