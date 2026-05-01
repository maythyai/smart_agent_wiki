import { Command, Notice, TFile, Editor, MarkdownView, MarkdownFileInfo } from 'obsidian';
import SmartAgentWikiPlugin from '../../main';

export interface SyncCommandOptions {
  syncAll?: boolean;
  showNotice?: boolean;
}

export type SyncResultStatus = 'synced' | 'pushed' | 'pulled' | 'conflict' | 'error';

export interface SyncResult {
  path: string;
  status: SyncResultStatus;
  message?: string;
}

/**
 * Create full sync command.
 */
export function createSyncAllCommand(plugin: SmartAgentWikiPlugin): Command {
  return {
    id: 'sync-all',
    name: 'Sync all files with Smart Agent Wiki',
    icon: 'refresh-cw',
    callback: async () => {
      await executeSyncAll(plugin, { showNotice: true });
    },
  };
}

/**
 * Create current file sync command.
 */
export function createSyncCurrentFileCommand(plugin: SmartAgentWikiPlugin): Command {
  return {
    id: 'sync-current-file',
    name: 'Sync current file',
    icon: 'file-sync',
    editorCallback: async (editor: Editor, ctx: MarkdownView | MarkdownFileInfo) => {
      const file = ctx instanceof MarkdownView ? ctx.file : null;
      if (!file) {
        new Notice('No file active');
        return;
      }
      await executeSyncFile(plugin, file, { showNotice: true });
    },
  };
}

/**
 * Create sync status command (show sync state).
 */
export function createSyncStatusCommand(plugin: SmartAgentWikiPlugin): Command {
  return {
    id: 'sync-status',
    name: 'Show sync status',
    icon: 'info',
    callback: async () => {
      const status = await getSyncStatusSummary(plugin);
      new Notice(status);
    },
  };
}

/**
 * Execute full vault sync.
 */
export async function executeSyncAll(
  plugin: SmartAgentWikiPlugin,
  options: SyncCommandOptions = {}
): Promise<SyncResult[]> {
  const { showNotice = true } = options;

  if (!plugin.settings.apiToken) {
    if (showNotice) new Notice('Please configure API token in settings');
    return [];
  }

  if (!plugin.syncManager) {
    if (showNotice) new Notice('Plugin not fully initialized');
    return [];
  }

  if (showNotice) new Notice('Starting sync...');

  const results = await plugin.syncManager.syncAll();
  await plugin.saveSettings();

  // Update badges after sync
  plugin.badgeManager?.start();

  if (showNotice) {
    const summary = summarizeResults(results);
    new Notice(summary);
  }

  return results;
}

/**
 * Execute single file sync.
 */
export async function executeSyncFile(
  plugin: SmartAgentWikiPlugin,
  file: TFile,
  options: SyncCommandOptions = {}
): Promise<SyncResultStatus | null> {
  const { showNotice = true } = options;

  if (!plugin.settings.apiToken) {
    if (showNotice) new Notice('Please configure API token in settings');
    return null;
  }

  if (!plugin.syncManager) {
    if (showNotice) new Notice('Plugin not fully initialized');
    return null;
  }

  const result = await plugin.syncManager.syncFile(file);
  await plugin.saveSettings();

  // Refresh badge for this file
  await plugin.badgeManager?.refreshFile(file.path);

  if (showNotice) {
    new Notice(`${file.basename}: ${result.status}`);
  }

  return result.status;
}

/**
 * Get sync status summary.
 */
async function getSyncStatusSummary(plugin: SmartAgentWikiPlugin): Promise<string> {
  const lastSync = Object.keys(plugin.settings.lastSync).length;
  const autoSync = plugin.settings.autoSync ? 'enabled' : 'disabled';
  const interval = plugin.settings.syncInterval / 60000;

  return `Sync status: ${lastSync} files tracked, auto-sync ${autoSync} (${interval}min interval)`;
}

/**
 * Summarize sync results.
 */
function summarizeResults(results: SyncResult[]): string {
  const counts = {
    synced: results.filter(r => r.status === 'synced').length,
    pushed: results.filter(r => r.status === 'pushed').length,
    pulled: results.filter(r => r.status === 'pulled').length,
    conflict: results.filter(r => r.status === 'conflict').length,
    error: results.filter(r => r.status === 'error').length,
  };

  const parts: string[] = [];
  if (counts.pushed > 0) parts.push(`${counts.pushed} pushed`);
  if (counts.pulled > 0) parts.push(`${counts.pulled} pulled`);
  if (counts.synced > 0) parts.push(`${counts.synced} unchanged`);
  if (counts.conflict > 0) parts.push(`${counts.conflict} conflicts`);
  if (counts.error > 0) parts.push(`${counts.error} errors`);

  return `Sync complete: ${parts.join(', ')}`;
}