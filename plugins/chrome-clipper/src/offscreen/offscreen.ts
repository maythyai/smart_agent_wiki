/**
 * Offscreen Document Entry Point
 *
 * Provides DOM access for Readability.js parsing.
 * Per CONTEXT.md Decision 1: Use Offscreen API for DOM operations
 * (Service workers don't have DOM access)
 */

import { parseWithReadability } from './readability';
import type { Message, ParsedArticle } from '../types';

/**
 * Handle messages from background service worker
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  const msg = message as Message;

  if (msg.type === 'parse-readability') {
    try {
      const { html, url } = msg.data as { html: string; url: string };
      const result = parseWithReadability(html, url);
      sendResponse({ success: true, data: result });
    } catch (error) {
      sendResponse({ success: false, error: String(error) });
    }
    return true; // Keep channel open for async response
  }

  return false;
});

console.log('SAW Clipper: Offscreen document loaded');
