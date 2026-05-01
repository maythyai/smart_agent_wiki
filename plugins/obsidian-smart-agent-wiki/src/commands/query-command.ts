import { Command, Notice } from 'obsidian';
import SmartAgentWikiPlugin from '../../main';
import { SAWSearchModal } from '../views/search-modal';

/**
 * Create search command.
 */
export function createSearchCommand(plugin: SmartAgentWikiPlugin): Command {
  return {
    id: 'search-saw',
    name: 'Search Smart Agent Wiki',
    icon: 'search',
    callback: () => {
      new SAWSearchModal(plugin).open();
    },
  };
}

/**
 * Create quick search command (with last query).
 */
export function createQuickSearchCommand(plugin: SmartAgentWikiPlugin): Command {
  return {
    id: 'quick-search-saw',
    name: 'Quick search SAW (repeat last query)',
    icon: 'zap',
    callback: async () => {
      const lastQuery = plugin.settings.lastQuery;
      if (!lastQuery) {
        new Notice('No previous query');
        return;
      }

      const results = await performSearch(plugin, lastQuery);
      if (results.length > 0) {
        // Navigate to first result
        await plugin.app.workspace.openLinkText(results[0].slug, '', true);
      } else {
        new Notice('No results');
      }
    },
  };
}

/**
 * Perform search via API.
 */
export async function performSearch(
  plugin: SmartAgentWikiPlugin,
  query: string,
  _options: {
    type?: string;
    minConfidence?: number;
  } = {}
): Promise<Array<{
  slug: string;
  title: string;
  snippet: string;
  confidence: number;
  score: number;
}>> {
  if (!plugin.settings.apiToken) {
    new Notice('Please configure API token in settings');
    return [];
  }

  try {
    const { APIClient } = await import('../api/client');
    const client = new APIClient({
      apiUrl: plugin.settings.apiUrl,
      apiToken: plugin.settings.apiToken,
    });

    const response = await client.search(query, 1);
    return response.results;
  } catch (error) {
    console.error('Search failed:', error);
    return [];
  }
}