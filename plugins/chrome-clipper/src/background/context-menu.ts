/**
 * Context Menu Integration
 *
 * Creates and handles context menu items for clipping.
 * Per CONTEXT.md specification (lines 420-427).
 */

export const CONTEXT_MENU_IDS = {
  CLIP_PAGE: 'saw-clip-page',
  CLIP_SELECTION: 'saw-clip-selection',
  CLIP_ALL_TABS: 'saw-clip-all-tabs',
} as const;

/**
 * Setup context menu items
 */
export function setupContextMenu(): void {
  // Remove existing menus first
  chrome.contextMenus.removeAll(() => {
    // Clip current page
    chrome.contextMenus.create({
      id: CONTEXT_MENU_IDS.CLIP_PAGE,
      title: 'Clip to SAW',
      contexts: ['page'],
    });

    // Clip selected text
    chrome.contextMenus.create({
      id: CONTEXT_MENU_IDS.CLIP_SELECTION,
      title: 'Clip selection to SAW',
      contexts: ['selection'],
    });

    // Separator
    chrome.contextMenus.create({
      id: 'saw-separator',
      type: 'separator',
      contexts: ['page', 'selection'],
    });

    // Clip all tabs (shown in extension icon context)
    chrome.contextMenus.create({
      id: CONTEXT_MENU_IDS.CLIP_ALL_TABS,
      title: 'Clip all tabs to SAW',
      contexts: ['action'],
    });

    console.log('SAW Clipper: Context menus created');
  });
}

/**
 * Handle context menu clicks
 */
export function handleContextMenuClick(
  info: chrome.contextMenus.OnClickData,
  tab: chrome.tabs.Tab | undefined
): void {
  switch (info.menuItemId) {
    case CONTEXT_MENU_IDS.CLIP_PAGE:
      if (tab?.id) {
        chrome.runtime.sendMessage({
          type: 'context-clip-page',
          tabId: tab.id,
        });
      }
      break;

    case CONTEXT_MENU_IDS.CLIP_SELECTION:
      if (tab?.id) {
        chrome.runtime.sendMessage({
          type: 'context-clip-selection',
          tabId: tab.id,
          selectionText: info.selectionText,
        });
      }
      break;

    case CONTEXT_MENU_IDS.CLIP_ALL_TABS:
      chrome.runtime.sendMessage({ type: 'context-clip-all-tabs' });
      break;
  }
}
