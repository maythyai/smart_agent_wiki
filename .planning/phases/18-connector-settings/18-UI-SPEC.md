---
phase: 18-connector-settings
created: 2026-05-03
design_contract: connector-settings
target_pages:
  - /integrations/:platform/settings
---

# UI Design Contract: Connector Settings

**Scope:** Phase 18 — Connector Settings
**Pages:** Connector Settings Page（每个连接器的配置页面）

## 1. Visual Language

### 1.1 Brand Colors
继承现有 TailwindCSS 配色：
- Primary: Blue-600 (#2563eb)
- Success: Green-500 (#22c55e)
- Warning: Yellow-500 (#eab308)
- Error: Red-500 (#ef4444)
- Neutral: Gray-900/600/400

### 1.2 Typography Scale

| Element | Size | Weight | Use |
|---------|------|--------|-----|
| Page Title | 24px | Bold | Settings page header |
| Section Heading | 18px | Semibold | Config section titles |
| Field Label | 14px | Medium | Form labels |
| Body Text | 14px | Regular | Descriptions |
| Help Text | 12px | Regular | Field hints |

### 1.3 Spacing Scale

| Token | Value | Use |
|-------|-------|-----|
| xs | 4px | Inline gaps |
| sm | 8px | Field internal |
| md | 16px | Section padding |
| lg | 24px | Section gaps |
| xl | 32px | Page margins |

## 2. Layout Architecture

### 2.1 Settings Page Layout

```
┌────────────────────────────────────────────────────────┐
│ ← Back to Integrations    [Platform] Settings          │
├────────────────────────────────────────────────────────┤
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Sync Configuration                               │  │
│  │ ────────────────────────────────────────────────│  │
│  │ Sync Interval:  [ 15 minutes ▼ ]                 │  │
│  │ Sync Direction: (•) Bidirectional               │  │
│  │                 ( ) Inbound only                 │  │
│  │                 ( ) Outbound only                │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Property Mappings                                │  │
│  │ ────────────────────────────────────────────────│  │
│  │ Title:        [ Name ▼ ]                         │  │
│  │ Content:      [ Body ▼ ]                         │  │
│  │ Confidence:   [ Confidence Score ▼ ]             │  │
│  │ Freshness:     [ Last Modified ▼ ]                 │  │
│  │                                                  │  │
│  │ [ + Add Mapping ]                                │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │ OAuth Status                                     │  │
│  │ ────────────────────────────────────────────────│  │
│  │ Status: ● Connected (expires in 30 days)        │  │
│  │ [ Re-authorize ]                                 │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  [ Save Changes ]  [ Reset to Defaults ]              │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### 2.2 Sync Interval Dropdown

Options:
- 5 minutes
- 15 minutes (default)
- 1 hour
- 6 hours
- Manual only

### 2.3 Sync Direction Radio

Visual radio buttons with icons:
- ⟳ Bidirectional (two-way sync)
- ↓ Inbound only (import to SAW)
- ↑ Outbound only (export to platform)

### 2.4 Property Mapping Editor

Dropdown selectors for each SAW field:
- Title → [Notion Property ▼]
- Content → [Notion Property ▼]
- Confidence → [Notion Property ▼]
- Freshness → [Notion Property ▼]

Dropdown shows available properties from connected Notion database.

## 3. Component States

### 3.1 OAuth Status Badge

| Status | Color | Icon | Text |
|--------|-------|------|------|
| Connected | Green-500 | ● | Connected (expires in N days) |
| Expiring Soon | Yellow-500 | ● | Expires in N days |
| Expired | Red-500 | ● | Token expired — re-authorize |

### 3.2 Save Button States

| State | Appearance |
|-------|------------|
| Default | Blue-600, enabled |
| Saving | Blue-600, spinner, "Saving..." |
| Saved | Green-600, "Saved!" (2s) |
| Error | Red-600, "Save failed" |

### 3.3 Re-authorize Button

| Token State | Button Text | Action |
|-------------|-------------|--------|
| Connected | "Refresh Token" | Optional refresh |
| Expiring | "Re-authorize" | OAuth flow |
| Expired | "Re-authorize Now" | Urgent OAuth flow |

## 4. Form Validation

### 4.1 Validation Rules

- Sync Interval: Required, one of preset options
- Sync Direction: Required, one of three values
- Property Mappings: Optional, valid property names

### 4.2 Error Display

Inline error messages below fields:
```
┌─────────────────────────────────────┐
│ Sync Interval: [ Select... ▼ ]     │
│                                     │
│ ⚠ Please select a sync interval     │
└─────────────────────────────────────┘
```

## 5. Accessibility Requirements

### 5.1 WCAG 2.1 Level AA

- [ ] All form fields have visible labels
- [ ] Error messages associated with fields
- [ ] Focus visible on all interactive elements
- [ ] Keyboard navigation through all controls
- [ ] Sufficient color contrast (4.5:1 minimum)

### 5.2 Form Accessibility

- [ ] `<fieldset>` and `<legend>` for grouped radios
- [ ] `aria-describedby` for help text
- [ ] `aria-invalid` for validation errors
- [ ] Focus trap in property mapping modal

## 6. User Flows

### 6.1 Access Settings Flow

```
Integration Dashboard → Click platform card → Click Settings → Settings Page
```

### 6.2 Update Settings Flow

```
Settings Page → Modify fields → Save Changes → Confirmation → Return to Dashboard
```

### 6.3 Re-authorize Flow

```
Settings Page → Click Re-authorize → OAuth redirect → Success → Return to Settings
```

## 7. API Integration

### 7.1 Get Settings

```typescript
const { data } = await api.get(`/connectors/${platform}/settings`);
// Returns: { sync_interval, sync_directions, property_mappings, oauth_status }
```

### 7.2 Update Settings

```typescript
await api.put(`/connectors/${platform}/settings`, {
  sync_interval: "15min",
  sync_directions: "bidirectional",
  property_mappings: { title: "Name", content: "Body" }
});
```

### 7.3 Re-authorize

```typescript
window.location.href = `/connectors/${platform}/reauth`;
```

---

*UI Design Contract for Phase 18*
*Created: 2026-05-03*
*Designer: Claude (autonomous mode)*