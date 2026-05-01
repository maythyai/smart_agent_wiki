/**
 * Page Content Extractor
 *
 * Extracts full page HTML and metadata for clipping.
 * Per Pitfall 23: Clone document to avoid modifying live DOM
 */

import type { ExtractedPage } from '../types';

/**
 * Extract full page content and metadata
 */
export function extractPageContent(): ExtractedPage {
  // Clone document to avoid modifying live DOM
  const clone = document.documentElement.cloneNode(true) as HTMLElement;

  // Remove script, style, and other non-content elements
  const removeSelectors = [
    'script',
    'style',
    'noscript',
    'iframe',
    'object',
    'embed',
    'applet',
    'form',
    'nav',
    'footer',
    'header[role="banner"]',
    '[role="navigation"]',
    '.sidebar',
    '.advertisement',
    '.ad',
    '.ads',
    '.social-share',
    '.comments',
  ];

  removeSelectors.forEach((selector) => {
    clone.querySelectorAll(selector).forEach((el) => el.remove());
  });

  return {
    url: window.location.href,
    title: getPageTitle(),
    html: clone.outerHTML,
    description: getMetaContent('description'),
    author: getMetaContent('author') || getMetaContent('article:author'),
    publishedTime: getMetaContent('article:published_time'),
    siteName: getMetaContent('og:site_name'),
    favicon: getFavicon(),
    images: collectImages(clone),
  };
}

/**
 * Get page metadata
 */
export function getPageMetadata(): {
  title: string;
  description?: string;
  author?: string;
  publishedTime?: string;
  siteName?: string;
} {
  return {
    title: getPageTitle(),
    description: getMetaContent('description'),
    author: getMetaContent('author') || getMetaContent('article:author'),
    publishedTime: getMetaContent('article:published_time'),
    siteName: getMetaContent('og:site_name'),
  };
}

/**
 * Get page title from various sources
 */
function getPageTitle(): string {
  // Try Open Graph title first
  const ogTitle = getMetaContent('og:title');
  if (ogTitle) return ogTitle;

  // Try Twitter card title
  const twitterTitle = getMetaContent('twitter:title');
  if (twitterTitle) return twitterTitle;

  // Fall back to document title
  return document.title || 'Untitled';
}

/**
 * Get meta tag content by name
 */
function getMetaContent(name: string): string | undefined {
  // Try standard meta tag
  const meta = document.querySelector(
    `meta[name="${name}"], meta[property="${name}"], meta[property="og:${name}"]`
  );
  return meta?.getAttribute('content') || undefined;
}

/**
 * Get favicon URL
 */
function getFavicon(): string | undefined {
  // Try link rel="icon"
  const iconLink = document.querySelector('link[rel~="icon"]');
  if (iconLink) {
    const href = iconLink.getAttribute('href');
    if (href) {
      return new URL(href, window.location.origin).href;
    }
  }

  // Try shortcut icon
  const shortcutLink = document.querySelector('link[rel="shortcut icon"]');
  if (shortcutLink) {
    const href = shortcutLink.getAttribute('href');
    if (href) {
      return new URL(href, window.location.origin).href;
    }
  }

  // Default favicon location
  return new URL('/favicon.ico', window.location.origin).href;
}

/**
 * Collect all image URLs from the page
 */
function collectImages(clone: HTMLElement): string[] {
  const images: string[] = [];

  clone.querySelectorAll('img[src]').forEach((img) => {
    const src = img.getAttribute('src');
    if (src) {
      try {
        const url = new URL(src, window.location.origin).href;
        if (!images.includes(url)) {
          images.push(url);
        }
      } catch {
        // Invalid URL, skip
      }
    }
  });

  return images;
}
