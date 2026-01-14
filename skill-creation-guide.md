# Skill Creation Guide (Platform Supplement)

This guide supplements `skill-creator/SKILL.md` with platform-specific integration steps. Read skill-creator/SKILL.md first for the core skill creation process.

## Platform Integration Checklist

After creating a skill following skill-creator/SKILL.md, complete these platform-specific steps:

| Step | File | When |
|------|------|------|
| Add Python dependency | `template/pyproject.toml.jinja` | If skill uses a Python SDK |
| Document env variable | `template/env.md` | If skill requires API key |
| Register skill | `template/ENTRY.md.jinja` | Always |
| Update container | `../e2b/e2b.Dockerfile` | If skill needs system packages or global tools |

## Using uv

All Python operations use `uv`:

```bash
# Initialize skill
uv run skill-creator/scripts/init_skill.py <name> --path template/skills

# Validate skill
uv run --with pyyaml skill-creator/scripts/quick_validate.py template/skills/<name>

# Run skill scripts
uv run template/skills/<name>/scripts/<script>.py

# Install dependencies after updating pyproject.toml.jinja
uv sync
```

## Adding Dependencies

Add SDK to `template/pyproject.toml.jinja`:

```toml
dependencies = [
    ...
    # <Skill name> skill
    "<package>>=<version>",
]
```

## Documenting Environment Variables

Add to `template/env.md`:

```markdown
| Variable | Service | Skills |
|----------|---------|--------|
| `<VAR>_API_KEY` | <Service> (injected by system) | `<skill>` |
```

Note: Environment variables are injected by the system at runtime.

## Registering Skills

Add to Available Skills table in `template/ENTRY.md.jinja`:

```markdown
| `<skill-name>` | Brief description |
```

## Example: Claude Skill Integration

After creating the claude skill per skill-creator/SKILL.md:

**pyproject.toml.jinja:**
```toml
# Claude skill
"anthropic>=0.40",
```

**env.md:**
```markdown
| `ANTHROPIC_API_KEY` | Claude API (injected by system) | `claude` |
```

**ENTRY.md.jinja:**
```markdown
| `claude` | LLM for text generation, JSON extraction, image analysis |
```

## Updating E2B Container

If a skill requires system-level dependencies (apt packages) or global tools (npm packages), update `../e2b/e2b.Dockerfile` (in the parent fulcrum-app repo):

```dockerfile
# System packages (apt)
RUN apt-get update && apt-get install -y \
    <package-name> \
    && rm -rf /var/lib/apt/lists/*

# Global npm packages
RUN npm install -g <package-name>
```

Current container includes:
- **PDF**: poppler-utils, qpdf
- **Documents**: libreoffice, pandoc
- **OCR**: tesseract-ocr
- **Node**: docx (npm)

Python packages do NOT require container changes - they're installed via `uv sync` at runtime from pyproject.toml.

## YAML Pitfall

If your skill description contains colons, quote it:

```yaml
# Wrong - YAML parsing error
description: Use for: task one, task two

# Correct
description: "Use for: task one, task two"
```
