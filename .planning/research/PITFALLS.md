# Pitfalls Research

**Domain:** Intelligent multi-agent knowledge platform (Smart Agent Wiki)
**Researched:** 2026-04-26
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

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Storing LLM API keys in config files tracked by git | Keys leak to public repos or shared with unintended parties | Store keys in environment variables or `.env` files (gitignored); `saw init` should create `.env.example` not `.env` |
| Agent file path traversal | Malicious or confused agent reads/writes outside wiki directory | Guardian enforces path sandboxing: all operations restricted to wiki root; reject paths containing `..` or absolute paths outside root |
| Ed25519 key stored alongside wiki data | Compromised wiki = compromised audit keys | Store signing keys in OS keychain or separate encrypted file; never in the wiki directory |
| MCP server binding to 0.0.0.0 | Remote code execution via MCP tools from any network | Default to `127.0.0.1` (localhost only); require explicit opt-in for network access |
| Claims DB injection via crafted document names | SQL injection through unsanitized document metadata | Use parameterized queries exclusively; never concatenate user input into SQL |
| Cross-agent context leaking | Agent A sees Agent B's private scratch data | Each agent gets isolated scratch space; shared state goes through Claims DB with proper access control |

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

---
*Pitfalls research for: Smart Agent Wiki (intelligent multi-agent knowledge platform)*
*Researched: 2026-04-26*
