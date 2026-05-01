# Smart Agent Wiki Obsidian Plugin

Bidirectional sync and knowledge graph visualization for Smart Agent Wiki.

## Features

- **Bidirectional Sync**: Sync notes between Obsidian and SAW
- **Knowledge Graph**: Visualize knowledge with Cytoscape.js
- **Confidence Badges**: See trust levels at a glance
- **Conflict Detection**: Highlight disputed claims
- **Quick Search**: Search SAW from command palette

## Installation

### Manual Installation

1. Download `main.js`, `manifest.json`, and `styles.css` from releases
2. Create folder `.obsidian/plugins/smart-agent-wiki/`
3. Copy files to that folder
4. Enable plugin in Obsidian settings

### Development Build

```bash
cd plugins/obsidian-smart-agent-wiki
npm install
npm run build
```

## Configuration

1. Open Obsidian Settings
2. Go to "Smart Agent Wiki" under Community Plugins
3. Configure:
   - **API URL**: Your SAW server URL (default: `http://localhost:8000`)
   - **API Token**: JWT token from SAW
   - **Sync Interval**: Auto-sync interval in minutes
   - **Conflict Strategy**: How to handle sync conflicts

## Commands

| Command | Description | Default Key |
|---------|-------------|-------------|
| `Sync all files` | Sync entire vault with SAW | - |
| `Sync current file` | Sync active file only | - |
| `Show sync status` | Display sync statistics | - |
| `Ingest current file` | Push file to SAW Vault | - |
| `Ingest with options...` | Ingest with tags/type | - |
| `Search SAW` | Open search modal | - |
| `Quick search SAW` | Repeat last search | - |
| `Show Knowledge Graph` | Open graph view | - |
| `Refresh badges` | Update confidence badges | - |

## Keyboard Shortcuts

Set custom shortcuts in Obsidian Settings > Hotkeys.

Recommended shortcuts:
- `Cmd/Ctrl + Shift + S`: Sync current file
- `Cmd/Ctrl + Shift + G`: Show graph
- `Cmd/Ctrl + Shift + F`: Search SAW

## Conflict Resolution

When both local and remote files changed:

1. **Create Conflict File** (default): Creates `filename.md.conflict` with remote content
2. **Prefer Local**: Keeps local changes
3. **Prefer Remote**: Uses remote changes

## Wikilink Conversion

| SAW Format | Obsidian Format |
|------------|-----------------|
| `[[entity:Name]]` | `[[Name]]` |
| `[[claim:ID]]` | `[[Claim ID]]` |
| `[[wiki:Page-Title]]` | `[[Page Title]]` |

## Confidence Badges

Colors indicate trust level:

- Gray: Unverified
- Bronze: Single Source
- Silver: Cross-Validated
- Gold: Human Verified

## License

MIT