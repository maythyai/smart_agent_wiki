import { App, TFile, MarkdownView } from 'obsidian';
import { parseFrontmatter } from './frontmatter';

export interface ConflictMarker {
  line: number;
  start: number;
  end: number;
  claimId: string;
  reason: string;
}

/**
 * Check if a file has conflicting claims.
 * Reads frontmatter for conflict_status field.
 */
export function hasConflicts(content: string): boolean {
  const frontmatter = parseFrontmatter(content);
  return frontmatter?.conflict_status === 'disputed' ||
         (Array.isArray(frontmatter?.conflicting_claims) && (frontmatter?.conflicting_claims as unknown[]).length > 0);
}

/**
 * Extract conflict markers from content.
 * Looks for <!-- SAW_CONFLICT: claim_id: reason --> comments.
 */
export function extractConflictMarkers(content: string): ConflictMarker[] {
  const markers: ConflictMarker[] = [];
  const lines = content.split('\n');

  const conflictRegex = /<!--\s*SAW_CONFLICT:\s*([^:]+):\s*([^>]+)\s*-->/;

  for (let i = 0; i < lines.length; i++) {
    const match = lines[i].match(conflictRegex);
    if (match) {
      markers.push({
        line: i,
        start: match.index!,
        end: match.index! + match[0].length,
        claimId: match[1].trim(),
        reason: match[2].trim(),
      });
    }
  }

  return markers;
}

/**
 * Create conflict resolution UI panel.
 */
export function createConflictPanel(conflicts: ConflictMarker[]): HTMLElement {
  const panel = document.createElement('div');
  panel.className = 'saw-conflict-panel';

  const header = panel.createEl('h4', { text: 'Claim Conflicts Detected' });
  header.style.marginBottom = '8px';

  const list = panel.createEl('ul');
  list.style.listStyle = 'none';
  list.style.padding = '0';

  for (const conflict of conflicts) {
    const item = list.createEl('li');
    item.style.marginBottom = '8px';
    item.style.padding = '8px';
    item.style.background = 'var(--background-modifier-error)';
    item.style.borderRadius = '4px';

    const claimId = item.createEl('strong', { text: conflict.claimId });
    claimId.style.color = '#F44336';

    const reason = item.createEl('div', { text: conflict.reason });
    reason.style.fontSize = '12px';
    reason.style.color = 'var(--text-muted)';

    const actions = item.createEl('div');
    actions.style.marginTop = '4px';

    const viewBtn = actions.createEl('button', { text: 'View' });
    viewBtn.style.marginRight = '4px';
    viewBtn.onclick = () => {
      // Navigate to claim
      console.log('Navigate to claim:', conflict.claimId);
    };

    const resolveBtn = actions.createEl('button', { text: 'Resolve' });
    resolveBtn.onclick = () => {
      // Open resolution dialog
      console.log('Resolve conflict:', conflict.claimId);
    };
  }

  return panel;
}

/**
 * Manager for conflict detection and highlighting.
 */
export class ConflictDetectionManager {
  private app: App;
  private activeConflicts: Map<string, ConflictMarker[]> = new Map();

  constructor(app: App) {
    this.app = app;
  }

  async checkFile(file: TFile): Promise<ConflictMarker[]> {
    const content = await this.app.vault.read(file);

    if (!hasConflicts(content)) {
      this.activeConflicts.delete(file.path);
      return [];
    }

    const markers = extractConflictMarkers(content);
    this.activeConflicts.set(file.path, markers);

    return markers;
  }

  applyToActiveView(): void {
    const view = this.app.workspace.getActiveViewOfType(MarkdownView);
    if (!view) return;

    const file = view.file;
    if (!file) return;

    const conflicts = this.activeConflicts.get(file.path);
    if (!conflicts || conflicts.length === 0) return;

    // Note: Editor.markText and getAllMarks are not available in Obsidian's Editor API
    // Conflict highlighting would need to be implemented via a different mechanism
    console.log('Conflicts detected:', conflicts);
  }

  getConflictsForFile(path: string): ConflictMarker[] | undefined {
    return this.activeConflicts.get(path);
  }

  hasAnyConflicts(): boolean {
    return this.activeConflicts.size > 0;
  }
}