# Context: Phase 14 - GitHub Connector

**Phase:** 14
**Goal:** Users can sync GitHub Issues and Discussions as knowledge sources
**Milestone:** v3.1 Third-Party Integrations

---

## Requirements

| ID | Description | Priority |
|----|-------------|----------|
| GITH-01 | User can connect GitHub account via OAuth 2.0 or GitHub App | HIGH |
| GITH-02 | User can select repositories to sync | HIGH |
| GITH-03 | System ingests Issues as Claims with proper field mapping | HIGH |
| GITH-04 | System ingests Discussions as Claims (GraphQL API) | MEDIUM |
| GITH-05 | System receives real-time updates via GitHub webhooks | HIGH |
| GITH-06 | System handles webhook delivery failures with reconciliation | MEDIUM |
| GITH-07 | System maps Issue labels to SAW tags | HIGH |
| GITH-08 | System captures Issue/Discussion comments as related Claims | MEDIUM |
| GITH-09 | System respects GitHub's 5000 req/hr rate limit | HIGH |
| GITH-10 | System uses conditional requests (ETag/Last-Modified) | MEDIUM |
| GITH-11 | System handles pagination via Link header correctly | HIGH |

## Success Criteria

1. User can connect GitHub account or install GitHub App
2. User can select repositories to sync for Issues/Discussions
3. System ingests Issues as Claims with proper field mapping
4. System ingests Discussions via GraphQL API
5. System receives real-time updates via GitHub webhooks
6. System handles webhook delivery failures with reconciliation job
7. Issue labels map to SAW tags correctly
8. Issue/Discussion comments are captured as related Claims
9. System respects GitHub's 5000 req/hr rate limit
10. System uses conditional requests (ETag/Last-Modified) for efficiency
11. System handles pagination via Link header correctly

## Technical Context

### Existing Architecture (Phase 10-13)

- **UnifiedConnectorInterface:** Protocol for all connectors
- **SyncEngine:** Bidirectional sync orchestration
- **ConnectorSink:** Write Queue integration
- **RateLimitManager:** Token bucket rate limiting
- **WebhookVerifier:** HMAC signature verification

### GitHub SDK

From STACK.md v3.1:
- `PyGithub 2.9.1` — Official Python library for GitHub REST API
- `authlib 1.7.0` — OAuth 2.0 and GitHub App authentication
- `PyJWT 2.10.1` — JWT generation for GitHub App auth

### GitHub API Patterns

**REST API (Issues):**
- `GET /repos/{owner}/{repo}/issues` — List issues
- `GET /repos/{owner}/{repo}/issues/{number}` — Get issue
- `GET /repos/{owner}/{repo}/issues/{number}/comments` — List comments

**GraphQL API (Discussions):**
- Discussions only available via GraphQL
- Query: `repository { discussions(first: 100) { nodes { ... } } }`

**Webhooks:**
- `issues` event — Issue opened, edited, closed
- `issue_comment` event — Comment created
- `discussion` event — Discussion created, answered

### Rate Limits

- **REST API:** 5000 requests/hour (authenticated)
- **GraphQL API:** 5000 points/hour (complexity-based)
- Use conditional requests to save quota

## Design Decisions (Auto-Decided)

Based on Phase 10-13 implementation and requirements:

1. **Authentication Mode:** Support both OAuth 2.0 (user) and GitHub App (server-to-server). OAuth for personal use, App for team/organization.

2. **Repository Selection:** Store selected repos in `ConnectorConfig.metadata["repo_ids"]`. Support wildcards like `owner/*`.

3. **Issue to Claim Mapping:**
   - `issue.title` → `claim.title`
   - `issue.body` → `claim.content`
   - `issue.labels` → `claim.tags`
   - `issue.user` → `claim.author`
   - `issue.created_at` → `claim.timestamp`
   - `issue.number` → `claim.metadata["github_issue_number"]`

4. **Comments as Sub-Claims:** Each comment becomes a Claim with `parent_claim_id` linking to the Issue Claim.

5. **GraphQL for Discussions:** Use `gql` library or direct HTTP requests. Discussion structure similar to Issues.

6. **Webhook Signature:** HMAC-SHA256 with `X-Hub-Signature-256` header. Use `HMAC-SHA256=signature` format.

7. **Conditional Requests:** Store `ETag` and `Last-Modified` per repo. Use `If-None-Match` and `If-Modified-Since` headers.

8. **Pagination:** Parse `Link` header for `rel="next"`. Follow until no next page.

9. **Rate Limit Handling:** Use `X-RateLimit-Remaining` header. Pause when approaching limit.

10. **Reconciliation:** Daily job to sync missed updates. Store `last_sync_at` per repo.

## Dependencies

- **Phase 10:** Connector framework (Complete)
- **Phase 11:** Sync engine (Complete)
- **PyGithub 2.9.1:** SDK to install

## Out of Scope

- GitHub PR creation (read + webhook only)
- GitHub Actions integration
- GitLab integration (deferred to v3.1+)

---

*Context generated: 2026-05-02*
*Auto-decisions based on user instruction to make reasonable choices*
