# Example 01: Initialization

Learn how to create and configure your first Smart Agent Wiki.

## Create a Wiki

```bash
# Create in current directory
saw init

# Create in specific directory
saw init --path ./my-wiki

# Create with specific name
saw init --name "Project Knowledge"
```

## Output

```
Creating Smart Agent Wiki in ./my-wiki...
✓ Created wiki.db (SQLite database)
✓ Created vault/ (document storage)
✓ Created claims/ (extracted claims)
✓ Created wiki/ (synthesized pages)
✓ Created saw.yaml (configuration)

Wiki initialized successfully!

Quick start:
  saw ingest ./documents    # Add documents
  saw query "topic"         # Search knowledge
  saw web                   # Launch web UI
```

## Configuration

The generated `saw.yaml` contains:

```yaml
# Smart Agent Wiki Configuration

wiki:
  name: "Project Knowledge"
  description: "My project documentation"

storage:
  database: "wiki.db"
  vault: "vault/"
  claims: "claims/"
  wiki: "wiki/"

llm:
  # Default: uses local model if available
  # Otherwise: prompts for API key
  provider: "auto"
  model: "auto"

ingest:
  # Confidence threshold for auto-validation
  auto_validate_threshold: 0.7
  # Supported formats
  formats: ["md", "pdf", "url", "py", "js", "ts"]

query:
  # Default query mode
  default_mode: "direct"
  # Max results per query
  max_results: 20
```

## Directory Structure

```
my-wiki/
├── wiki.db          # SQLite database (all data)
├── vault/           # Original documents (immutable)
│   ├── document.pdf
│   └── notes.md
├── claims/          # Extracted assertions
│   ├── claim-001.json
│   └── claim-002.json
├── wiki/            # Synthesized pages (editable)
│   ├── overview.md
│   └── topics/
└── saw.yaml         # Configuration
```

## Agent Configurations

Generate agent-specific config files:

```bash
# Claude Code
saw init --agent claude-code
# Creates: CLAUDE.md

# Cursor
saw init --agent cursor
# Creates: .cursorrules

# Copilot
saw init --agent copilot
# Creates: .github/copilot-instructions.md
```

## Verification

Check initialization:

```bash
saw status
```

Output:
```
Wiki: Project Knowledge
Path: ./my-wiki
Documents: 0
Claims: 0
Wiki Pages: 0
Status: Ready
```

---

*Next: [02-ingest.md](./02-ingest.md) — Adding documents*