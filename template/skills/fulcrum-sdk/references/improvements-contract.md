# Improvements Contract Specification

This document defines the complete contract for the Fulcrum improvements system.

## Overview

The improvements system tracks suggestions for SOP and workflow enhancements discovered during agent execution. These are reviewed by developers to improve future runs.

## Design Principles

### Best-Effort Delivery

- All methods return `False` on any error (never raise exceptions)
- No retries are attempted
- Requests timeout after 1.5 seconds by default
- Agent execution continues regardless of success/failure

### Automatic Protections

- Sensitive keys (`api_key`, `token`, `password`, `secret`, etc.) are automatically redacted
- Payloads exceeding 64KB are truncated
- Titles exceeding 256 characters are truncated

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `FULCRUM_IMPROVEMENTS_URL` | The improvements API endpoint URL |
| `FULCRUM_RUN_TOKEN` | Authentication token (preferred) |
| `FULCRUM_DISPATCH_TOKEN` | Deprecated authentication token (fallback) |
| `FULCRUM_RUN_UUID` | UUID of the current execution run |

**Note:** `FULCRUM_DISPATCH_TOKEN` is deprecated. Use `FULCRUM_RUN_TOKEN` instead. The client prefers `FULCRUM_RUN_TOKEN` when both are set.

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `FULCRUM_PROJECT_UUID` | UUID of the project | None |
| `FULCRUM_TICKET_UUID` | UUID of the ticket | None |
| `FULCRUM_IMPROVEMENTS_DEBUG` | Set to "1" to enable debug logging | Disabled |
| `FULCRUM_IMPROVEMENTS_TIMEOUT_MS` | Request timeout in milliseconds | 1500 |
| `FULCRUM_IMPROVEMENTS_MAX_BYTES` | Maximum payload size in bytes | 65536 |

## Data Models

### Improvement

Response model for improvement records.

```python
class Improvement:
    uuid: str                    # Unique identifier
    project_uuid: str            # Parent project UUID
    ticket_uuid: str | None      # Associated ticket (optional)
    run_uuid: str | None         # Creating run UUID (optional)
    title: str                   # Brief description (max 256 chars)
    description: str | None      # Detailed explanation
    status: str                  # "open" | "in_progress" | "resolved" | "dismissed"
    dedupe_key: str | None       # Deduplication key (max 256 chars)
    created_at: str | None       # ISO timestamp
    updated_at: str | None       # ISO timestamp
```

### ImprovementCreate

Payload for creating new improvements.

```python
class ImprovementCreate:
    title: str                   # Required, max 256 chars
    description: str | None      # Optional detailed description
    dedupe_key: str | None       # Optional deduplication key
    status: str                  # Default: "open"
```

### ImprovementUpdate

Payload for updating improvements.

```python
class ImprovementUpdate:
    title: str | None            # New title
    description: str | None      # New description
    status: str | None           # New status
```

### ImprovementEvent

Payload for recording actions on improvements.

```python
class ImprovementEvent:
    improvement_uuid: str        # Parent improvement UUID
    action: str                  # Action name (max 64 chars)
    payload: dict | None         # Additional data (max 64KB)
```

## Status Values

| Status | Description |
|--------|-------------|
| `open` | New improvement, not yet addressed |
| `in_progress` | Being worked on |
| `resolved` | Fixed or implemented |
| `dismissed` | Won't fix / not applicable |

## Client API

### Initialization

```python
from fulcrum_sdk._internal.improvements import get_improvements_client

# From environment variables (recommended)
improvements = get_improvements_client()

# Manual configuration (advanced)
from fulcrum_sdk._internal.improvements import ImprovementsClient
improvements = ImprovementsClient(
    improvements_url="https://api.fulcrum.ai/improvements",
    run_token="token",
    project_uuid="project-uuid",
    ticket_uuid="ticket-uuid",
    run_uuid="run-uuid",
    timeout_ms=1500,
    max_bytes=65536,
    debug=False,
)
```

### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `list_improvements(project_uuid?)` | `list[Improvement]` | List improvements for the current run |
| `create_improvement(title, description?, dedupe_key?, status?)` | `bool` | Create a new improvement |
| `update_improvement(uuid, **fields)` | `bool` | Update improvement fields |
| `delete_improvement(uuid)` | `bool` | Delete an improvement |
| `emit_improvement_event(uuid, action, payload?)` | `bool` | Record an action on an improvement |

### Properties

| Property | Description |
|----------|-------------|
| `enabled` | `True` if client is properly configured |

## Wire Protocol

### List Improvements (GET)

```http
GET {FULCRUM_IMPROVEMENTS_URL}?run_uuid={run_uuid}&project_uuid={project_uuid}
Authorization: Bearer {token}
```

**Query Parameters:**
| Parameter | Required | Description |
|-----------|----------|-------------|
| `run_uuid` | Yes | Filter by run UUID |
| `project_uuid` | No | Filter by project UUID |

**Response:**
```json
{
  "improvements": [
    {
      "uuid": "imp-123",
      "project_uuid": "proj-456",
      "title": "Add retry logic",
      "status": "open"
    }
  ]
}
```

### Create Improvement (POST)

```http
POST {FULCRUM_IMPROVEMENTS_URL}
Authorization: Bearer {token}
Content-Type: application/json

{
  "run_uuid": "run-789",
  "project_uuid": "proj-456",
  "ticket_uuid": "ticket-123",
  "title": "Add retry logic for API failures",
  "description": "Transient network errors cause job failures",
  "dedupe_key": "retry-logic",
  "status": "open"
}
```

**Response:**
- `201`: Created successfully
- `4xx`: Client error
- `5xx`: Server error

### Update Improvement (PATCH)

```http
PATCH {FULCRUM_IMPROVEMENTS_URL}/{uuid}
Authorization: Bearer {token}
Content-Type: application/json

{
  "run_uuid": "run-789",
  "status": "resolved",
  "title": "Updated title"
}
```

**Response:**
- `200`: Updated successfully
- `4xx`: Client error
- `5xx`: Server error

### Delete Improvement (DELETE)

```http
DELETE {FULCRUM_IMPROVEMENTS_URL}/{uuid}?run_uuid={run_uuid}
Authorization: Bearer {token}
```

**Response:**
- `204`: Deleted successfully
- `4xx`: Client error
- `5xx`: Server error

### Emit Event (POST)

```http
POST {FULCRUM_IMPROVEMENTS_URL}/{uuid}/events
Authorization: Bearer {token}
Content-Type: application/json

{
  "run_uuid": "run-789",
  "improvement_uuid": "imp-123",
  "action": "resolved",
  "payload": {
    "resolution": "Added exponential backoff"
  }
}
```

**Response:**
- `201`: Event recorded
- `4xx`: Client error
- `5xx`: Server error

## Redaction

The following keys are automatically redacted from event payloads:

- `api_key`
- `token`
- `password`
- `secret`
- `credentials`
- `authorization`
- `auth_token`
- `private_key`
- `secret_key`
- `access_key`
- `refresh_token`

Redacted values are replaced with `"[REDACTED]"`.

## Deduplication

Use `dedupe_key` to prevent duplicate improvements across runs:

```python
# First run creates improvement
improvements.create_improvement(
    title="Add retry logic",
    dedupe_key="retry-logic"
)

# Second run with same dedupe_key won't create duplicate
improvements.create_improvement(
    title="Add retry logic",
    dedupe_key="retry-logic"  # Same key = no duplicate
)
```

## Error Handling

All methods return `bool`:
- `True`: Operation succeeded
- `False`: Operation failed (any reason)

Failures are logged to stderr if `FULCRUM_IMPROVEMENTS_DEBUG=1`.

Common failure reasons:
- Missing environment variables (client disabled)
- Network timeout
- API error response
- Payload too large
