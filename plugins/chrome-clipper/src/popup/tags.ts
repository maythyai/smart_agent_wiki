/**
 * Tag Input Component
 *
 * Implements pill-style tag input with suggestions (CHRE-04, CHRE-06).
 */

import type { ClippedContent } from '../types';

export interface TagInputState {
  tags: string[];
  suggestions: string[];
  maxTags: number;
}

const state: TagInputState = {
  tags: [],
  suggestions: [],
  maxTags: 10,
};

// DOM elements
let tagsList: HTMLElement;
let tagInput: HTMLInputElement;
let suggestionsContainer: HTMLElement;

/**
 * Initialize tag input component
 */
export function initTagInput(content: ClippedContent | null) {
  tagsList = document.getElementById('tags-list')!;
  tagInput = document.getElementById('tag-input')! as HTMLInputElement;
  suggestionsContainer = document.getElementById('tag-suggestions')!;

  // Load existing tags if any
  if (content?.tags) {
    state.tags = [...content.tags];
    renderTags();
  }

  // Setup event listeners
  tagInput.addEventListener('keydown', handleKeyDown);
  tagInput.addEventListener('input', handleInput);
  tagInput.addEventListener('blur', handleBlur);

  // Fetch tag suggestions from SAW API
  if (content) {
    fetchTagSuggestions(content);
  }
}

/**
 * Handle keydown in tag input
 */
function handleKeyDown(e: KeyboardEvent) {
  if (e.key === 'Enter' || e.key === ',') {
    e.preventDefault();
    const value = tagInput.value.trim();
    if (value) {
      addTag(value);
      tagInput.value = '';
    }
  } else if (
    e.key === 'Backspace' &&
    tagInput.value === '' &&
    state.tags.length > 0
  ) {
    removeTag(state.tags.length - 1);
  }
}

/**
 * Handle input changes for filtering suggestions
 */
function handleInput() {
  const value = tagInput.value.trim();
  if (value.length >= 2) {
    filterSuggestions(value);
  } else {
    hideSuggestions();
  }
}

/**
 * Handle blur - add pending tag
 */
function handleBlur() {
  const value = tagInput.value.trim();
  if (value) {
    addTag(value);
    tagInput.value = '';
  }
}

/**
 * Add a tag
 */
function addTag(tag: string) {
  // Normalize tag: lowercase, alphanumeric + dash/underscore
  const normalized = tag.toLowerCase().replace(/[^a-z0-9-_]/g, '');

  if (
    normalized &&
    !state.tags.includes(normalized) &&
    state.tags.length < state.maxTags
  ) {
    state.tags.push(normalized);
    renderTags();
    updateContentTags();
  }
}

/**
 * Remove a tag by index
 */
function removeTag(index: number) {
  state.tags.splice(index, 1);
  renderTags();
  updateContentTags();
}

/**
 * Render tags as pill elements
 */
function renderTags() {
  tagsList.innerHTML = state.tags
    .map(
      (tag, i) =>
        `<span class="tag-pill">
      ${escapeHtml(tag)}
      <button type="button" class="tag-remove" data-index="${i}">&#x2715;</button>
    </span>`
    )
    .join('');

  // Add click handlers for remove buttons
  tagsList.querySelectorAll('.tag-remove').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      const index = parseInt((e.target as HTMLElement).dataset.index!, 10);
      removeTag(index);
    });
  });
}

/**
 * Fetch tag suggestions from SAW API
 */
async function fetchTagSuggestions(content: ClippedContent) {
  try {
    const response = await chrome.runtime.sendMessage({
      type: 'get-tag-suggestions',
      data: { content: content.textContent?.slice(0, 1000) || content.excerpt },
    });

    if (response.success && response.data?.tags) {
      state.suggestions = response.data.tags.slice(0, 5);
      renderSuggestions();
    }
  } catch (error) {
    console.warn('Failed to fetch tag suggestions:', error);
  }
}

/**
 * Render suggestion buttons
 */
function renderSuggestions() {
  if (state.suggestions.length === 0) {
    hideSuggestions();
    return;
  }

  const suggestionsList = suggestionsContainer.querySelector(
    '.suggestions-list'
  )!;
  suggestionsList.innerHTML = state.suggestions
    .map(
      (tag) =>
        `<button type="button" class="suggestion-tag" data-tag="${escapeHtml(tag)}">${escapeHtml(tag)}</button>`
    )
    .join('');

  suggestionsList.querySelectorAll('.suggestion-tag').forEach((btn) => {
    btn.addEventListener('click', () => {
      const tag = (btn as HTMLElement).dataset.tag!;
      addTag(tag);
      // Remove from suggestions
      state.suggestions = state.suggestions.filter((t) => t !== tag);
      renderSuggestions();
    });
  });

  suggestionsContainer.classList.remove('hidden');
}

/**
 * Filter suggestions based on input
 */
function filterSuggestions(query: string) {
  const filtered = state.suggestions.filter((t) =>
    t.includes(query.toLowerCase())
  );

  if (filtered.length > 0) {
    const suggestionsList = suggestionsContainer.querySelector(
      '.suggestions-list'
    )!;
    suggestionsList.innerHTML = filtered
      .map(
        (tag) =>
          `<button type="button" class="suggestion-tag" data-tag="${escapeHtml(tag)}">${escapeHtml(tag)}</button>`
      )
      .join('');

    suggestionsList.querySelectorAll('.suggestion-tag').forEach((btn) => {
      btn.addEventListener('click', () => {
        const tag = (btn as HTMLElement).dataset.tag!;
        addTag(tag);
        tagInput.value = '';
        hideSuggestions();
      });
    });

    suggestionsContainer.classList.remove('hidden');
  } else {
    hideSuggestions();
  }
}

/**
 * Hide suggestions panel
 */
function hideSuggestions() {
  suggestionsContainer.classList.add('hidden');
}

/**
 * Update content tags via custom event
 */
function updateContentTags() {
  window.dispatchEvent(
    new CustomEvent('tags-updated', { detail: state.tags })
  );
}

/**
 * Get current tags
 */
export function getTags(): string[] {
  return [...state.tags];
}

/**
 * Escape HTML special characters
 */
function escapeHtml(text: string): string {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
