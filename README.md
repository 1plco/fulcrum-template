# Fulcrum Template

A [Copier](https://copier.readthedocs.io/) template for scaffolding Python workflow projects from Standard Operating Procedures (SOPs).

Part of the Fulcrum system for turning SOPs into agentic workflows.

## Overview

Fulcrum Template creates structured Python projects that follow a manifest-driven development pattern:

```
SOP Document → manifest.json → Generated Code (Models, Functions, Tests)
```

## Requirements

- [Copier](https://copier.readthedocs.io/) 9.0.0+
- [uv](https://docs.astral.sh/uv/)
- Python 3.11+

## Usage

### Create a New Project

```bash
copier copy ./fulcrum-template ./projects/my-workflow
```

You'll be prompted for:

| Prompt | Description |
|--------|-------------|
| `project_name` | Human-readable name (e.g., "Invoice Processing") |
| `project_slug` | Package name in snake_case |
| `description` | Brief project description |
| `python_version` | Python version (3.11, 3.12, or 3.13) |

Then:

```bash
cd ./projects/my-workflow
uv sync
uv run pytest
```

### Update an Existing Project

```bash
cd projects/my-workflow
copier update
```

User files (`sop.md`, `manifest.json`, `env.md`, `skills/`, `functions/*.py`, `models/*.py`, `tests/test_*.py`) are preserved during updates.

## Generated Project Structure

```
my_workflow/
├── sop.md              # Source SOP document
├── manifest.json       # Function & model specifications
├── env.md              # External services documentation
├── UNFURL.md           # Code generation instructions
├── ENTRY.md            # Project layout reference
│
├── models/             # Pydantic data models
├── functions/          # Function implementations
├── skills/             # Reusable patterns
└── tests/              # Pytest test suite
```

## Workflow

1. **Document** — Write your SOP in `sop.md`
2. **Specify** — Define models and functions in `manifest.json`
3. **Generate** — Follow `UNFURL.md` to generate code from the manifest
4. **Validate** — Run tests and linting

## Stack

- **Pydantic 2.0** — Data validation
- **Pytest** — Testing with async support
- **Ruff** — Linting and formatting
- **ty** — Type checking
- **uv** — Package management
