/**
 * Background Service Worker Entry Point
 *
 * Chrome Extension Manifest V3 service worker that handles:
 * - Message routing between content script, popup, and offscreen document
 * - Context menu management
 * - Periodic sync alarms
 * - Extension lifecycle events
 *
 * Per Pitfall 22: Service worker dies after ~30s idle. All state must be
 * restored from chrome.storage.local on init().
 */

import { StorageManager } from './storage';
import {
  setupMessaging,
  createDefaultHandlers,
  MessageHandlers,
} from './messaging';
import { setupCommands } from './commands';
import { setupContextMenu, handleContextMenuClick } from './context-menu';
import { Clipper, extractFromTab } from './clipper';
import { BatchClipper } from './batch-clipper';
import { SyncQueue } from './sync-queue';
import { getAPIClient } from '../api/client';
import type { ExtensionSettings, ClippedContent } from '../types';

/**
 * Background Worker - main service worker class
 */
export default class BackgroundWorker {
  private storage: StorageManager;
  private settings: ExtensionSettings | null = null;
  private isInitialized = false;
  private syncQueue: SyncQueue | null = null;

  constructor() {
    this.storage = new StorageManager();
    this.init();
  }

  /**
   * Initialize service worker
   * Called on extension install, browser startup, and service worker wake
   */
  async init(): Promise<void> {
    if (this.isInitialized) {
      // Already initialized (service worker woke from idle)
      return;
    }

    console.log('SAW Clipper: Initializing background worker...');

    // 1. Restore state from storage (Pitfall 22)
    this.settings = await this.storage.getSettings();

    // 2. Initialize API client if configured
    if (this.settings.apiToken) {
      const apiClient = getAPIClient({
        apiUrl: this.settings.apiUrl,
        apiToken: this.settings.apiToken,
      });
      this.syncQueue = new SyncQueue(this.storage, apiClient);
    }

    // 3. Setup message handlers
    const handlers = this.createMessageHandlers();
    setupMessaging(handlers, this.storage);

    // 4. Setup keyboard commands
    setupCommands(this.storage);

    // 5. Setup context menus
    setupContextMenu();
    chrome.contextMenus.onClicked.addListener((info, tab) => {
      handleContextMenuClick(info, tab);
    });

    // 6. Setup alarms for periodic sync
    this.setupAlarms();

    // 7. Listen for tab removal to clean up content-ready tracking
    chrome.tabs.onRemoved.addListener((tabId) => {
      this.storage.removeContentReadyTab(tabId);
    });

    this.isInitialized = true;
    console.log('SAW Clipper: Background worker initialized');
  }

  /**
   * Create message handlers for extension operations
   */
  private createMessageHandlers(): MessageHandlers {
    return {
      ...createDefaultHandlers(this.storage),

      // Handle clip-page request from popup
      'clip-page': async (data: unknown) => {
        const content = data as ClippedContent;
        return await this.handleClipPage(content);
      },

      // Handle tag suggestions request
      'get-tag-suggestions': async (data: unknown) => {
        return await this.handleGetTagSuggestions(data);
      },

      // Handle context menu clip page
      'context-clip-page': async (data: unknown) => {
        const { tabId } = data as { tabId: number };
        return await this.handleContextClipPage(tabId);
      },

      // Handle context menu clip selection
      'context-clip-selection': async (data: unknown) => {
        const { tabId } = data as { tabId: number };
        return await this.handleContextClipSelection(tabId);
      },

      // Handle context menu clip all tabs
      'context-clip-all-tabs': async () => {
        return await this.handleClipAllTabs();
      },
    };
  }

  /**
   * Handle clip page request
   */
  private async handleClipPage(content: ClippedContent): Promise<{ status: string; id?: string; error?: string }> {
    if (!this.settings?.apiToken) {
      return { status: 'error', error: 'API token not configured' };
    }

    try {
      const apiClient = getAPIClient({
        apiUrl: this.settings.apiUrl,
        apiToken: this.settings.apiToken,
      });

      const result = await apiClient.clipPage(content);

      if (result.status === 'success') {
        await this.storage.addToHistory(content, true, result.id);
        return { status: 'success', id: result.id };
      } else {
        // Add to sync queue for retry
        await this.storage.addToPendingSync(content);
        return { status: 'error', error: 'API returned error status' };
      }
    } catch (error) {
      // Add to sync queue for offline retry
      await this.storage.addToPendingSync(content);
      return { status: 'error', error: String(error) };
    }
  }

  /**
   * Handle tag suggestions request
   */
  private async handleGetTagSuggestions(data: unknown): Promise<{ tags: string[]; confidence: number }> {
    if (!this.settings?.apiToken) {
      return { tags: [], confidence: 0 };
    }

    try {
      const { content } = data as { content: string };
      const apiClient = getAPIClient({
        apiUrl: this.settings.apiUrl,
        apiToken: this.settings.apiToken,
      });

      const result = await apiClient.getTagSuggestions(content);
      return result;
    } catch (error) {
      console.warn('Failed to get tag suggestions:', error);
      return { tags: [], confidence: 0 };
    }
  }

  /**
   * Handle context menu clip page
   */
  private async handleContextClipPage(tabId: number): Promise<{ status: string }> {
    if (!this.settings?.apiToken) {
      this.showNotification('SAW Clipper', 'Please configure API token in settings');
      return { status: 'error' };
    }

    try {
      const apiClient = getAPIClient({
        apiUrl: this.settings.apiUrl,
        apiToken: this.settings.apiToken,
      });

      const { page } = await extractFromTab(tabId, 'page');
      if (!page) {
        throw new Error('Failed to extract page content');
      }

      const clipper = new Clipper(this.storage);
      const content = await clipper.clipPage(tabId, page);

      const result = await apiClient.clipPage(content);

      if (result.status === 'success') {
        await this.storage.addToHistory(content, true, result.id);
        this.showNotification('SAW Clipper', `Clipped: ${content.title}`);
        return { status: 'success' };
      } else {
        throw new Error('API returned error status');
      }
    } catch (error) {
      this.showNotification('SAW Clipper', `Error: ${String(error)}`);
      return { status: 'error' };
    }
  }

  /**
   * Handle context menu clip selection
   */
  private async handleContextClipSelection(tabId: number): Promise<{ status: string }> {
    if (!this.settings?.apiToken) {
      this.showNotification('SAW Clipper', 'Please configure API token in settings');
      return { status: 'error' };
    }

    try {
      const apiClient = getAPIClient({
        apiUrl: this.settings.apiUrl,
        apiToken: this.settings.apiToken,
      });

      const { selection } = await extractFromTab(tabId, 'selection');
      if (!selection || !selection.text) {
        this.showNotification('SAW Clipper', 'No selection found');
        return { status: 'error' };
      }

      const tab = await chrome.tabs.get(tabId);
      const clipper = new Clipper(this.storage);
      const content = await clipper.clipSelection(
        tabId,
        selection,
        tab.title || 'Untitled',
        tab.url || ''
      );

      const result = await apiClient.clipPage(content);

      if (result.status === 'success') {
        await this.storage.addToHistory(content, true, result.id);
        this.showNotification('SAW Clipper', `Clipped selection: ${content.title}`);
        return { status: 'success' };
      } else {
        throw new Error('API returned error status');
      }
    } catch (error) {
      this.showNotification('SAW Clipper', `Error: ${String(error)}`);
      return { status: 'error' };
    }
  }

  /**
   * Handle clip all tabs
   */
  private async handleClipAllTabs(): Promise<{ status: string; succeeded?: number; failed?: number }> {
    if (!this.settings?.apiToken) {
      this.showNotification('SAW Clipper', 'Please configure API token in settings');
      return { status: 'error' };
    }

    try {
      const apiClient = getAPIClient({
        apiUrl: this.settings.apiUrl,
        apiToken: this.settings.apiToken,
      });

      const batchClipper = new BatchClipper(this.storage, apiClient);

      this.showNotification('SAW Clipper', 'Starting batch clip...');

      const { succeeded, failed } = await batchClipper.clipAllTabs((progress) => {
        console.log(`Batch progress: ${progress.completed}/${progress.total}`);
      });

      this.showNotification(
        'SAW Clipper',
        `Batch complete: ${succeeded.length} succeeded, ${failed.length} failed`
      );

      return { status: 'success', succeeded: succeeded.length, failed: failed.length };
    } catch (error) {
      this.showNotification('SAW Clipper', `Batch error: ${String(error)}`);
      return { status: 'error' };
    }
  }

  /**
   * Setup alarms for periodic operations
   */
  private setupAlarms(): void {
    // Create periodic sync alarm (every 5 minutes)
    chrome.alarms.create('sync-queue', { periodInMinutes: 5 });

    // Create cleanup alarm (every hour)
    chrome.alarms.create('cleanup', { periodInMinutes: 60 });

    // Handle alarm events
    chrome.alarms.onAlarm.addListener((alarm) => {
      switch (alarm.name) {
        case 'sync-queue':
          this.processSyncQueue();
          break;

        case 'cleanup':
          this.cleanupStorage();
          break;
      }
    });

    console.log('SAW Clipper: Alarms setup complete');
  }

  /**
   * Process pending sync queue
   */
  private async processSyncQueue(): Promise<void> {
    if (!this.syncQueue) {
      return;
    }

    const pending = await this.storage.getPendingSync();
    if (pending.length === 0) {
      return;
    }

    console.log(`SAW Clipper: Processing ${pending.length} pending clips`);

    const { processed, failed } = await this.syncQueue.processQueue();

    if (processed > 0) {
      console.log(`SAW Clipper: Synced ${processed} clips`);
    }
    if (failed > 0) {
      console.warn(`SAW Clipper: Failed to sync ${failed} clips`);
    }
  }

  /**
   * Cleanup old storage data
   */
  private async cleanupStorage(): Promise<void> {
    const stats = await this.storage.getStorageStats();
    console.log(`SAW Clipper: Storage usage: ${stats.used} / ${stats.quota} bytes`);

    // If storage is getting full, trim history
    if (stats.used > stats.quota * 0.8) {
      const history = await this.storage.getClipHistory();
      if (history.length > 50) {
        // Clear and keep only recent 50
        await this.storage.clearHistory();
        for (const entry of history.slice(0, 50)) {
          await this.storage.addToHistory(
            entry,
            entry.success,
            entry.apiId,
            entry.errorMessage
          );
        }
        console.log('SAW Clipper: Trimmed history to 50 entries');
      }
    }
  }

  /**
   * Show system notification
   */
  private showNotification(title: string, message: string): void {
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/icon48.png',
      title,
      message,
    });
  }
}

// Initialize service worker on load
new BackgroundWorker();