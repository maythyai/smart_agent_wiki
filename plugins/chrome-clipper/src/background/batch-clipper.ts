/**
 * Batch Clipper for Multiple Tabs
 *
 * Implements batch clipping for CHRE-07.
 * Per CONTEXT.md (lines 293-299): Uses chrome.tabs.query() to iterate tabs.
 */

import { APIClient } from '../api/client';
import { StorageManager } from './storage';
import { Clipper, extractFromTab } from './clipper';
import type { ClippedContent, BatchClipProgress } from '../types';

export type ProgressCallback = (progress: BatchClipProgress) => void;

export class BatchClipper {
  constructor(
    private storage: StorageManager,
    private apiClient: APIClient
  ) {}

  /**
   * Clip all tabs in current window
   */
  async clipAllTabs(
    onProgress?: ProgressCallback
  ): Promise<{ succeeded: ClippedContent[]; failed: Array<{ url: string; error: string }> }> {
    // Get all tabs in current window
    const tabs = await chrome.tabs.query({ currentWindow: true });

    const progress: BatchClipProgress = {
      total: tabs.length,
      completed: 0,
      failed: 0,
    };

    const succeeded: ClippedContent[] = [];
    const failed: Array<{ url: string; error: string }> = [];

    const clipper = new Clipper(this.storage);

    for (const tab of tabs) {
      if (!tab.id || !tab.url) {
        continue;
      }

      progress.current = tab.title || tab.url;

      try {
        // Extract content from tab
        const { page } = await extractFromTab(tab.id, 'page');
        if (!page) {
          throw new Error('Failed to extract page content');
        }

        // Build clipped content
        const content = await clipper.clipPage(tab.id, page);

        // Send to SAW API
        const result = await this.apiClient.clipPage(content);

        if (result.status === 'success') {
          succeeded.push(content);
          progress.completed++;

          // Add to history
          await this.storage.addToHistory(content, true, result.id);
        } else {
          throw new Error(result.id || 'API returned error');
        }
      } catch (error) {
        failed.push({
          url: tab.url,
          error: String(error),
        });
        progress.failed++;
      }

      onProgress?.(progress);
    }

    return { succeeded, failed };
  }

  /**
   * Clip tabs in a specific tab group
   */
  async clipTabGroup(
    groupId: number,
    onProgress?: ProgressCallback
  ): Promise<{ succeeded: ClippedContent[]; failed: Array<{ url: string; error: string }> }> {
    // Get tabs in specific group
    const tabs = await chrome.tabs.query({ groupId });

    const progress: BatchClipProgress = {
      total: tabs.length,
      completed: 0,
      failed: 0,
    };

    const succeeded: ClippedContent[] = [];
    const failed: Array<{ url: string; error: string }> = [];

    const clipper = new Clipper(this.storage);

    for (const tab of tabs) {
      if (!tab.id || !tab.url) {
        continue;
      }

      progress.current = tab.title || tab.url;

      try {
        const { page } = await extractFromTab(tab.id, 'page');
        if (!page) {
          throw new Error('Failed to extract page content');
        }

        const content = await clipper.clipPage(tab.id, page);
        const result = await this.apiClient.clipPage(content);

        if (result.status === 'success') {
          succeeded.push(content);
          progress.completed++;
          await this.storage.addToHistory(content, true, result.id);
        } else {
          throw new Error(result.id || 'API returned error');
        }
      } catch (error) {
        failed.push({
          url: tab.url,
          error: String(error),
        });
        progress.failed++;
      }

      onProgress?.(progress);
    }

    return { succeeded, failed };
  }
}
