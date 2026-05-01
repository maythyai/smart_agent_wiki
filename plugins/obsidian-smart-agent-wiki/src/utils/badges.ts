import { App, TFile } from 'obsidian';
import { parseFrontmatter } from './frontmatter';

// Confidence tier colors (per CONTEXT.md Decision 3)
export const CONFIDENCE_COLORS: Record<number, string> = {
  1: '#808080', // Unverified - Gray
  2: '#CD7F32', // Single Source - Bronze
  3: '#C0C0C0', // Cross-Validated - Silver
  4: '#FFD700', // Human Verified - Gold
};

export const CONFIDENCE_LABELS: Record<number, string> = {
  1: 'Unverified',
  2: 'Single Source',
  3: 'Cross-Validated',
  4: 'Human Verified',
};

/**
 * Render a confidence badge element.
 */
export function renderConfidenceBadge(confidence: number, size: number = 8): HTMLElement {
  const badge = document.createElement('span');
  badge.className = 'saw-confidence-badge';
  badge.style.width = `${size}px`;
  badge.style.height = `${size}px`;
  badge.style.backgroundColor = CONFIDENCE_COLORS[confidence] || CONFIDENCE_COLORS[1];
  badge.style.borderRadius = '50%';
  badge.style.display = 'inline-block';
  badge.style.marginLeft = '4px';
  badge.setAttribute('data-confidence', String(confidence));
  return badge;
}

/**
 * Get confidence from file's frontmatter.
 */
export function getFileConfidence(app: App, file: TFile): number {
  const cache = app.metadataCache.getFileCache(file);
  if (cache?.frontmatter?.confidence) {
    return cache.frontmatter.confidence;
  }

  // Fallback: return default
  return 1;
}

/**
 * Get confidence from file content (async version).
 */
export async function getFileConfidenceAsync(app: App, file: TFile): Promise<number> {
  try {
    const content = await app.vault.read(file);
    const frontmatter = parseFrontmatter(content);
    return frontmatter?.confidence || 1;
  } catch {
    return 1;
  }
}

/**
 * Update file explorer with confidence badges.
 */
export async function updateFileExplorerBadges(app: App): Promise<void> {
  const fileExplorer = app.workspace.getLeavesOfType('file-explorer')[0];
  if (!fileExplorer) return;

  const files = app.vault.getMarkdownFiles();

  for (const file of files) {
    // Skip files in .obsidian directory
    if (file.path.startsWith('.obsidian/')) continue;

    const confidence = await getFileConfidenceAsync(app, file);
    updateFileItemBadge(file.path, confidence);
  }
}

/**
 * Update a single file item in the file explorer.
 */
export function updateFileItemBadge(path: string, confidence: number): void {
  const fileItem = document.querySelector(`.nav-file-title[data-path="${CSS.escape(path)}"]`);
  if (!fileItem) return;

  // Remove existing badge
  const existingBadge = fileItem.querySelector('.saw-confidence-badge');
  if (existingBadge) {
    existingBadge.remove();
  }

  // Add new badge if confidence > 1
  if (confidence > 1) {
    const badge = renderConfidenceBadge(confidence);
    const titleEl = fileItem.querySelector('.nav-file-title-content');
    if (titleEl) {
      titleEl.appendChild(badge);
    }
  }

  // Set data attribute for CSS styling
  fileItem.setAttribute('data-saw-confidence', String(confidence));
}

/**
 * Remove all confidence badges from file explorer.
 */
export function clearFileExplorerBadges(): void {
  document.querySelectorAll('.saw-confidence-badge').forEach((el) => el.remove());
  document.querySelectorAll('[data-saw-confidence]').forEach((el) => {
    el.removeAttribute('data-saw-confidence');
  });
}

/**
 * Create a detailed confidence info tooltip.
 */
export function createConfidenceTooltip(confidence: number, derivation?: string): HTMLElement {
  const container = document.createElement('div');
  container.className = 'saw-confidence-info';

  const label = document.createElement('div');
  label.className = 'saw-confidence-label';
  label.innerHTML = `<strong>${CONFIDENCE_LABELS[confidence]}</strong>`;
  container.appendChild(label);

  const tier = document.createElement('div');
  tier.className = 'saw-confidence-tier';
  tier.style.color = CONFIDENCE_COLORS[confidence];
  tier.textContent = `Tier ${confidence}`;
  container.appendChild(tier);

  if (derivation) {
    const derivationEl = document.createElement('div');
    derivationEl.className = 'saw-confidence-derivation';
    derivationEl.textContent = derivation;
    container.appendChild(derivationEl);
  }

  return container;
}

/**
 * Add confidence badge to active file's title.
 */
export function addBadgeToActiveFile(app: App, confidence: number): void {
  const activeLeaf = app.workspace.activeLeaf;
  if (!activeLeaf) return;

  const viewHeader = activeLeaf.view.containerEl.querySelector('.view-header-title');
  if (!viewHeader) return;

  // Remove existing badge
  const existingBadge = viewHeader.querySelector('.saw-confidence-badge');
  if (existingBadge) {
    existingBadge.remove();
  }

  // Add new badge
  if (confidence > 1) {
    const badge = renderConfidenceBadge(confidence, 10);
    viewHeader.appendChild(badge);
  }
}

/**
 * Confidence badge manager for reactive updates.
 */
export class ConfidenceBadgeManager {
  private app: App;
  private updateInterval: ReturnType<typeof setInterval> | null = null;

  constructor(app: App) {
    this.app = app;
  }

  start(): void {
    // Initial update
    updateFileExplorerBadges(this.app);

    // Periodic updates (every 30 seconds)
    this.updateInterval = setInterval(() => {
      updateFileExplorerBadges(this.app);
    }, 30000);
  }

  stop(): void {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
      this.updateInterval = null;
    }
    clearFileExplorerBadges();
  }

  async refreshFile(path: string): Promise<number> {
    const file = this.app.vault.getAbstractFileByPath(path);
    if (file instanceof TFile) {
      const confidence = await getFileConfidenceAsync(this.app, file);
      updateFileItemBadge(path, confidence);
      return confidence;
    }
    return 1;
  }
}