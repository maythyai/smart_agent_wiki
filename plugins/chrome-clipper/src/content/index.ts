/**
 * Content Script Entry Point
 *
 * Injected into all web pages to handle:
 * - Page content extraction
 * - Selection extraction
 * - Communication with background service worker
 *
 * Per Pitfall 23: Content script cannot access page JavaScript directly
 */

import { extractPageContent } from './extractor';
import { extractSelection, hasSelection } from './selection';
import type { Message } from '../types';

// Track if content script is ready
let isReady = false;

/**
 * Handle messages from background and popup
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  const msg = message as Message;

  switch (msg.type) {
    case 'extract-page':
      try {
        const content = extractPageContent();
        sendResponse({ success: true, data: content });
      } catch (error) {
        sendResponse({ success: false, error: String(error) });
      }
      break;

    case 'extract-selection':
      try {
        const selection = extractSelection();
        sendResponse({ success: true, data: selection });
      } catch (error) {
        sendResponse({ success: false, error: String(error) });
      }
      break;

    case 'ping':
      sendResponse({ success: true, ready: isReady });
      break;

    default:
      // Unknown message type — ignore
      break;
  }

  return true; // Keep channel open for async response
});

// Notify background that content script is ready
isReady = true;
chrome.runtime.sendMessage({ type: 'content-ready' });

console.log('SAW Clipper: Content script loaded');
