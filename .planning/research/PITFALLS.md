# Pitfalls Research

**Domain:** Intelligent multi-agent knowledge platform (Smart Agent Wiki)
**Researched:** 2026-04-26
**Updated:** 2026-05-01 (Third-Party Integrations v3.1)
**Confidence:** HIGH (based on official documentation for SQLite FTS5, LiteLLM, FastMCP, plus 181-project ecosystem audit)

## Critical Pitfalls

### Pitfall 1: FTS5 External Content Table Inconsistency

**What goes wrong:**
FTS5 external content tables (`CREATE VIRTUAL TABLE ... USING fts5(..., content='wiki_table', content_rowid='id')`) silently diverge from their source tables. When the content table is updated but the FTS5 index is not (or vice versa), queries return stale or missing results. The FTS5 documentation explicitly warns: "It is the responsibility of the user to ensure that the content table and the FTS5 index are consistent." There is no automatic enforcement.

In Smart Agent Wiki, this manifests when the Write Queue writes to the Wiki Pages sink (Sink 3) but the FTS5 Index sink (Sink 5) fails or is delayed. The FTS5 index will not reflect the new content, making it unsearchable. Worse, deletes from the content table without corresponding FTS5 deletes cause phantom results.

**Why it happens:**
- FTS5 external content mode reads from the content table at query time but maintains its own index for matching
- INSERT/UPDATE/DELETE on the content table does NOT automatically propagate to the FTS5 index
- Triggers are needed but easy to get wrong (especially DELETE order -- FTS5 delete must happen before content table delete)
- Write Queue partial failures leave sinks in inconsistent states

**How to avoid:**
1. Never allow direct writes to the content table. All writes go through the Write Queue, which fans out to all sinks atomically
2. Use `INSERT INTO fts_index(fts_index) VALUES('rebuild')` as a consistency check -- schedule periodic rebuilds (e.g., after every 100 writes or on `saw lint`)
3. For critical operations, wrap content table + FTS5 updates in the same SQLite transaction (FTS5 supports this)
4. Implement a consistency check in `saw_lint`: `SELECT count(*) FROM wiki_content` vs `SELECT count(*) FROM fts_index` -- any mismatch triggers a rebuild
5. In the Outbox pattern, track sink completion status per message; if Sink 5 fails, retry it before marking the message complete

**Warning signs:**
- `saw_search` returns fewer results than expected for known content
- Count mismatch between content table and FTS5 table
- Users report content they ingested is not findable
- Write Queue shows partial sink completions for FTS5 sink

**Phase to address:**
Phase 1 (Core Foundation) -- Write Queue + FTS5 setup is foundational. If this is wrong, every subsequent feature built on search is unreliable.

---

### Pitfall 2: LiteLLM Per-Deployment Cooldown Cascading Failure

**What goes wrong:**
LiteLLM Router applies cooldowns per deployment (not per model group). When using model routing (Haiku for Librarian, Sonnet for Writer, Opus for Scholar), a single deployment's rate limit or timeout can cascade: cooldown kicks in, traffic shifts to remaining deployments, which then also hit limits, causing total system outage. The default `allowed_fails=0` means ONE failure puts a deployment in cooldown.

For Smart Agent Wiki's cost model (<$0.5/day), this is acute: the system uses cheap models heavily (Librarian/Linker on Haiku) and expensive models sparingly (Scholar on Opus). A burst of ingest operations can exhaust Haiku's rate limit, which cascades to block all Librarian and Linker operations, stalling the entire ingest pipeline.

**Why it happens:**
- Default `allowed_fails=0` is too aggressive for production
- Cooldown time defaults (60s) may be too short for sustained rate limiting
- Rate-limit-aware routing (`rate-limit-aware-shuffle`) adds overhead and requires Redis
- Teams use a single API key for all model groups, sharing rate limits across deployments
- `simple-shuffle` does not check rate limits before routing

**How to avoid:**
1. Set `allowed_fails=3` minimum for each deployment (allows transient failures before cooldown)
2. Set `cooldown_time=120` (2 minutes) to avoid rapid retry storms
3. Use separate API keys per model tier when possible (Haiku key, Sonnet key, Opus key) to isolate rate limits
4. Implement the three-layer degradation: if all Haiku deployments are in cooldown, fall back to Sonnet for Librarian tasks (higher cost but not blocked)
5. Add pre-call context window checks (`context_window_fallbacks=True`) to avoid wasting a call on a prompt that exceeds the model's limit
6. Configure `RetryPolicy` per exception type: retry `RateLimitError` and `Timeout` but NOT `ContentPolicyViolationError` or `ContextWindowExceededError`
7. Monitor cooldown events via LiteLLM's spend logs; alert when >50% of deployments for a tier are in cooldown

**Warning signs:**
- Ingest operations taking progressively longer or timing out
- All queries falling back to expensive models (cost spike)
- LiteLLM logs show consecutive deployment cooldowns
- Daily cost exceeds $0.5 budget without increased usage

**Phase to address:**
Phase 2 (Intelligence Enhancement) -- when multi-LLM support and model routing are implemented. The fallback/degradation logic must be designed before Phase 3's multi-agent orchestration.

---

### Pitfall 3: Confidence Score Inflation Through Circular Validation

**What goes wrong:**
The 4-layer confidence system (Unverified -> Single Source -> Cross-Validated -> Human Verified) can be gamed by circular validation. Two LLMs extracting from the same source document are supposed to provide "cross-validation," but if both LLMs share training data or if the second LLM sees the first's output (even indirectly through shared context), the "cross-validation" is actually single-source in disguise. This inflates confidence from Layer 2 to Layer 3 without genuine independent verification.

Additionally, the page-level confidence aggregation rule ("all extracted -> Layer 3, contains inferred -> Layer 2, contains ambiguous -> Layer 1") can be gamed: a page with 9 extracted claims and 1 ambiguous claim gets Layer 1, while a page with 3 extracted claims and 0 ambiguous gets Layer 3. The long tail of ambiguous claims drags down pages unfairly.

**Why it happens:**
- "Cross-validation" is defined as "multiple LLMs agree" but doesn't verify independence
- LiteLLM may route to different model names that share the same underlying model
- Writer Agent output from one model can leak into Critic Agent context through shared Claims DB state
- The aggregation rule uses strict "any ambiguous -> Layer 1" without weighted scoring
- Human verification (Layer 4) is expensive, creating pressure to accept Layer 3 as "good enough"

**How to avoid:**
1. Enforce strict context isolation between parallel extraction LLMs: separate conversation threads, no shared scratch space, different system prompts
2. Define "cross-validation" as requiring: (a) different model families (e.g., Claude + Gemini, NOT Claude Haiku + Claude Sonnet), AND (b) independent extraction runs with no shared intermediate state
3. Implement weighted confidence aggregation instead of strict minimum: confidence_score = sum(claim_weights * claim_confidence) / total_claims, where ambiguous claims get lower weight but don't zero out the page
4. Require explicit human verification for any claim used in high-stakes decisions (medical, legal, financial), regardless of automated confidence level
5. Add a "validation provenance" field to Claims DB: record which models validated, their independence score, and the evidence they used

**Warning signs:**
- >90% of claims reach Layer 3 (Cross-Validated) -- suspiciously high
- Cross-validation always agrees (no contradictions found between validating LLMs)
- Pages with many claims all share the same confidence level
- Users trust Layer 3 claims that later turn out to be wrong

**Phase to address:**
Phase 2 (Intelligence Enhancement) -- when the governance engine, confidence system, and multi-LLM extraction are implemented. Must be correct before Phase 3's multi-agent workflows depend on confidence scores for gating.

---

### Pitfall 4: Knowledge Graph Entity Resolution Explosion

**What goes wrong:**
Entity resolution (determining whether "Transformer" in one document and "Transformers architecture" in another refer to the same entity) either over-merges (collapsing distinct entities like "Apple (company)" and "Apple (fruit)") or under-merges (creating duplicate entities for "GPT-4" and "gpt4" and "GPT 4"). At scale (1000+ pages), this creates either a tangled graph with spurious connections or a fragmented graph with no connections.

Smart Agent Wiki's 4-signal association model (direct links + source overlap + Adamic-Adar + type affinity) amplifies the problem: bad entity resolution propagates through all 4 signals, creating false associations that appear strong because multiple signals agree (they all inherited the same entity resolution error).

**Why it happens:**
- Entity extraction is LLM-dependent and non-deterministic; the same entity can be extracted with different surface forms across documents
- No canonical entity registry exists; entities are created on-the-fly during extraction
- Adamic-Adar and type affinity signals amplify shared errors: if two false-merged entities share neighbors, Adamic-Adar boosts their association score
- At >200 pages, manual entity deduplication becomes infeasible
- The Linker Agent (Haiku) lacks the reasoning capability for nuanced entity disambiguation

**How to avoid:**
1. Build a canonical entity registry in Phase 1: every extracted entity must match against existing entities before creating a new one. Use fuzzy matching (Levenshtein + embedding similarity) with a high threshold (0.9+)
2. Assign entity IDs that are independent of surface form. Store all known aliases for each entity
3. Entity resolution should be a Scholar (Opus) task, not a Linker (Haiku) task. Cheap matching for obvious cases, expensive disambiguation for ambiguous ones
4. Implement entity confidence: when resolution is uncertain, create a "pending merge" that requires human or Scholar verification
5. Periodically run entity consistency checks in `saw_lint`: find entities with >80% overlapping aliases, neighbors, or sources
6. The 4-signal model should include a "resolution confidence" weight: signals derived from low-confidence entity resolutions get downweighted

**Warning signs:**
- Entity count grows faster than document count (under-merging)
- Popular entities have hundreds of unrelated connections (over-merging)
- Graph visualization shows "hairball" clusters instead of distinct communities
- Adamic-Adar scores are uniformly high (everything is connected to everything)

**Phase to address:**
Phase 1 (entity registry in Claims DB) and Phase 3 (graph visualization and multi-agent entity resolution). The registry must exist before significant ingestion begins.

---

### Pitfall 5: FTS5 Segment B-Tree Proliferation at Scale

**What goes wrong:**
FTS5 stores data as a series of segment b-trees, not a single index structure. Each write transaction creates at least one new segment. Without proper merging, query performance degrades linearly with segment count. At 1000+ pages with frequent updates (typical after Phase 2), queries that were millisecond-fast become seconds-slow.

The `automerge` config parameter controls background merging, but it only merges segments when a write occurs. Read-heavy periods (many queries, few ingestions) never trigger merging, and stale segments accumulate. The `crisismerge` threshold (default 16) means the system tolerates up to 16 segments before emergency merging, which causes visible latency spikes.

For Smart Agent Wiki's adaptive index evolution (flat -> hierarchical -> indexed), this is critical: the transition from flat to hierarchical at 50 pages may mask segment issues because the dataset is small. By 200 pages (indexed mode), accumulated segments cause the very performance degradation the index evolution was designed to prevent.

**Why it happens:**
- Each `INSERT INTO fts_index` creates a new segment b-tree
- `automerge` only runs during write operations, not reads
- `crisismerge` threshold is reactive, not proactive
- The `detail` option affects index size dramatically: `detail=full` (default) creates 5.5x larger indexes than `detail=none`
- Frequent small writes (one-at-a-time ingestion) create more segments than batch writes
- WAL mode transactions don't automatically trigger FTS5 merges

**How to avoid:**
1. Set `automerge=8` (merge when 8+ segments exist) and `crisismerge=4` (emergency merge at 4 segments, not 16) in FTS5 config: `INSERT INTO fts_index(fts_index, rank) VALUES('automerge', 8)`
2. Batch writes when possible: instead of inserting one document at a time, accumulate and write batches of 10-50 documents
3. Schedule explicit `optimize` calls after heavy ingestion: `INSERT INTO fts_index(fts_index) VALUES('optimize')` -- this merges all segments into one
4. Choose `detail=column` instead of `detail=full` for the main index. This sacrifices NEAR and phrase queries (acceptable for keyword search) but halves the index size and reduces segment overhead. If phrase queries are needed, maintain a secondary index
5. Monitor segment count: `SELECT count(*) FROM fts_index_segments` -- if >50, trigger manual optimize
6. In the Write Queue, batch FTS5 updates: accumulate writes in the outbox and flush to FTS5 in batches every N seconds or N documents

**Warning signs:**
- Query latency increases non-linearly with document count
- `saw_search` takes >500ms for simple keyword queries
- FTS5 segment count exceeds 50
- Ingestion speed is fast but query speed degrades after heavy ingestion

**Phase to address:**
Phase 1 (FTS5 setup) -- the `automerge`/`crisismerge` config and `detail` option must be set correctly from day one. Changing `detail` after creation requires a full rebuild.

---

### Pitfall 6: MCP Tool Schema Drift Between Server and Agent Clients

**What goes wrong:**
Smart Agent Wiki exposes 23 MCP tools via FastMCP. When a tool's signature changes (parameter added, type changed, parameter renamed), existing agent clients (Claude Code, Cursor, Copilot) cache the old schema and send malformed requests. The MCP protocol does not have built-in schema versioning or cache invalidation.

This manifests silently: an agent calls `saw_query` with the old parameter format, the server returns an error or (worse) silently ignores the new parameter and produces incorrect results. Because agents don't always surface MCP errors clearly, users see degraded behavior without understanding why.

FastMCP 3.0 auto-generates schemas from Python function signatures, which means any code change to a tool function automatically changes the schema. There is no "schema freeze" mechanism.

**Why it happens:**
- FastMCP derives schemas from function signatures -- code changes = schema changes
- MCP clients cache tool schemas for the session duration
- No standard mechanism for schema version negotiation in MCP protocol
- 23 tools = 23 potential drift points
- Development velocity (changing tool signatures during Phases 1-3) makes drift almost certain

**How to avoid:**
1. Define tool schemas as separate Pydantic models, not inline function parameters. Changes to the model are explicit and reviewable
2. Implement schema versioning: each tool carries a `version` field in its description. Clients can detect version mismatches
3. Add backward-compatible parameter handling: new parameters must have defaults; renamed parameters must accept old names as aliases for at least one major version
4. In `saw_status`, include a schema version check that agents can call to detect drift
5. During Phase 2-3 development, maintain a changelog of tool schema changes and test with at least 2 different MCP clients
6. Consider pinning FastMCP version -- FastMCP 3.0 is in RC; pin to v2 for production stability until v3 is fully released

**Warning signs:**
- Agent calls fail with "invalid parameters" errors after updates
- Agent behavior degrades after server restart (old cached schema)
- Tool works in CLI but fails when called through MCP
- FastMCP upgrade changes schema generation behavior

**Phase to address:**
Phase 2 (MCP Server implementation) -- schema design decisions are locked in when the MCP server is built. Phase 3 adds agents that depend on stable schemas.

---

### Pitfall 7: Write Queue Outbox Orphan Messages

**What goes wrong:**
The Write Queue (Outbox pattern) guarantees durability by persisting messages before processing. But messages can become orphans: the system crashes after writing to some sinks but before marking the message complete. On restart, the system must decide whether to retry (risking duplicate writes) or skip (risking data loss).

For Smart Agent Wiki's 6 sinks (Vault, Claims DB, Wiki Pages, Graph Index, FTS5 Index, Vector Index), the combinatorics are brutal: with 6 sinks and crash at any point, there are 2^6 = 64 possible partial-completion states. Most of these are inconsistent.

The design doc specifies "Outbox persistence rate > 99.9%" but doesn't define the recovery mechanism. Without idempotent sinks, retries create duplicates. Without idempotent sinks AND proper tracking, the system either loses writes or creates phantom data.

**Why it happens:**
- Crash between sink writes is inevitable (power loss, OOM, kill -9)
- Sinks have different write characteristics: Vault (file system) is not atomic with Claims DB (SQLite) or FTS5 Index
- Git commits (Vault version control) can fail mid-commit, leaving the working directory dirty
- Idempotency requires sink-specific deduplication logic
- WAL mode SQLite helps but doesn't solve cross-sink atomicity

**How to avoid:**
1. Every outbox message must have a unique ID (UUID). Every sink must track the last processed message ID. This enables exactly-once processing: a sink skips messages it has already processed
2. Make each sink idempotent: Vault uses content-addressable storage (hash = ID, write same hash = no-op); Claims DB uses `INSERT OR IGNORE` with claim UUID as primary key; FTS5 uses `DELETE + INSERT` pattern
3. Use a state machine per message: `PENDING -> PROCESSING -> [SINK1_OK, SINK2_OK, ...] -> COMPLETED`. On restart, scan for messages in `PROCESSING` state and retry only incomplete sinks
4. Vault writes happen first (they're the source of truth). If Vault fails, the entire message fails. If Vault succeeds but other sinks fail, only the failed sinks are retried
5. Git commits should be the LAST sink, after all database writes succeed. A dirty git working directory is recoverable; missing database records are not
6. Add a `saw_lint --queue` command that checks outbox for orphan messages and offers recovery options

**Warning signs:**
- `saw_status` shows messages stuck in PROCESSING state
- Count mismatches between Vault files and Claims DB records
- Git working directory has uncommitted changes after clean shutdown
- FTS5 search returns results that have no corresponding Claims DB entries

**Phase to address:**
Phase 1 (Core Foundation) -- Write Queue is the backbone of all writes. If it's not reliable, every feature that writes data (ingestion, editing, governance) is unreliable.

---

### Pitfall 8: PDF Parsing Silent Failures and Content Loss

**What goes wrong:**
The three-tier PDF parsing pipeline (MinerU -> Docling -> PyMuPDF) is designed for resilience, but silent failures are the norm. MinerU may successfully parse a PDF but lose 20% of the content (especially tables, formulas, multi-column layouts) without reporting any error. Docling may preserve structure but garble special characters. PyMuPDF may extract raw text but lose all formatting and structure.

The critical issue is that the ingestion pipeline reports success (the PDF was parsed, text was extracted) but the extracted text is incomplete or incorrect. This feeds bad data into Claims extraction, which produces low-quality claims that get confidence scores and enter the knowledge base. The user never knows the PDF was poorly parsed.

For academic papers (a primary use case), this is devastating: formulas become garbled text, figure captions are lost, table structures are flattened, and footnotes disappear. The resulting claims are literally wrong but appear valid because they were "extracted from a PDF."

**Why it happens:**
- PDF parsing libraries differ dramatically in quality depending on PDF structure (scanned vs. native, single vs. multi-column, with/without OCR layer)
- MinerU and Docling both attempt layout analysis but use different heuristics; neither is 100% accurate
- The degradation path (MinerU fails -> try Docling -> try PyMuPDF) doesn't distinguish between "parse succeeded with quality loss" and "parse succeeded accurately"
- No standard metric exists for "parsing quality" -- character count, word count, and structure preservation are imperfect proxies
- Users don't review extracted text before claims are generated from it

**How to avoid:**
1. After parsing, compute quality metrics: character count, word count, paragraph count, table count, image/figure count. Compare against PDF metadata (page count, file size). Flag documents where extracted word count is <50% of expected (based on page count heuristic)
2. Require user review of extracted text for documents exceeding a configurable length threshold. Show a diff-friendly summary: "Extracted 45 pages, 12 tables, 8 figures. 3 pages had low confidence extraction (highlighted)."
3. For MinerU, use its built-in quality metrics if available (layout confidence scores). For Docling, check its document structure output for completeness
4. Store the parsing tier used in Vault metadata: `meta.yaml` records `parser: mineru`, `parser: docling`, or `parser: pymupdf`. Downstream consumers (Writer, Critic) can adjust confidence based on parser quality
5. Implement a "re-parse with higher tier" command for documents flagged as low quality: `saw ingest --reparse document.pdf`
6. Add structure validation: if a PDF has a table of contents but the extracted text doesn't match the TOC entries, flag it

**Warning signs:**
- Extracted text contains garbled characters (e.g., "ff" ligatures become missing, math symbols become "?")
- Claim extraction produces unusually high "ambiguous" source markings
- Users report claims that contradict what they read in the original PDF
- PDF with known tables produces no table-like claims
- Word count per page drops below 50 (likely image-only pages missed by OCR)

**Phase to address:**
Phase 1 (Ingest Engine) -- PDF parsing is a Phase 1 feature. Quality metrics must be built into the parsing pipeline from the start, not retrofitted.

---

### Pitfall 9: Embedding Model Domain Mismatch for Technical Content

**What goes wrong:**
The default embedding model `all-MiniLM-L6-v2` (80MB, local, zero API) is a general-purpose sentence transformer trained on web text and NLI data. It performs poorly on technical content: code snippets, mathematical notation, chemical formulas, domain-specific jargon, and multilingual text (Chinese technical terms). Two semantically similar code snippets can have low cosine similarity, while unrelated code with similar variable names can have high similarity.

For Smart Agent Wiki's use case (knowledge workers, researchers, developers), this means the optional vector search returns poor results for the most valuable content: technical documentation, code analysis, and domain-specific research. The BM25 fallback is better for exact keyword matching but misses semantic relationships.

The 384-dimensional output of MiniLM also limits discrimination at scale: with thousands of documents, embedding vectors become crowded, reducing the effective search space.

**Why it happens:**
- MiniLM was trained on English web text and NLI; it has minimal exposure to code, math, or technical jargon
- Chinese technical terms may be tokenized into meaningless sub-word units
- Code embeddings require understanding of syntax and semantics, not just text similarity
- The model is frozen -- it cannot adapt to the user's domain vocabulary
- 384 dimensions provide ~50 bits of effective information, which saturates at ~10K distinct documents

**How to avoid:**
1. Use `all-MiniLM-L6-v2` only as the default for the "zero API" mode (Level 3 offline). For Level 1/2 modes, use a larger model: `BAAI/bge-large-en-v1.5` (1024 dimensions) or `intfloat/multilingual-e5-large` (for Chinese support)
2. For code content, use a code-specific embedding model or fall back to AST-based matching (already designed for structured extraction)
3. Implement a hybrid search score: `final_score = alpha * bm25_score + (1 - alpha) * vector_score`. Start with `alpha=0.6` (favor BM25) and tune based on user feedback
4. Add domain vocabulary fine-tuning as a Phase 4 feature: collect user corrections to search results as training signal
5. Monitor search quality: track click-through rates and "not found" complaints. If vector search consistently underperforms BM25, reduce its weight or disable it
6. Consider `BAAI/bge-m3` for multilingual support (Chinese + English + technical content) as an upgrade path

**Warning signs:**
- Vector search returns semantically irrelevant results for technical queries
- BM25 search outperforms vector search on user satisfaction metrics
- Chinese content has significantly worse retrieval quality than English
- Search quality degrades as knowledge base grows past 500 documents
- Embedding similarity scores cluster around 0.7-0.8 for most pairs (low discrimination)

**Phase to address:**
Phase 1 (default embedding setup) and Phase 3 (optional vector search). The hybrid scoring and model selection must be decided before the vector search integration is built.

---

### Pitfall 10: Multi-Agent Deadlock in YAML Workflow Execution

**What goes wrong:**
YAML workflow orchestration (e.g., Scholar -> Critic -> Writer pipeline with confidence gates) can deadlock when gates cannot be satisfied. For example, a workflow requires `confidence >= 3` but the Critic always finds `confidence = 2` due to a systematic extraction issue. The workflow loops forever: Scholar produces draft, Critic rejects, Scholar revises, Critic rejects again.

More subtly, multi-agent coordination can deadlock when agents hold resources (file locks, Claims DB write locks) while waiting for other agents to complete. The Librarian holds a read lock on the entity registry while the Writer waits for an entity resolution to write a claim. Neither can proceed.

A2A protocol message passing can also deadlock if message queues fill up or if agents form circular wait chains (Agent A waits for Agent B's response, which waits for Agent C's response, which waits for Agent A).

**Why it happens:**
- YAML workflow gates don't specify retry limits or fallback actions
- Agent roles have implicit resource dependencies that aren't declared
- File locks (from the governance engine's check-out mechanism) have TTL but no deadlock detection
- A2A JSON-RPC is synchronous by default; agents block while waiting for responses
- The `Spark field` mechanism (forcing candidate solutions on contradiction) can create infinite correction loops

**How to avoid:**
1. Every YAML workflow step must have `max_retries` and `fallback` fields. If Scholar can't produce a draft that passes Critic after 3 attempts, fall back to writing a "needs human review" page
2. Implement a workflow timeout: if a workflow hasn't completed in N minutes (configurable), abort and roll back all changes from that workflow
3. Use lock ordering: agents must acquire locks in a defined order (Vault -> Claims -> Wiki -> Graph -> Index). This prevents circular wait
4. A2A communication should be async with message queues, not synchronous RPC. Agents process messages from their queue and send responses asynchronously
5. Add deadlock detection in the Guardian (rules engine): periodically check for circular wait chains using a wait-for graph. If detected, abort the youngest transaction
6. YAML workflow gates should support `fallback_action: accept_with_flag` -- if confidence can't reach the threshold after retries, accept the result with a "low confidence" flag rather than blocking forever

**Warning signs:**
- Workflows stuck in "running" state for >10 minutes
- Agent log shows the same Critic rejection message repeating
- File locks held for >5 minutes
- A2A message queue depth growing without shrinking
- Knowledge base not updating despite active ingestion

**Phase to address:**
Phase 3 (Collaboration Engine) -- YAML workflows and A2A are Phase 3 features. But the lock ordering and timeout mechanisms should be designed in Phase 1 (when the Write Queue and Claims DB are built) because they constrain the lock acquisition pattern.

---

### Pitfall 11: FTS5 Trigram Tokenizer Bloat with CJK Content

**What goes wrong:**
For Chinese/Japanese/Korean text, the default `unicode61` tokenizer produces poor results because CJK languages don't use spaces as word boundaries. The trigram tokenizer (`tokenize="trigram"`) solves this by indexing every 3-character sequence, but it creates enormous indexes: a 100-page Chinese knowledge base can produce a trigram index 3-5x larger than the source content.

Smart Agent Wiki's design includes multilingual support as a Phase 4 goal, but the FTS5 tokenizer choice must be made at table creation time. Changing from `unicode61` to `trigram` requires a full index rebuild. If the initial implementation uses `unicode61` (optimized for English), Chinese content ingested during Phases 1-3 will be poorly indexed, and migrating to `trigram` later requires rebuilding the entire index.

**Why it happens:**
- `unicode61` tokenizer splits on spaces and punctuation -- useless for Chinese text without spaces
- `trigram` tokenizer indexes every 3-character window, creating massive indexes for CJK
- FTS5 tokenizer is set at `CREATE VIRTUAL TABLE` time and cannot be changed without recreating the table
- Mixing English and Chinese content in the same FTS5 table means no single tokenizer is optimal
- The design doc defaults to English but has a Chinese-speaking target audience

**How to avoid:**
1. Use `unicode61` for Phase 1-2 (English content) but design the FTS5 schema to support a tokenizer migration path
2. For Chinese support, use a CJK-aware segmenter (jieba for Chinese, MeCab for Japanese) as a custom FTS5 tokenizer, NOT trigram. This produces word-level tokens without the index bloat
3. Consider separate FTS5 tables for different languages, each with its own tokenizer. The query engine routes to the appropriate table based on detected language
4. If trigram is used, set `detail=none` to reduce index size (trigram + detail=full is especially bloated)
5. Monitor index-to-content ratio: if the FTS5 index exceeds 2x the source content size, investigate tokenizer inefficiency

**Warning signs:**
- FTS5 index file size grows faster than source content
- Chinese text search returns poor results (misses obvious matches)
- `saw_search` for Chinese terms returns only exact character matches, no partial/semantic matches
- Query latency increases for Chinese content but not English

**Phase to address:**
Phase 1 (tokenizer choice at table creation) and Phase 4 (multilingual support). The tokenizer architecture must be forward-compatible from Phase 1.

---

### Pitfall 12: Guardian Rules Engine Complexity Spiral

**What goes wrong:**
The Guardian agent is a rules engine (zero LLM cost) responsible for security checks, permission control, Cedar policy enforcement, and the "second rule" auto-defense mechanism. As the system grows, the rule set expands: Cedar policies for each tool, CVE-anchored defense rules, agent capability tokens, file lock policies, write-protection rules, blast radius policies.

The rules become so complex that: (a) rule interactions produce unexpected behavior (rule A permits what rule B forbids -- Cedar's resolution is "deny" but the interaction may not be obvious); (b) performance degrades as every operation must be evaluated against hundreds of rules; (c) debugging becomes impossible because the user cannot understand why an operation was denied.

The "second rule" auto-defense is particularly dangerous: the second time a pattern occurs, it auto-creates a defense rule. If the first occurrence was a false positive, the auto-created rule blocks legitimate operations permanently.

**Why it happens:**
- Cedar policy evaluation is O(rules * conditions) per operation
- Auto-generated rules (from "second rule" pattern) accumulate without pruning
- Rule interaction effects are non-obvious (permit + forbid = deny, but partial overlaps create confusion)
- No rule impact analysis before adding new rules
- The rule set grows monotonically -- rules are added but never removed

**How to avoid:**
1. Cap the Guardian rule set at a maximum size (e.g., 200 rules). When the cap is reached, require manual review and pruning before adding new rules
2. Every auto-generated rule must have a TTL (e.g., 30 days). If not promoted to a permanent rule by human review, it expires
3. Implement rule simulation: before adding a rule, test it against the last N operations to see what would be blocked. Show the user the projected impact
4. Add a `saw_lint --rules` command that checks for conflicting rules, redundant rules, and overly broad rules
5. "Second rule" auto-defense should only create advisory rules (log warning, don't block) for the first 3 occurrences. Only promote to blocking rules after human confirmation
6. Log all Guardian decisions with rule IDs, making debugging traceable

**Warning signs:**
- Guardian evaluation takes >100ms per operation
- Legitimate operations are unexpectedly denied
- Rule count grows faster than feature count
- Users disable the Guardian to get work done
- Cedar policy conflicts logged in `saw_lint`

**Phase to address:**
Phase 2 (Governance Engine) -- when Cedar policies and Guardian are implemented. The TTL and cap mechanisms must be designed from the start.

---

### Pitfall 13: Cedar Policy Binding Immaturity (Phase 03)

**What goes wrong:**
The `cedar-python 0.1.4` binding is early-stage and may lack full coverage of Cedar features or have Python-specific bugs. When the binding fails or produces incorrect authorization decisions, the entire multi-agent orchestration is blocked because Guardian can't verify if an agent is permitted to perform an action.

**Why it happens:**
- cedar-python is marked experimental by Amazon
- Feature parity with the Rust/JS Cedar implementations is incomplete
- Python binding may not receive updates at the same cadence as core Cedar

**How to avoid:**
1. Implement a `PolicyEngine` protocol with two adapters: `CedarPythonAdapter` and `CedarCLIAdapter`
2. `CedarCLIAdapter` invokes the official Cedar CLI as a subprocess (slower but authoritative)
3. At startup, run a feature detection test. If cedar-python fails, auto-fallback to CLI
4. Log all authorization decisions for audit trail regardless of adapter used
5. The Guardian should treat policy engine failures as "deny by default" (fail-secure)

**Warning signs:**
- cedar-python import fails or produces AttributeError
- Authorization decisions differ between cedar-python and Cedar CLI
- Policy parsing errors that work in the Cedar playground

**Phase to address:**
Phase 3 (Collaboration Engine) -- when Guardian and Cedar policies are first used for agent authorization.

---

### Pitfall 14: Cytoscape.js Performance Degradation at Scale (Phase 03)

**What goes wrong:**
Cytoscape.js renders all nodes and edges in the browser. With >500 entities, the DOM manipulation and canvas rendering becomes slow. User interactions (pan, zoom, drag) become jerky. The knowledge graph visualization that should aid exploration becomes a frustration.

**Why it happens:**
- Every node/edge is a DOM element or canvas draw call
- Force-directed layout algorithms (CoSE) are O(n squared) per iteration
- No built-in lazy loading or clustering
- Browser memory grows with graph size

**How to avoid:**
1. Use `cy.batch()` for all initial graph loads
2. Enable performance optimizations: `hideEdgesOnViewport: true`, `textureOnViewport: true`
3. Implement lazy loading: load only 2-hop neighbors on expand, not entire graph
4. At >200 nodes, switch to community view (cluster by page type)
5. At >500 nodes, switch to topic cluster view with drill-down
6. Use WebWorker for layout computation (CoSE supports this)

**Warning signs:**
- Initial graph render takes >3 seconds
- Pan/zoom feels jerky
- Browser memory exceeds 500MB
- User reports "graph is broken" for large knowledge bases

**Phase to address:**
Phase 3 (Web UI) -- when Cytoscape.js component is built.

---

### Pitfall 15: A2A Protocol Version Drift (Phase 03)

**What goes wrong:**
The A2A protocol (Google/Linux Foundation, v1.0.2) is new and evolving. Smart Agent Wiki implements the current spec, but external agents or future A2A versions may use different message formats. Interoperability breaks silently.

**Why it happens:**
- A2A spec is not yet finalized
- Different implementations may interpret "optional" fields differently
- Agent Cards (capability advertisements) may use different schemas
- JSON-RPC 2.0 error codes are implementation-specific

**How to avoid:**
1. Include A2A protocol version in Agent Card metadata
2. Implement version negotiation: reject connections from incompatible versions
3. Log all A2A message types received; flag unknown types for investigation
4. Monitor the A2A spec repository for changes
5. Design the A2A adapter to be pluggable: `A2AAdapterV1`, `A2AAdapterV2`, etc.

**Warning signs:**
- External agents can't connect or produce errors
- A2A messages with unrecognized fields
- Agent Cards that don't match expected schema
- Interoperability works in dev but breaks in production

**Phase to address:**
Phase 3 (Collaboration Engine) -- when A2A protocol is implemented.

---

### Pitfall 16: React State Desync with WebSocket (Phase 03)

**What goes wrong:**
The Web UI uses WebSocket for real-time updates. When the WebSocket disconnects and reconnects, the frontend state may have missed events. The UI shows stale data while the backend has newer state. User actions based on stale state produce incorrect results or conflicts.

**Why it happens:**
- WebSocket connections drop silently (network issues, browser sleep)
- Reconnect doesn't automatically replay missed events
- Zustand stores update on message receipt but don't track gaps
- No acknowledgment mechanism for WebSocket messages

**How to avoid:**
1. On WebSocket connect, fetch current state via REST API (sync point)
2. Implement message sequence numbers; detect gaps on reconnect
3. Show connection status indicator (connected/connecting/disconnected)
4. When disconnected, disable actions that require real-time data
5. Use TanStack Query for server state; it handles refetch-on-reconnect automatically
6. For critical operations (edits), use REST API with optimistic updates, not WebSocket

**Warning signs:**
- UI shows different data than `saw status` CLI output
- User edits conflict with other users' changes
- WebSocket reconnects frequently
- Actions fail with "stale state" errors

**Phase to address:**
Phase 3 (Web UI) -- when WebSocket integration is built.

---

### Pitfall 17: YAML Workflow Gate Loop (Phase 03)

**What goes wrong:**
YAML workflows with gates (e.g., `confidence >= 3`) can loop infinitely when the gate cannot be satisfied. A Scholar to Critic to Writer workflow keeps retrying because the Critic always finds issues. No maximum retry limit is defined. The workflow consumes resources endlessly.

**Why it happens:**
- YAML gates don't specify `max_retries` by default
- No fallback action when gate can't be satisfied
- LLM variability means retrying the same step may not improve results
- The Writer Agent lacks context about why the Critic rejected the draft

**How to avoid:**
1. Every gate MUST have `max_retries` (default: 3) and `fallback_action`
2. `fallback_action` can be: `accept_with_flag`, `escalate_to_human`, `abort`
3. Track retry count in workflow execution state
4. When max retries exceeded, execute fallback and log the failure reason
5. The Critic should provide specific, actionable feedback (not just "quality too low")
6. Add a workflow-level timeout: if not complete in N minutes, abort

**Warning signs:**
- Workflows stuck in "running" for >10 minutes
- Same gate failure repeating in logs
- Resource consumption (LLM calls) without progress
- No completed workflows despite active ingestion

**Phase to address:**
Phase 3 (Collaboration Engine) -- when YAML workflow executor is built.

---

## Ecosystem Integration Pitfalls (v3.0)

*The following pitfalls are specific to adding Obsidian Plugin, Chrome Extension, and RSS Subscription features to the existing Smart Agent Wiki system.*

---

### Pitfall 18: Obsidian Plugin Race Condition on File Operations (Vault.read vs Vault.cachedRead)

**What goes wrong:**
Using `cachedRead()` when intending to modify the file causes overwrites with stale data. Another concurrent modification between your read and write will be lost.

**Why it happens:**
Developers default to `cachedRead()` for performance, but it returns cached content that may not reflect current disk state. The Obsidian documentation explicitly warns: "Use this if you intend to modify the file content afterwards. Use Vault.cachedRead() otherwise for better performance."

**Consequences:**
- Data loss when two operations modify the same file
- Sync conflicts with Obsidian Sync
- User edits silently overwritten by plugin background operations

**How to avoid:**
1. Use `Vault.read()` when you intend to modify and rewrite the file
2. Use `Vault.process()` for atomic read-modify-write operations
3. Never use `cachedRead()` before modifications

```typescript
// WRONG: Race condition risk
const content = await this.app.vault.cachedRead(file);
await this.app.vault.modify(file, modifyContent(content));

// RIGHT: Atomic operation
await this.app.vault.process(file, (content) => modifyContent(content));
```

**Warning signs:**
- Sync conflict files appearing in vault
- User reports of lost edits
- File modification timestamps change unexpectedly

**Phase to address:** Phase 07 (Obsidian Plugin Core)

---

### Pitfall 19: Obsidian Event Listener Memory Leaks on Plugin Unload

**What goes wrong:**
Event listeners registered with `app.vault.on()` or `app.workspace.on()` continue firing after plugin unload, causing errors and memory leaks.

**Why it happens:**
Developers forget that plugins can be disabled and reloaded; raw event subscriptions are not automatically cleaned up. The Obsidian Developer Docs state: "It is crucial to detach registered event handlers when a plugin unloads to prevent memory leaks."

**Consequences:**
- Console errors flooding the UI
- Stale callback execution after plugin disabled
- Crashes when unloaded plugin tries to update UI elements
- Memory consumption grows over time

**How to avoid:**
Always use `this.registerEvent()` inside plugin class:

```typescript
// WRONG: Never cleaned up
this.app.vault.on('modify', (file) => this.handleModify(file));

// RIGHT: Auto-cleaned on plugin unload
this.registerEvent(
  this.app.vault.on('modify', (file) => this.handleModify(file))
);

// For DOM events
this.registerDomEvent(element, 'click', (evt) => this.handleClick(evt));

// For intervals
this.registerInterval(window.setInterval(() => this.poll(), 60000));
```

**Warning signs:**
- DevTools showing event listeners after plugin disable
- Console errors referencing disposed plugin
- Memory not released after plugin unload

**Phase to address:** Phase 07 (Obsidian Plugin Core)

---

### Pitfall 20: Incorrect File Type Checking (TFile vs TFolder vs TAbstractFile)

**What goes wrong:**
Operations like `Vault.read()` or `MetadataCache.getFileCache()` crash when passed a TFolder instead of TFile.

**Why it happens:**
Methods like `Vault.getAbstractFileByPath()` return `TAbstractFile` which could be either file or folder. The Obsidian API docs show: "Determines if a TAbstractFile object is a file or a folder using instanceof."

**Consequences:**
- Plugin crashes on vaults with folders matching expected file paths
- Confusing error messages for users
- Plugin appears "broken" on certain vault structures

**How to avoid:**
Always check with `instanceof` before file-specific operations:

```typescript
const abstractFile = this.app.vault.getAbstractFileByPath('some/path');
if (abstractFile instanceof TFile) {
  const content = await this.app.vault.read(abstractFile);
} else if (abstractFile instanceof TFolder) {
  // Handle folder case
}
```

**Warning signs:**
- Plugin crashes on startup for certain vault structures
- Errors mentioning "TFile" type mismatches
- Works on some vaults, fails on others

**Phase to address:** Phase 07 (Obsidian Plugin Core)

---

### Pitfall 21: Chrome Extension Manifest V3 Remote Code Prohibition

**What goes wrong:**
Extension rejected by Chrome Web Store or crashes because it tries to load external JavaScript.

**Why it happens:**
Manifest V3 prohibits remotely hosted code - no CDN scripts, no dynamically fetched code execution. Chrome documentation states: "In Manifest V3, all of your extension's logic must be part of the extension package. You can no longer load and execute remotely hosted files."

**Consequences:**
- Extension cannot be published
- Users cannot install
- Complete architecture rewrite needed after discovering limitation

**How to avoid:**
1. Bundle all JavaScript with the extension package
2. Use web APIs directly instead of loading libraries from CDN
3. If you need external data, fetch JSON/configuration, not code
4. Use declarativeNetRequest instead of dynamic webRequest blocking

```json
// WRONG: Remote script
"content_scripts": [{
  "js": ["https://cdn.example.com/library.js"]
}]

// RIGHT: Bundled script
"content_scripts": [{
  "js": ["bundled-library.js"]
}]
```

**Warning signs:**
- Chrome Web Store rejection email
- Console errors about CSP violations
- Extension fails to load after manifest changes

**Phase to address:** Phase 08 (Chrome Extension) - architecture decision before implementation

---

### Pitfall 22: Chrome Service Worker Lifecycle Breaks State

**What goes wrong:**
Background state (variables, connections, timers) disappears because MV3 service workers terminate after ~30 seconds of inactivity.

**Why it happens:**
MV3 replaced persistent background pages with event-driven service workers that can be terminated at any time. Chrome documentation: "Service workers do not have direct DOM access... Service workers are designed to run only when needed."

**Consequences:**
- Lost authentication tokens
- Broken WebSocket connections
- Incomplete background tasks
- Timers stop firing unexpectedly

**How to avoid:**
1. Persist all state to `chrome.storage.local` or `chrome.storage.session`
2. Use IndexedDB for complex data structures
3. Re-establish connections on service worker wake (`chrome.runtime.onStartup`)
4. Use `chrome.alarms` for scheduled tasks instead of `setInterval`

```javascript
// WRONG: Lost when service worker terminates
let authToken = null;
setInterval(() => poll(), 60000);

// RIGHT: Persisted state
chrome.storage.local.get(['authToken'], (result) => {
  // Always read from storage
});
chrome.alarms.create('poll', { periodInMinutes: 1 });
```

**Warning signs:**
- Extension loses state after idle period
- WebSocket connections drop silently
- Timers stop working after browser idle
- Background tasks incomplete after resume

**Phase to address:** Phase 08 (Chrome Extension) - fundamental MV3 architecture

---

### Pitfall 23: Chrome Content Script Isolation Blocking

**What goes wrong:**
Content script cannot access page JavaScript variables or functions; page cannot directly call extension functions.

**Why it happens:**
Content scripts run in isolated "island" context - separate from page JavaScript for security. Chrome docs: "Content scripts and their host pages have isolated execution environments but share access to the page's DOM."

**Consequences:**
- Cannot directly interact with page application state
- Complex message passing workarounds needed
- Authentication state from page inaccessible
- Cannot call page JavaScript libraries

**How to avoid:**
1. Use `window.postMessage` for page-to-content-script communication
2. Inject script tags into page DOM for direct page access (but loses extension APIs)
3. Use custom events with `CustomEvent` for structured data

```javascript
// Content script - receives from page
window.addEventListener('message', (event) => {
  if (event.source !== window) return;
  if (event.data.type === 'FROM_PAGE') {
    chrome.runtime.sendMessage(event.data.payload);
  }
});

// Page script - sends to content script
window.postMessage({ type: 'FROM_PAGE', payload: data }, '*');
```

**Warning signs:**
- Content script sees `undefined` for page variables
- Direct function calls fail silently
- Console shows "not defined" errors for page globals
- Extension cannot read page's authentication state

**Phase to address:** Phase 08 (Chrome Extension) - affects integration design

---

### Pitfall 24: Chrome Storage Sync Quota Exceeded

**What goes wrong:**
`chrome.storage.sync.set()` silently fails or throws quota exceeded errors.

**Why it happens:**
`storage.sync` has strict limits per Chrome documentation:
- 100KB total (QUOTA_BYTES)
- 8KB per item (QUOTA_BYTES_PER_ITEM)
- 120 writes per hour (MAX_WRITE_OPERATIONS_PER_HOUR)
- 10 writes per minute (MAX_WRITE_OPERATIONS_PER_MINUTE)
- 512 maximum items (MAX_ITEMS)

**Consequences:**
- Settings not persisting
- Sync failing silently
- User frustration when preferences lost
- Cross-device state desynchronized

**How to avoid:**
1. Use `storage.local` for large data (10MB default, unlimited with permission)
2. Only use `storage.sync` for settings that need cross-device sync
3. Implement quota-aware write batching
4. Check `chrome.runtime.lastError` after storage operations

```javascript
// Check limits first
const QUOTA_BYTES = chrome.storage.sync.QUOTA_BYTES; // ~100KB

// For large data, use local storage
chrome.storage.local.set({ largeData: data }, () => {
  if (chrome.runtime.lastError) {
    console.error(chrome.runtime.lastError);
  }
});
```

**Warning signs:**
- Settings not syncing across devices
- `QUOTA_BYTES_EXCEEDED` errors in console
- Write operations silently failing
- Partial data saved

**Phase to address:** Phase 08 (Chrome Extension) - affects data model design

---

### Pitfall 25: RSS Feed GUID Changes Breaking Deduplication

**What goes wrong:**
RSS items appear as duplicates because feed publisher changed the GUID format or domain.

**Why it happens:**
GUIDs are often URL-based; when sites migrate or restructure, GUIDs change while content remains the same. Many feed readers only use GUID for deduplication.

**Consequences:**
- Duplicate entries in knowledge base
- Broken "read" state tracking
- User confusion seeing same content twice
- Ingestion history polluted

**How to avoid:**
1. Use multiple deduplication keys: GUID + title hash + content hash
2. Implement fuzzy matching for similar titles (edit distance)
3. Store historical GUIDs for each source and match against all
4. Normalize URLs before comparison (remove tracking parameters)

```python
# Multi-key deduplication
def get_item_hash(item):
    title_hash = hashlib.md5(item.title.encode()).hexdigest()[:8]
    # Strip HTML, normalize whitespace for content hash
    content_clean = re.sub(r'\s+', ' ', strip_html(item.description or ''))
    content_hash = hashlib.md5(content_clean.encode()).hexdigest()[:8]
    return f"{item.guid}:{title_hash}:{content_hash}"
```

**Warning signs:**
- Sudden spike in "new" items that are clearly old content
- Users reporting duplicates
- Feed ingestion count jumps unexpectedly
- Same content with different GUIDs

**Phase to address:** Phase 09 (RSS Subscription) - core ingestion logic

---

### Pitfall 26: RSS Feed Parsing Encoding Issues

**What goes wrong:**
Text appears garbled (Mojibake) - accented characters broken, quotes replaced with question marks.

**Why it happens:**
Some feeds declare wrong encoding in XML header; others don't declare encoding at all; HTTP headers conflict with XML declaration.

**Consequences:**
- Unreadable content
- Broken search indexing
- User frustration with non-English content
- Metadata extraction failures

**How to avoid:**
1. Use robust parsing library (Python: feedparser handles encoding detection)
2. Normalize all content to UTF-8 after parsing
3. Log encoding warnings for manual review
4. Fallback to HTTP Content-Type header encoding if XML parsing fails

```python
import feedparser

# feedparser handles most encoding issues automatically
feed = feedparser.parse(url, request_headers={'Accept': 'application/xml'})

# Check for encoding problems
if feed.bozo:  # bozo bit indicates parsing issue
    logger.warning(f"Feed {url} has encoding issues: {feed.bozo_exception}")
    # Attempt recovery strategies
```

**Warning signs:**
- Garbled text in ingested content
- `feed.bozo` flag true during parsing
- Missing or corrupted special characters
- Non-ASCII content malformed

**Phase to address:** Phase 09 (RSS Subscription) - ingestion robustness

---

### Pitfall 27: RSS Aggressive Polling Leading to IP Blocks

**What goes wrong:**
Feed sources block your IP or return 429 errors; feeds stop updating.

**Why it happens:**
Polling every feed every hour for hundreds of sources looks like a DDoS attack.

**Consequences:**
- Missing new content
- IP bans affecting other features
- Reputation damage to the service
- All feeds appear "stuck"

**How to avoid:**
1. Implement adaptive polling intervals based on feed update frequency
2. Use conditional GET with `If-Modified-Since` and `If-None-Match` headers
3. Respect `ttl` and `sy:updatePeriod` elements in feeds
4. Exponential backoff for failing feeds
5. Stagger polling across time windows, not all at once

```python
import datetime

headers = {}
if last_modified:
    headers['If-Modified-Since'] = last_modified
if etag:
    headers['If-None-Match'] = etag

response = requests.get(url, headers=headers)
if response.status_code == 304:
    # Not modified, skip parsing
    return None

# Store new last_modified and etag for next request
```

**Warning signs:**
- 429 responses in logs
- Feeds showing old entries despite known updates
- IP blocks reported by other users on same IP
- All feeds return same timestamp

**Phase to address:** Phase 09 (RSS Subscription) - scheduler design

---

### Pitfall 28: Bidirectional Sync State Corruption (Obsidian + Wiki)

**What goes wrong:**
Changes made in Obsidian and Smart Agent Wiki simultaneously cause unresolvable conflicts.

**Why it happens:**
No clear authority model; both systems think they're the source of truth.

**Consequences:**
- Data divergence between systems
- User confusion about which version is correct
- Potential data loss during conflict resolution
- Sync loop (changes never stabilizing)

**How to avoid:**
1. Establish clear authority model: Vault is source of truth for content, Wiki for metadata
2. Use last-write-wins with conflict file generation for unresolvable cases
3. Implement change vectors (similar to vector clocks) for conflict detection
4. Consider CRDT for specific fields like tags
5. User must explicitly resolve conflicts before sync continues

```typescript
// Conflict detection
interface ChangeVector {
  source: 'obsidian' | 'saw';
  timestamp: number;
  hash: string;
}

// Detect conflicting changes
function detectConflict(local: ChangeVector, remote: ChangeVector): boolean {
  return local.hash !== remote.hash && 
         local.timestamp > remote.timestamp &&
         remote.source !== local.source;
}
```

**Warning signs:**
- Users seeing different content in different views
- Sync loop detected (changes never stabilizing)
- Conflict files accumulating without resolution
- Data reverting after sync completes

**Phase to address:** Phase 07 (Obsidian Plugin Core) - sync strategy is foundational

---

### Pitfall 29: Chrome Extension CORS Blocking to Local Server

**What goes wrong:**
Chrome extension cannot communicate with local Smart Agent Wiki API server.

**Why it happens:**
CORS policy blocks cross-origin requests; local server may not have proper headers configured for extension origin.

**Consequences:**
- Extension cannot save clipped content
- Broken user workflow
- "Network error" messages
- Extension appears non-functional

**How to avoid:**
1. Add extension ID to CORS allowed origins in local server
2. Use `chrome.runtime.sendMessage` to background script for API calls (bypasses CORS)
3. Consider native messaging for deep local integration
4. Configure FastAPI CORS middleware to allow extension origin

```python
# FastAPI CORS configuration
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "chrome-extension://YOUR_EXTENSION_ID",
        "http://localhost:*",  # Development
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Warning signs:**
- Network errors in extension DevTools
- "CORS policy" errors in console
- Extension works for external sites but not local API
- Requests show as "(failed)" in network tab

**Phase to address:** Phase 08 (Chrome Extension) - requires server configuration changes

---

### Pitfall 30: Schema Mismatch Between Sources (Obsidian + Chrome + RSS)

**What goes wrong:**
Data from Obsidian, Chrome, and RSS have incompatible structures when stored in the same database.

**Why it happens:**
Each source has different metadata, content formats, and reference models.

**Consequences:**
- Query failures when joining across sources
- Lost metadata during ingestion
- Complex workarounds in code
- Inconsistent search results

**How to avoid:**
1. Design a unified source-agnostic schema with source-specific extensions
2. Use content-addressed storage for deduplication across sources
3. Implement source adapters that normalize to common format

```python
# Unified schema with source extensions
class UnifiedDocument:
    id: str  # content hash
    title: str
    content: str
    source_type: Literal['obsidian', 'web_clip', 'rss']
    source_id: str
    source_metadata: dict  # Source-specific fields
    created_at: datetime
    updated_at: datetime

# Source-specific adapter pattern
class SourceAdapter(Protocol):
    def normalize(self, raw_data: Any) -> UnifiedDocument: ...
    def denormalize(self, doc: UnifiedDocument) -> Any: ...
```

**Warning signs:**
- Query errors when joining across sources
- Missing fields in UI for certain source types
- Duplicate content appearing from different sources
- Metadata not preserved after sync

**Phase to address:** Phase 07 (Obsidian Plugin Core) - must be designed before any source implementation

---

## Third-Party Integration Pitfalls (v3.1)

*The following pitfalls are specific to adding Notion, Logseq, IM (Slack/Discord/Feishu), and GitHub integrations to the existing Smart Agent Wiki system.*

---

### Pitfall 31: Notion API Rate Limit Underestimation

**What goes wrong:**
Developers assume Notion's rate limits are generous, then hit "429 Too Many Requests" during bulk sync operations, causing data loss or incomplete syncs.

**Why it happens:**
- Notion API has per-integration rate limits (approximately 3 requests per second)
- Rate limits vary by endpoint type (search is more restricted than read)
- Bulk operations accumulate requests faster than expected
- Error responses don't always include proper retry-after headers

**Consequences:**
- Incomplete database syncs
- Data loss during initial setup
- Timeout errors on large queries
- User frustration with sync failures

**How to avoid:**
1. Implement exponential backoff with jitter starting at 1 second
2. Use request queue with configurable rate limiting (max 2-3 req/s)
3. Batch operations: prefer `query` with larger `page_size` over many small requests
4. Store sync cursor before processing to enable resume after rate limit recovery
5. Monitor 429 responses and adjust rate limit budget accordingly

```python
import time
import random

def with_rate_limit(func, max_retries=5):
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError as e:
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait_time)
    raise MaxRetriesExceeded()
```

**Warning signs:**
- Intermittent 429 errors during initial sync
- Timeout errors on large database queries
- Sync operations taking progressively longer
- API responses with increasing latency

**Phase to address:** Phase 10-01 (Notion Integration Core)

---

### Pitfall 32: Notion Property Type Mutation

**What goes wrong:**
Notion allows users to change property types (e.g., "Select" to "Multi-select", "Number" to "Text"), causing integration code to crash or silently corrupt data.

**Why it happens:**
- Notion API doesn't enforce property type stability
- Property schema changes happen outside integration control
- Type coercion logic is often incomplete (e.g., handling null values in converted properties)
- Select-to-Multi-select conversion duplicates values with commas

**Consequences:**
- Sync crashes on schema change
- Data appearing in wrong format after sync
- Missing values that existed before
- User confusion about data integrity

**How to avoid:**
1. Store property type at first discovery, validate on each sync
2. Implement defensive type coercion layer per property type
3. Log schema changes for manual review (don't auto-migrate without confirmation)
4. Maintain property type mapping table in local config
5. Support common type transitions: Select<->Multi-select, Number<->Text

```python
def coerce_property(value, from_type, to_type):
    if from_type == 'select' and to_type == 'multi_select':
        if value is None:
            return []
        # Single select becomes single-item array
        return [value] if isinstance(value, str) else []
    # ... handle other transitions
```

**Warning signs:**
- API errors mentioning "property type mismatch"
- Data appearing in wrong format after sync
- Missing values that existed before
- Property names returning different types

**Phase to address:** Phase 10-01 (Notion Integration Core)

---

### Pitfall 33: Notion Pagination Cursor Loss

**What goes wrong:**
Paginated queries return incomplete results because developers assume `has_more: false` or missing `next_cursor` is the only termination condition, missing edge cases.

**Why it happens:**
- Notion pagination uses base64-encoded cursors that can expire
- `next_cursor` may be null even when `has_more: true` during rate limiting
- Empty results don't always mean "no more data" (could be filtered out)
- Cursor format changes between API versions

**Consequences:**
- Incomplete data sync
- Missing pages in knowledge base
- Inconsistent results between syncs
- User reports of missing content

**How to avoid:**
1. Always check `has_more` AND `next_cursor` exists AND is non-empty
2. Implement cursor persistence for long-running syncs (enable resume)
3. Set explicit `page_size` (default is 100, max 100)
4. Track total results returned vs. expected for verification
5. Store last successful cursor for recovery

```python
def fetch_all_pages(query_fn, page_size=100):
    results = []
    has_more = True
    next_cursor = None
    
    while has_more:
        response = query_fn(page_size=page_size, start_cursor=next_cursor)
        results.extend(response.results)
        has_more = response.has_more
        next_cursor = response.next_cursor
        
        # Guard against missing cursor with has_more
        if has_more and not next_cursor:
            logger.warning("has_more=true but no cursor, stopping")
            break
    
    return results
```

**Warning signs:**
- Fewer results than expected from large databases
- Sync completes but data is incomplete
- Different result counts on repeated syncs
- Pagination stopping at 100 items

**Phase to address:** Phase 10-01 (Notion Integration Core)

---

### Pitfall 34: Logseq File Format Breaking Changes

**What goes wrong:**
Logseq's `.edn` config and `.md` file format can break between versions, causing parsing failures or data corruption.

**Why it happens:**
- Logseq is in active development with frequent format changes
- Block ID format is not stable across versions
- Metadata in file headers can change structure
- Custom properties may use reserved keywords in newer versions

**Consequences:**
- Parse errors after Logseq update
- Missing block references
- Corrupted metadata fields
- Sync failures between Logseq versions

**How to avoid:**
1. Pin Logseq version in documentation (recommend specific version)
2. Implement format version detection on file read
3. Parse defensively: skip unknown fields rather than crash
4. Maintain backup of files before any modification
5. Test integration against multiple Logseq versions

```python
LOGSEQ_FORMAT_VERSIONS = {
    '0.9.0': parse_v090,
    '0.10.0': parse_v010,
}

def detect_logseq_version(config_path):
    # Parse config.edn to extract version
    pass

def parse_logseq_file(content, version):
    parser = LOGSEQ_FORMAT_VERSIONS.get(version, parse_latest)
    return parser(content)
```

**Warning signs:**
- Parse errors after Logseq update
- Missing block references
- Corrupted metadata fields
- Unknown property warnings in logs

**Phase to address:** Phase 10-02 (Logseq Integration Core)

---

### Pitfall 35: Logseq Concurrent Edit Conflicts

**What goes wrong:**
When SAW and user both edit Logseq files, or multiple devices sync, changes are lost or files corrupted.

**Why it happens:**
- Logseq uses file-based storage without built-in conflict resolution
- No atomic file locking mechanism across devices
- Block UUIDs can collide if generated independently
- Git-based sync doesn't handle conflicts well

**Consequences:**
- User reports missing content
- Duplicate blocks appearing after sync
- File corruption requiring restoration from backup
- Lost work for users

**How to avoid:**
1. Implement file locking using `.lock` files or similar mechanism
2. Use last-write-wins with timestamp comparison as fallback
3. Never modify blocks created by user manually (mark SAW blocks with special property)
4. Create conflict backup files before overwriting (`file.conflict.md`)
5. Detect concurrent modification by comparing modification timestamps

```python
import os
import time

def safe_write_file(path, content, timeout=30):
    lock_path = path + '.lock'
    
    # Try to acquire lock
    start = time.time()
    while os.path.exists(lock_path):
        if time.time() - start > timeout:
            raise LockTimeout()
        time.sleep(0.1)
    
    try:
        # Create lock
        with open(lock_path, 'w') as f:
            f.write(str(os.getpid()))
        
        # Check for concurrent modification
        if file_modified_since_read(path):
            create_conflict_backup(path)
        
        # Write file
        with open(path, 'w') as f:
            f.write(content)
    finally:
        os.remove(lock_path)
```

**Warning signs:**
- User reports missing content
- Duplicate blocks appearing after sync
- File corruption requiring restoration
- Conflict files accumulating

**Phase to address:** Phase 10-02 (Logseq Integration Core)

---

### Pitfall 36: Slack/Discord Webhook Signature Verification Bypass

**What goes wrong:**
Webhook endpoints accept forged requests because signature verification is missing or implemented incorrectly.

**Why it happens:**
- Developers skip verification in development and forget to enable in production
- Timing attacks in string comparison leak information
- Using `==` instead of constant-time comparison
- Not validating timestamp to prevent replay attacks

**Consequences:**
- Forged webhook requests processed
- Data injection from malicious actors
- Unauthorized actions on behalf of users
- Security breach

**How to avoid:**
1. Always verify HMAC-SHA256 signature using constant-time comparison
2. Use platform SDK's built-in verification (don't roll your own)
3. Reject requests older than 5 minutes (timestamp validation)
4. Log all verification failures for security audit
5. Test signature verification with invalid signatures

```python
import hmac
import hashlib
import time

def verify_slack_signature(body: bytes, timestamp: str, signature: str, signing_secret: str) -> bool:
    # Check timestamp to prevent replay attacks
    if abs(time.time() - float(timestamp)) > 300:  # 5 minutes
        return False
    
    # Create signature base
    sig_basestring = f"v0:{timestamp}:{body.decode()}"
    
    # Calculate expected signature
    expected_sig = 'v0=' + hmac.new(
        signing_secret.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Constant-time comparison
    return hmac.compare_digest(expected_sig, signature)
```

**Warning signs:**
- Webhooks processing without `X-Hub-Signature` header
- Requests from unexpected IP addresses
- Duplicate message processing
- Unusual activity in webhook logs

**Phase to address:** Phase 10-03 (IM Integration Core)

---

### Pitfall 37: Slack/Discord Message Format Parsing Fragility

**What goes wrong:**
Integration breaks when message formats change or contain unexpected content types (attachments, threads, blocks).

**Why it happens:**
- Message payloads have many optional fields
- New message types added without warning (e.g., Slack Blocks, Discord Embeds)
- Thread messages have different structure than channel messages
- Bot messages vs user messages have different fields

**Consequences:**
- KeyError/AttributeError on message parsing
- Missing content in stored messages
- Crashes on specific message types
- Incomplete message ingestion

**How to avoid:**
1. Parse only fields you need, ignore unknown fields gracefully
2. Implement message type dispatcher (handle each type separately)
3. Store original JSON alongside extracted content for future re-parsing
4. Write tests for edge cases: empty messages, deleted messages, edited messages
5. Version your message parsing logic

```python
def parse_slack_message(message: dict) -> ParsedMessage:
    # Extract core fields safely
    msg_type = message.get('type', 'unknown')
    text = message.get('text', '')
    user = message.get('user', message.get('bot_id', 'unknown'))
    ts = message.get('ts', '')
    
    # Handle thread messages
    thread_ts = message.get('thread_ts')
    is_thread_reply = thread_ts is not None and thread_ts != ts
    
    # Handle attachments
    attachments = message.get('attachments', [])
    files = message.get('files', [])
    
    # Handle blocks (rich formatting)
    blocks = message.get('blocks', [])
    block_text = extract_text_from_blocks(blocks) if blocks else ''
    
    return ParsedMessage(
        text=text or block_text,
        user=user,
        timestamp=ts,
        is_thread_reply=is_thread_reply,
        attachments=attachments,
        files=files,
        raw=message  # Keep for future re-parsing
    )
```

**Warning signs:**
- KeyError/AttributeError on message parsing
- Missing content in stored messages
- Crashes on specific message types
- Incomplete message history

**Phase to address:** Phase 10-03 (IM Integration Core)

---

### Pitfall 38: Slack/Discord Rate Limit Cascade Failure

**What goes wrong:**
Rate limiting on one API call triggers retry logic that compounds the problem, eventually exhausting all rate limits and blocking the integration.

**Why it happens:**
- Slack has tiered rate limits (Tier 1-4) with different limits per method
- Discord uses bucket-based rate limiting with per-route limits
- Retrying without backoff consumes remaining quota
- Different rate limit headers for different API versions

**Consequences:**
- 429 errors increasing in frequency
- Integration falling behind real-time messages
- Rate limit exhaustion blocking all operations
- Complete integration shutdown

**How to avoid:**
1. Implement per-route rate limit tracking
2. Use exponential backoff with jitter (start at 1s, max 60s)
3. Parse `Retry-After` header for precise wait times
4. Maintain rate limit budget: track usage, pause before hitting limits
5. Prioritize critical operations when rate limited

```python
import time
import random
from collections import defaultdict

class RateLimitManager:
    def __init__(self):
        self.route_buckets = defaultdict(lambda: {'remaining': 100, 'reset': 0})
    
    def wait_if_needed(self, route: str, response_headers: dict):
        bucket = self.route_buckets[route]
        
        # Update bucket info from headers
        bucket['remaining'] = int(response_headers.get('X-RateLimit-Remaining', 1))
        bucket['reset'] = float(response_headers.get('X-RateLimit-Reset', 0))
        
        if bucket['remaining'] <= 1:
            wait_time = max(0, bucket['reset'] - time.time())
            time.sleep(wait_time + random.uniform(0, 0.5))
    
    def handle_rate_limit(self, retry_after: float):
        wait_time = retry_after + random.uniform(0, 1)
        time.sleep(wait_time)
```

**Warning signs:**
- 429 errors increasing in frequency
- Integration falling behind real-time messages
- Rate limit exhaustion blocking all operations
- API latency increasing

**Phase to address:** Phase 10-03 (IM Integration Core)

---

### Pitfall 39: GitHub API Pagination Exhaustion

**What goes wrong:**
Large repositories return incomplete results because pagination stops early or hits rate limits.

**Why it happens:**
- GitHub uses `Link` header for pagination (not cursor-based)
- Different pagination for different endpoints (cursor vs offset vs link)
- Search API has different pagination limits than REST API
- Rate limits reset hourly (5000 requests for authenticated, 60 for unauthenticated)

**Consequences:**
- Missing issues/PRs in search results
- Incomplete repository scans
- Rate limit errors during pagination
- Data inconsistency

**How to avoid:**
1. Parse `Link` header correctly (`rel="next"` pattern)
2. Use conditional requests with `If-None-Match` / ETag for efficiency
3. Implement cursor persistence for long-running operations
4. Prefer GraphQL API for complex queries (single request, precise fields)
5. Track pagination progress for resume capability

```python
import re
import requests

def parse_link_header(link_header: str) -> dict:
    """Parse GitHub Link header for pagination URLs."""
    links = {}
    for part in link_header.split(','):
        match = re.match(r'\s*<([^>]+)>;\s*rel="([^"]+)"', part)
        if match:
            links[match.group(2)] = match.group(1)
    return links

def fetch_all_issues(owner: str, repo: str, token: str):
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    all_issues = []
    while url:
        response = requests.get(url, headers=headers, params={'state': 'all', 'per_page': 100})
        all_issues.extend(response.json())
        
        # Check rate limit
        remaining = int(response.headers.get('X-RateLimit-Remaining', 1))
        if remaining <= 1:
            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
            wait_time = max(0, reset_time - time.time())
            time.sleep(wait_time)
        
        # Get next page from Link header
        link_header = response.headers.get('Link', '')
        links = parse_link_header(link_header)
        url = links.get('next')
    
    return all_issues
```

**Warning signs:**
- Missing issues/PRs in search results
- Incomplete repository scans
- Rate limit errors during pagination
- Fewer results than expected

**Phase to address:** Phase 10-04 (GitHub Integration Core)

---

### Pitfall 40: GitHub Webhook Delivery Failure Handling

**What goes wrong:**
Webhook deliveries fail silently, causing sync to diverge from actual repository state.

**Why it happens:**
- GitHub retries failed webhooks with exponential backoff (up to ~24 hours)
- Delivery failures don't always notify the integration owner
- Network issues can cause partial delivery
- Large payloads may timeout

**Consequences:**
- Missing events in sync log
- Webhook delivery showing "failure" in GitHub settings
- State divergence between SAW and GitHub
- Missing critical updates

**How to avoid:**
1. Implement idempotent webhook handlers (safe to process same event twice)
2. Acknowledge quickly (return 200, process asynchronously)
3. Use webhook secret verification before processing
4. Implement manual sync trigger as fallback (full reconciliation)
5. Track last processed event ID for gap detection

```python
import hmac
import hashlib

def verify_github_webhook(payload: bytes, signature: str, secret: str) -> bool:
    expected_sig = 'sha256=' + hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_sig, signature)

def handle_webhook_event(event_id: str, event_type: str, payload: dict):
    # Check if already processed (idempotency)
    if event_already_processed(event_id):
        return {'status': 'already_processed'}
    
    # Quick ack - process in background
    queue_task(process_webhook_event, event_id, event_type, payload)
    
    return {'status': 'accepted'}

def process_webhook_event(event_id: str, event_type: str, payload: dict):
    try:
        # Process based on event type
        handlers = {
            'issues': handle_issue_event,
            'pull_request': handle_pr_event,
            'push': handle_push_event,
        }
        handler = handlers.get(event_type, handle_generic_event)
        handler(payload)
        
        # Mark as processed
        mark_event_processed(event_id)
    except Exception as e:
        log_webhook_error(event_id, e)
        raise
```

**Warning signs:**
- Missing events in sync log
- Webhook delivery showing "failure" in GitHub settings
- State divergence between SAW and GitHub
- Missing critical updates

**Phase to address:** Phase 10-04 (GitHub Integration Core)

---

### Pitfall 41: OAuth Token Refresh Race Condition

**What goes wrong:**
Multiple concurrent requests using the same OAuth token trigger multiple refresh attempts, causing token revocation or race conditions.

**Why it happens:**
- Token refresh isn't atomic
- Multiple sync operations can start before first refresh completes
- Some APIs revoke old tokens immediately on refresh
- Refresh response race condition with pending requests

**Consequences:**
- "Invalid token" errors after successful refresh
- Multiple refresh requests in logs
- Authentication failures on concurrent operations
- Cascading sync failures

**How to avoid:**
1. Implement token lock/mutex before refresh
2. Use single token manager with refresh coordination
3. Queue requests during active refresh
4. Store refresh token separately from access token
5. Handle "invalid_token" errors by forcing re-authentication

```python
import threading
from datetime import datetime, timedelta

class TokenManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._access_token = None
        self._refresh_token = None
        self._expires_at = None
        self._refreshing = False
    
    def get_valid_token(self) -> str:
        with self._lock:
            # Check if token needs refresh
            if self._needs_refresh():
                self._refresh_token_sync()
            return self._access_token
    
    def _needs_refresh(self) -> bool:
        if not self._access_token or not self._expires_at:
            return True
        # Refresh 5 minutes before expiry
        return datetime.now() >= self._expires_at - timedelta(minutes=5)
    
    def _refresh_token_sync(self):
        # Only one thread should refresh
        if self._refreshing:
            # Wait for refresh to complete
            while self._refreshing:
                time.sleep(0.1)
            return
        
        self._refreshing = True
        try:
            new_tokens = oauth_refresh(self._refresh_token)
            self._access_token = new_tokens['access_token']
            self._refresh_token = new_tokens.get('refresh_token', self._refresh_token)
            self._expires_at = datetime.now() + timedelta(seconds=new_tokens['expires_in'])
        finally:
            self._refreshing = False
```

**Warning signs:**
- "Invalid token" errors after successful refresh
- Multiple refresh requests in logs
- Authentication failures on concurrent operations
- Token appearing invalid after refresh

**Phase to address:** Phase 10-01/10-03/10-04 (All OAuth-based integrations)

---

### Pitfall 42: OAuth Token Storage Security Breach

**What goes wrong:**
OAuth tokens stored in plaintext in config files or databases are exposed in logs, backups, or git repositories.

**Why it happens:**
- Convenience over security during development
- Config files accidentally committed to git
- Tokens appearing in error logs or debug output
- Backup systems capturing plaintext tokens

**Consequences:**
- Unauthorized API access
- Data breach
- Account compromise
- Compliance violations

**How to avoid:**
1. Encrypt tokens at rest using OS keychain or environment-based encryption
2. Never log full tokens (mask after first 8 characters)
3. Use `.gitignore` for token files, use templates for examples
4. Rotate tokens regularly (every 90 days)
5. Use short-lived tokens when possible (refresh token pattern)

```python
import os
import json
from cryptography.fernet import Fernet

class SecureTokenStorage:
    def __init__(self, key: bytes = None):
        if key is None:
            # Get or generate key from OS keychain
            key = self._get_or_create_key()
        self._fernet = Fernet(key)
    
    def _get_or_create_key(self) -> bytes:
        """Get key from OS keychain or generate new one."""
        import keyring
        key = keyring.get_password('saw', 'token_key')
        if key is None:
            key = Fernet.generate_key()
            keyring.set_password('saw', 'token_key', key.decode())
        else:
            key = key.encode()
        return key
    
    def store_token(self, service: str, token: str):
        encrypted = self._fernet.encrypt(token.encode())
        # Store in secure location (not in git)
        token_file = self._get_token_path(service)
        with open(token_file, 'wb') as f:
            f.write(encrypted)
    
    def get_token(self, service: str) -> str:
        token_file = self._get_token_path(service)
        with open(token_file, 'rb') as f:
            encrypted = f.read()
        return self._fernet.decrypt(encrypted).decode()
```

**Warning signs:**
- Tokens visible in git history
- Tokens in log files
- Unauthorized API access detected
- Tokens in backup archives

**Phase to address:** Phase 10-01 (Shared Auth Infrastructure)

---

### Pitfall 43: Sync Loop (Infinite Update Cycle)

**What goes wrong:**
Integration enters infinite loop: SAW updates Notion -> Notion webhook triggers SAW -> SAW updates Notion again -> ...

**Why it happens:**
- Webhook triggers on all changes, including changes made by integration
- No origin tracking for "who made this change"
- Timestamp precision insufficient to distinguish cause vs effect
- Conflict resolution triggers update that triggers webhook again

**Consequences:**
- Same record updated hundreds of times
- API quota exhaustion
- User confusion about "who changed this"
- Performance degradation

**How to avoid:**
1. Add `source: "saw"` metadata to all outbound updates
2. Ignore webhooks from own integration (check `bot_id` or `author`)
3. Use idempotency keys for updates
4. Implement circuit breaker: stop after N updates to same record in M minutes
5. Track update origin in metadata

```python
import time
from collections import defaultdict

class SyncLoopDetector:
    def __init__(self, max_updates_per_record=3, window_minutes=5):
        self.max_updates = max_updates_per_record
        self.window = window_minutes * 60
        self.update_history = defaultdict(list)
    
    def should_skip_update(self, record_id: str, source: str) -> bool:
        if source == 'saw':
            return False  # Never skip our own updates
        
        now = time.time()
        history = self.update_history[record_id]
        
        # Remove old entries
        history[:] = [t for t in history if now - t < self.window]
        
        # Check threshold
        if len(history) >= self.max_updates:
            return True  # Skip to prevent loop
        
        history.append(now)
        return False

def apply_update(record_id: str, changes: dict, source: str = 'unknown'):
    if sync_detector.should_skip_update(record_id, source):
        logger.warning(f"Skipping update to {record_id} - possible sync loop")
        return
    
    # Apply update with source metadata
    changes['_source'] = source
    changes['_timestamp'] = time.time()
    
    # ... apply changes to platform
```

**Warning signs:**
- Same record updated hundreds of times
- API quota exhaustion
- User confusion about "who changed this"
- Webhook logs showing repeated updates

**Phase to address:** Phase 10-05 (Sync Orchestration)

---

### Pitfall 44: Data Loss During Conflict Resolution

**What goes wrong:**
Conflict resolution logic incorrectly chooses wrong version, causing user data loss.

**Why it happens:**
- Timestamp comparison fails when clocks are not synchronized
- "Last write wins" discards important changes
- Merge logic doesn't understand field semantics
- No audit trail of what was discarded

**Consequences:**
- User reports missing data
- One-sided conflict resolution
- Unexplained data inconsistencies
- Loss of user trust

**How to avoid:**
1. Never auto-delete user data without confirmation
2. Implement conflict backup before resolution
3. Use field-level merging (don't replace entire record)
4. Log all conflict resolutions with before/after state
5. Provide UI for user to review conflicts

```python
import json
from datetime import datetime
from typing import Optional

class ConflictResolver:
    def __init__(self, backup_dir: str):
        self.backup_dir = backup_dir
    
    def resolve(self, local: dict, remote: dict, strategy: str = 'merge') -> dict:
        # Create backup of both versions
        self._backup_conflict(local, remote)
        
        if strategy == 'last_write_wins':
            return self._lww_resolve(local, remote)
        elif strategy == 'merge':
            return self._merge_resolve(local, remote)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    def _backup_conflict(self, local: dict, remote: dict):
        timestamp = datetime.now().isoformat()
        record_id = local.get('id', 'unknown')
        
        backup = {
            'timestamp': timestamp,
            'record_id': record_id,
            'local': local,
            'remote': remote
        }
        
        path = f"{self.backup_dir}/{record_id}_{timestamp}.json"
        with open(path, 'w') as f:
            json.dump(backup, f, indent=2)
    
    def _merge_resolve(self, local: dict, remote: dict) -> dict:
        """Field-level merge with conflict tracking."""
        merged = {}
        conflicts = []
        
        all_keys = set(local.keys()) | set(remote.keys())
        
        for key in all_keys:
            local_val = local.get(key)
            remote_val = remote.get(key)
            
            if local_val == remote_val:
                merged[key] = local_val
            elif local_val is None:
                merged[key] = remote_val
            elif remote_val is None:
                merged[key] = local_val
            else:
                # Both have different values - need resolution
                conflicts.append(key)
                # Default to remote (last write wins per field)
                merged[key] = remote_val
        
        if conflicts:
            merged['_conflict_fields'] = conflicts
            merged['_needs_review'] = True
        
        return merged
```

**Warning signs:**
- User reports missing data
- One-sided conflict resolution
- Unexplained data inconsistencies
- No conflict audit trail

**Phase to address:** Phase 10-05 (Sync Orchestration)

---

### Pitfall 45: Feishu/Lark API Token Type Confusion

**What goes wrong:**
Using wrong token type causes "permission denied" errors or access to wrong tenant data.

**Why it happens:**
- Feishu has app_access_token, tenant_access_token, and user_access_token
- Different endpoints require different token types
- Token types have different permissions and expiry
- Multi-tenant apps need to track which tenant each token belongs to

**Consequences:**
- "Permission denied" on valid requests
- Access to wrong tenant's data
- Token expiry causing cascading failures
- Security issues with wrong permissions

**How to avoid:**
1. Clear token type constants and documentation
2. Token manager that returns correct token type per endpoint
3. Validate token type before API call
4. Store tenant_id alongside tenant token
5. Implement token type auto-selection based on endpoint

```python
from enum import Enum
from typing import Optional

class TokenType(Enum):
    APP = 'app_access_token'
    TENANT = 'tenant_access_token'
    USER = 'user_access_token'

class FeishuTokenManager:
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self._tokens = {
            TokenType.APP: None,
            TokenType.TENANT: None,
            TokenType.USER: None,
        }
        self._tenant_id = None
    
    def get_token(self, token_type: TokenType, tenant_id: Optional[str] = None) -> str:
        if token_type == TokenType.USER:
            raise ValueError("User token requires OAuth flow")
        
        cached = self._tokens.get(token_type)
        if cached and not cached.is_expired():
            return cached.value
        
        if token_type == TokenType.APP:
            return self._get_app_token()
        elif token_type == TokenType.TENANT:
            return self._get_tenant_token(tenant_id)
    
    def _get_app_token(self) -> str:
        # API call to get app_access_token
        pass
    
    def _get_tenant_token(self, tenant_id: str) -> str:
        # API call to get tenant_access_token
        self._tenant_id = tenant_id
        pass

# Endpoint token requirements
ENDPOINT_TOKEN_MAP = {
    '/openapi/contact/v3/users': TokenType.TENANT,
    '/openapi/bot/v3/info': TokenType.APP,
    '/openapi/drive/v1/files': TokenType.TENANT,
}

def get_token_for_endpoint(endpoint: str) -> TokenType:
    for path, token_type in ENDPOINT_TOKEN_MAP.items():
        if endpoint.startswith(path):
            return token_type
    return TokenType.TENANT  # Default
```

**Warning signs:**
- "Permission denied" on valid requests
- Access to wrong tenant's data
- Token expiry causing cascading failures
- Token type mismatch errors

**Phase to address:** Phase 10-03 (IM Integration Core)

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Use `detail=full` FTS5 (default) | Supports NEAR and phrase queries out of the box | 3-5x larger index, slower at scale, more segments | Phase 1 MVP only; migrate to `detail=column` before 200 pages |
| Single FTS5 table for all languages | Simpler schema, one search call | CJK content poorly indexed, requires full rebuild to fix | Phase 1-2 English-only; never if Chinese content is expected early |
| Store entity resolution in Claims DB only | No separate entity registry needed | Entity deduplication requires full DB scan, O(n^2) at scale | Phase 1 <50 pages; never for production |
| Skip outbox per-sink tracking | Simpler Write Queue implementation | Cannot detect or recover partial writes | Never -- this is the core value proposition of the Write Queue |
| Use `allowed_fails=0` LiteLLM default | Fast failure detection | Single transient error blocks deployment for 60s | Only for non-critical Opus/Scholar tasks; never for Haiku/Librarian |
| Guardian rules without TTL | Simpler rule management | Rule accumulation blocks legitimate operations | Phase 2 initial rules only; never for auto-generated rules |
| Skip PDF quality metrics | Faster ingestion pipeline | Silent content loss feeds bad claims into knowledge base | Never -- even minimal metrics (word count check) are essential |
| Use MiniLM for all content types | One model, simple config | Technical/code content poorly represented | Phase 1 offline mode only; add domain-specific models in Phase 3 |
| Direct FTS5 writes (no batching) | Simpler code, immediate indexing | Segment proliferation, slow queries at scale | Phase 1 <100 documents only |
| Hard-code confidence thresholds | No configuration complexity | Cannot tune for different domains or user preferences | Phase 2 initial implementation; make configurable by Phase 3 |
| Skip pagination, use default limit | Faster initial development | Missing data on large datasets | Never acceptable |
| Store OAuth tokens in plaintext | Simpler config management | Security breach risk | Never acceptable |
| Skip webhook verification | Faster local testing | Security vulnerability in production | Only in isolated dev environment |
| Assume property types stable | Less validation code | Crashes on user schema changes | Never acceptable |
| Last-write-wins without backup | Simpler conflict handling | Silent data loss | Never acceptable |
| Hard-code API rate limits | Avoids config complexity | Breaks when limits change | Acceptable for MVP with TODO |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| FastMCP + LiteLLM | Blocking LLM calls inside MCP tool handlers freeze the server | Use `async` LiteLLM calls with timeouts; return "processing" status for long-running operations |
| SQLite WAL mode + FTS5 | Assuming WAL mode makes FTS5 writes atomic across tables | WAL mode helps within one table; cross-table consistency still requires explicit transactions wrapping both content and FTS5 writes |
| LiteLLM + multiple providers | Using the same API key for Haiku, Sonnet, and Opus deployments | Use separate API keys per model tier to isolate rate limits |
| Git + Write Queue | Committing to git before all database sinks complete | Git commit is the LAST sink; if DB writes fail, no git commit is made |
| FastMCP 3.0 RC | Using RC features in production | Pin FastMCP to v2 stable; test v3 RC in development only |
| MinerU + Docling | Assuming MinerU always produces better output than Docling | Run both on a test set and compare; MinerU excels at layout but Docling may be better for specific PDF types |
| Cedar policies + Agent capabilities | Overlapping permit/forbid rules creating ambiguous authorization | Test policy combinations with `saw_lint --rules`; ensure deny rules are explicit and permit rules are scoped |
| FSRS interval repetition + 9-level freshness | Treating FSRS intervals and freshness levels as independent | FSRS determines review schedule; freshness level determines priority. A page at freshness 7 with low FSRS stability should be reviewed before a page at freshness 5 with high stability |
| Notion | Assuming all databases have same schema | Query and cache schema per database |
| Notion | Using title property name directly | Title property can be renamed, use `type: "title"` to find it |
| Logseq | Modifying files without backup | Create `.backup` files before any modification |
| Logseq | Assuming block IDs are unique globally | Block IDs are only unique per page |
| Slack | Processing webhooks synchronously | Return 200 immediately, process in background queue |
| Slack | Using same token for all workspaces | Each workspace needs its own token |
| Discord | Ignoring rate limit buckets | Track per-route rate limits separately |
| GitHub | Using unauthenticated API | Always use authenticated requests (5000 vs 60 req/hour) |
| GitHub | Polling instead of webhooks | Use webhooks for real-time, poll only for reconciliation |
| All OAuth | Storing tokens in config files | Use encrypted storage (OS keychain or environment variables) |
| Feishu | Using app token for tenant endpoints | Use tenant_access_token for most API calls |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| FTS5 segment accumulation | Query latency grows linearly with ingest count | Set `automerge=8`, `crisismerge=4`, batch writes, periodic optimize | >200 documents with frequent small writes |
| Entity resolution O(n^2) | Ingestion time grows quadratically | Canonical entity registry with fuzzy matching index (not full scan) | >500 entities |
| Claims DB without proper indexes | `saw_query` slow for claim lookups | Index on `source_uuid`, `confidence`, `freshness`, `claim_type` from day one | >1000 claims |
| Full graph loading on every query | Memory usage spikes, query latency high | Load only subgraph relevant to query (BFS depth-limited from seed entities) | >200 entities in graph |
| LiteLLM synchronous calls in async context | Event loop blocked, all requests queue up | Always use `litellM.acompletion` in FastAPI/MCP async handlers | Immediately with any concurrent usage |
| Embedding computation during ingestion | Ingestion blocked by embedding model inference | Compute embeddings async in Write Queue, not in the ingestion hot path | >50 documents per ingestion batch |
| All-hot L0 memory index | Boot tokens grow beyond 8K target | Hard cap L0 at 100 lines; auto-condense when exceeded; use L1 for overflow | >500 wiki pages |
| Sequential API calls | Sync taking hours | Batch requests, parallel execution | >100 records |
| No pagination | Incomplete data | Always implement pagination from day one | >100 records |
| In-memory sync state | Memory exhaustion | Persist sync state to database | >10K records |
| Full sync every time | API quota exhaustion | Incremental sync with cursors | >1K records |
| No rate limiting | 429 errors | Request queue with rate limiting | Immediately on bulk operations |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Storing LLM API keys in config files tracked by git | Keys leak to public repos or shared with unintended parties | Store keys in environment variables or `.env` files (gitignored); `saw init` should create `.env.example` not `.env` |
| Agent file path traversal | Malicious or confused agent reads/writes outside wiki directory | Guardian enforces path sandboxing: all operations restricted to wiki root; reject paths containing `..` or absolute paths outside root |
| Ed25519 key stored alongside wiki data | Compromised wiki = compromised audit keys | Store signing keys in OS keychain or separate encrypted file; never in the wiki directory |
| MCP server binding to 0.0.0.0 | Remote code execution via MCP tools from any network | Default to `127.0.0.1` (localhost only); require explicit opt-in for network access |
| Claims DB injection via crafted document names | SQL injection through unsanitized document metadata | Use parameterized queries exclusively; never concatenate user input into SQL |
| Cross-agent context leaking | Agent A sees Agent B's private scratch data | Each agent gets isolated scratch space; shared state goes through Claims DB with proper access control |
| Plaintext token storage | Credential theft, unauthorized access | Encrypt at rest, use OS keychain |
| Missing webhook signature verification | Request forgery, data injection | Always verify HMAC signature |
| Timing attack on signature comparison | Signature bypass | Use constant-time comparison |
| Tokens in logs | Credential exposure | Mask tokens, audit log output |
| No token expiry handling | Expired token causing cascading failures | Track expiry, proactively refresh |
| Missing HTTPS validation | MITM attacks | Always validate SSL certificates |
| Accepting unvalidated redirect URIs | Open redirect, OAuth phishing | Whitelist allowed redirect URIs |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Silent confidence inflation | Users trust high-confidence claims that are actually unvalidated | Show confidence derivation chain: "Layer 3 (Cross-Validated by Claude+Gemini, 2/2 agree)" not just "High Confidence" |
| 5-minute onboarding fails on first PDF parse error | User's first experience is a confusing error about MinerU dependencies | Pre-validate dependencies during `saw init`; if MinerU unavailable, auto-downgrade to Docling with clear message |
| 9-level freshness system overwhelming users | Users see red freshness indicators everywhere and don't know what to do | Show actionable recommendations: "3 pages need review (click to start)" not "Freshness distribution: 5 green, 3 yellow, 8 orange, 12 red" |
| Write Queue failures invisible to users | Users ingest documents but search can't find them | Surface Write Queue status in `saw_status`: "2 messages in processing, 0 in queue, last error: 3 hours ago" |
| Agent role opacity | Users don't know which agent did what | Tag every claim and wiki edit with the agent role that created it: "[Librarian/Haiku] extracted metadata" |
| YAML workflow errors without context | Workflow fails with "gate not satisfied" and user has no idea why | Show gate evaluation details: "Critic rejected: confidence 2 < threshold 3. Reason: ambiguous claim about X. Retrying (2/3)." |
| Graph visualization hairball at scale | Knowledge graph becomes an unreadable mess past 100 nodes | Use adaptive visualization: <50 nodes = full graph, 50-200 = community view, >200 = topic clusters with drill-down |
| Silent sync failures | Data inconsistency, trust loss | Show sync status in UI, notify on failures |
| No conflict visibility | User confused about what changed | Conflict review UI with before/after |
| Missing progress indicator | User thinks sync is stuck | Progress bar with estimated time |
| Auto-delete conflicts | Data loss, user frustration | Move to "conflict" folder, don't delete |
| No undo for sync actions | Mistakes are permanent | Implement sync history with rollback |

## "Looks Done But Isn't" Checklist

- [ ] **FTS5 search**: Often missing segment optimization -- verify query latency stays <100ms after 500 ingests
- [ ] **Confidence scoring**: Often missing validation provenance -- verify each claim records which models validated it and their independence
- [ ] **Write Queue**: Often missing per-sink completion tracking -- verify crash recovery correctly resumes partial writes
- [ ] **PDF parsing**: Often missing quality metrics -- verify extracted text word count is within 80% of expected for test documents
- [ ] **Entity resolution**: Often missing canonical registry -- verify entity count grows sub-linearly with document count
- [ ] **Multi-LLM extraction**: Often missing context isolation -- verify parallel extraction runs have zero shared state
- [ ] **MCP tools**: Often missing schema versioning -- verify tool schema changes don't break existing agent clients
- [ ] **Guardian rules**: Often missing TTL and cap -- verify auto-generated rules expire after 30 days
- [ ] **Graceful degradation**: Often missing actual testing -- verify Level 2 and Level 3 modes work with real workloads, not just unit tests
- [ ] **FSRS freshness review**: Often missing integration with contradiction detection -- verify freshness reviews trigger governance checks
- [ ] **Git blame traceability**: Often missing session branch cleanup -- verify old session branches are pruned after merge
- [ ] **Chrome clipper**: Often missing content-type detection -- verify clipped pages are correctly categorized (article vs. video vs. code)
- [ ] **Notion Integration**: Often missing property type validation -- verify schema check on every sync
- [ ] **Notion Integration**: Often missing pagination handling -- verify all paginated endpoints
- [ ] **Logseq Integration**: Often missing concurrent edit protection -- verify file locking
- [ ] **Slack Integration**: Often missing thread message handling -- verify thread parsing
- [ ] **Discord Integration**: Often missing embed formatting -- verify all message types
- [ ] **GitHub Integration**: Often missing Link header pagination -- verify pagination implementation
- [ ] **All Integrations**: Often missing rate limit handling -- verify exponential backoff
- [ ] **All OAuth**: Often missing token refresh -- verify refresh before expiry
- [ ] **All Webhooks**: Often missing signature verification -- verify production has verification enabled

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| FTS5 index inconsistency | LOW | `INSERT INTO fts_index(fts_index) VALUES('rebuild')` -- rebuilds from content table, seconds to minutes |
| FTS5 segment b-tree bloat | LOW | `INSERT INTO fts_index(fts_index) VALUES('optimize')` -- merges all segments, fast |
| FTS5 tokenizer migration (unicode61 to trigram) | MEDIUM | Create new FTS5 table with correct tokenizer, copy data, drop old table, rename. Requires downtime. |
| LiteLLM deployment cooldown cascade | LOW | Wait for cooldown to expire (configurable), or restart with `allowed_fails` increased |
| Confidence inflation | HIGH | Re-run all cross-validations with strict independence checks; downgrade affected claims to Layer 1; requires re-ingestion or manual review |
| Entity resolution explosion | HIGH | Full entity deduplication: extract all entities, re-cluster, merge duplicate entities, update all references. O(n^2) on entity count. |
| Write Queue orphan messages | MEDIUM | `saw_lint --queue` to detect orphans; replay failed sinks; verify idempotency prevents duplicates |
| PDF content loss (silent) | HIGH | Re-parse affected PDFs with quality metrics; re-extract claims; update wiki pages. Requires identifying which PDFs were affected. |
| Knowledge graph corruption | HIGH | Rebuild graph from Claims DB (source of truth); re-run entity resolution; re-compute association signals |
| Guardian rule conflicts | MEDIUM | `saw_lint --rules` to detect conflicts; remove conflicting rules; test remaining rules against historical operations |
| Agent deadlock | LOW | Abort stuck workflows; release all file locks; restart agent processes. No data loss if Write Queue is durable. |
| Rate limit exhaustion | LOW | Wait for reset, implement proper rate limiting |
| Token exposure | HIGH | Revoke tokens, rotate all credentials, audit access logs |
| Sync loop | MEDIUM | Identify loop source, add source tracking, manually resolve |
| Data loss from conflict | HIGH | Restore from conflict backup, implement proper backup |
| Incomplete sync | MEDIUM | Trigger full sync, verify pagination cursors |
| Webhook verification bypass | HIGH | Enable verification, audit processed requests for forgery |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| FTS5 external content inconsistency | Phase 1 | Write Queue sink completion tracking + `saw_lint` consistency check |
| FTS5 segment b-tree proliferation | Phase 1 | Automerge/crisismerge config set; segment count monitored; query latency benchmarked at 100/500/1000 docs |
| FTS5 tokenizer choice for CJK | Phase 1 | Schema designed for tokenizer migration; jieba custom tokenizer prototyped |
| Write Queue orphan messages | Phase 1 | Crash recovery test: kill process mid-write, restart, verify all sinks consistent |
| PDF parsing silent failures | Phase 1 | Quality metrics computed for every parsed document; test suite with known difficult PDFs |
| LiteLLM cooldown cascading | Phase 2 | Simulate rate limit exhaustion; verify graceful degradation to backup models |
| Confidence score inflation | Phase 2 | Audit cross-validation independence; verify no shared context between validating LLMs |
| Guardian rules complexity spiral | Phase 2 | Rule cap enforced; TTL on auto-generated rules; `saw_lint --rules` passes |
| Embedding model domain mismatch | Phase 2 | Hybrid search benchmarks: BM25 vs. vector vs. hybrid on technical content test set |
| Entity resolution explosion | Phase 1 (registry) + Phase 3 (resolution) | Entity count grows sub-linearly; no duplicate entities for known test set |
| MCP tool schema drift | Phase 2 | Schema version field in tool descriptions; test with 2+ MCP clients after schema changes |
| Multi-agent deadlock | Phase 3 | Workflow timeout enforced; deadlock detection active; YAML gates have fallback actions |
| Cedar policy binding immaturity | Phase 3 | PolicyEngine protocol with CLI fallback; feature detection at startup |
| Cytoscape.js performance at scale | Phase 3 | Performance optimizations enabled; lazy loading tested at 500+ nodes |
| A2A protocol version drift | Phase 3 | Version negotiation; pluggable adapter architecture |
| React state desync with WebSocket | Phase 3 | REST sync on connect; message sequence tracking; connection status indicator |
| YAML workflow gate loop | Phase 3 | Max retries enforced; fallback actions defined; workflow timeout active |
| Obsidian file race condition | Phase 07 | Use Vault.process() exclusively |
| Obsidian event listener leaks | Phase 07 | Use registerEvent() pattern |
| Obsidian type checking | Phase 07 | instanceof checks before operations |
| Chrome MV3 remote code | Phase 08 | Bundle all dependencies |
| Chrome service worker state | Phase 08 | Persist to storage APIs |
| Chrome content script isolation | Phase 08 | window.postMessage pattern |
| Chrome storage quota | Phase 08 | Use storage.local for large data |
| RSS GUID changes | Phase 09 | Multi-key deduplication |
| RSS encoding issues | Phase 09 | Use feedparser, normalize UTF-8 |
| RSS polling blocks | Phase 09 | Adaptive polling intervals |
| Bidirectional sync corruption | Phase 07 | Define clear authority model |
| Chrome CORS blocking | Phase 08 | Configure server CORS headers |
| Schema mismatch between sources | Phase 07 | Unified source-agnostic schema |
| Notion Rate Limits | Phase 10-01 | Test with 1000+ record database |
| Notion Property Types | Phase 10-01 | Test schema change during sync |
| Notion Pagination | Phase 10-01 | Test with database > 1000 pages |
| Logseq Format Changes | Phase 10-02 | Test with different Logseq versions |
| Logseq Concurrent Edits | Phase 10-02 | Test simultaneous edits |
| Webhook Signature Verification | Phase 10-03 | Security audit of webhook endpoints |
| Message Format Parsing | Phase 10-03 | Test with all message types |
| IM Rate Limits | Phase 10-03 | Load test with high message volume |
| GitHub Pagination | Phase 10-04 | Test with repository > 1000 issues |
| GitHub Webhook Failures | Phase 10-04 | Test webhook delivery failure |
| OAuth Token Race | Phase 10-01 (Shared) | Test concurrent token refresh |
| OAuth Token Security | Phase 10-01 (Shared) | Security audit of token storage |
| Sync Loop | Phase 10-05 | Test bidirectional sync |
| Data Loss from Conflict | Phase 10-05 | Test conflict resolution with audit |
| Feishu Token Types | Phase 10-03 | Test multi-tenant scenarios |

## Sources

- SQLite FTS5 Official Documentation (sqlite.org/fts5.html) -- external content tables, segment b-trees, automerge/crisismerge, detail option, tokenizer options
- LiteLLM Router Documentation (docs.litellm.ai/docs/routing) -- cooldowns, allowed_fails, routing strategies, context window checks
- LiteLLM Exception Mapping (docs.litellm.ai/docs/exception_mapping) -- exception types, retry policies, provider-specific errors
- FastMCP GitHub README (github.com/jlowin/fastmcp) -- v2/v3 status, schema auto-generation, three pillars architecture
- Smart Agent Wiki Design Document (docs/smart_agent_wiki_design.md) -- architecture, 5 engines, 4-layer storage, agent roles
- LLM Wiki Ecosystem Analysis (docs/llm_wiki_ecosystem_analysis.md) -- 181-project audit, user pain points, design patterns
- Remote Project Audit Findings (docs/remote_project_audit_findings.md) -- 27 Tier 1 project unique features, innovation patterns
- TreeSearch project audit -- structure-aware FTS5, zero-vector search proof of concept
- Knowledge Pipeline project audit -- claims database, contradiction detection patterns
- ContextLattice project audit -- multi-sink fanout, outbox durability patterns
- scopeblind-gateway project audit -- Ed25519 signed receipts, Cedar policy engine
- unified-memory-ai-agents project audit -- L0/L1/L2 progressive depth, WIP momentum, knowledge expiry
- MindOS project audit -- Echo cognitive distillation, A2A protocol, YAML workflows
- codesight project audit -- AST zero-LLM extraction, blast radius analysis

### Ecosystem Integration Sources

- Obsidian Developer Documentation (Context7) -- HIGH confidence
  - [Vault.read()](https://github.com/obsidianmd/obsidian-developer-docs/blob/main/en/Reference/TypeScript%20API/Vault/read.md) -- use read() before modify
  - [Vault.process()](https://github.com/obsidianmd/obsidian-developer-docs/blob/main/en/Reference/TypeScript%20API/Vault/process.md) -- atomic read-modify-write
  - [registerEvent()](https://github.com/obsidianmd/obsidian-developer-docs/blob/main/en/Plugins/Events.md) -- auto-cleanup on unload
  - [TFile/TFolder](https://github.com/obsidianmd/obsidian-developer-docs/blob/main/en/Plugins/Vault.md) -- instanceof type checking
- Obsidian Help Documentation (Context7) -- HIGH confidence
  - [Sync conflict resolution](https://github.com/obsidianmd/obsidian-help/blob/master/en/Obsidian%20Sync/Troubleshoot%20Obsidian%20Sync.md) -- conflict handling behavior
- Chrome Extensions Documentation (Context7) -- HIGH confidence
  - [Storage API](https://developer.chrome.com/docs/extensions/reference/api/storage) -- sync vs local limits
  - [Service worker lifecycle](https://developer.chrome.com/docs/extensions/develop/migrate/to-service-workers) -- state persistence
  - [Content script isolation](https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts) -- message passing patterns
  - [Remote code prohibition](https://developer.chrome.com/docs/extensions/develop/migrate/improve-security) -- bundled code only
  - [Offscreen documents](https://developer.chrome.com/docs/extensions/how-to/web-platform/geolocation) -- DOM access workaround
- RSS Parsing (MEDIUM confidence -- general Python patterns)
  - feedparser library documentation -- encoding detection, bozo bit
  - Conditional GET patterns -- If-Modified-Since, ETag

### Third-Party Integration Sources

- GitHub API rate limit endpoint direct query (60 req/hour unauthenticated, 5000 req/hour authenticated)
- Notion OpenAPI specification (page_size default 100, max 100)
- Slack webhook verification documentation (HMAC-SHA256)
- Discord rate limit documentation (bucket-based)
- Logseq file format documentation (EDN + Markdown)
- OAuth 2.0 Security Best Current Practice (RFC draft)
- Community discussions on API integration pitfalls (WebSearch)
- Platform-specific developer forums and Stack Overflow

---

*Pitfalls research for: Smart Agent Wiki (intelligent multi-agent knowledge platform)*
*Researched: 2026-04-26*
*Ecosystem Integration pitfalls added: 2026-04-30*
*Third-Party Integration pitfalls added: 2026-05-01*
