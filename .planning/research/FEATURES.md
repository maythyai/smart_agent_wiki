# Feature Landscape

**Domain:** Intelligent multi-agent knowledge management platform (LLM Wiki)
**Researched:** 2026-04-27 (Phase 03 features added)
**Sources:** Design document, 181-project ecosystem analysis, 25+ project deep audits, 666 user comments, official documentation (Cedar, Cytoscape.js, Milkdown, CrewAI, LangGraph, A2A Protocol)

---

## Table Stakes

Features users expect. Missing = product feels incomplete. Derived from user pain points (666 comments), coverage across 181 existing projects, and Karpathy's foundational pattern.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Multi-format ingestion (PDF/Markdown/URL)** | Core value proposition; 35+ competing projects offer this | Med | PDF parsing needs 3-tier fallback (MinerU -> Docling -> PyMuPDF). Markdown and URL are table stakes |
| **Full-text search (BM25/FTS5)** | Without search, wiki is unusable beyond ~50 pages; Karpathy's original pattern assumes index.md but recommends search at scale | Low | SQLite FTS5 built-in, zero dependencies. Structure-aware Tree Mode (from TreeSearch) adds differentiation |
| **Wiki page creation and maintenance** | The core Karpathy pattern; LLM reads sources and maintains interlinked markdown pages | Med | Must support: entity pages, concept pages, summaries, cross-references |
| **CLI interface** | Developer audience expects `init/ingest/query/lint` commands; 25+ projects are CLI-first | Med | Typer framework; 5-minute onboarding promise |
| **Immutable raw source storage** | Karpathy's original design has three layers; raw sources must be immutable. 8+ projects emphasize provenance | Low | Git-based Vault layer; zero modifications after ingest |
| **Cross-reference / Wikilink system** | The entire value of a wiki over flat files is interconnection; Obsidian's graph view proves this | Med | Bidirectional links, backlinks, orphan detection |
| **Multi-LLM support** | Users refuse vendor lock-in; 30+ projects support multiple providers; pain point from comments | Low | LiteLLM provides 100+ model routing out of the box |
| **Local-first / offline capable** | Privacy is a top-3 pain point; 15+ projects emphasize local operation; sensitive documents should not require cloud API | Med | Three-tier degradation ensures wiki never becomes "read-only ruin" |
| **Version control (Git)** | Karpathi's original pattern assumes git; audit trail is expected by power users | Low | Auto-commit on ingest and edit; git blame provenance chain |
| **Health check / Lint** | Karpathi's original "Lint" operation; wiki rots without maintenance; stale links, contradictions, orphans | Low | Periodic scan for: contradictions, stale claims, orphan pages, broken links, missing metadata |
| **Source provenance** | Users need to know where knowledge came from; "hallucination/accuracy" is the #1 pain point from comments | Med | Every claim traces back to Vault source with page number/timestamp/line number |
| **Incremental knowledge building** | Core Karpathi concept: knowledge compounds, never re-derived. This is the fundamental paradigm shift from RAG | Med | Wiki persists across sessions; new sources update existing pages rather than creating duplicates |
| **MCP Server** | 20+ projects expose MCP; becoming the standard protocol for agent-tool interaction | Med | 23 tools covering ingest, query, govern, learn, collaborate operations |

---

## Differentiators

Features that set the product apart from all 181 existing projects. Not expected by users (because no one has them), but strongly valued once discovered.

### Phase 1-2 Differentiators (Already Designed)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **4-layer confidence system** | No existing project implements full confidence layering; directly addresses #1 pain point | High | Page-level confidence + per-claim source marking (extracted/inferred/ambiguous) |
| **Contradiction detection + 3-strategy resolution** | Only 3 projects attempt any contradiction handling, none with automatic resolution | High | Temporal/opinion/factual classification + automated or human-reviewed resolution |
| **Learning engine** | Zero competing projects have learning capability | High | 30-day training period + FSRS interval repetition + trend sensing |
| **Structured zero-LLM extraction** | Codesight achieves 60-131x token savings; no other LLM Wiki project does this | Med | AST for code, schema for JSON/tables |
| **Cryptographic audit layer** | Combining Ed25519 audit + Cedar policy for knowledge governance is novel | High | Offline-verifiable receipt chain |
| **4-layer storage architecture** | No project combines all four layers; most use 1-2 layers | Med | Vault -> Claims -> Wiki -> Index |
| **Research-on-Miss** | Only llm-wiki1 has positive feedback loop | Med | Auto-research loop for knowledge gaps |
| **Cross-session work momentum** | Only unified-memory-ai-agents captures "where was I?" | Low | .saw/wip.yaml with active tasks |
| **Knowledge lifecycle management** | Only unified-memory-ai-agents has expiring lessons | Med | Tactical (30-day) vs strategic classification |

---

## Phase 03 Features: Collaboration & Visualization

Features added for Phase 03 milestone. Focus on multi-agent collaboration, workflow orchestration, and Web UI.

### Multi-Agent System Features

| Feature | Why It Matters | Complexity | Dependencies | Expected Behavior |
|---------|---------------|------------|--------------|-------------------|
| **6 Specialized Agents (Librarian/Writer/Critic/Linker/Scholar/Guardian)** | Enables task-specific expertise with cost routing; Haiku for high-freq low-cost, Sonnet for quality, Opus for deep reasoning | High | LiteLLM routing, MCP Server, Claims DB | Agents are dispatched per-task: Librarian indexes/searches, Writer creates content, Critic reviews quality, Linker discovers cross-links, Scholar synthesizes, Guardian enforces rules |
| **Agent Role Definitions** | CrewAI pattern: each agent has role/goal/backstory | Low | YAML config | Each agent defined with: role (function), goal (purpose), backstory (expertise context), tools (allowed MCP tools), model (Haiku/Sonnet/Opus/rules) |
| **Task Delegation (allow_delegation)** | Agents can hand off work when outside expertise | Med | A2A protocol | When agent encounters task outside its role, delegates to appropriate agent. Enabled via `allow_delegation: true` in agent config |
| **Model Routing by Task** | Cost control: 19/20 tasks use Haiku, only Scholar needs Opus | Med | LiteLLM config | Routing logic: Librarian/Linker -> Haiku, Writer/Critic -> Sonnet, Scholar -> Opus, Guardian -> Zero LLM (rules only) |

**Agent Specifications:**

| Agent | Model | Role | Primary Tools | Key Behavior |
|-------|-------|------|---------------|--------------|
| **Librarian** | Haiku | Index maintenance, search optimization | saw_search, saw_graph, saw_status | High-frequency low-cost operations; categorizes and indexes content |
| **Writer** | Sonnet | Page creation, content synthesis | saw_ingest, saw_compile | Creates wiki drafts with proper YAML frontmatter; quality-focused |
| **Critic** | Sonnet | Quality review, contradiction detection | saw_lint, saw_conflicts, saw_verify | Reviews Writer output; flags issues; suggests improvements |
| **Linker** | Haiku | Cross-reference discovery | saw_graph, saw_compare | Pattern-matches entities; suggests wikilinks; updates graph |
| **Scholar** | Opus | Deep reasoning, synthesis generation | saw_query, saw_compile, saw_compare | Most capable; handles complex queries; generates综述 pages |
| **Guardian** | Rules (Zero LLM) | Authorization, safety checks | Cedar policy engine | No LLM calls; enforces permit/forbid rules; validates operations |

### Workflow Orchestration Features

| Feature | Why It Matters | Complexity | Dependencies | Expected Behavior |
|---------|---------------|------------|--------------|-------------------|
| **YAML Workflow Definition** | Users define multi-step workflows without programming; democratizes complex operations | Med | Agent scheduler, state machine | YAML files define: name, steps (agent+action+input+output), gate conditions. Popular pattern from MindOS and CrewAI |
| **Step-by-Step Execution Engine** | Sequential agent coordination with state persistence | Med | Write Queue (Outbox) | Each step: 1) Dispatch agent with input, 2) Collect output, 3) Check gates, 4) Persist state, 5) Proceed or halt |
| **Gate Conditions** | Quality gates prevent bad output from propagating | Med | Confidence system | Gates checked before next step: `confidence >= 3`, `contradiction_count == 0`, `human_approval: true`. Failed gates halt workflow or route to recovery |
| **Conditional Routing** | Different paths based on intermediate results | High | State machine | After step, route based on output: pass -> next step, fail -> recovery agent, ambiguous -> human review |
| **Workflow Templates** | Reusable patterns for common operations | Low | YAML files | Pre-built: literature_review.yaml, contradiction_resolution.yaml, knowledge_synthesis.yaml |

**Example Workflow (literature_review.yaml):**

```yaml
name: literature_review
description: Generate synthesis from multiple sources
triggers:
  - type: manual
  - type: scheduled
    cron: "0 9 * * 1"  # Weekly Monday 9am

steps:
  - id: search
    agent: Librarian
    action: search
    input: "{{ query }}"
    output: related_pages

  - id: validate_sources
    agent: Guardian
    action: check_coverage
    input: "{{ related_pages }}"
    gates:
      - condition: "coverage >= 0.7"
        fail_route: need_more_sources

  - id: synthesize
    agent: Scholar
    action: synthesize
    input: "{{ related_pages }}"
    output: draft_synthesis

  - id: review
    agent: Critic
    action: review
    input: "{{ draft_synthesis }}"
    gates:
      - condition: "confidence >= 3"
      - condition: "contradiction_count == 0"

  - id: publish
    agent: Writer
    action: publish
    input: "{{ draft_synthesis }}"
    output: wiki_page
    gates:
      - condition: "human_approval: true"

recovery:
  need_more_sources:
    agent: Librarian
    action: suggest_sources
    input: "{{ query }}"
```

### A2A Protocol Features

| Feature | Why It Matters | Complexity | Dependencies | Expected Behavior |
|---------|---------------|------------|--------------|-------------------|
| **Agent Cards (Capability Discovery)** | Agents advertise capabilities; others can discover and invoke | Med | JSON-RPC 2.0 | Each agent exposes Agent Card JSON: role, tools, model, input/output schema, connection endpoint |
| **JSON-RPC 2.0 Communication** | Standard protocol; interop with external systems | Med | A2A spec | All agent communication via JSON-RPC: request/response pattern with standardized error handling |
| **Task State Machine** | Long-running tasks with status tracking | High | State persistence | States: pending -> running -> completed/failed. Intermediate states stored for recovery |
| **Streaming (SSE)** | Real-time progress updates for long operations | Med | FastAPI WebSocket | Scholar synthesis streams intermediate results; UI shows progress |
| **Async Push Notifications** | Background completion notification | Med | Write Queue | Long tasks push notification when done; WIP file updated; UI subscription |

### Cedar Policy Engine Features

| Feature | Why It Matters | Complexity | Dependencies | Expected Behavior |
|---------|---------------|------------|--------------|-------------------|
| **Permit/Forbid Rules** | Fine-grained agent authorization; prevents unauthorized operations | Med | Cedar library | Format: `permit(agent, action, resource) when { conditions }`. `forbid(agent, action) when { conditions }`. Explicit deny override allows |
| **Principal-Action-Resource Model** | Standard authorization pattern aligns with agent-tool-claim mapping | Low | Cedar schema | Principal = Agent (Librarian/Writer/etc), Action = Tool (saw_ingest/saw_query/etc), Resource = Target (vault_uuid/wiki_page/etc) |
| **Context-Aware Conditions** | Policies can consider request context (time, confidence, user) | High | Context injection | Conditions like: `when { context.confidence >= 2 && context.user == "admin" }`. Enables dynamic authorization |
| **Policy Templates** | Reusable policies for common patterns | Med | YAML policy files | Pre-built: `permit(Waiter, saw_query)`, `forbid(Critic, saw_ingest)`, `permit(Librarian, saw_*)` |
| **Audit Trail Integration** | Every authorization decision logged with Ed25519 receipt | Med | Existing audit layer | Cedar decision + Ed25519 signature creates tamper-proof authorization log |

**Example Cedar Policies:**

```cedar
// Permit Librarian to search and read
permit(
  principal == Agent::"Librarian",
  action in [Action::"saw_search", Action::"saw_graph", Action::"saw_status"],
  resource
);

// Permit Writer to create but not verify (separation of duties)
permit(
  principal == Agent::"Writer",
  action in [Action::"saw_ingest", Action::"saw_compile"],
  resource
);

// Forbid Writer from self-verification
forbid(
  principal == Agent::"Writer",
  action == Action::"saw_verify",
  resource
);

// Permit Guardian to audit but not modify
permit(
  principal == Agent::"Guardian",
  action in [Action::"saw_lint", Action::"saw_audit", Action::"saw_schema_validate"],
  resource
);

// Context-aware: only allow low-confidence edits with human approval
permit(
  principal == Agent::"Writer",
  action == Action::"saw_edit",
  resource
) when {
  context.confidence >= 3 || context.human_approval == true
};
```

### Web UI Features

| Feature | Why It Matters | Complexity | Dependencies | Expected Behavior |
|---------|---------------|------------|--------------|-------------------|
| **Search Interface** | Primary knowledge access point; Web UI alternative to CLI | Med | FastAPI backend, existing query engine | Search bar with autocomplete; results show page title, snippet, confidence badge, freshness indicator. Supports both keyword (BM25) and natural language query |
| **Knowledge Graph Visualization** | Visual exploration of entity relationships; 10+ projects offer this | High | Cytoscape.js, existing graph index | Interactive graph: nodes = wiki pages, edges = wikilinks. Features: zoom, pan, drag, click-to-navigate, filter by type/tag/confidence |
| **Wiki Page Editor (Milkdown)** | Human review of LLM-generated content; approve/reject/edit workflow | Med | Milkdown, React | WYSIWYG Markdown editing; side-by-side view: original LLM draft vs current; approve/reject buttons; edit mode with live preview |
| **Review Queue** | Pending pages awaiting human approval; part of confidence workflow | Med | Claims DB, confidence system | Lists Unverified pages; shows: source count, freshness, contradictions. Actions: approve (upgrade to Verified), reject (with reason), edit then approve |
| **Dashboard** | Knowledge base overview at-a-glance | Low | Existing saw_status | Shows: total pages, claims, freshness distribution, recent activity, health score from lint |

**Cytoscape.js Graph Features:**

| Feature | Implementation | User Experience |
|---------|---------------|-----------------|
| **Interactive gestures** | Built-in: pinch-to-zoom, box selection, panning | Mobile-friendly; natural navigation |
| **Multiple layouts** | Circle, Concentric, Grid, CoSE (force), Dagre (hierarchical) | User selects layout based on exploration need; CoSE for organic discovery, Dagre for hierarchy |
| **Node styling** | CSS-like selectors for size/color/shape based on data | Confidence determines color (gray=unverified, bronze=single-source, silver=cross-validated, gold=verified). Type determines shape (circle=concept, square=entity, diamond=debate) |
| **Edge styling** | Arrow types, line styles, labels | Bidirectional links show double arrows; link strength shows in thickness |
| **Filter/search** | Selector-based filtering + text search | Filter by: type, tag, confidence range, freshness range. Search highlights matching nodes |
| **Performance** | hideEdgesOnViewport, textureOnViewport, batch updates | Handles 500+ nodes smoothly; edge hiding during pan/zoom prevents jank |
| **Click actions** | tap-to-select, tap-hold-to-unselect, modifier+tap multi-select | Click node -> navigates to wiki page; click edge -> shows relationship details |

**Milkdown Editor Features:**

| Feature | Implementation | User Experience |
|---------|---------------|-----------------|
| **Plugin-driven** | Syntax, theme, UI plugins | Only needed features loaded; extensible for custom needs |
| **Headless styling** | No built-in CSS | Matches application theme; consistent visual design |
| **WYSIWYG Markdown** | ProseMirror + Remark | Type formatted text; see rendered output; raw Markdown toggle |
| **Y.js collaboration** | Real-time collaborative editing | Future: multiple users edit simultaneously (Phase 4) |
| **React integration** | @milkdown/react package | Seamless integration with existing React components |

### Chrome Clipper Features (Phase 3 Optional)

| Feature | Why It Matters | Complexity | Dependencies | Expected Behavior |
|---------|---------------|------------|--------------|-------------------|
| **One-click capture** | Frictionless web content ingestion | Med | Chrome extension API | Click extension icon -> page captured -> sent to local ingest endpoint -> confirm or edit metadata |
| **Selection clipping** | Capture only relevant portions | Med | DOM selection API | Highlight text -> right-click "Clip to Smart Agent Wiki" -> selected text captured with source URL |
| **Metadata extraction** | Auto-extract title, author, date | Med | DOM parsing | Extract from: `<title>`, meta tags, Open Graph, Schema.org. User can edit before ingest |
| **Batch clip** | Capture multiple tabs | Low | Tab API | Right-click extension -> "Clip all tabs" -> batch ingest with single confirmation |

---

## Anti-Features

Features to explicitly NOT build. Each has been considered and rejected with clear reasoning.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **General-purpose chatbot UI** | Users already have ChatGPT, Claude, Gemini. Building another chatbot dilutes focus | Provide query interface only (CLI command, MCP tool, Web UI search bar); no free-form conversational UI |
| **Real-time collaboration (Google Docs style)** | Massive engineering complexity (CRDT/OT); core use case is individual knowledge worker | File-lock + session branch model; Git-based conflict resolution; async collaboration via A2A protocol |
| **Built-in LLM hosting** | Ollama, LM Studio, llama.cpp already do this well | Support local LLM via API (Ollama compatible endpoint); let users choose their hosting solution |
| **Custom embedding model training** | Niche requirement, massive engineering effort | Use pre-trained models; allow users to swap embedding model via config |
| **Visual page builder / WYSIWYG content creation** | Wiki content is LLM-generated; visual editor implies human writing | Milkdown for review/editing only; all generation is LLM-driven; humans approve/reject/edit |
| **Social features (comments, likes, feeds)** | Personal/small-team platform; social adds privacy complexity | P2P knowledge sharing (Phase 4) for explicit opt-in exchange; no social graph |
| **Mobile app** | Knowledge work at desktop; mobile requires different UX | Responsive Web UI; Chrome clipper for mobile capture |
| **Plugin/extension marketplace** | Premature; marketplace requires curation, version management | YAML workflow definitions and SOPs as extensibility mechanism |
| **Automated web scraping at scale** | Legal risk; scope creep; users want curated sources | URL ingestion; Chrome clipper for manual capture; RSS for subscribed feeds; Research-on-Miss for targeted search |
| **Knowledge graph query language (SPARQL/Cypher)** | Over-engineered for target audience | Simple graph traversal APIs (BFS/DFS); visual exploration via Cytoscape.js |
| **Multi-tenant SaaS** | Architecture, billing, compliance contradict local-first | Three deployment modes (local / local+cloud / team Docker); self-hosted only |
| **Visual workflow builder (drag-and-drop)** | YAML workflows sufficient; visual builder adds maintenance burden | Text-based YAML workflows with syntax highlighting; future VS Code extension if demand exists |

---

## Feature Dependencies (Phase 03 Additions)

```
# Phase 03 Dependencies

MCP Server (Phase 2) --> Agent Tools --> Agent Definitions --> Multi-Agent System
                                                      |
                                                      +--> A2A Protocol --> Agent Cards
                                                      |                        |
                                                      |                        +--> JSON-RPC Communication
                                                      |
                                                      +--> Task State Machine --> Write Queue

Confidence System (Phase 2) --> Gate Conditions --> Conditional Routing
                                |
                                +--> Workflow Engine --> YAML Workflow Definition
                                                              |
                                                              +--> Step Execution --> State Persistence

Cedar Policy (Phase 2) --> Agent Authorization --> Permit/Forbid Rules
                              |
                              +--> Principal-Action-Resource Model
                              |
                              +--> Context-Aware Conditions --> Audit Trail

Claims DB (Phase 1) --> Graph Index --> Cytoscape.js Visualization
                                             |
                                             +--> Layout Algorithms (CoSE, Dagre)
                                             |
                                             +--> Node Styling (confidence, type)
                                             |
                                             +--> User Interaction (click, drag, filter)

Wiki Pages (Phase 1) --> Milkdown Editor --> Review/Approve Workflow
                                    |
                                    +--> WYSIWYG Editing --> Live Preview
                                    |
                                    +--> Reject with Reason --> Feedback Files

LiteLLM (Phase 1) --> Model Routing --> Agent Dispatch
                              |
                              +--> Task Complexity Assessment
                              |
                              +--> Cost Control (Haiku default, Opus sparing)
```

---

## Phase 03 MVP Recommendation

**Must Have (Core Collaboration):**
1. **6 Agent Definitions** -- Without agents, workflow engine has nothing to orchestrate. Foundation for all collaboration features.
2. **YAML Workflow Engine + Gate Conditions** -- Enables multi-step operations. Gates ensure quality control.
3. **Cedar Policy Engine** -- Prevents unauthorized agent actions. Required for production safety.
4. **Web UI Search Interface** -- Primary user access point. Search + results display.

**Should Have (Visualization):**
1. **Cytoscape.js Graph Visualization** -- High-value for exploration; 10+ competing projects have this. Basic layout + interaction.
2. **Milkdown Editor + Review Queue** -- Closes the human-approval loop. Essential for confidence system to work.

**Nice to Have (Polish):**
1. **A2A Streaming (SSE)** -- Real-time progress for long operations. Enhances UX but not critical.
2. **Chrome Clipper** -- Reduces ingestion friction. More valuable for active users.
3. **A2A Agent Cards** -- Required for external agent interoperability. Internal agents can work without it.

**Defer to Phase 4:**
1. **Real-time collaboration (Y.js)** -- Requires WebRTC/WebSocket infrastructure; team mode focus.
2. **A2A Protocol External Integration** -- P2P sharing requires this; not needed for single-user.

---

## Expected User Behavior by Feature

### Multi-Agent System User Flow

```
User: saw workflow run literature_review.yaml --query "Transformer architecture evolution"

System:
1. Parse YAML workflow
2. Create execution context with variables
3. Step 1: Dispatch Librarian(Haiku) to search
   - Librarian calls saw_search "Transformer evolution"
   - Returns list of related pages
4. Gate check: coverage >= 0.7?
   - Yes -> continue
   - No -> route to recovery (Librarian suggests more sources)
5. Step 2: Dispatch Scholar(Opus) to synthesize
   - Scholar reads related pages, generates synthesis
   - Streams intermediate results (SSE if connected)
   - Returns draft_synthesis
6. Step 3: Dispatch Critic(Sonnet) to review
   - Critic checks contradictions, confidence
   - Gate check: confidence >= 3, contradiction_count == 0?
   - Pass -> continue, Fail -> return to Scholar with feedback
7. Step 4: Dispatch Writer(Sonnet) to publish
   - Writer formats synthesis as wiki page
   - Gate check: human_approval: true?
   - Adds to Review Queue
8. Notify user: "Synthesis ready for review: [[Transformer Evolution]]"
```

### Knowledge Graph Visualization User Flow

```
User visits /graph:
1. Initial view: All nodes visible, CoSE layout (force-directed)
2. User options:
   - Filter by type: [Concept] [Entity] [Debate] (checkbox)
   - Filter by confidence: Min [2] Max [4] (slider)
   - Filter by freshness: [Last 30 days] (dropdown)
   - Search: [Type to highlight matching nodes]
3. User clicks node:
   - Sidebar shows: title, type, confidence, freshness, summary
   - "Open page" link navigates to wiki page
4. User drags node:
   - Node moves, attached edges follow
   - Physics simulation settles nearby nodes
5. User double-clicks node:
   - Navigate to wiki page (/wiki/Transformer)
6. User hovers edge:
   - Tooltip shows: source page -> target page, relationship type
```

### Wiki Page Editor User Flow

```
LLM generates draft -> enters Review Queue
User visits /review:
1. Queue shows pending pages
2. User clicks "Transformer Evolution" draft
3. Side-by-side view:
   - Left: Original LLM draft with citations
   - Right: Current editable version (Milkdown)
4. User actions:
   - Approve: Draft becomes wiki page, confidence upgrades to Single Source
   - Reject: Dialog for reason, stored in feedback files, confidence stays Unverified
   - Edit: WYSIWYG editing -> Save -> confidence stays Unverified pending re-review
   - Edit + Approve: User modifications saved, confidence upgrades to Human Verified
5. After action: Return to queue or navigate to next pending
```

---

## Competitive Feature Matrix: Phase 03

| Feature | Best Existing Coverage | Smart Agent Wiki | Gap | Confidence |
|---------|----------------------|------------------|-----|------------|
| Multi-agent roles | CrewAI (role/goal/backstory) | 6 specialized + model routing + Cedar policy | Significant | HIGH |
| Workflow orchestration | LangGraph (state machine), CrewAI (sequential/hierarchical) | YAML definition + gates + conditional routing | Moderate | HIGH |
| A2A protocol | Google A2A spec, MindOS implementation | JSON-RPC + Agent Cards + Task state | Standard | MEDIUM |
| Policy engine | Cedar (AWS), scopeblind-gateway | Cedar for agent authorization + audit trail integration | Novel combination | HIGH |
| Graph visualization | Obsidian Graph, Cytoscape.js (library) | Cytoscape.js with confidence/freshness styling + click-to-navigate | Standard | HIGH |
| WYSIWYG editor | Milkdown (library), Obsidian | Milkdown + review queue + approve/reject workflow | Novel combination | HIGH |

---

## Sources

**Phase 03 Sources (2026-04-27):**
- Cedar Policy Language: https://docs.cedarpolicy.com/ (authorization patterns, permit/forbid syntax) -- HIGH confidence
- Cytoscape.js: https://js.cytoscape.org/ (graph visualization features, layouts, interaction) -- HIGH confidence
- Milkdown: https://milkdown.dev/ (WYSIWYG markdown editing, plugin architecture) -- HIGH confidence
- Google A2A Protocol: https://github.com/google/A2A (agent-to-agent communication spec) -- MEDIUM confidence (spec evolving)
- CrewAI Agents: https://docs.crewai.com/concepts/agents (role definition pattern, delegation) -- HIGH confidence
- LangGraph: https://langchain-ai.github.io/langgraph/ (stateful multi-agent orchestration) -- HIGH confidence

**Phase 1-2 Sources (from original research):**
- Design document: `docs/smart_agent_wiki_design.md` -- Full architecture with 23 appendix design decisions
- Ecosystem analysis: `docs/llm_wiki_ecosystem_analysis.md` -- 181-project categorization
- Remote audit findings: `docs/remote_project_audit_findings.md` -- 27 project deep audits
- Karpathy's LLM Wiki: `docs/llm-wiki.md` -- Foundational pattern
- User comments: `docs/karpathy_llm_wiki_comments.md` -- 666 comments analysis

---

*Phase 03 features researched: 2026-04-27*
*Original FEATURES.md: 2026-04-26*
