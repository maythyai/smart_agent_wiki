/**
 * Storage Manager for Chrome Extension
 *
 * Handles all persistence to chrome.storage.local following:
 * - Pitfall 22: All state persisted to storage (service worker lifecycle)
 * - Pitfall 24: Use storage.local (not sync) for large data
 *
 * Note: chrome.storage.sync has 100KB limit, 8KB per item, 120 writes/hour
 * chrome.storage.local has 10MB default (unlimitedStorage permission)
 */

import type {
  ExtensionSettings,
  ClippedContent,
  ClipHistoryEntry,
  QueuedClip,
  DEFAULT_SETTINGS,
} from '../types';

const STORAGE_KEYS = {
  SETTINGS: 'saw_settings',
  CLIP_HISTORY: 'saw_clip_history',
  PENDING_SYNC: 'saw_pending_sync',
  CONTENT_READY_TABS: 'saw_content_ready_tabs',
};

/**
 * Storage Manager - wraps chrome.storage.local with type-safe methods
 */
export class StorageManager {
  /**
   * Get current extension settings
   */
  async getSettings(): Promise<ExtensionSettings> {
    try {
      const result = await chrome.storage.local.get(STORAGE_KEYS.SETTINGS);
      const settings = result[STORAGE_KEYS.SETTINGS];

      // Merge with defaults for missing fields
      if (settings) {
        return { ...DEFAULT_SETTINGS, ...settings } as ExtensionSettings;
      }

      return DEFAULT_SETTINGS;
    } catch (error) {
      this.handleStorageError(error);
      return DEFAULT_SETTINGS;
    }
  }

  /**
   * Update extension settings (partial update)
   */
  async updateSettings(partial: Partial<ExtensionSettings>): Promise<void> {
    try {
      const current = await this.getSettings();
      const updated = { ...current, ...partial };

      await chrome.storage.local.set({ [STORAGE_KEYS.SETTINGS]: updated });

      this.checkLastError();
    } catch (error) {
      this.handleStorageError(error);
    }
  }

  /**
   * Get clip history (last 100 clips)
   */
  async getClipHistory(): Promise<ClipHistoryEntry[]> {
    try {
      const result = await chrome.storage.local.get(STORAGE_KEYS.CLIP_HISTORY);
      return result[STORAGE_KEYS.CLIP_HISTORY] || [];
    } catch (error) {
      this.handleStorageError(error);
      return [];
    }
  }

  /**
   * Add clip to history with size limit check
   */
  async addToHistory(clip: ClippedContent, success: boolean, apiId?: string, errorMessage?: string): Promise<void> {
    try {
      const settings = await this.getSettings();
      const history = await this.getClipHistory();

      const entry: ClipHistoryEntry = {
        ...clip,
        id: crypto.randomUUID(),
        success,
        apiId,
        errorMessage,
      };

      // Add to front of history
      history.unshift(entry);

      // Trim to max size
      const maxSize = settings.maxHistorySize || 100;
      if (history.length > maxSize) {
        history.splice(maxSize);
      }

      await chrome.storage.local.set({ [STORAGE_KEYS.CLIP_HISTORY]: history });

      this.checkLastError();
    } catch (error) {
      this.handleStorageError(error);
    }
  }

  /**
   * Clear all clip history
   */
  async clearHistory(): Promise<void> {
    try {
      await chrome.storage.local.remove(STORAGE_KEYS.CLIP_HISTORY);
      this.checkLastError();
    } catch (error) {
      this.handleStorageError(error);
    }
  }

  /**
   * Get pending sync queue (offline clips)
   */
  async getPendingSync(): Promise<QueuedClip[]> {
    try {
      const result = await chrome.storage.local.get(STORAGE_KEYS.PENDING_SYNC);
      return result[STORAGE_KEYS.PENDING_SYNC] || [];
    } catch (error) {
      this.handleStorageError(error);
      return [];
    }
  }

  /**
   * Add clip to pending sync queue
   */
  async addToPendingSync(clip: ClippedContent): Promise<void> {
    try {
      const pending = await this.getPendingSync();

      const queuedClip: QueuedClip = {
        id: crypto.randomUUID(),
        content: clip,
        attempts: 0,
        queuedAt: new Date().toISOString(),
      };

      pending.push(queuedClip);

      await chrome.storage.local.set({ [STORAGE_KEYS.PENDING_SYNC]: pending });

      this.checkLastError();
    } catch (error) {
      this.handleStorageError(error);
    }
  }

  /**
   * Remove clip from pending sync queue after successful upload
   */
  async removeFromPendingSync(id: string): Promise<void> {
    try {
      const pending = await this.getPendingSync();
      const filtered = pending.filter(clip => clip.id !== id);

      await chrome.storage.local.set({ [STORAGE_KEYS.PENDING_SYNC]: filtered });

      this.checkLastError();
    } catch (error) {
      this.handleStorageError(error);
    }
  }

  /**
   * Update a queued clip's attempt count and error
   */
  async updateQueuedClip(id: string, error?: string): Promise<void> {
    try {
      const pending = await this.getPendingSync();
      const clip = pending.find(c => c.id === id);

      if (clip) {
        clip.attempts++;
        clip.lastAttempt = new Date().toISOString();
        if (error) {
          clip.error = error;
        }
      }

      await chrome.storage.local.set({ [STORAGE_KEYS.PENDING_SYNC]: pending });

      this.checkLastError();
    } catch (error) {
      this.handleStorageError(error);
    }
  }

  /**
   * Clear pending sync queue
   */
  async clearPendingSync(): Promise<void> {
    try {
      await chrome.storage.local.remove(STORAGE_KEYS.PENDING_SYNC);
      this.checkLastError();
    } catch (error) {
      this.handleStorageError(error);
    }
  }

  /**
   * Track which tabs have content script ready
   */
  async markContentReady(tabId: number): Promise<void> {
    try {
      const result = await chrome.storage.local.get(STORAGE_KEYS.CONTENT_READY_TABS);
      const readyTabs: number[] = result[STORAGE_KEYS.CONTENT_READY_TABS] || [];

      if (!readyTabs.includes(tabId)) {
        readyTabs.push(tabId);
        await chrome.storage.local.set({ [STORAGE_KEYS.CONTENT_READY_TABS]: readyTabs });
      }

      this.checkLastError();
    } catch (error) {
      this.handleStorageError(error);
    }
  }

  /**
   * Check if content script is ready for a tab
   */
  async isContentReady(tabId: number): Promise<boolean> {
    try {
      const result = await chrome.storage.local.get(STORAGE_KEYS.CONTENT_READY_TABS);
      const readyTabs: number[] = result[STORAGE_KEYS.CONTENT_READY_TABS] || [];
      return readyTabs.includes(tabId);
    } catch (error) {
      this.handleStorageError(error);
      return false;
    }
  }

  /**
   * Remove tab from content ready tracking (on tab close)
   */
  async removeContentReadyTab(tabId: number): Promise<void> {
    try {
      const result = await chrome.storage.local.get(STORAGE_KEYS.CONTENT_READY_TABS);
      const readyTabs: number[] = result[STORAGE_KEYS.CONTENT_READY_TABS] || [];
      const filtered = readyTabs.filter(id => id !== tabId);

      await chrome.storage.local.set({ [STORAGE_KEYS.CONTENT_READY_TABS]: filtered });

      this.checkLastError();
    } catch (error) {
      this.handleStorageError(error);
    }
  }

  /**
   * Get storage usage stats
   */
  async getStorageStats(): Promise<{ used: number; quota: number }> {
    try {
      const usage = await chrome.storage.local.getBytesInUse();
      // Default quota is 10MB (10,485,760 bytes)
      const quota = 10485760;
      return { used: usage, quota };
    } catch (error) {
      this.handleStorageError(error);
      return { used: 0, quota: 10485760 };
    }
  }

  /**
   * Check chrome.runtime.lastError on storage operations
   */
  private checkLastError(): void {
    if (chrome.runtime.lastError) {
      console.warn('Chrome storage error:', chrome.runtime.lastError.message);
    }
  }

  /**
   * Handle storage errors with logging
   */
  private handleStorageError(error: unknown): void {
    console.error('Storage operation failed:', error);
    if (chrome.runtime.lastError) {
      console.error('Chrome runtime error:', chrome.runtime.lastError.message);
    }
  }
}

// Import DEFAULT_SETTINGS for use in getSettings
import { DEFAULT_SETTINGS } from '../types';