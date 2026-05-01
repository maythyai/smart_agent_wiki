/**
 * Popup Entry Point
 *
 * Handles popup UI initialization and content extraction.
 */

import { initTagInput } from './tags';
import { showNotification } from './notifications';
import type { ExtensionSettings, ClippedContent } from '../types';

// State
let currentContent: ClippedContent | null = null;
let settings: ExtensionSettings | null = null;
let isSelectionMode = false;

// DOM elements
const elements = {
  loadingState: document.getElementById('loading-state'),
  mainContent: document.getElementById('main-content'),
  errorState: document.getElementById('error-state'),
  pageTitle: document.getElementById('page-title') as HTMLInputElement,
  pageUrl: document.getElementById('page-url') as HTMLAnchorElement,
  favicon: document.getElementById('favicon') as HTMLImageElement,
  contentPreview: document.getElementById('content-preview'),
  selectionIndicator: document.getElementById('selection-indicator'),
  notes: document.getElementById('notes') as HTMLTextAreaElement,
  clipBtn: document.getElementById('clip-btn'),
  cancelBtn: document.getElementById('cancel-btn'),
  connectionStatus: document.getElementById('connection-status'),
  retryBtn: document.getElementById('retry-btn'),
};

/**
 * Initialize popup
 */
async function init() {
  console.log('SAW Clipper: Initializing popup...');

  // 1. Load settings from background
  try {
    settings = await getSettings();
    updateConnectionStatus();
  } catch (error) {
    console.error('Failed to load settings:', error);
    showError('Failed to load extension settings');
    return;
  }

  // 2. Get current tab
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) {
    showError('No active tab found');
    return;
  }

  // 3. Show loading state
  showLoading();

  // 4. Extract content from tab
  try {
    const extracted = await extractContentFromTab(tab.id);
    currentContent = extracted.content;
    isSelectionMode = extracted.selectionMode || false;
    displayContent(extracted);
  } catch (error) {
    showError(String(error));
    return;
  }

  // 5. Initialize tag input
  initTagInput(currentContent);

  // 6. Setup event listeners
  setupEventListeners();

  console.log('SAW Clipper: Popup initialized');
}

/**
 * Get settings from background service worker
 */
async function getSettings(): Promise<ExtensionSettings> {
  const response = await chrome.runtime.sendMessage({ type: 'get-settings' });
  if (!response.success) {
    throw new Error(response.error || 'Failed to get settings');
  }
  return response.data;
}

/**
 * Extract content from a tab via content script
 */
async function extractContentFromTab(tabId: number): Promise<{
  content: ClippedContent;
  selectionMode?: boolean;
  excerpt?: string;
}> {
  const response = await chrome.tabs.sendMessage(tabId, { type: 'extract-page' });
  if (!response.success) {
    throw new Error(response.error || 'Failed to extract content');
  }

  // Build ClippedContent from extracted data
  const extracted = response.data;
  return {
    content: {
      url: extracted.url,
      title: extracted.title,
      content: extracted.html,
      textContent: '', // Will be filled by Readability
      excerpt: extracted.description || '',
      tags: [],
      notes: '',
      source: 'chrome-extension',
      clippedAt: new Date().toISOString(),
    },
    excerpt: extracted.description,
  };
}

/**
 * Display extracted content in popup
 */
function displayContent(content: ClippedContent & { excerpt?: string }) {
  hideLoading();

  // Set title
  elements.pageTitle.value = content.title;

  // Set URL
  elements.pageUrl.href = content.url;
  elements.pageUrl.textContent = new URL(content.url).hostname;

  // Set preview
  const previewText =
    content.excerpt ||
    content.textContent?.slice(0, 300) ||
    'No preview available';
  elements.contentPreview.querySelector('.preview-text').textContent =
    previewText + '...';

  // Show selection indicator if applicable
  if (isSelectionMode) {
    elements.selectionIndicator.classList.remove('hidden');
  }

  // Show main content
  elements.mainContent.classList.remove('hidden');
}

/**
 * Setup event listeners for UI interactions
 */
function setupEventListeners() {
  // Clip button
  elements.clipBtn.addEventListener('click', handleClip);

  // Cancel button
  elements.cancelBtn.addEventListener('click', () => window.close());

  // Retry button
  elements.retryBtn.addEventListener('click', init);

  // Title edit
  elements.pageTitle.addEventListener('input', () => {
    if (currentContent) {
      currentContent.title = elements.pageTitle.value;
    }
  });

  // Notes edit
  elements.notes.addEventListener('input', () => {
    if (currentContent) {
      currentContent.notes = elements.notes.value;
    }
  });

  // Listen for tag updates
  window.addEventListener('tags-updated', ((event: CustomEvent) => {
    if (currentContent) {
      currentContent.tags = event.detail;
    }
  }) as EventListener);
}

/**
 * Handle clip button click
 */
async function handleClip() {
  if (!currentContent) return;

  elements.clipBtn.setAttribute('disabled', 'true');
  elements.clipBtn.textContent = 'Clipping...';

  try {
    const response = await chrome.runtime.sendMessage({
      type: 'clip-page',
      data: currentContent,
    });

    if (response.success) {
      showNotification('success', 'Clipped successfully!');
      window.close();
    } else {
      showNotification('error', response.error || 'Failed to clip');
    }
  } catch (error) {
    showNotification('error', String(error));
  } finally {
    elements.clipBtn.removeAttribute('disabled');
    elements.clipBtn.innerHTML =
      '<span class="btn-icon">&#x1F4CB;</span> Clip to SAW';
  }
}

/**
 * Update connection status indicator
 */
function updateConnectionStatus() {
  const statusDot = elements.connectionStatus.querySelector('.status-dot');
  if (!settings?.apiToken) {
    statusDot.classList.add('disconnected');
    statusDot.classList.remove('connected');
    elements.connectionStatus.title = 'Not configured - add API token';
  } else {
    statusDot.classList.remove('disconnected');
    statusDot.classList.add('connected');
    elements.connectionStatus.title = 'Connected to ' + settings.apiUrl;
  }
}

/**
 * Show loading state
 */
function showLoading() {
  elements.loadingState.classList.remove('hidden');
  elements.mainContent.classList.add('hidden');
  elements.errorState.classList.add('hidden');
}

/**
 * Hide loading state
 */
function hideLoading() {
  elements.loadingState.classList.add('hidden');
}

/**
 * Show error state
 */
function showError(message: string) {
  elements.loadingState.classList.add('hidden');
  elements.mainContent.classList.add('hidden');
  elements.errorState.classList.remove('hidden');
  document.getElementById('error-message').textContent = message;
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', init);
