/**
 * Clipper - Content Extraction Orchestrator
 *
 * Coordinates content extraction from tabs, Readability parsing via
 * offscreen documents, and building ClippedContent for API submission.
 *
 * Per CONTEXT.md Decision 1: Uses Offscreen API for DOM parsing
 */

import { StorageManager } from './storage';
import type {
  ClippedContent,
  ParsedArticle,
  ExtractedPage,
  ExtractedSelection,
} from '../types';

export class Clipper {
  constructor(private storage: StorageManager) {}

  /**
   * Clip full page content from a tab
   */
  async clipPage(
    tabId: number,
    extractedPage: ExtractedPage
  ): Promise<ClippedContent> {
    // 1. Parse with Readability via offscreen document
    const article = await this.parseWithOffscreen(
      extractedPage.html,
      extractedPage.url
    );

    // 2. Build ClippedContent
    const content: ClippedContent = {
      url: extractedPage.url,
      title: article?.title || extractedPage.title,
      content: article?.content || this.sanitizeHtml(extractedPage.html),
      textContent: article?.textContent || '',
      excerpt: article?.excerpt || extractedPage.description || '',
      tags: [],
      notes: '',
      source: 'chrome-extension',
      clippedAt: new Date().toISOString(),
    };

    // 3. Add metadata
    if (article?.byline || extractedPage.author) {
      // Store author info as note
      content.notes = `Author: ${article?.byline || extractedPage.author}`;
    }

    if (extractedPage.publishedTime) {
      const existingNotes = content.notes;
      content.notes = existingNotes
        ? `${existingNotes}\nPublished: ${extractedPage.publishedTime}`
        : `Published: ${extractedPage.publishedTime}`;
    }

    return content;
  }

  /**
   * Clip selected text from a tab
   */
  async clipSelection(
    tabId: number,
    selection: ExtractedSelection,
    pageTitle: string,
    pageUrl: string
  ): Promise<ClippedContent> {
    // For selections, we use the text directly and minimal Readability parsing
    const content: ClippedContent = {
      url: pageUrl,
      title: `[Selection] ${pageTitle}`,
      content: selection.html || `<p>${this.escapeHtml(selection.text)}</p>`,
      textContent: selection.text,
      excerpt: selection.text.slice(0, 200) + (selection.text.length > 200 ? '...' : ''),
      tags: [],
      notes: `Clipped selection from: ${pageUrl}`,
      source: 'chrome-extension',
      clippedAt: new Date().toISOString(),
    };

    return content;
  }

  /**
   * Parse HTML with Readability.js via offscreen document
   */
  private async parseWithOffscreen(
    html: string,
    url: string
  ): Promise<ParsedArticle | null> {
    try {
      // Check if offscreen document exists
      const existingContexts = await chrome.runtime.getContexts({
        contextTypes: [chrome.runtime.ContextType.OFFSCREEN_DOCUMENT],
      });

      if (existingContexts.length === 0) {
        // Create offscreen document for DOM parsing
        await chrome.offscreen.createDocument({
          url: 'src/offscreen/offscreen.html',
          reasons: [chrome.offscreen.Reason.DOM_PARSER],
          justification:
            'Parse HTML with Readability.js for content extraction',
        });
      }

      // Send message to offscreen document
      const response = await chrome.runtime.sendMessage({
        type: 'parse-readability',
        data: { html, url },
      });

      if (response.success) {
        return response.data as ParsedArticle;
      }

      console.warn('Readability parsing failed:', response.error);
      return null;
    } catch (error) {
      console.error('Error parsing with offscreen:', error);
      return null;
    } finally {
      // Clean up offscreen document
      try {
        await chrome.offscreen.closeDocument();
      } catch {
        // May already be closed
      }
    }
  }

  /**
   * Basic HTML sanitization for fallback
   */
  private sanitizeHtml(html: string): string {
    // Remove script, style, and other dangerous elements
    const dangerousTags = [
      'script',
      'style',
      'iframe',
      'object',
      'embed',
      'form',
    ];

    let sanitized = html;
    for (const tag of dangerousTags) {
      const regex = new RegExp(`<${tag}[^>]*>.*?</${tag}>`, 'gis');
      sanitized = sanitized.replace(regex, '');
    }

    // Remove event handlers
    sanitized = sanitized.replace(/\s*on\w+\s*=\s*["'][^"']*["']/gi, '');

    return sanitized;
  }

  /**
   * Escape HTML special characters
   */
  private escapeHtml(text: string): string {
    const htmlEntities: Record<string, string> = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;',
    };
    return text.replace(/[&<>"']/g, (char) => htmlEntities[char] || char);
  }
}

/**
 * Helper: Extract content from a tab via content script
 */
export async function extractFromTab(
  tabId: number,
  type: 'page' | 'selection'
): Promise<{ page?: ExtractedPage; selection?: ExtractedSelection }> {
  const response = await chrome.tabs.sendMessage(tabId, {
    type: type === 'page' ? 'extract-page' : 'extract-selection',
  });

  if (!response.success) {
    throw new Error(response.error || `Failed to extract ${type}`);
  }

  return {
    [type]: response.data,
  } as { page?: ExtractedPage; selection?: ExtractedSelection };
}
