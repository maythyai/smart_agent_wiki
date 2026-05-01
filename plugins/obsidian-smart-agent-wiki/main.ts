import { Plugin, TFile, TFolder, PluginManifest, App, Notice, WorkspaceLeaf, View, TAbstractFile } from 'obsidian';
import { SAWPluginSettings, DEFAULT_SETTINGS } from './src/types';
import { SAWSettingsTab } from './src/settings';
import { APIClient } from './src/api/client';
import { SyncManager } from './src/api/sync';
import { SAWGraphView, GRAPH_VIEW_TYPE } from './src/views/graph-view';
import { ConfidenceBadgeManager } from './src/utils/badges';
import { createSyncAllCommand, createSyncCurrentFileCommand, createSyncStatusCommand } from './src/commands/sync-command';
import { createIngestCommand, createIngestWithOptionsCommand } from './src/commands/ingest-command';
import { createSearchCommand, createQuickSearchCommand } from './src/commands/query-command';

export default class SmartAgentWikiPlugin extends Plugin {
  settings: SAWPluginSettings;
  client: APIClient | null = null;
  syncManager: SyncManager | null = null;
  badgeManager: ConfidenceBadgeManager | null = null;

  constructor(app: App, manifest: PluginManifest) {
    super(app, manifest);
    this.settings = DEFAULT_SETTINGS;
  }

  async onload() {
    console.log('Loading Smart Agent Wiki plugin');

    await this.loadSettings();

    // Initialize API client
    this.client = new APIClient({
      apiUrl: this.settings.apiUrl,
      apiToken: this.settings.apiToken,
    });

    // Initialize sync manager
    this.syncManager = new SyncManager(this.app, this.client, this.settings);

    // Initialize badge manager
    this.badgeManager = new ConfidenceBadgeManager(this.app);

    // Register graph view
    this.registerView(GRAPH_VIEW_TYPE, (leaf: WorkspaceLeaf): View => new SAWGraphView(leaf, this));

    // Add settings tab
    this.addSettingTab(new SAWSettingsTab(this.app, this));

    // Add ribbon icon
    this.addRibbonIcon('brain', 'Smart Agent Wiki', (evt) => {
      this.openGraphView();
    });

    // Sync commands
    this.addCommand(createSyncAllCommand(this));
    this.addCommand(createSyncCurrentFileCommand(this));
    this.addCommand(createSyncStatusCommand(this));

    // Ingest commands
    this.addCommand(createIngestCommand(this));
    this.addCommand(createIngestWithOptionsCommand(this));

    // Search commands
    this.addCommand(createSearchCommand(this));
    this.addCommand(createQuickSearchCommand(this));

    // Graph view command
    this.addCommand({
      id: 'show-graph',
      name: 'Show Knowledge Graph',
      callback: () => this.openGraphView(),
    });

    // Refresh badges command
    this.addCommand({
      id: 'refresh-badges',
      name: 'Refresh Confidence Badges',
      callback: () => this.badgeManager?.start(),
    });

    // Register event handlers with auto-cleanup (per Pitfall 19)
    this.registerEvent(
      this.app.vault.on('modify', (file: TAbstractFile) => this.onFileModify(file as TFile | TFolder))
    );

    this.registerEvent(
      this.app.workspace.on('file-open', (file) => this.onFileOpen(file))
    );

    // Start badge manager
    this.badgeManager.start();

    // Auto-sync on startup if enabled
    if (this.settings.autoSync && this.settings.apiToken) {
      setTimeout(() => this.syncAllFiles(), 5000);
    }

    console.log('Smart Agent Wiki plugin loaded successfully');
  }

  onunload() {
    console.log('Unloading Smart Agent Wiki plugin');
    this.badgeManager?.stop();

    // Clean up graph view leaves
    this.app.workspace.getLeavesOfType(GRAPH_VIEW_TYPE).forEach((leaf) => {
      leaf.detach();
    });
  }

  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }

  async saveSettings() {
    await this.saveData(this.settings);
    if (this.client) {
      this.client.updateConfig({
        apiUrl: this.settings.apiUrl,
        apiToken: this.settings.apiToken,
      });
    }
  }

  async openGraphView() {
    const leaves = this.app.workspace.getLeavesOfType(GRAPH_VIEW_TYPE);

    if (leaves.length > 0) {
      // Already open, focus it
      this.app.workspace.revealLeaf(leaves[0]);
    } else {
      // Open new graph view in right sidebar
      const leaf = this.app.workspace.getRightLeaf(false);
      if (leaf) {
        await leaf.setViewState({ type: GRAPH_VIEW_TYPE, active: true });
        this.app.workspace.revealLeaf(leaf);
      }
    }
  }

  async syncAllFiles() {
    if (!this.syncManager) {
      new Notice('Plugin not fully initialized');
      return;
    }

    if (!this.settings.apiToken) {
      new Notice('Please configure API token in settings');
      return;
    }

    new Notice('Starting sync...');
    await this.syncManager.syncAll();
    await this.saveSettings();

    // Refresh badges after sync
    this.badgeManager?.start();
  }

  async syncCurrentFile(file: TFile) {
    if (!this.syncManager) {
      new Notice('Plugin not fully initialized');
      return;
    }

    if (!this.settings.apiToken) {
      new Notice('Please configure API token in settings');
      return;
    }

    const result = await this.syncManager.syncFile(file);
    new Notice(`${file.path}: ${result.status}`);
    await this.saveSettings();

    // Refresh badge for this file
    await this.badgeManager?.refreshFile(file.path);
  }

  onFileModify(file: TFile | TFolder) {
    if (!this.settings.autoSync) return;

    // Per Pitfall 20: Always check instanceof TFile
    if (file instanceof TFile && file.extension === 'md') {
      this.syncManager?.scheduleDebouncedSync(file);

      // Update badge for modified file
      this.badgeManager?.refreshFile(file.path);
    }
  }

  async onFileOpen(file: TFile | null) {
    if (!file || !(file instanceof TFile)) return;

    // Update badge for opened file
    await this.badgeManager?.refreshFile(file.path);
  }
}