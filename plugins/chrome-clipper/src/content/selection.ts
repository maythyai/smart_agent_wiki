/**
 * Selection Extractor
 *
 * Handles extraction of selected text/range for partial page clipping.
 * Implements CHRE-03: Support for selection-based clipping
 */

import type { ExtractedSelection } from '../types';

/**
 * Check if user has selected text
 */
export function hasSelection(): boolean {
  const selection = window.getSelection();
  return selection !== null && !selection.isCollapsed && selection.toString().trim().length > 0;
}

/**
 * Extract current text selection
 */
export function extractSelection(): ExtractedSelection | null {
  const selection = window.getSelection();

  if (!selection || selection.isCollapsed) {
    return null;
  }

  const text = selection.toString().trim();

  if (text.length === 0) {
    return null;
  }

  // Try to get HTML of selection
  let html: string | undefined;
  try {
    html = extractSelectionHTML(selection);
  } catch {
    // Selection HTML extraction may fail for cross-element selections
  }

  // Get bounding rect for UI positioning
  let boundingRect: ExtractedSelection['boundingRect'] | undefined;
  try {
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    boundingRect = {
      top: rect.top,
      left: rect.left,
      width: rect.width,
      height: rect.height,
    };
  } catch {
    // Bounding rect may fail in some cases
  }

  return {
    text,
    html,
    rangeCount: selection.rangeCount,
    isCollapsed: selection.isCollapsed,
    boundingRect,
  };
}

/**
 * Get HTML representation of selection
 */
export function getSelectionHTML(): string | null {
  const selection = window.getSelection();

  if (!selection || selection.rangeCount === 0) {
    return null;
  }

  return extractSelectionHTML(selection);
}

/**
 * Internal: Get HTML from a Selection object
 */
function extractSelectionHTML(selection: Selection): string | null {
  if (selection.rangeCount === 0) {
    return null;
  }

  const range = selection.getRangeAt(0);
  const container = document.createElement('div');
  container.appendChild(range.cloneContents());

  return container.innerHTML;
}

/**
 * Get selection range details
 */
export function getSelectionRange(): {
  startContainer: string;
  endContainer: string;
  startOffset: number;
  endOffset: number;
} | null {
  const selection = window.getSelection();

  if (!selection || selection.rangeCount === 0) {
    return null;
  }

  const range = selection.getRangeAt(0);

  return {
    startContainer: describeNode(range.startContainer),
    endContainer: describeNode(range.endContainer),
    startOffset: range.startOffset,
    endOffset: range.endOffset,
  };
}

/**
 * Describe a DOM node for debugging
 */
function describeNode(node: Node): string {
  if (node.nodeType === Node.TEXT_NODE) {
    return `#text(${node.textContent?.slice(0, 20)}...)`;
  }
  if (node.nodeType === Node.ELEMENT_NODE) {
    const el = node as Element;
    return `<${el.tagName.toLowerCase()}${el.id ? `#${el.id}` : ''}>`;
  }
  return node.nodeName;
}
