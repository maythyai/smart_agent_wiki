/**
 * Readability.js Wrapper
 *
 * Wraps @mozilla/readability for HTML content extraction.
 * Runs in offscreen document context (has DOM access).
 */

import { Readability } from '@mozilla/readability';
import type { ParsedArticle } from '../types';

/**
 * Parse HTML with Readability.js
 *
 * @param html - Raw HTML content
 * @param url - Original URL for link resolution
 * @returns Parsed article or null if parsing fails
 */
export function parseWithReadability(html: string, url: string): ParsedArticle | null {
  // Create a DOM parser
  const parser = new DOMParser();
  const doc = parser.parseFromString(html, 'text/html');

  // Set base URL for resolving relative links
  const baseEl = doc.createElement('base');
  baseEl.href = url;
  doc.head.prepend(baseEl);

  // Clone document for Readability (it modifies DOM)
  const documentClone = doc.cloneNode(true) as Document;

  // Create Readability instance
  const reader = new Readability(documentClone, {
    charThreshold: 500,      // Minimum chars for content detection
    debug: false,
  });

  // Parse
  const article = reader.parse();

  if (!article) {
    return null;
  }

  return {
    title: article.title,
    content: article.content,
    textContent: article.textContent,
    excerpt: article.excerpt,
    byline: article.byline,
    siteName: article.siteName,
    publishedTime: article.publishedTime,
  };
}

/**
 * Check if HTML is parseable (has readable content)
 */
export function isParseable(html: string): boolean {
  const parser = new DOMParser();
  const doc = parser.parseFromString(html, 'text/html');

  // Check for minimum content
  const textContent = doc.body?.textContent?.trim() || '';
  return textContent.length >= 500;
}
