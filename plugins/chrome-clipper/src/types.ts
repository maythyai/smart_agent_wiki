/**
 * Smart Agent Wiki Chrome Extension - Shared Types
 *
 * These types define the data structures used throughout the extension
 * for communication between content script, background service worker,
 * popup, and the SAW API.
 */

// ============================================================
// Extension Settings
// ============================================================

/**
 * User-configurable extension settings
 * Persisted to chrome.storage.local (Pitfall 22)
 */
export interface ExtensionSettings {
  /** SAW API base URL */
  apiUrl: string;
  /** Authentication token for SAW API */
  apiToken: string;
  /** Auto-sync clipped content */
  autoSync: boolean;
  /** Show notifications on clip success/failure */
  showNotifications: boolean;
  /** Timestamp of last successful clip */
  lastClipTime?: string;
  /** Maximum number of clips to keep in history */
  maxHistorySize: number;
}

/**
 * Default settings applied on first install
 */
export const DEFAULT_SETTINGS: ExtensionSettings = {
  apiUrl: 'http://localhost:8000',
  apiToken: '',
  autoSync: true,
  showNotifications: true,
  maxHistorySize: 100,
};

// ============================================================
// Message Types
// ============================================================

/**
 * All message types used for extension communication
 */
export type MessageType =
  // Content script -> Background
  | 'content-ready'
  | 'extract-page'
  | 'extract-selection'
  // Popup -> Background
  | 'clip-page'
  | 'clip-selection'
  | 'get-settings'
  | 'update-settings'
  | 'get-history'
  | 'get-tag-suggestions'
  // Background -> Offscreen
  | 'parse-readability'
  // Context menu handlers
  | 'context-clip-page'
  | 'context-clip-selection'
  | 'context-clip-all-tabs'
  // Utility
  | 'ping';

/**
 * Generic message envelope for all extension communication
 */
export interface Message<T = unknown> {
  type: MessageType;
  data?: T;
  tabId?: number;
}

// ============================================================
// Content Extraction Types
// ============================================================

/**
 * Raw page content extracted by content script
 */
export interface ExtractedPage {
  url: string;
  title: string;
  html: string;
  description?: string;
  author?: string;
  publishedTime?: string;
  siteName?: string;
  favicon?: string;
  images: string[];
}

/**
 * Selected text/range extracted by content script
 */
export interface ExtractedSelection {
  text: string;
  html?: string;
  rangeCount: number;
  isCollapsed: boolean;
  boundingRect?: {
    top: number;
    left: number;
    width: number;
    height: number;
  };
}

// ============================================================
// Clipped Content Types
// ============================================================

/**
 * Final clipped content ready for API submission
 */
export interface ClippedContent {
  url: string;
  title: string;
  content: string;        // Cleaned HTML
  textContent: string;    // Plain text
  excerpt: string;        // Summary
  tags: string[];
  notes: string;
  source: 'chrome-extension';
  clippedAt: string;
}

/**
 * Article parsed by Readability.js
 */
export interface ParsedArticle {
  title: string;
  content: string;        // Cleaned HTML
  textContent: string;    // Plain text
  excerpt: string;        // Summary
  byline?: string;        // Author
  siteName?: string;
  publishedTime?: string;
}

// ============================================================
// API Response Types
// ============================================================

/**
 * Response from clip submission
 */
export interface ClipResponse {
  status: 'success' | 'error';
  id?: string;
  error?: string;
}

/**
 * Response from tag suggestion endpoint
 */
export interface TagSuggestionResponse {
  tags: string[];
  confidence: number;
}

/**
 * Response from auth verification
 */
export interface AuthVerifyResponse {
  valid: boolean;
  user_id?: string;
  expires_at?: string;
}

// ============================================================
// Storage Types
// ============================================================

/**
 * Clip history entry stored in chrome.storage.local
 */
export interface ClipHistoryEntry extends ClippedContent {
  id: string;
  success: boolean;
  apiId?: string;
  errorMessage?: string;
}

/**
 * Queued clip waiting for sync
 */
export interface QueuedClip {
  id: string;
  content: ClippedContent;
  attempts: number;
  lastAttempt?: string;
  error?: string;
  queuedAt: string;
}

/**
 * Sync queue status
 */
export type SyncStatus = 'idle' | 'syncing' | 'error' | 'complete';

// ============================================================
// Batch Operations
// ============================================================

/**
 * Progress info for batch clipping
 */
export interface BatchClipProgress {
  total: number;
  completed: number;
  failed: number;
  current?: string;
}

/**
 * Result of batch clip operation
 */
export interface BatchClipResult {
  succeeded: ClippedContent[];
  failed: Array<{ url: string; error: string }>;
}
