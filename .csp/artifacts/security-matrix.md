# Security Matrix — T-F-C-1-1 (AC-SEC-1)

> Bare-route detection + permission matrix for the FastAPI web assembly.
> Grounded in `src/saw/auth/permissions.py` (`PermissionService`) and
> `src/saw/drivers/web/app.py` include_router calls.

## AC-SEC-1 verdict

`scripts/security_check.sh` parses the 30 `app.include_router(...)` calls in
`app.py`, classifies each by dependency type + comment + name pattern, and
exits 0 only when there are **0 bare (unprotected, non-public) write routes**.

Last run: **30 routers, 22 protected, 8 legitimate public, 0 bare, PASS (exit 0).**

## Permission matrix (role × capability)

| Role | READ | WRITE | ADMIN |
|------|:----:|:-----:|:-----:|
| viewer  | ✅ | ❌ | ❌ |
| editor  | ✅ | ✅ | ❌ |
| admin   | ✅ | ✅ | ✅ |

Source: `PermissionService` (`src/saw/auth/permissions.py`).

### Vault access rules (`check_vault_access`)

- **Owner** → full access (`reason=owner`)
- **Admin** → full access (`reason=admin_role`)
- **Private vault** → owner only
- **Shared vault** → role-based: viewer=READ, editor=READ+WRITE, admin=ALL

### Feature matrix

| Feature           | viewer | editor         | admin              |
|-------------------|:------:|:--------------:|:------------------:|
| Create vault      | ❌ | ✅ (active) | ✅ |
| Delete vault      | ❌ | ❌ (owner) | ✅ (or owner) |
| Share vault       | ❌ | ❌ (owner) | ✅ (or owner) |
| Invite user       | ❌ | ❌ | ✅ |
| Change user role  | ❌ | ❌ | ✅ (not self) |

## Web route auth wiring

- `auth_dep = [Depends(get_current_user)]` — `app.py:275` — 22 protected routers
- `connector_auth_dep = [Depends(get_current_user), Depends(require_role("admin", "editor"))]` — `app.py:277` — connector_settings_router

### Legitimate public (8, no auth_dep)

health (×2), oauth, webhook_inbound, github_webhook, auth (login/register), websocket (×2).

## CMS line drift

- SPEC/CMS recorded `auth_dep` at `app.py:267`; actual line is `app.py:275` (+8 drift).
- Command name [TBD] → landed as standalone shell script (`bash scripts/security_check.sh`),
  not a `saw security-check routes` CLI subcommand.
