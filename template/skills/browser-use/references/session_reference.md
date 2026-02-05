# Session & Profile Reference

## Table of Contents

1. [Concepts](#concepts)
2. [Profile API](#profile-api)
3. [Session API](#session-api)
4. [SDK Methods](#sdk-methods)

---

## Concepts

- **Profile**: Persistent storage for browser state (cookies, local storage, settings). Created once during unfurl, reused across ticket sessions.
- **Session**: Active browser instance linked to a profile. Tasks within the same session share auth cookies/tokens, local storage, session data, browser history, form data, and cache.
- **Implicit sessions**: Auto-created per task when no `session_id` is provided. State is discarded after the task completes.
- **Custom sessions**: Explicitly created, persist state across multiple tasks. Required for login flows or multi-step workflows that share browser state.

---

## Profile API

**Base URL**: `https://api.browser-use.com/api/v2`

### POST /profiles — Create Profile

**Body**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | `str` | No | Human-readable profile name |

**Returns**: `ProfileView`

### GET /profiles — List Profiles

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pageSize` | `int` | No | Number of results per page |
| `pageNumber` | `int` | No | Page number |

**Returns**: Paginated list of `ProfileView`

### GET /profiles/{profile_id} — Get Profile

**Returns**: `ProfileView`

### PATCH /profiles/{profile_id} — Update Profile

**Body**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | `str` | No | Updated profile name |

**Returns**: `ProfileView`

### DELETE /profiles/{profile_id} — Delete Profile

Permanently deletes the profile and its stored state.

### ProfileView Schema

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Profile UUID |
| `name` | `str` | Profile name |
| `lastUsedAt` | `str\|null` | ISO timestamp of last use |
| `createdAt` | `str` | ISO timestamp |
| `updatedAt` | `str` | ISO timestamp |
| `cookieDomains` | `list[str]` | Domains with stored cookies |

---

## Session API

**Base URL**: `https://api.browser-use.com/api/v2`

### POST /sessions — Create Session

**Body**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `profileId` | `str` | No | — | Profile to attach (enables persistent state) |
| `proxyCountryCode` | `str` | No | — | Country code for proxy routing |
| `startUrl` | `str` | No | — | Initial URL to load |
| `browserScreenWidth` | `int` | No | — | Browser viewport width |
| `browserScreenHeight` | `int` | No | — | Browser viewport height |
| `persistMemory` | `bool` | No | `true` | Whether to persist agent memory across tasks |
| `keepAlive` | `bool` | No | `true` | Keep session alive between tasks |
| `customProxy` | `str` | No | — | Custom proxy URL |

**Returns**: `SessionView`

### PATCH /sessions/{session_id} — Stop Session

**Body**:
```json
{"action": "stop"}
```

**Returns**: Full `SessionView` with tasks list.

### SessionView Schema

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Session UUID |
| `status` | `str` | Current status (e.g., `running`, `stopped`) |
| `liveUrl` | `str\|null` | Live browser view URL |
| `startedAt` | `str` | ISO timestamp |
| `finishedAt` | `str\|null` | ISO timestamp |
| `persistMemory` | `bool` | Whether memory persists across tasks |
| `keepAlive` | `bool` | Whether session stays alive between tasks |
| `proxyUsedMb` | `float` | Proxy data used in MB |
| `proxyCost` | `float` | Proxy cost |

---

## SDK Methods

### Profile Methods

| Method | Description |
|--------|-------------|
| `client.profiles.create_profile(name=...)` | Create a new profile |
| `client.profiles.list_profiles()` | List all profiles |
| `client.profiles.get_profile(profile_id)` | Get a single profile |
| `client.profiles.update_profile(profile_id, name=...)` | Update profile name |
| `client.profiles.delete_profile(profile_id)` | Delete a profile |

### Session Methods

| Method | Description |
|--------|-------------|
| `client.sessions.create_session(profile_id=...)` | Create a session (optionally linked to a profile) |
| `client.sessions.stop_session(session_id)` | Stop a running session |

### Task with Session

Pass `session_id` when creating a task to run it within an existing session:

```python
task = client.tasks.create_task(
    task="...",
    session_id=session.id,
    llm="browser-use-llm",
)
```

See [api_reference.md](api_reference.md) for full `create_task` parameters.
