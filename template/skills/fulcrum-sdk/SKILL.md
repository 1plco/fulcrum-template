---
name: fulcrum-sdk
description: "Dispatch milestones to user-facing timeline and track improvement suggestions. Use dispatch for significant steps (API calls, external refs, DB operations). Use improvements to suggest SOP enhancements, bug fixes, or optimizations. Environment variables FULCRUM_RUN_TOKEN, FULCRUM_DISPATCH_URL, FULCRUM_IMPROVEMENTS_URL, FULCRUM_TICKET_UUID, and FULCRUM_RUN_UUID must be set (injected by system)."
license: "© 2025 Daisyloop Technologies Inc. See LICENSE.txt"
---

# Fulcrum SDK

## Overview

The Fulcrum SDK provides two systems for agent-to-platform communication:

1. **Dispatch** - Send milestones to the user-facing timeline (what users see)
2. **Improvements** - Track suggestions for SOP/workflow enhancements (what developers review)

Both systems are best-effort: methods return `False` on error and never raise exceptions.

## Quick Start

### Dispatch (Timeline Milestones)

```python
from fulcrum_sdk._internal.dispatch import get_dispatch_client

dispatch = get_dispatch_client()

# Text milestone
dispatch.dispatch_text("Starting invoice processing")

# API call with context
dispatch.dispatch_api_call(
    "Called Phonic to confirm appointment",
    service="phonic",
    operation="outbound_call"
)
```

### Improvements (SOP Suggestions)

```python
from fulcrum_sdk._internal.improvements import get_improvements_client

improvements = get_improvements_client()

# Suggest an enhancement
improvements.create_improvement(
    title="Add retry logic for transient API failures",
    dedupe_key="retry-logic"  # Prevents duplicates
)
```

---

## Dispatch System

User-facing timeline milestones. Dispatch **significant events**, not tool traces.

### When to Dispatch

| DO Dispatch | Example |
|-------------|---------|
| Starting major phases | `dispatch_text("Starting data extraction")` |
| External API calls | `dispatch_api_call("Geocoding address", service="mapbox", ...)` |
| External references | `dispatch_external_ref("Browser task created", provider="browser-use", ...)` |
| Database operations | `dispatch_db("Inserted invoices", operation="insert", table="invoices", rows=15)` |

| DO NOT Dispatch | Why |
|-----------------|-----|
| Every tool call | Users don't need internal traces |
| Debug logs | Use stdout/stderr instead |
| Secrets | Never dispatch credentials |

### Dispatch Methods

| Method | Use When |
|--------|----------|
| `dispatch_text(summary, text?)` | General milestones, phase transitions |
| `dispatch_api_call(summary, service, operation, **details)` | External API calls |
| `dispatch_external_ref(summary, provider, ref_type, ref_id, url?)` | References for later display |
| `dispatch_db(summary, operation, table, rows?, query?)` | Database operations |
| `dispatch_model(summary, model, input_summary?)` | Pydantic model display |

### Dispatch Examples

```python
# API call
dispatch.dispatch_api_call(
    "Generated summary with Claude",
    service="anthropic",
    operation="messages.create",
    model="claude-sonnet-4-5-20250929"
)

# External reference
dispatch.dispatch_external_ref(
    "Browser task created",
    provider="browser-use",
    ref_type="task",
    ref_id=task.id
)

# Database operation
dispatch.dispatch_db(
    "Inserted invoice records",
    operation="insert",
    table="invoices",
    rows=15
)
```

---

## Improvements System

Track suggestions for SOP and workflow improvements discovered during execution.

### When to Create Improvements

| Situation | Example |
|-----------|---------|
| Logic enhancement | `"Add retry logic for transient API failures"` |
| Checkpointing | `"Add checkpointing to resume long-running extractions"` |
| SOP edge case | `"SOP should handle empty input files gracefully"` |
| Parallelism | `"Steps 3-5 are independent and could run in parallel"` |
| New capability | `"Add email notification when processing completes"` |
| Bug to fix | `"Date parser fails on ISO formats with timezone offset"` |

### Improvements Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `list_improvements(project_uuid?)` | `list[Improvement]` | List improvements for run |
| `create_improvement(title, description?, dedupe_key?, status?)` | `bool` | Create improvement |
| `update_improvement(uuid, **fields)` | `bool` | Update title/description/status |
| `delete_improvement(uuid)` | `bool` | Delete improvement |
| `emit_improvement_event(uuid, action, payload?)` | `bool` | Record action on improvement |

### Improvements Examples

```python
from fulcrum_sdk._internal.improvements import get_improvements_client

improvements = get_improvements_client()

# Create with deduplication
improvements.create_improvement(
    title="Add retry logic for API failures",
    description="Transient network errors cause job failures",
    dedupe_key="retry-logic"
)

# Update status
improvements.update_improvement(
    uuid="improvement-uuid",
    status="resolved"
)

# Emit event
improvements.emit_improvement_event(
    improvement_uuid="improvement-uuid",
    action="resolved",
    payload={"resolution": "Added exponential backoff"}
)
```

---

## Best Practices

### Write Good Summaries

- **Present tense**: "Processing invoices" not "Processed invoices"
- **User-focused**: What matters to them, not implementation details
- **Specific**: "Extracted 12 line items" not "Extracted data"

### Use Deduplication

Always provide `dedupe_key` for improvements to prevent duplicates across runs:

```python
improvements.create_improvement(
    title="Handle rate limits gracefully",
    dedupe_key="rate-limit-handling"  # Same key = no duplicate
)
```

### Handle Failures Gracefully

Both clients return `False` on any error without raising exceptions:

```python
# Failures don't affect execution
result = dispatch.dispatch_text("Starting")
# result is False if failed, but code continues
```

---

## Scripts

Validation scripts for testing environment setup:

```bash
# Test dispatch
uv run skills/fulcrum-sdk/scripts/dispatch.py

# Test improvements
uv run skills/fulcrum-sdk/scripts/improvements.py
```

---

## Token Deprecation

`FULCRUM_DISPATCH_TOKEN` is deprecated. Use `FULCRUM_RUN_TOKEN` instead. Both clients accept either token, preferring `FULCRUM_RUN_TOKEN` when both are set.

---

## References

- [Dispatch Contract](references/dispatch-contract.md) - Complete dispatch API specification
- [Improvements Contract](references/improvements-contract.md) - Complete improvements API specification
