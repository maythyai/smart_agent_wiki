import { FuzzySuggestModal, FuzzyMatch, Notice, TFile } from 'obsidian';
import SmartAgentWikiPlugin from '../../main';
import { performSearch } from '../commands/query-command';
import { renderConfidenceBadge } from '../utils/badges';

interface SearchResult {
  slug: string;
  title: string;
  snippet: string;
  confidence: number;
  score: number;
}

/**
 * Search modal with confidence badges.
 */
export class SAWSearchModal extends FuzzySuggestModal<SearchResult> {
  private plugin: SmartAgentWikiPlugin;
  private results: SearchResult[] = [];
  private query: string = '';
  private isLoading: boolean = false;
  private debounceTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(plugin: SmartAgentWikiPlugin) {
    super(plugin.app);
    this.plugin = plugin;

    // Customize placeholder
    this.setPlaceholder('Search Smart Agent Wiki...');

    // Add instructions
    this.setInstructions([
      { command: 'Arrow keys', purpose: 'navigate' },
      { command: 'Enter', purpose: 'open' },
      { command: 'Shift + Enter', purpose: 'open in new pane' },
      { command: 'Esc', purpose: 'close' },
    ]);

    // Listen for input changes
    this.inputEl.addEventListener('input', this.onInputChanged.bind(this));
  }

  private async onInputChanged(event: Event) {
    const input = event.target as HTMLInputElement;
    this.query = input.value.trim();

    if (this.query.length < 2) {
      this.results = [];
      return;
    }

    // Debounce search
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
    }

    this.debounceTimer = setTimeout(async () => {
      await this.performSearch();
    }, 300);
  }

  private async performSearch() {
    if (this.isLoading) return;

    this.isLoading = true;
    this.results = await performSearch(this.plugin, this.query);
    this.isLoading = false;

    // Save last query
    this.plugin.settings.lastQuery = this.query;
    await this.plugin.saveSettings();
  }

  getItems(): SearchResult[] {
    return this.results;
  }

  getItemText(item: SearchResult): string {
    return `${item.title} ${item.snippet}`;
  }

  onChooseItem(item: SearchResult, evt: MouseEvent | KeyboardEvent): void {
    this.openResult(item, evt);
  }

  private openResult(item: SearchResult, evt: MouseEvent | KeyboardEvent) {
    const openInNewPane = evt instanceof KeyboardEvent && evt.shiftKey;

    // Find matching file in vault
    const matchingFile = this.findMatchingFile(item);

    if (matchingFile) {
      this.plugin.app.workspace.openLinkText(
        matchingFile.path,
        '',
        openInNewPane
      );
    } else {
      // File doesn't exist locally - open from API
      this.openFromAPI(item, openInNewPane);
    }
  }

  private findMatchingFile(item: SearchResult): TFile | null {
    const files = this.app.vault.getMarkdownFiles();
    return files.find((f) => {
      const slug = f.basename.toLowerCase().replace(/\s+/g, '-');
      return slug === item.slug || f.basename === item.title;
    }) || null;
  }

  private async openFromAPI(item: SearchResult, newPane: boolean) {
    new Notice(`Fetching ${item.title}...`);

    try {
      const { APIClient } = await import('../api/client');
      const client = new APIClient({
        apiUrl: this.plugin.settings.apiUrl,
        apiToken: this.plugin.settings.apiToken,
      });

      const page = await client.getPage(item.slug);

      // Create new file with content
      const fileName = `${item.title}.md`;
      const content = `---
title: ${page.title}
confidence: ${page.confidence}
freshness: ${page.freshness}
saw_synced_at: ${new Date().toISOString()}
saw_path: ${item.slug}
---

${page.content}`;

      // Create file in vault
      const file = await this.app.vault.create(fileName, content);

      // Open the new file
      this.plugin.app.workspace.openLinkText(file.path, '', newPane);

      new Notice(`Created ${fileName}`);
    } catch (error) {
      new Notice(`Failed to fetch ${item.title}`);
      console.error('Failed to fetch page:', error);
    }
  }

  /**
   * Override to render confidence badges in results.
   */
  renderSuggestion(match: FuzzyMatch<SearchResult>, el: HTMLElement): void {
    // Call parent for default rendering
    super.renderSuggestion(match, el);

    // Add confidence badge
    const item = match.item;
    const container = el.querySelector('.suggestion-content');
    if (container) {
      const badge = renderConfidenceBadge(item.confidence, 8);
      container.appendChild(badge);
    }

    // Add snippet as secondary text
    const snippet = el.createDiv({ cls: 'suggestion-note' });
    snippet.textContent = item.snippet.slice(0, 100) + (item.snippet.length > 100 ? '...' : '');
  }
}