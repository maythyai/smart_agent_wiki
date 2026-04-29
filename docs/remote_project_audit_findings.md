# Remote Project Audit Findings (Full Audit)

> Audited from 181-project list, excluding 25 locally cloned projects
> Date: 2026-04-25

---

## Tier 1: Significant Unique Features

### 1. Venn (1024205457-boop/Venn)
- **OWL-RL formal ontology**: 8 knowledge types + 8 relationship types for automated reasoning
- **Dual-write storage**: Oxigraph (RDF/SPARQL) + SQLite (FTS5/BM25)
- **5 intelligence presentation modes**: briefing, dossier, document, synthesis, alert
- **Hybrid retrieval**: keyword + semantic + graph-boosted ranking in single pipeline
- **Automated pipeline**: Classify → Extract entities → Link → Enrich → Reason
- **Contradiction/pattern/gap detection** across knowledge objects
- **PID-locked canonical MCP HTTP server**: CLI, dashboard, Claude Code all as HTTP clients
- **Cross-document synthesis tool**
- **Symmetric/transitive relationship handling** (contradicts=symmetric, supersedes=transitive)

### 2. Thinking-Space (anuragrpatil23/Thinking-Space)
- **Self-modifying app**: ships source code in DMG, AI agents can modify and rebuild from within
- **Hierarchical thinking**: Programs > Epics > Ideas > Thoughts (hierarchy in metadata, not folders)
- **55+ typed capability operations** with policy enforcement, audit trails, dry-run
- **Emotion-tagged thought capture** with YAML frontmatter
- **Embedded VS Code-style terminal** (xterm.js + node-pty)
- **AI-powered extension builder** from natural language
- **Per-scope AI provider/model defaults** (different models for different tasks)
- **Conflict-safe file editing** with mtime/hash checks
- **Built-in password manager** with passphrase-encrypted vault

### 3. tracecraft (Arrmlet)
- **S3 as coordination backend**: MinIO/AWS/R2/HuggingFace Buckets — no servers, no databases
- **Task claiming with handoff notes**: agents "claim a step" to prevent collisions
- **Barrier synchronization**: `wait-for` blocks until dependencies complete
- **Agent messaging**: direct + broadcast modes, persisted as JSON in S3
- **Dot-notation keys auto-map** to nested S3 paths

### 4. personal-knowledge-base (aarora79)
- **Auto-generated "shared-tag edges"**: connects articles across folders sharing 2+ tags
- **Configurable summary depth** (100/300/500 words) with Feynman to Expert styles
- **Self-contained D3.js force-directed graph** as single HTML file — no server needed
- **3 edge types**: explicit cross-refs, shared-tag connections, article-to-summary links

### 5. basic-memory (basicmachines-co)
- **Schema system**: infer, validate, and diff knowledge base structure (`schema_infer`, `schema_validate`, `schema_diff`)
- **Semantic vector search**: hybrid FTS + FastEmbed embeddings
- **Per-project cloud routing**: individual projects through cloud while others stay local
- **Canvas visualization tool**: generates knowledge graph visualizations
- **Observation/Relation semantic Markdown patterns**: `[category] content #tag (context)` and `relation_type [[WikiLink]]`
- **Dual DB backend**: SQLite (default) + PostgreSQL (team), automatic migration
- **Real-time file sync** via `sync --watch`
- **Edit operations**: append/prepend, find/replace, replace_section with expected-replacements validation

### 6. llmbase (Hosuke)
- **Trilingual by default**: EN / 中文 / 日本語 with alias map resolving cross-script references
- **Two-layer recall**: TF-IDF on compiled concepts + separate raw source recall for verbatim fallback
- **Tone modes**: scholar 🎓, wenyan 📜, ELI5 👶, caveman 🦣
- **One contract, three surfaces**: single Operation registry powers CLI/HTTP/MCP simultaneously
- **Self-healing 7-step auto-fix**: clean → metadata → broken-links → dedup → taxonomy
- **Autonomous worker**: continuously learns from corpus sources (CBETA, ctext, Wikisource)
- **Library-not-framework**: customize via module constants + hooks, no forking
- **叠加进化 (stacked evolution)**: concepts merge, never overwrite
- **Corpus plugins**: domain-specific ingest sources registerable via `register_learn_source`

### 7. scopeblind-gateway (scopeblind)
- **Ed25519 signed receipts** for every MCP tool call
- **Cedar policy engine** (AWS) for authorization: permit/forbid per tool
- **Swarm tracking**: 11 hook events tracking agent topology
- **CVE-anchored policy packs**: prevents real documented attacks
- **Offline-verifiable audit bundles**: no server needed for verification
- **Receipt DAG visualization**: trace tool call chains
- **IETF Internet-Draft** for signed receipts standard
- **Microsoft AGT integration**: merged into Agent Governance Toolkit

### 8. skillnote (luna-prompts)
- **Portable CLI skill**: `npx skills add` across Codex, Claude Code, Gemini
- **File-based embeddings**: accelerates queries at scale without external DBs
- **Self-correction**: logs failures against lint rules to improve future generation

### 9. MindOS (GeminiLight/MindOS)
- **Human-AI Symbiotic Mind Model**: "human thinks and agents act" — AI extracts reusable SOPs from every interaction
- **Echo Cognitive Distillation**: automatically extracts corrections, preferences into reusable SOPs
- **Agent Inspector**: filterable timeline to audit every tool call in detail
- **A2A Protocol**: Agent-to-Agent communication via JSON-RPC with Agent Cards
- **YAML Workflow Orchestration**: visual editor for multi-step agent workflows
- **INSTRUCTION.md Write-Protection**: core files protected from agent modification
- **Path Sandboxing**: restricts agent file operations to designated directories
- **Dual Transport MCP**: stdio + HTTP simultaneously for local + remote agents
- **Atomic Writes**: prevents data corruption during crashes or concurrent access

### 10. unified-memory-ai-agents (glaucobrito)
- **Three-Layer Memory Architecture**: Subconscious (auto-capture) → Conscious (curated workspace) → Persistent (behavioral identity)
- **Progressive Memory Depth (L0/L1/L2)**: always-loaded index → summary indexes → full content on demand
- **Cross-Platform Memory Unification**: Python bridge syncs Telegram + Claude Code every 30min
- **Expiring Tactical Lessons**: tactical lessons (⏳) auto-expire after 30 days; strategic lessons (🔒) permanent
- **Memory Health Check**: zero-token governance detecting 6 types of inconsistencies
- **Feedback Dual-File Pattern**: approved.json + rejected.json as behavioral reinforcement
- **WIP File**: captures momentum between sessions, not just artifacts

### 11. ContextLattice (sheawinkler)
- **Multi-Sink Fanout Architecture**: /memory/write → durable outbox → Qdrant, Mongo, MindsDB, Letta, memory-bank
- **Retrieval Learning Loops**: merges multi-source recall, improves ranking through feedback loop
- **Operator-Grade Controls**: env-gated controls for code-context enrichment + reranking
- **Staged Read Lane**: topic_rollups, postgres_pgvector indexes in separate lane
- **Strict Runtime Lock**: prevents tuning drift across restarts

### 12. TreeSearch (shibing624)
- **Structure-Aware Document Retrieval**: NO vector embeddings, NO chunk splitting
- **SQLite FTS5 Tree Mode**: anchor retrieval → tree walk → path aggregation for hierarchical docs
- **Auto Mode Intelligence**: three-layer strategy (type mapping + depth verification + proportion threshold)
- **Millisecond Latency**: searches tens of thousands of docs without embeddings

### 13. silverbullet (silverbulletmd)
- **Space Lua Programming**: programmable PKM with Lua dialect for dynamic content generation
- **Plug System**: create custom Commands, Page Templates, Widgets
- **Objects and Queries**: database-style querying within Markdown
- **Bi-directional Links**: wiki-style navigation with backlinks
- **Go Backend + TypeScript Frontend**: performance + modern editor (CodeMirror 6)

### 14. semantic vector search: FastEmbed embeddings hybrid with FTS5 (from basic-memory audit)
- **Per-project cloud routing**: individual projects through cloud while others stay local (from basic-memory)
- **Observation/Relation semantic Markdown patterns**: `[category] content #tag (context)` (from basic-memory)

### 15. Trilingual KB compilation (from llmbase)
- **Two-layer recall**: TF-IDF on compiled concepts + separate raw source recall
- **Emergent taxonomy**: LLM-generated classification adapts over time
- **Autonomous worker**: continuously learns from corpus sources

### 16. Cedar Policy Engine + Ed25519 Signed Receipts (from scopeblind-gateway)
- **CVE-anchored policy packs**: prevents real documented attacks
- **Offline-verifiable audit bundles**: no server needed for verification
- **Swarm tracking**: 11 hook events tracking agent topology

### 17. Cog (marciopuga/cog)
- **Convention system, not code**: entire architecture lives in plain-text instructions, no server/runtime
- **Three-Tier Memory with Temperature-Based Retrieval**: hot (<50 lines) / warm / glacier hierarchy
- **Progressive Condensation Pipeline**: hot → warm → glacier auto-condensation
- **Self-evolving conventions**: the rules themselves change over time via pipeline skills

### 18. blink-query (arpitnath)
- **Typed Wiki for LLMs**: 5 typed record types (SUMMARY, META, SOURCE, ALIAS, COLLECTION)
- **Namespaces**: slash-delimited paths group records by topic
- **Title-weighted BM25 search**: deterministic path resolution in SQLite
- **524 tests passing**

### 19. sp-context (qiuyanxin)
- **Zero RAG, Zero vectors**: just Git + BM25 + ~100 tokens per session
- **Cross-agent persistent memory**: gives any agent access to team knowledge
- **Catalog overview**: tiny footprint always loaded

### 20. Compound Engineering Plugin (EveryInc)
- **Anti-debt framework**: each unit of work makes subsequent units easier
- **Multi-Skill Iterative Workflow**: /ce-ideate → /ce-brainstorm → /ce-plan structured cycle
- **Compounding quality**: accumulating knowledge base enriches future cycles

### 21. omega-memory (omega-memory)
- **Cross-model persistent memory**: works with Claude, GPT, Gemini, Cursor — not locked to one provider
- **1123 tests**: high test coverage
- **Local-first with MCP integration**: memory that travels across agents

### 22. Venn (1024205457-boop) — Chinese project
- **AI-generated nested Venn diagrams + Wiki**: visual concept hierarchy with bidirectional editing
- **Collect mode + Organize mode**: keyword expansion → structured description → visual graph
- **2-3 layer nesting**: sub-concepts auto-layout within parent circles

### 23. Semantica (Hawksight-AI)
- **Context Graphs and Decision Intelligence Layer**: framework for building decision intelligence
- **Python library with CI**: production-grade framework

### 24. Agentic Wiki Builder (ap0phasi)
- **Git blame provenance**: each session on its own branch, merged back to main
- **Session-based processing**: git blame tracks what raw data motivated which wiki updates
- **Anti-triple-store philosophy**: rejects knowledge graph triples in favor of LLM-harnessed wiki

### 25. grover / vfs (ClayGendron)
- **Virtual File System for Agents**: VFS abstraction layer
- **PostgreSQL-native FTS + pgvector**: optional postgres backend
- **Agent file operations through virtualized layer**

### 26. beyond-the-token-bottleneck (CompleteTech-LLC-AI-Research)
- **Research wiki on latent-space reasoning**: maps frontier of continuous thought
- **120+ wiki pages, 1400+ cross references**: demonstrated at scale
- **Communication depth spectrum**: novel classification of LLM interaction layers

### 27. remember-md/remember
- **Self-building second brain**: auto-extracts knowledge from every session
- **Pattern learning**: learns user's organizational patterns over time

---

## Tier 2: Notable Features (need more detail)

### 17. obsidian-seed (dkushnikov)
- **Questionnaire-driven vault building**: structured knowledge collection through guided questions
- Systematic knowledge acquisition from seed prompts

### 18. llm-wiki-compiler (atomicmemory)
- Automated wiki compilation pipeline (need details)

### 19. synthadoc (axoviq-ai)
- Multi-provider document synthesis (6 LLM providers)

### 20. openaugi (bitsofchris)
- Augmented intelligence features (need details)

### 21. AgriciDaniel/claude-canvas
- Canvas-based interaction for Claude (from same author as claude-obsidian)

### 22. AI-Context-OS (alexdcd)
- Operating system metaphor for AI context management

### 23. mnemovault (kimsiwon-osifa7878)
- Memory vault concept for persistent AI knowledge

### 24. WikiStrata (kogarashi86)
- Stratified wiki architecture (need details)

### 25. claude-ltm (LaserPhaser)
- Long-term memory system for Claude (need details)

### 26. codedna (Larens94)
- Code DNA: knowledge representation for codebases (need details)

### 27. mindflow (liqing-ustc)
- Mind flow: cognitive-inspired knowledge management (need details)

### 28. owletto (lobu-ai)
- Knowledge management assistant (need details)

### 29. wikimind (manavgup)
- Mind-mapping meets wiki (need details)

### 30. memora (marvellousz)
- Memory-oriented knowledge storage (need details)

### 31. omega-memory + omega-obsidian-plugin
- Memory system with Obsidian integration (need details)

### 32. agent-wiki (originlabs-app)
- Agent-native wiki architecture (need details)

### 33. palinode (Paul-Kyle)
- Knowledge recantation/correction system (need details)

### 34. prism (payneio)
- Multi-faceted knowledge view (need details)

### 35. browzy.ai (VihariKanukollu)
- Terminal TUI knowledge base with insight crystallizer (need details)

---

## Projects Likely SKIP (templates/clones/minimal)
- llm-wiki-skill, axiom-wiki, quicky-wiki, md2LLM, karpathy-llm-wiki, llm-wiki-template
- llm-wiki-go, llm-wiki (various forks), llm-wiki-claude-skills, vanillaflava/llm-wiki-claude-skills
- Most simple forks/templates of Karpathy's pattern (estimated 40-50 projects)

---

## Key Design Patterns Extracted

### Storage Innovation
| Pattern | Source | Unique Value |
|---------|--------|--------------|
| OWL-RL formal ontology | Venn | Automated reasoning, contradiction detection |
| Three-layer memory (Subconscious/Conscious/Persistent) | unified-memory-ai-agents | Mirrors human cognition |
| Multi-sink fanout | ContextLattice | Durability + retrieval quality |
| Structure-aware FTS5 (no vectors) | TreeSearch | Zero embedding cost, millisecond latency |
| L0/L1/L2 progressive depth | unified-memory-ai-agents | 20K→8K token reduction |

### Governance Innovation
| Pattern | Source | Unique Value |
|---------|--------|--------------|
| Ed25519 signed receipts | scopeblind-gateway | Cryptographic audit trail |
| Cedar policy engine | scopeblind-gateway | AWS-grade authorization |
| INSTRUCTION.md write-protection | MindOS | Agent cannot overwrite human rules |
| Expiring tactical lessons | unified-memory-ai-agents | Auto-prune stale knowledge |
| Memory health check (zero-token) | unified-memory-ai-agents | Governance without LLM cost |

### Agent Architecture Innovation
| Pattern | Source | Unique Value |
|---------|--------|--------------|
| Self-modifying app | Thinking-Space | AI can modify and rebuild from within |
| A2A Protocol (Agent-to-Agent) | MindOS | Multi-agent collaboration via JSON-RPC |
| S3 as coordination backend | tracecraft | No servers, no databases |
| 55+ typed capability operations | Thinking-Space | Policy enforcement per operation |
| Echo cognitive distillation | MindOS | Auto-extract SOPs from interactions |

### Knowledge Representation Innovation
| Pattern | Source | Unique Value |
|---------|--------|--------------|
| Observation/Relation semantic Markdown | basic-memory | `[category] content #tag (context)` |
| Trilingual KB by default | llmbase | EN/中文/日本語 with alias map |
| Schema system (infer/validate/diff) | basic-memory | KB structure governance |
| Emergent taxonomy via LLM | llmbase | Classification adapts over time |
| Space Lua programming | silverbullet | End-user programmable PKM |

---

*This document consolidates findings from 181-project audit (25 local + 156 remote).*
*Last updated: 2026-04-25*
