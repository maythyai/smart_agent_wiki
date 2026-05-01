/**
 * Offline Sync Queue
 *
 * Manages offline clip queue with automatic retry.
 * Per Pitfall 22: State persisted to chrome.storage.local.
 */

import { APIClient } from '../api/client';
import { StorageManager } from './storage';
import type { ClippedContent, QueuedClip, SyncStatus } from '../types';

export class SyncQueue {
  private syncStatus: SyncStatus = 'idle';
  private maxRetries: number = 3;
  private retryDelayMs: number = 60000; // 1 minute

  constructor(
    private storage: StorageManager,
    private apiClient: APIClient
  ) {}

  /**
   * Add clip to pending sync queue
   */
  async enqueue(content: ClippedContent): Promise<string> {
    const queuedClip: QueuedClip = {
      id: crypto.randomUUID(),
      content,
      attempts: 0,
      queuedAt: new Date().toISOString(),
    };

    await this.storage.addToPendingSync(content);
    console.log('SAW Clipper: Added to sync queue:', content.url);

    return queuedClip.id;
  }

  /**
   * Process pending sync queue
   */
  async processQueue(
    onStatusChange?: (status: SyncStatus) => void
  ): Promise<{ processed: number; failed: number }> {
    const pending = await this.storage.getPendingSync();

    if (pending.length === 0) {
      return { processed: 0, failed: 0 };
    }

    this.syncStatus = 'syncing';
    onStatusChange?.(this.syncStatus);

    let processed = 0;
    let failed = 0;

    for (const clip of pending) {
      try {
        const result = await this.apiClient.clipPage(clip.content);

        if (result.status === 'success') {
          await this.storage.removeFromPendingSync(clip.url);
          processed++;
          console.log('SAW Clipper: Synced:', clip.content.url);
        } else {
          throw new Error('API returned error status');
        }
      } catch (error) {
        failed++;
        // Keep in queue for retry
        console.warn(`SAW Clipper: Sync failed for ${clip.content.url}:`, error);

        // Update attempt count
        await this.storage.updateQueuedClip(clip.id, String(error));
      }
    }

    this.syncStatus = pending.length > 0 && failed > 0 ? 'error' : 'complete';
    onStatusChange?.(this.syncStatus);

    console.log(`SAW Clipper: Sync complete - ${processed} processed, ${failed} failed`);

    return { processed, failed };
  }

  /**
   * Get number of items in queue
   */
  async getQueueLength(): Promise<number> {
    const pending = await this.storage.getPendingSync();
    return pending.length;
  }

  /**
   * Get current sync status
   */
  getStatus(): SyncStatus {
    return this.syncStatus;
  }

  /**
   * Clear all pending clips from queue
   */
  async clearQueue(): Promise<void> {
    await this.storage.clearPendingSync();
    console.log('SAW Clipper: Sync queue cleared');
  }
}
