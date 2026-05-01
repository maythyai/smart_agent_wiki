/**
 * Message Handler for Chrome Extension
 *
 * Implements type-safe message routing following CONTEXT.md Decision 2:
 * Use @webext-core/messaging pattern for type safety.
 *
 * Message flow:
 * - Content script -> Background: 'extract-page', 'extract-selection', 'content-ready'
 * - Popup -> Background: 'clip-page', 'get-settings', 'get-history'
 * - Background -> Offscreen: 'parse-readability'
 */

import type { Message, MessageType } from '../types';
import { StorageManager } from './storage';

export type MessageHandler = (
  data: unknown,
  sender: chrome.runtime.MessageSender
) => Promise<unknown> | unknown;

export interface MessageHandlers {
  [key: string]: MessageHandler;
}

/**
 * Setup message listeners for the background service worker
 */
export function setupMessaging(
  handlers: MessageHandlers,
  storage: StorageManager
): void {
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    const msg = message as Message;

    // Handle message based on type
    const handler = handlers[msg.type];

    if (handler) {
      try {
        const result = handler(msg.data, sender);

        // Handle both sync and async handlers
        if (result instanceof Promise) {
          result
            .then((data) => sendResponse({ success: true, data }))
            .catch((error) =>
              sendResponse({ success: false, error: String(error) })
            );
          return true; // Keep channel open for async response
        } else {
          sendResponse({ success: true, data: result });
          return false;
        }
      } catch (error) {
        sendResponse({ success: false, error: String(error) });
        return false;
      }
    }

    // Unknown message type — log and ignore
    console.debug('Unknown message type:', msg.type);
    return false;
  });
}

/**
 * Create default message handlers for extension operations
 */
export function createDefaultHandlers(storage: StorageManager): MessageHandlers {
  return {
    // Get current settings
    'get-settings': async () => {
      return await storage.getSettings();
    },

    // Update settings
    'update-settings': async (data: unknown) => {
      const partial = data as Partial<import('../types').ExtensionSettings>;
      await storage.updateSettings(partial);
      return await storage.getSettings();
    },

    // Get clip history
    'get-history': async () => {
      return await storage.getClipHistory();
    },

    // Clear clip history
    'clear-history': async () => {
      await storage.clearHistory();
      return { success: true };
    },

    // Content script ready signal
    'content-ready': async (_data: unknown, sender: chrome.runtime.MessageSender) => {
      const tabId = sender.tab?.id;
      if (tabId) {
        await storage.markContentReady(tabId);
      }
      return { acknowledged: true };
    },

    // Ping for connection check
    'ping': async () => {
      return { ready: true, timestamp: new Date().toISOString() };
    },
  };
}

/**
 * Send message to content script in a specific tab
 */
export async function sendToContentScript<T = unknown>(
  tabId: number,
  message: Message
): Promise<{ success: boolean; data?: T; error?: string }> {
  try {
    const response = await chrome.tabs.sendMessage(tabId, message);
    return response || { success: false, error: 'No response from content script' };
  } catch (error) {
    return { success: false, error: String(error) };
  }
}

/**
 * Send message to offscreen document
 */
export async function sendToOffscreen<T = unknown>(
  message: Message
): Promise<{ success: boolean; data?: T; error?: string }> {
  try {
    const response = await chrome.runtime.sendMessage(message);
    return response || { success: false, error: 'No response from offscreen' };
  } catch (error) {
    return { success: false, error: String(error) };
  }
}
