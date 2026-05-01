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
import type { ExtensionSettings, ClippedContent } from '../types';

/**
 * Background Worker - main service worker class
 */
export default class BackgroundWorker {
  private storage: StorageManager;
  private settings: ExtensionSettings | null = null;
  private isInitialized = false;

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

    // 2. Setup message handlers
    const handlers: MessageHandlers = {
      ...createDefaultHandlers(this.storage),

      // Add custom handlers for clipping operations
      // These will be implemented in Plan 08-04
      'clip-page': async (data: unknown) => {
        const content = data as ClippedContent;
        // TODO: Implement in Plan 08-04
        console.log('Clip page requested:', content.url);
        return { status: 'pending', message: 'Clipping not yet implemented' };
      },

      'get-tag-suggestions': async (data: unknown) => {
        // TODO: Implement in Plan 08-04
        console.log('Tag suggestions requested');
        return { tags: [], confidence: 0 };
      },

      'context-clip-page': async (data: unknown) => {
        const { tabId } = data as { tabId: number };
        console.log('Context menu clip page:', tabId);
        return { status: 'pending' };
      },

      'context-clip-selection': async (data: unknown) => {
        const { tabId, selectionText } = data as { tabId: number; selectionText: string };
        console.log('Context menu clip selection:', tabId, selectionText?.slice(0, 50));
        return { status: 'pending' };
      },

      'context-clip-all-tabs': async () => {
        console.log('Context menu clip all tabs');
        return { status: 'pending' };
      },
    };

    setupMessaging(handlers, this.storage);

    // 3. Setup context menus
    this.setupContextMenus();

    // 4. Setup alarms for periodic sync
    this.setupAlarms();

    // 5. Listen for tab removal to clean up content-ready tracking
    chrome.tabs.onRemoved.addListener((tabId) => {
      this.storage.removeContentReadyTab(tabId);
    });

    this.isInitialized = true;
    console.log('SAW Clipper: Background worker initialized');
  }

  /**
   * Setup context menu items
   */
  private setupContextMenus(): void {
    // Remove existing menus first
    chrome.contextMenus.removeAll(() => {
      // Clip current page
      chrome.contextMenus.create({
        id: 'saw-clip-page',
        title: 'Clip to SAW',
        contexts: ['page'],
      });

      // Clip selected text
      chrome.contextMenus.create({
        id: 'saw-clip-selection',
        title: 'Clip selection to SAW',
        contexts: ['selection'],
      });

      // Separator
      chrome.contextMenus.create({
        id: 'saw-separator',
        type: 'separator',
        contexts: ['page', 'selection'],
      });

      // Clip all tabs
      chrome.contextMenus.create({
        id: 'saw-clip-all-tabs',
        title: 'Clip all tabs to SAW',
        contexts: ['action'],
      });

      // Handle context menu clicks
      chrome.contextMenus.onClicked.addListener((info, tab) => {
        this.handleContextMenuClick(info, tab);
      });

      console.log('SAW Clipper: Context menus created');
    });
  }

  /**
   * Handle context menu item clicks
   */
  private handleContextMenuClick(
    info: chrome.contextMenus.OnClickData,
    tab: chrome.tabs.Tab | undefined
  ): void {
    switch (info.menuItemId) {
      case 'saw-clip-page':
        if (tab?.id) {
          chrome.runtime.sendMessage({
            type: 'context-clip-page',
            tabId: tab.id,
          });
        }
        break;

      case 'saw-clip-selection':
        if (tab?.id) {
          chrome.runtime.sendMessage({
            type: 'context-clip-selection',
            tabId: tab.id,
            selectionText: info.selectionText,
          });
        }
        break;

      case 'saw-clip-all-tabs':
        chrome.runtime.sendMessage({ type: 'context-clip-all-tabs' });
        break;
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
    const pending = await this.storage.getPendingSync();

    if (pending.length === 0) {
      return;
    }

    console.log(`SAW Clipper: Processing ${pending.length} pending clips`);

    // TODO: Implement actual sync in Plan 08-04
    // For now, just log that we would process them
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
        // Trim to 50 entries
        const trimmed = history.slice(0, 50);
        // Note: We'd need to add a method to set history directly
        console.log('SAW Clipper: Would trim history from', history.length, 'to 50');
      }
    }
  }
}

// Initialize service worker on load
new BackgroundWorker();