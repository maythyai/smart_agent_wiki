# Feature Landscape

**Domain:** Intelligent multi-agent knowledge management platform (LLM Wiki)
**Researched:** 2026-04-26
**Sources:** Design document, 181-project ecosystem analysis, 25+ project deep audits, 666 user comments

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

## Differentiators

Features that set the product apart from all 181 existing projects. Not expected by users (because no one has them), but strongly valued once discovered.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **4-layer confidence system (Unverified -> Single Source -> Cross-Validated -> Human Verified)** | No existing project implements full confidence layering; directly addresses the #1 pain point (hallucination) | High | Page-level confidence combined with per-claim source marking (extracted/inferred/ambiguous) for orthogonal trust scoring |
| **Contradiction detection + 3-strategy resolution (Superseded/Disputed/Historical)** | Only 3 projects attempt any contradiction handling, none with automatic resolution; users cannot manually track contradictions across 200+ pages | High | Requires: new-vs-existing claim comparison, temporal/opinion/factual classification, automated or human-reviewed resolution |
| **Learning engine (training period adaptation + spaced repetition + cognitive distillation)** | Zero competing projects have learning capability; FSRS algorithm for knowledge freshness is borrowed from flashcard science, novel for wiki | High | Three mechanisms: 30-day training period (user preference learning), FSRS interval repetition (freshness-driven review), trend sensing (gap detection) |
| **Structured zero-LLM extraction (AST for code, schema for JSON/tables)** | Codesight achieves 60-131x token savings; no other LLM Wiki project does this; cost control is a major differentiator | Med | Format detection -> structured path (AST/schema parse, zero LLM) vs unstructured path (LLM extraction). Saves significant cost on code and structured data |
| **Multi-agent role-based collaboration (6 specialized agents)** | Only 1 project (Multi-Agent Wiki) has multi-agent integrity governance; most projects are single-agent | High | Librarian(Haiku/high-freq), Writer(Sonnet/balanced), Critic(Sonnet/quality), Linker(Haiku/pattern-match), Scholar(Opus/deep-reasoning), Guardian(rules/zero-LLM). Cost-controlled by model routing |
| **Cryptographic audit layer (Ed25519 receipts + Cedar policy engine)** | Only scopeblind-gateway does this, and only for security; combining audit + policy for knowledge governance is novel | High | Every agent operation generates signed receipt; Cedar policy defines permit/forbid per agent per tool; offline-verifiable receipt chain |
| **4-layer storage architecture (Vault -> Claims -> Wiki -> Index)** | No project combines immutable evidence + structured claims + mutable synthesis + adaptive indexing; most use 1-2 layers | Med | Vault (immutable originals), Claims (structured assertions DB), Wiki (mutable markdown synthesis), Index (FTS5 + optional vector). The dual-track approach is the key innovation |
| **Research-on-Miss auto-research loop** | Only llm-wiki1 has this; creates positive feedback: query -> gap discovery -> auto-research -> knowledge growth -> better answers | Med | When query coverage falls below threshold, trigger parallel web/academic/code search, ingest results, answer from enriched KB |
| **YAML workflow orchestration** | Only MindOS has this; users define multi-step agent workflows without programming; democratizes complex knowledge operations | Med | Visual YAML editor; step-by-step agent coordination with gate conditions (e.g., confidence >= 3, contradiction_count == 0) |
| **Cross-session work momentum (WIP files)** | Only unified-memory-ai-agents has this; captures "what was I doing?" between sessions, not just static knowledge artifacts | Low | .saw/wip.yaml with active tasks, next steps, pending questions; auto-updated on each session |
| **Knowledge lifecycle management (expiry + pruning)** | Only unified-memory-ai-agents has expiring lessons; no project has tactical/strategic classification with automatic pruning | Med | Tactical knowledge auto-expires after 30 days; strategic knowledge permanent; linked to 9-level freshness system |
| **Adaptive index evolution (flat -> hierarchical -> indexed)** | Only Memex does this; solves the "150 pages and index breaks" pain point | Med | Automatic upgrade: flat (<=50 pages) -> hierarchical (<=200) -> indexed (>200) with concept clustering and synthesis routing |
| **9-level freshness system** | Only llm-wiki1 has freshness levels; provides actionable intelligence about knowledge staleness | Low | Color-coded (green/yellow/orange/red); linked to review triggers and pruning decisions |
| **Blast radius analysis** | Only codesight has this; before modifying a wiki page, show what other pages and claims will be affected | Med | Graph traversal to determine downstream impact of any edit |
| **Multi-sink persistent write queue (Outbox)** | Only ContextLattice has fanout architecture; ensures writes never lost even if a sink is temporarily unavailable | Med | Single write entry -> durable outbox -> parallel distribution to Vault/Claims/Wiki/Graph/Index sinks |
| **Progressive memory depth (L0/L1/L2)** | Only unified-memory-ai-agents has this; reduces boot tokens from ~20K to ~8-10K while maintaining full knowledge awareness | Low | L0: always-loaded index (~85 lines), L1: summary index (~15 recent topics), L2: full content on demand |
| **16+ agent compatibility layer** | No project is this portable; core logic in CLI/MCP, one config file per agent (Claude Code, Cursor, Copilot, Codex, Gemini CLI, etc.) | Low | `saw init --agent <name>` generates agent-specific config; all configs reference same core instructions |
| **Git blame dual provenance chain** | Only Agentic Wiki Builder uses git blame for provenance; more reliable than anchor cites (agents can hallucinate anchors, git cannot) | Low | Claims -> Vault (claim to original document) + git blame -> session branch (wiki edit to processing session) |
| **Typed wiki records with namespaces** | Only blink-query has typed records; agents know how to consume each page without guessing | Low | 5 types (SUMMARY/META/SOURCE/ALIAS/COLLECTION) + namespace organization (wiki/concepts/, decisions/, people/) |
| **Temperature-tiered retrieval (hot/warm/glacier)** | Only Cog has this; different storage/access strategy based on usage frequency, not flat treatment of all information | Low | Hot (<50 lines, always loaded) -> warm (recent, L1 indexed) -> glacier (archive, L2 only). Orthogonal to memory depth |
| **Model comparison advisor** | Only obsidian-llm-wiki-local has this; users fear switching LLMs will degrade quality | Med | Run side-by-side comparison on user's own KB data; output accuracy/hallucination/token cost comparison |
| **Dual feedback reinforcement (approved/rejected patterns)** | Only unified-memory-ai-agents has this; explicit positive/negative behavioral signals improve agent output over time | Low | approved.yaml + rejected.yaml injected into Writer/Scholar system prompts; linked to cognitive distillation for SOP extraction |
| **Anti-debt compounding framework** | Only Compound Engineering Plugin has this philosophy; ensures knowledge base compounds value rather than accumulates cost | Low | Each ingest checked: does it create reusable patterns? Each query checked: does it reduce future query cost? Debt ratio > 30% triggers governance |

## Anti-Features

Features to explicitly NOT build. Each has been considered and rejected with clear reasoning.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **General-purpose chatbot UI** | Users already have ChatGPT, Claude, Gemini. Building another chatbot dilutes focus and creates a mediocre chatbot AND a mediocre wiki | Provide query interface only (CLI command, MCP tool, Web UI search bar); no free-form conversational UI |
| **Real-time collaboration (Google Docs style)** | Massive engineering complexity (CRDT/OT); team mode is Phase 4; core use case is individual knowledge worker | File-lock + session branch model; Git-based conflict resolution; async collaboration via A2A protocol |
| **Built-in LLM hosting** | Ollama, LM Studio, llama.cpp already do this well; reinventing wastes effort and creates GPU support headaches | Support local LLM via API (Ollama compatible endpoint); let users choose their hosting solution |
| **Custom embedding model training** | Niche requirement, massive engineering effort, requires ML expertise most users don't have | Use pre-trained models (all-MiniLM-L6-v2 by default); allow users to swap embedding model via config |
| **Visual page builder / WYSIWYG editor** | Wiki content is LLM-generated; a visual editor implies human writing, which contradicts the core paradigm | Milkdown for review/editing only; all generation is LLM-driven; humans approve/reject/edit, not create from scratch |
| **Social features (comments, likes, sharing feeds)** | This is a personal/small-team knowledge platform, not a social platform; social features add privacy complexity and moderation burden | P2P knowledge sharing (Phase 4) for explicit opt-in knowledge exchange; no social graph, no feed |
| **Mobile app** | Knowledge work happens at desktop; mobile requires entirely different UX paradigm and doubles maintenance cost | Responsive Web UI as sole mobile interface; Chrome clipper extension for mobile capture |
| **Plugin/extension marketplace** | Premature optimization for ecosystem; marketplace requires curation, review process, version compatibility management | YAML workflow definitions and SOPs as the extensibility mechanism; CLI tools as integration points |
| **Automated web scraping at scale** | Legal risk (copyright, ToS violations); scope creep into crawler territory; users want curated sources, not firehose | URL ingestion (single page); Chrome clipper for manual capture; RSS for subscribed feeds; Research-on-Miss for targeted search |
| **Knowledge graph query language (SPARQL/Cypher)** | Over-engineered for target audience; requires graph DB expertise; Venn tried OWL-RL and even that is Phase 4 for us | Simple graph traversal APIs (BFS/DFS); visual graph exploration via Cytoscape.js; relationship queries via MCP tools |
| **Multi-tenant SaaS** | Architecture, billing, isolation, compliance; completely different product; contradicts local-first philosophy | Three deployment modes (local / local+cloud LLM / team Docker); self-hosted only |
| **Video/audio editing tools** | Platform is for knowledge management, not media editing; editing tools are feature creep | Extract knowledge from media (Whisper transcription -> claim extraction); store original media in Vault unmodified |
| **Custom authentication system** | Password management, MFA, session handling, OAuth integration -- all non-trivial and not core value | Leverage existing: API keys for LLM access, Git credentials for version control, Cedar policies for agent authorization; team mode uses Docker network isolation |

## Feature Dependencies

```
Vault Storage (L0) --> Claims DB (L1) --> Wiki Pages (L2) --> Index (L3)
                                                          |
                                                          +--> Search (FTS5)
                                                          |
Source Provenance --------------------------------------->+--> Confidence System
   |                                                     |
   +--> Git Integration --> Git Blame Provenance         |
                                                         |
Multi-format Ingestion --> Format Detection --> Structured Extraction (zero LLM)
                                        |
                                        +--> Unstructured Extraction (LLM) --> Multi-LLM Competition
                                                                             |
                                                                             +--> Cross-validation --> Confidence Assessment
                                                                             |
Contradiction Detection --> Resolution Strategies --> Human Review Queue
        |
        +--> Freshness System --> Review Triggers --> Spaced Repetition (FSRS)
        |                                        |
        |                                        +--> Knowledge Expiry --> Pruning
        |
CLI (init/ingest/query/lint) --> MCP Server --> Agent Compatibility Layer
        |                              |
        +--> Write Queue (Outbox) ---->+--> Multi-sink Persistence
        |
Web UI --> Graph Visualization (Cytoscape.js)
        |
        +--> Milkdown Editor --> Review/Approve Workflow --> Feedback Files
                                                          |
                                                          +--> Cognitive Distillation --> SOP Extraction
                                                          |
YAML Workflow Engine --> Agent Orchestration --> A2A Protocol
        |
        +--> Gate Conditions --> Confidence Thresholds
        |
Research-on-Miss --> Web/Academic Search --> Auto-ingest --> Knowledge Growth Loop
        |
Training Period Adaptation (30 days) --> User Preference Learning --> SOP Auto-generation
        |
        +--> Feedback Reinforcement (approved/rejected)
        |
Blast Radius --> Impact Analysis --> Pre-edit Warning
        |
Adaptive Index --> Scale Monitoring --> Auto-upgrade (flat/hierarchical/indexed)
        |
Progressive Memory (L0/L1/L2) --> Token Budget Management --> Boot Sequence Optimization
        |
Temperature Tiers (hot/warm/glacier) --> Storage Optimization --> Retrieval Priority
```

## MVP Recommendation

**Phase 1 (Core Foundation - 6 weeks):**
Prioritize these table-stakes features that create a working product:

1. **Vault + Claims + Wiki storage layers** -- Without storage, nothing works. This is the data foundation.
2. **Multi-format ingestion (PDF/Markdown/URL)** -- Users must be able to feed content in. Start with these three formats.
3. **FTS5 full-text search** -- Makes ingested content findable. Include structure-aware Tree Mode as early differentiator.
4. **CLI (init/ingest/query/lint)** -- Primary user interface; 5-minute onboarding promise depends on this.
5. **Source provenance** -- Core value promise ("knowledge is traceable"); even basic provenance sets the product apart.
6. **Git version control** -- Enables audit trail and branch-based processing.
7. **Multi-LLM support (LiteLLM)** -- Users refuse vendor lock-in; must work on day one.
8. **Write Queue (Outbox)** -- Architectural foundation; ensures no data loss; hard to retrofit later.
9. **WIP cross-session momentum** -- Low complexity, high impact; solves the "where was I?" problem.

**Defer to Phase 2+:**
- Confidence system: Complex; start with simple source marking (extracted/inferred/ambiguous)
- Contradiction detection: Requires mature Claims DB; defer
- Learning engine: Requires user behavior data that doesn't exist yet
- Multi-agent collaboration: Requires all five engines to be functional
- Cryptographic audit: Important but not MVP
- Web UI: CLI first, Web second

**Phase 2 (Intelligence Enhancement - 4 weeks):**
Add the trust and governance layer that differentiates:

1. **4-layer confidence system** -- The headline differentiator
2. **Contradiction detection + resolution** -- Completes the trust story
3. **MCP Server (23 tools)** -- Enables agent ecosystem integration
4. **Learning engine (training period + cognitive distillation)** -- Starts the self-improvement loop
5. **Knowledge expiry + pruning** -- Keeps KB healthy at scale
6. **Cryptographic audit (Ed25519 + Cedar)** -- Enterprise-grade trust
7. **Multi-sink write architecture** -- Production-grade reliability

**Phase 3 (Collaboration and Scale - 4 weeks):**
Add collaboration and visualization:

1. **Multi-agent role-based collaboration** -- The full agent orchestra
2. **YAML workflow orchestration** -- User-defined knowledge workflows
3. **Knowledge graph visualization** -- Visual exploration
4. **Web UI** -- React + Cytoscape.js + Milkdown
5. **Research-on-Miss** -- Auto-research loop
6. **Chrome clipper extension** -- Easy web capture
7. **Adaptive index evolution** -- Scale without degradation

## Competitive Feature Matrix

Based on analysis of 181 projects. Shows how Smart Agent Wiki's planned features compare to the best existing implementations.

| Feature Category | Best Existing Coverage | Smart Agent Wiki Coverage | Gap |
|-----------------|----------------------|--------------------------|-----|
| Storage architecture | 2 layers (most projects) | 4 layers | Unique |
| Confidence/trust | None (0 projects) | 4-layer + per-claim marking | Unique |
| Contradiction handling | Detection only (3 projects) | Detection + 3-strategy resolution | Significant |
| Learning/adaptation | Single feature (2 projects) | 4-mechanism integrated engine | Unique |
| Multi-agent collaboration | Basic (1 project) | 6 roles + A2A + workflows + audit | Significant |
| Search quality | FTS5 or vector (not both) | FTS5 + Tree Mode + optional vector + Research-on-Miss | Moderate |
| Multi-format ingestion | 6 formats (some projects) | 10+ formats with zero-LLM structured extraction | Moderate |
| Governance | None (0 projects) | Freshness + audit + policy + blast radius | Unique |
| Agent compatibility | 1-2 agents (most) | 16+ agents via config files | Significant |
| Cost control | Single LLM (most) | Zero-LLM structured + multi-model routing + 3-tier degradation | Significant |

## Sources

- Design document: `docs/smart_agent_wiki_design.md` -- Full architecture with 23 appendix design decisions
- Ecosystem analysis: `docs/llm_wiki_ecosystem_analysis.md` -- 181-project categorization and feature coverage matrix
- Remote audit findings: `docs/remote_project_audit_findings.md` -- Deep audit of 27 projects with unique feature extraction
- Karpathy's original LLM Wiki concept: `docs/llm-wiki.md` -- Foundational pattern and user expectations
- User pain points: `docs/karpathy_llm_wiki_comments.md` -- 666 comments with pain point frequency analysis
- Project list: `docs/karpathy_llm_wiki_projects.md` -- Full enumeration of 181 derivative projects

**Confidence:** HIGH -- Based on comprehensive analysis of 181 existing projects, 666 user comments, and 25 deep code audits. Feature categorization is grounded in extensive primary research.
