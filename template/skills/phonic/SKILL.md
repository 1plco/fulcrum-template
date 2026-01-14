---
name: phonic
description: "AI telephone agent for outbound calls including sales, appointments, surveys, reminders, and data collection. Initiates calls with inline agent configuration (system_prompt, voice), monitors completion via polling, and retrieves transcripts. Use with Claude skill for structured data extraction from transcripts. Environment variable PHONIC_API_KEY must be set."
license: "© 2025 Daisyloop Technologies Inc. See LICENSE.txt"
---

# Phonic AI Telephone Agent

## Overview

Phonic provides AI-powered voice agents for telephone calls with sub-500ms latency. This skill enables outbound calls with automatic transcript retrieval using a polling-based approach (webhooks not available in sandbox environments).

**Call flow**: Initiate call -> Poll for completion -> Retrieve transcript

## Quick Start

```python
from phonic import Phonic

client = Phonic()  # Uses PHONIC_API_KEY from environment

# Start an outbound call
result = client.conversations.outbound_call(
    to_phone_number="+1234567890",
    config={
        "system_prompt": "You are a friendly dental office assistant calling to confirm an appointment for tomorrow at 2pm. Be polite and concise.",
        "voice_id": "grant",
    }
)

conversation_id = result.conversation_id
```

Or use the provided script for complete call handling with polling:

```bash
uv run skills/phonic/scripts/make_call.py "+1234567890" \
    --system-prompt "You are a friendly survey assistant collecting feedback." \
    --voice grant
```

## Call Configuration

Configure calls inline with `system_prompt` and `voice_id`. All config options override any pre-configured agent settings.

### Required Options

| Option | Description |
|--------|-------------|
| `system_prompt` | Instructions for the AI agent's behavior and goals |
| `voice_id` | Voice selection (default: "grant") |

### Optional Options

| Option | Description |
|--------|-------------|
| `welcome_message` | Custom opening line. Only specify if you need a specific greeting; otherwise the agent generates one from system_prompt |
| `template_variables` | Dict of variables for `{{variable}}` placeholders in prompts |
| `languages` | ISO 639-1 codes for speech recognition (e.g., ["en", "es"]) |
| `boosted_keywords` | Words/phrases for improved recognition accuracy |
| `tools` | List of tool names to enable (built-in or custom) |
| `no_input_poke_sec` | Seconds of silence before reminder message (default: 180) |
| `no_input_poke_text` | Reminder message (default: "Are you still there?") |
| `no_input_end_conversation_sec` | Seconds of silence before ending call |

### Example with Options

```python
result = client.conversations.outbound_call(
    to_phone_number="+1234567890",
    config={
        "system_prompt": "You are conducting a customer satisfaction survey for {{company}}. Ask about their recent experience.",
        "voice_id": "grant",
        "template_variables": {"company": "Acme Corp"},
        "languages": ["en", "es"],
        "boosted_keywords": ["satisfaction", "rating", "feedback"],
        "no_input_poke_sec": 30,
    }
)
```

## Call Flow and Polling

After initiating a call, poll for completion by checking `ended_at`:

```python
import time

conversation_id = result.conversation_id

while True:
    response = client.conversations.get(conversation_id)
    conversation = response.conversation
    if conversation.ended_at is not None:
        break
    time.sleep(5)  # Poll every 5 seconds

# Call completed
print(f"Ended by: {conversation.ended_by}")
print(f"Duration: {conversation.duration_ms / 1000:.1f}s")
```

The `make_call.py` script handles this automatically with progress output.

## Transcript Handling

Two transcript types are available:

| Type | Field | Description |
|------|-------|-------------|
| Live | `live_transcript` | Real-time transcription during call |
| Post-call | `post_call_transcript` | Refined transcript after processing (preferred) |

Access transcripts after call completion:

```python
# Prefer post-call transcript for accuracy
transcript = conversation.post_call_transcript or conversation.live_transcript

# Or access individual turns
for item in conversation.items:
    speaker = "Agent" if item.role == "assistant" else "User"
    text = item.post_call_transcript or item.live_transcript
    print(f"{speaker}: {text}")
```

## Data Extraction with Claude

For structured data extraction from transcripts, use the Claude skill:

```python
from anthropic import Anthropic

claude = Anthropic()

# Extract appointment details
message = claude.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    temperature=0,
    system="""Extract appointment details from this call transcript.
Return JSON: {"confirmed": bool, "date": string|null, "time": string|null, "notes": string}""",
    messages=[{"role": "user", "content": transcript}]
)

import json
appointment = json.loads(message.content[0].text)
```

## Error Handling

### Call Termination

Check `ended_by` to understand how the call ended:

| Value | Meaning |
|-------|---------|
| `"user"` | Caller hung up |
| `"user_canceled"` | Caller canceled |
| `"assistant"` | Agent ended the call |
| `"error"` | Error occurred |

### Common Errors

```python
from phonic import Phonic, APIError

try:
    result = client.conversations.outbound_call(...)
except APIError as e:
    if e.status_code == 400:
        print("Invalid phone number format")
    elif e.status_code == 402:
        print("Insufficient credits")
    else:
        print(f"API error: {e}")
```

### Timeout Handling

```bash
# Increase timeout for long calls
uv run skills/phonic/scripts/make_call.py "+1234567890" \
    --system-prompt "..." \
    --max-wait 900  # 15 minutes
```

## Scripts

### make_call.py

Complete outbound call workflow with polling, transcript output, and optional audio download.

```bash
uv run skills/phonic/scripts/make_call.py "+1234567890" \
    --system-prompt "You are a friendly assistant..." \
    --voice grant \
    --max-wait 600 \
    --poll-interval 5 \
    --output-dir ./recordings \
    --json  # Output as JSON
```

| Option | Default | Description |
|--------|---------|-------------|
| `--system-prompt` | Required | Agent instructions |
| `--voice` | grant | Voice ID |
| `--welcome-message` | None | Custom opening (optional) |
| `--max-wait` | 600 | Max seconds to wait |
| `--poll-interval` | 5 | Seconds between polls |
| `--output-dir` | None | Directory to save audio recording (auto-extracts zip files) |
| `--json` | False | Output JSON instead of text |

## Use Cases

### Appointment Confirmation

```bash
uv run skills/phonic/scripts/make_call.py "+1234567890" \
    --system-prompt "You are calling to confirm a dental appointment for tomorrow at 2pm. Ask if they can make it, and if not, offer to reschedule. Be friendly and professional."
```

### Survey Collection

```bash
uv run skills/phonic/scripts/make_call.py "+1234567890" \
    --system-prompt "You are conducting a brief customer satisfaction survey. Ask: 1) How satisfied were they with their recent purchase (1-5)? 2) Would they recommend us? 3) Any feedback to share? Thank them when done."
```

### Payment Reminder

```bash
uv run skills/phonic/scripts/make_call.py "+1234567890" \
    --system-prompt "You are calling about an outstanding balance of $150. Politely remind them of the payment due, ask if they need payment options, and offer to transfer to billing if needed."
```

## References

For detailed API type definitions, see [references/api_types.md](references/api_types.md).
