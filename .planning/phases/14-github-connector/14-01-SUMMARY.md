---
phase: 14-github-connector
plan: 01
subsystem: connectors
tags: [github, oauth, app-installation, repository-selection, rate-limiting]
requires: [10-connector-framework, 11-sync-engine]
provides: [GitHubConnector, GitHubOAuthHandler, GitHubAppInstallationHandler, RepositorySelector]
affects: [connectors, sync-engine]
tech-stack:
  added: [PyGithub 2.9.1, PyJWT]
  patterns: [dual-auth, rate-limiting, cursor-persistence]
key-files:
  created:
    - src/saw/connectors/github/__init__.py
    - src/saw/connectors/github/models.py
    - src/saw/connectors/github/oauth.py
    - src/saw/connectors/github/app_installation.py
    - src/saw/connectors/github/connector.py
    - src/saw/connectors/github/repository_selector.py
    - src/saw/db/github_models.py
    - src/saw/api/github.py
  modified:
    - src/saw/db/__init__.py
decisions:
  - id: D-14-01
    choice: "Dual authentication support (OAuth + GitHub App)"
    rationale: "GitHub Apps provide higher rate limits (15000/hr) and fine-grained permissions for organizations"
  - id: D-14-02
    choice: "PyGithub SDK for API interactions"
    rationale: "Official Python SDK handles pagination, rate limiting, and conditional requests internally"
  - id: D-14-03
    choice: "Sync cursor with ETag for conditional requests"
    rationale: "ETag-based conditional requests reduce API calls when no changes detected (304 response)"
metrics:
  duration_minutes: 25
  tasks_completed: 3
  tests_added: 42
  files_created: 8
  files_modified: 1
---

# Phase 14 Plan 01: GitHub Connector Core and OAuth Summary

## One-Liner

GitHub connector with dual authentication (OAuth/App), repository selection, and rate limiting infrastructure implementing UnifiedConnectorInterface.

## Completed Tasks

| Task | Description | Commit | Status |
|------|-------------|--------|--------|
| 1 | Create GitHub models and database schema | 366b88e | Complete |
| 2 | Implement GitHubConnector core with dual auth | 7a44703 | Complete |
| 3 | Repository selection and API endpoints | 4d4fe99 | Complete |

## Deliverables

### Models (Task 1)
- `GitHubUser`, `GitHubLabel`, `GitHubMilestone`, `GitHubIssue`
- `GitHubComment`, `GitHubDiscussion`, `GitHubDiscussionCategory`
- `GitHubRepository`, `GitHubRateLimit`, `GitHubWebhookEvent`
- `GitHubAuthType`, `GitHubAppInstallation`

### Database Schema (Task 1)
- `GitHubSyncCursorModel`: Sync position with ETag, issue/discussion numbers
- `GitHubRepositoryConfigModel`: Repository selection with sync preferences
- `GitHubRateLimitStateModel`: Rate limit tracking for conditional requests
- `GitHubWebhookDeliveryModel`: Deduplication log (24-hour TTL)

### Connector Implementation (Task 2)
- `GitHubOAuthHandler`: OAuth 2.0 flow with repo, read:org, read:user scopes
- `GitHubAppInstallationHandler`: JWT-based App auth, installation token refresh
- `GitHubConnector`: UnifiedConnectorInterface implementation
  - `authenticate()`: Dual auth (OAuth code or installation ID)
  - `get_items()`: Issues from selected repositories
  - `put_item()`: Comment posting
  - `list_repositories()`: Repository discovery
  - `check_rate_limit()`: Rate limit status

### Repository Selection (Task 3)
- `RepositorySelector`: Repository management
- FastAPI endpoints: `/connectors/github/repositories`, `/select`, `/selected`, `/rate-limit`

## Deviations from Plan

None - plan executed exactly as written.

## Key Decisions

1. **Dual Authentication** (D-14-01): Support both OAuth (for individual users) and GitHub App (for organizations with higher rate limits)
2. **PyGithub SDK** (D-14-02): Leverage PyGithub for automatic pagination and rate limit handling
3. **ETag Conditional Requests** (D-14-03): Store ETag in sync cursor for 304 responses when unchanged

## Test Coverage

| Category | Tests | Status |
|----------|-------|--------|
| Models | 20 | Passing |
| Connector | 14 | Passing |
| Repository Selector | 8 | Passing |
| **Total** | **42** | **Passing** |

## Threat Model Compliance

| Threat ID | Mitigation | Status |
|-----------|------------|--------|
| T-14-01 | OAuth state validation (15-min TTL) | Implemented via GitHubOAuthHandler |
| T-14-02 | Sync cursor stored server-side | Implemented via GitHubSyncCursorModel |
| T-14-03 | Tokens encrypted via Fernet | Uses existing TokenEncryption |
| T-14-04 | Tokens masked in logs | Uses existing TokenMasker |
| T-14-06 | Minimal scopes (repo, read:org) | Scopes configured in OAuth handler |
| T-14-07 | App installation verification | JWT-based validation in app_installation.py |

## Requirements Coverage

| Requirement | Description | Status |
|-------------|-------------|--------|
| GITH-01 | OAuth/App auth | Complete |
| GITH-02 | Repository selection | Complete |
| GITH-09 | Rate limiting (5000 req/hr) | Complete |
| GITH-10 | Sync cursor persistence | Complete |

## Next Steps

- Plan 14-02: Issue/Discussion ingestion with GraphQL
- Plan 14-03: Webhooks and reconciliation

---

*Completed: 2026-05-02*