import { App, TFile, TFolder, Notice, EventRef } from 'obsidian';
import { APIClient, SyncStatusResponse } from './client';
import { SAWPluginSettings } from '../types';
import { parseFrontmatter, updateFrontmatter, getSAWMetadata } from '../utils/frontmatter';
import { convertToObsidianLinks, convertToSAWLinks } from '../utils/wikilinks';

export type SyncStatus = 'synced' | 'pushed' | 'pulled' | 'conflict' | 'error';

export interface SyncResult {
  path: string;
  status: SyncStatus;
  message?: string;
}

export class SyncManager {
  private app: App;
  private client: APIClient;
  private settings: SAWPluginSettings;
  private syncDebounceTimers: Map<string, ReturnType<typeof setTimeout>> = new Map();
  private syncInProgress: boolean = false;

  constructor(app: App, client: APIClient, settings: SAWPluginSettings) {
    this.app = app;
    this.client = client;
    this.settings = settings;
  }

  /**
   * Sync a single file with SAW.
   * Per Decision 1: Last-Write-Wins with conflict files.
   */
  async syncFile(file: TFile): Promise<SyncResult> {
    try {
      // Read local file using Vault.process for atomicity (per Pitfall 18)
      const localContent = await this.app.vault.read(file);
      const localMtime = file.stat.mtime;
      const metadata = getSAWMetadata(localContent);
      const lastSyncAt = this.settings.lastSync[file.path];

      // Check sync status
      const status = await this.determineSyncStatus(
        file.path,
        localMtime,
        metadata.syncedAt,
        lastSyncAt
      );

      switch (status) {
        case 'in-sync':
          return { path: file.path, status: 'synced', message: 'Already in sync' };

        case 'local-ahead':
          return await this.pushToRemote(file, localContent);

        case 'remote-ahead':
          return await this.pullFromRemote(file);

        case 'conflict':
          return await this.handleConflict(file, localContent);

        default:
          return { path: file.path, status: 'error', message: 'Unknown sync status' };
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      console.error(`Sync failed for ${file.path}:`, error);
      return { path: file.path, status: 'error', message };
    }
  }

  /**
   * Determine sync status based on timestamps.
   * Per Pitfall 28: Clear authority model.
   */
  private async determineSyncStatus(
    path: string,
    localMtime: number,
    lastLocalSync: string | null,
    lastRecordedSync: string | undefined
  ): Promise<'in-sync' | 'local-ahead' | 'remote-ahead' | 'conflict'> {
    try {
      // Get remote status
      const remoteStatus = await this.client.getSyncStatus(path, localMtime);
      const remoteMtime = new Date(remoteStatus.remote_mtime).getTime();

      // If no last sync, remote is authority
      if (!lastRecordedSync && !lastLocalSync) {
        if (localMtime > remoteMtime) return 'local-ahead';
        if (remoteMtime > localMtime) return 'remote-ahead';
        return 'in-sync';
      }

      const lastSync = lastRecordedSync || lastLocalSync;
      const lastSyncTime = lastSync ? new Date(lastSync).getTime() : 0;

      // Check if both sides modified since last sync
      const localChanged = localMtime > lastSyncTime;
      const remoteChanged = remoteMtime > lastSyncTime;

      if (localChanged && remoteChanged) return 'conflict';
      if (localChanged) return 'local-ahead';
      if (remoteChanged) return 'remote-ahead';
      return 'in-sync';
    } catch (error) {
      // If remote status fails, assume local-ahead (push)
      console.warn('Could not get remote status, assuming local-ahead');
      return 'local-ahead';
    }
  }

  /**
   * Push local content to SAW.
   */
  private async pushToRemote(file: TFile, content: string): Promise<SyncResult> {
    const { body } = this.extractBody(content);
    const sawContent = convertToSAWLinks(body).content;

    // Generate slug from file path
    const slug = this.pathToSlug(file.path);

    await this.client.updatePage(slug, sawContent, `Synced from Obsidian: ${file.path}`);

    // Update local frontmatter with sync timestamp
    const now = new Date().toISOString();
    const updatedContent = updateFrontmatter(content, {
      saw_synced_at: now,
      saw_path: slug,
    });

    // Use Vault.process for atomic update (per Pitfall 18)
    await this.app.vault.process(file, () => updatedContent);

    // Update settings
    this.settings.lastSync[file.path] = now;

    return { path: file.path, status: 'pushed', message: 'Pushed to SAW' };
  }

  /**
   * Pull remote content from SAW.
   */
  private async pullFromRemote(file: TFile): Promise<SyncResult> {
    const slug = this.pathToSlug(file.path);
    const page = await this.client.getPage(slug);

    // Convert SAW links to Obsidian format
    const obsidianContent = convertToObsidianLinks(page.content).content;

    // Read existing frontmatter
    const localContent = await this.app.vault.read(file);
    const localFrontmatter = parseFrontmatter(localContent);

    // Merge frontmatter: keep local but update SAW metadata
    const mergedFrontmatter = {
      ...localFrontmatter,
      confidence: page.confidence,
      freshness: page.freshness,
      saw_synced_at: new Date().toISOString(),
      saw_path: slug,
    };

    // Reconstruct content with frontmatter
    const newContent = this.reconstructWithFrontmatter(obsidianContent, mergedFrontmatter);

    // Use Vault.process for atomic update (per Pitfall 18)
    await this.app.vault.process(file, () => newContent);

    // Update settings
    this.settings.lastSync[file.path] = new Date().toISOString();

    return { path: file.path, status: 'pulled', message: 'Pulled from SAW' };
  }

  /**
   * Handle sync conflict.
   * Per Decision 1: Create conflict file.
   */
  private async handleConflict(file: TFile, localContent: string): Promise<SyncResult> {
    const strategy = this.settings.conflictStrategy;

    switch (strategy) {
      case 'prefer-local':
        return this.pushToRemote(file, localContent);

      case 'prefer-remote':
        return this.pullFromRemote(file);

      case 'create-conflict':
      default:
        // Create conflict file with remote content
        const slug = this.pathToSlug(file.path);
        const page = await this.client.getPage(slug);
        const remoteContent = convertToObsidianLinks(page.content).content;

        // Create .conflict file
        const conflictPath = `${file.path}.conflict`;
        const conflictFile = this.app.vault.getAbstractFileByPath(conflictPath);

        if (conflictFile instanceof TFile) {
          await this.app.vault.modify(conflictFile, remoteContent);
        } else {
          await this.app.vault.create(conflictPath, remoteContent);
        }

        return {
          path: file.path,
          status: 'conflict',
          message: `Conflict detected. Remote saved to ${conflictPath}`,
        };
    }
  }

  /**
   * Sync all markdown files in vault.
   */
  async syncAll(): Promise<SyncResult[]> {
    if (this.syncInProgress) {
      new Notice('Sync already in progress');
      return [];
    }

    this.syncInProgress = true;
    const results: SyncResult[] = [];

    try {
      const files = this.app.vault.getMarkdownFiles();

      for (const file of files) {
        // Skip files in .obsidian directory
        if (file.path.startsWith('.obsidian/')) continue;

        const result = await this.syncFile(file);
        results.push(result);

        // Show notice for non-synced files
        if (result.status !== 'synced') {
          new Notice(`${file.path}: ${result.status}`);
        }
      }

      const summary = {
        synced: results.filter(r => r.status === 'synced').length,
        pushed: results.filter(r => r.status === 'pushed').length,
        pulled: results.filter(r => r.status === 'pulled').length,
        conflicts: results.filter(r => r.status === 'conflict').length,
        errors: results.filter(r => r.status === 'error').length,
      };

      new Notice(
        `Sync complete: ${summary.pushed} pushed, ${summary.pulled} pulled, ` +
        `${summary.conflicts} conflicts, ${summary.errors} errors`
      );
    } finally {
      this.syncInProgress = false;
    }

    return results;
  }

  /**
   * Debounced sync on file modify.
   */
  scheduleDebouncedSync(file: TFile, delayMs: number = 5000): void {
    const existing = this.syncDebounceTimers.get(file.path);
    if (existing) {
      clearTimeout(existing);
    }

    const timer = setTimeout(() => {
      this.syncDebounceTimers.delete(file.path);
      if (this.settings.autoSync) {
        this.syncFile(file);
      }
    }, delayMs);

    this.syncDebounceTimers.set(file.path, timer);
  }

  // Utility methods
  private pathToSlug(path: string): string {
    return path
      .replace(/\.md$/, '')
      .replace(/\//g, '-')
      .replace(/\s+/g, '-');
  }

  private extractBody(content: string): { body: string } {
    const match = content.match(/^---\n[\s\S]*?\n---\n([\s\S]*)$/);
    return { body: match ? match[1] : content };
  }

  private reconstructWithFrontmatter(
    body: string,
    frontmatter: Record<string, unknown>
  ): string {
    const lines = ['---'];
    for (const [key, value] of Object.entries(frontmatter)) {
      if (value !== undefined) {
        lines.push(`${key}: ${value}`);
      }
    }
    lines.push('---', '', body);
    return lines.join('\n');
  }
}