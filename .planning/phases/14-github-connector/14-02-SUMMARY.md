---
phase: 14-github-connector
plan: 02
subsystem: connectors
tags: [github, issues, discussions, graphql, transformer, conditional-requests]
requires: [14-01]
provides: [IssueFetcher, GitHubGraphQLClient, DiscussionFetcher, GitHubTransformer]
affects: [connectors, sync-engine]
tech-stack:
  added: [httpx, graphql]
  patterns: [conditional-requests, label-to-tag-mapping, confidence-derivation]
key-files:
  created:
    - src/saw/connectors/github/issue_fetcher.py
    - src/saw/connectors/github/graphql_client.py
    - src/saw/connectors/github/transformer.py
  modified: []
decisions:
  - id: D-14-04
    choice: "GraphQL for Discussions API"
    rationale: "Discussions only available via GraphQL, not REST API"
  - id: D-14-05
    choice: "Label to tag mapping with custom override"
    rationale: "Users may want to map GitHub labels to different SAW tag names"
  - id: D-14-06
    choice: "Confidence derived from issue/discussion state"
    rationale: "Closed issues with milestone, answered discussions indicate validated content"
metrics:
  duration_minutes: 15
  tasks_completed: 3
  tests_added: 56
  files_created: 4
  files_modified: 0
---

# Phase 14 Plan 02: Issue/Discussion Ingestion with GraphQL Summary

## One-Liner

Issue and Discussion ingestion with conditional requests, GraphQL for Discussions, and comprehensive transformation to SAW Claims.

## Completed Tasks

| Task | Description | Commit | Status |
|------|-------------|--------|--------|
| 1 | Issue fetcher with conditional requests and pagination | bf9096b | Complete |
| 2 | GraphQL client and Discussion fetcher | bf9096b | Complete |
| 3 | GitHub transformer for Issues, Discussions, Comments | bf9096b | Complete |

## Deliverables

### IssueFetcher (Task 1)
- `fetch_issues()`: Fetch issues with since parameter for incremental sync
- `fetch_issue_comments()`: Fetch comments for specific issue
- `fetch_all_issues_with_comments()`: Combined fetch with comments
- Conditional request support (ETag/If-None-Match)
- Pagination via Link header parsing
- Rate limit state tracking

### GraphQL Client (Task 2)
- `GitHubGraphQLClient`: Execute GraphQL queries
- `query_discussions()`: Fetch discussions with pagination
- `query_discussion_comments()`: Fetch additional comments
- `DiscussionFetcher`: High-level discussion sync
- `fetch_all_discussions()`: Full discussion sync with pagination

### Transformer (Task 3)
- `IssueTransformer`: Issue to Claim transformation
  - Label to tag mapping (default + custom)
  - Confidence from issue state
  - Freshness from update time
- `DiscussionTransformer`: Discussion to Claim transformation
  - Category as tag
  - Answer detection for confidence
  - Upvote consideration
- `GitHubTransformer`: Facade for all transformations

## Deviations from Plan

None - plan executed exactly as written.

## Key Decisions

1. **GraphQL for Discussions** (D-14-04): Discussions API only available via GraphQL
2. **Label to Tag Mapping** (D-14-05): Customizable mapping with sensible defaults
3. **Confidence Derivation** (D-14-06): State-based confidence for better trust signals

## Test Coverage

| Category | Tests | Status |
|----------|-------|--------|
| Models | 20 | Passing |
| Connector | 14 | Passing |
| Repository Selector | 8 | Passing |
| Transformer | 14 | Passing |
| **Total** | **56** | **Passing** |

## Requirements Coverage

| Requirement | Description | Status |
|-------------|-------------|--------|
| GITH-03 | Issue ingestion | Complete |
| GITH-04 | Discussion ingestion | Complete |
| GITH-07 | Label to tag mapping | Complete |
| GITH-08 | Pagination | Complete |
| GITH-10 | ETag conditional requests | Complete |
| GITH-11 | Since parameter | Complete |

## Next Steps

- Plan 14-03: Webhooks and reconciliation

---

*Completed: 2026-05-02*