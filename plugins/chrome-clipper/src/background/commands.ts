/**
 * Keyboard Commands Handler
 *
 * Implements keyboard shortcut handling for quick clipping.
 * Per manifest.json: Alt+S opens popup, Alt+Shift+S quick clips.
 */

import { Clipper, extractFromTab } from './clipper';
import { StorageManager } from './storage';
import { getAPIClient } from '../api/client';
import type { ExtensionSettings } from '../types';

/**
 * Setup keyboard command listeners
 */
export function setupCommands(storage: StorageManager): void {
  chrome.commands.onCommand.addListener(async (command) => {
    switch (command) {
      case 'clip-page':
        await handleQuickClip(storage);
        break;

      case 'clip-selection':
        await handleQuickClipSelection(storage);
        break;
    }
  });
}

/**
 * Handle quick clip of current page (no popup)
 */
async function handleQuickClip(storage: StorageManager): Promise<void> {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id || !tab.url) {
    console.warn('No active tab for quick clip');
    return;
  }

  const settings = await storage.getSettings();
  if (!settings.apiToken) {
    showNotification('SAW Clipper', 'Please configure API token in settings');
    return;
  }

  try {
    // Initialize API client
    const apiClient = getAPIClient({
      apiUrl: settings.apiUrl,
      apiToken: settings.apiToken,
    });

    // Extract content from tab
    const { page } = await extractFromTab(tab.id, 'page');
    if (!page) {
      throw new Error('Failed to extract page content');
    }

    // Clip via Clipper
    const clipper = new Clipper(storage);
    const content = await clipper.clipPage(tab.id, page);

    // Submit to API
    const result = await apiClient.clipPage(content);

    if (result.status === 'success') {
      // Save to history
      await storage.addToHistory(content, true, result.id);
      showNotification('SAW Clipper', `Clipped: ${content.title}`);
    } else {
      throw new Error('API returned error status');
    }
  } catch (error) {
    console.error('Quick clip failed:', error);
    showNotification('SAW Clipper', `Error: ${String(error)}`);
  }
}

/**
 * Handle quick clip of selection
 */
async function handleQuickClipSelection(storage: StorageManager): Promise<void> {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id || !tab.url) {
    console.warn('No active tab for selection clip');
    return;
  }

  const settings = await storage.getSettings();
  if (!settings.apiToken) {
    showNotification('SAW Clipper', 'Please configure API token in settings');
    return;
  }

  try {
    // Initialize API client
    const apiClient = getAPIClient({
      apiUrl: settings.apiUrl,
      apiToken: settings.apiToken,
    });

    // Extract selection from tab
    const { selection } = await extractFromTab(tab.id, 'selection');
    if (!selection || !selection.text) {
      showNotification('SAW Clipper', 'No selection found');
      return;
    }

    // Clip via Clipper
    const clipper = new Clipper(storage);
    const content = await clipper.clipSelection(
      tab.id,
      selection,
      tab.title || 'Untitled',
      tab.url
    );

    // Submit to API
    const result = await apiClient.clipPage(content);

    if (result.status === 'success') {
      await storage.addToHistory(content, true, result.id);
      showNotification('SAW Clipper', `Clipped selection: ${content.title}`);
    } else {
      throw new Error('API returned error status');
    }
  } catch (error) {
    console.error('Selection clip failed:', error);
    showNotification('SAW Clipper', `Error: ${String(error)}`);
  }
}

/**
 * Show system notification
 */
function showNotification(title: string, message: string): void {
  // Create basic notification
  chrome.notifications.create({
    type: 'basic',
    iconUrl: '../icons/icon48.png',
    title,
    message,
  });
}
