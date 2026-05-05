# Example 03: Query Your Knowledge

Learn how to search and retrieve information from your Smart Agent Wiki.

## Basic Queries

```bash
# Simple search
saw query "machine learning"

# With limit
saw query "python" --limit 10

# Show citations
saw query "budget" --citations
```

## Query Modes

### Direct Retrieval (`--mode direct`)
Find pages containing exact terms.

```bash
saw query "API design" --mode direct
```

```
Results:
[1] API Design Guidelines
    Source: design-docs.md
    Confidence: 0.85
    → "Use REST for CRUD, GraphQL for queries"

[2] REST API Reference
    Source: api-ref.md
    Confidence: 0.72
    → "Endpoints follow /api/v1/* pattern"
```

### Graph Traversal (`--mode graph`)
Explore related concepts.

```bash
saw query "authentication" --mode graph --depth 2
```

```
Graph for "authentication":

authentication (root)
  ├── OAuth 2.0
  │     ├── token flow
  │     └── refresh mechanism
  ├── JWT
  │     ├── signing algorithm
  │     └── expiration handling
  └── session management
        ├── cookie storage
        └── security considerations
```

### Reasoning Chain (`--mode reasoning`)
Answer "why" and "how" questions.

```bash
saw query "why did we choose PostgreSQL?" --mode reasoning
```

```
Reasoning chain:

[1] Decision: Use PostgreSQL over MySQL
    Source: tech-decision.md
    Confidence: 0.85
    Reason: "Better JSON support with jsonb"

[2] Evidence: Performance comparison
    Source: benchmarks.pdf
    Confidence: 0.72
    → "PostgreSQL: 15% faster on complex queries"

[3] Context: Team experience
    Source: team-skills.md
    Confidence: 0.68
    → "3 team members have PostgreSQL experience"

Conclusion: High confidence (0.78) that PostgreSQL
was chosen for JSON support and team expertise.
```

### Contrast Analysis (`--mode contrast`)
Compare different approaches.

```bash
saw query "React vs Vue" --mode contrast
```

```
Comparison: React vs Vue

React advantages:
  ✓ Larger ecosystem (confidence: 0.85)
  ✓ Better TypeScript support (0.72)
  ✓ More job market demand (0.68)

Vue advantages:
  ✓ Simpler learning curve (0.85)
  ✓ Better performance (0.72)
  ✓ Smaller bundle size (0.68)

Common points:
  • Both support composition (0.95)
  • Both have reactive state (0.95)

Recommendation in sources: React for large teams,
Vue for rapid prototyping (confidence: 0.72)
```

### Synthesis Generation (`--mode synthesis`)
Generate comprehensive summaries.

```bash
saw query "project status overview" --mode synthesis
```

```
Synthesis: Project Status Overview

Based on 23 sources (confidence: 0.78):

Current Phase: Implementation (Phase 2)
Progress: 65% complete
Timeline: On track for Q2 delivery

Key Accomplishments:
  • Core API implemented (verified)
  • Authentication module complete (cross-validated)
  • Database schema finalized (verified)

Pending Items:
  • Web UI redesign (in progress)
  • Performance optimization (planned)
  • Documentation update (assigned)

Risks Identified:
  • Dependency on external API (single-source)
  • Resource allocation concerns (unverified)

Sources: project-plan.md, status-reports/, meeting-notes/
```

## Query Options

```bash
# Time filter
saw query "decisions" --since "2024-01-01"

# Confidence filter
saw query "important" --min-confidence 0.8

# Source filter
saw query "API" --source "api-docs.md"

# Format output
saw query "summary" --output json
saw query "details" --output markdown
```

## Output Formats

### JSON
```bash
saw query "topic" --output json
```

```json
{
  "query": "topic",
  "mode": "direct",
  "results": [
    {
      "title": "Document Title",
      "source": "doc.md",
      "confidence": 0.85,
      "claims": ["claim 1", "claim 2"]
    }
  ],
  "total": 5,
  "time_ms": 23
}
```

### Markdown
```bash
saw query "topic" --output markdown
```

Generates formatted markdown suitable for wiki pages.

---

*Next: [../advanced/mcp-integration.md](../advanced/mcp-integration.md) — MCP integration*