---
phase: 18-connector-settings
plan: 02
subsystem: frontend
tags: [settings, ui, react, routing, forms]
requires: [CONF-01, CONF-04, CONF-06]
provides: [settings-ui, property-mapping-ui, oauth-reauth-ui]
affects: [integration-dashboard]
tech_stack:
  added: [react-hooks, react-router, tailwind-forms]
  patterns: [controlled-components, local-state-sync, conditional-rendering]
key_files:
  created: [web/src/pages/ConnectorSettings.tsx, web/src/hooks/useConnectorSettings.ts, web/src/components/settings/SyncConfigSection.tsx, web/src/components/settings/PropertyMappingEditor.tsx, web/src/components/settings/OAuthStatusSection.tsx]
  modified: [web/src/routes/router.tsx, web/src/components/integrations/IntegrationActions.tsx]
decisions:
  - D-04: React Router nested route for settings page
  - D-05: Local form state synced with fetched settings
  - D-06: Conditional rendering based on platform type
metrics:
  duration_minutes: 20
  completed_date: "2026-05-03"
  tasks_completed: 5
  files_created: 5
  files_modified: 2
---

# Phase 18 Plan 02: Settings UI Summary

Implemented the Connector Settings UI page with sync configuration, property mapping editor, and OAuth re-authorization controls. Accessible from the Integration Dashboard via the Settings button on each connector card.

## Implementation Details

### useConnectorSettings Hook (Task 1)

Created in `web/src/hooks/useConnectorSettings.ts`:
- `settings`: Current settings state from API
- `loading`, `error`, `saving`, `saved`: Loading and status states
- `updateSettings`: PUT request to update settings
- `reauthorize`: POST request to get OAuth URL and redirect
- `resetToDefaults`: Reset form to default values
- `refresh`: Re-fetch settings from API

### SyncConfigSection Component (Task 2)

Created in `web/src/components/settings/SyncConfigSection.tsx`:
- Sync interval dropdown with options: 5min, 15min, 1hr, 6hr, Manual only
- Sync direction radio group with icons:
  - Bidirectional (two-way sync)
  - Inbound only (import to SAW)
  - Outbound only (export to platform)
- Accessible markup with fieldset/legend
- Disabled state support

### PropertyMappingEditor Component (Task 3)

Created in `web/src/components/settings/PropertyMappingEditor.tsx`:
- SAW standard fields: Title, Content, Confidence, Freshness
- Property dropdowns for each field
- Custom mapping support
- Conditional rendering for Notion/Logseq only
- Logseq default properties list

### OAuthStatusSection Component (Task 4)

Created in `web/src/components/settings/OAuthStatusSection.tsx`:
- Status badge with color coding:
  - Connected (Green-500)
  - Expiring Soon (Yellow-500)
  - Expired (Red-500)
- Re-authorize button with state-dependent text
- `getOAuthStatus` helper for status determination
- Loading state with spinner

### ConnectorSettings Page (Task 5 - Checkpoint)

Created in `web/src/pages/ConnectorSettings.tsx`:
- Route: `/integrations/:platform/settings`
- Header with back button and platform name
- Loading skeleton
- Error banner with dismiss
- Success indicator on save
- Integrates all settings sections
- Save Changes and Reset to Defaults buttons
- Last updated timestamp

Routing updates in `web/src/routes/router.tsx`:
- Added route for `/integrations/:platform/settings`

IntegrationActions update:
- Changed "Details" button to "Settings" button
- Navigates to settings page

## Auto-Approved Checkpoint

Checkpoint Task 5 (human-verify) was auto-approved in auto mode.

Verification steps:
1. Navigate to Integration Dashboard at http://localhost:5173/integrations
2. Click Settings button on any Notion connector card
3. Settings page loads at /integrations/notion/settings
4. Sync Configuration section shows current values
5. Property Mapping editor shows dropdowns for Notion
6. OAuth Status shows status badge
7. Change sync interval and click Save
8. "Saved!" confirmation appears
9. Settings persist after page refresh
10. Re-authorize button triggers OAuth flow

## Deviations from Plan

None — plan executed exactly as written.

## Commits

| Commit | Message |
|--------|---------|
| beed376 | feat(18-02): create useConnectorSettings hook |
| f2cf40c | feat(18-02): create SyncConfigSection component |
| 9b58e73 | feat(18-02): create PropertyMappingEditor component |
| 6050405 | feat(18-02): create OAuthStatusSection component |
| de5a7f6 | feat(18-02): create ConnectorSettings page with routing |

## Self-Check: PASSED

- [x] `web/src/pages/ConnectorSettings.tsx` exists
- [x] `web/src/hooks/useConnectorSettings.ts` exists
- [x] `web/src/components/settings/SyncConfigSection.tsx` exists
- [x] `web/src/components/settings/PropertyMappingEditor.tsx` exists
- [x] `web/src/components/settings/OAuthStatusSection.tsx` exists
- [x] Frontend build passes
- [x] Commits beed376, f2cf40c, 9b58e73, 6050405, de5a7f6 verified in git log