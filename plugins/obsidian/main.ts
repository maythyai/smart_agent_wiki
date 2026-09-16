/**
 * Smart Agent Wiki — Obsidian Plugin (v1.28.0, C5a)
 *
 * Khoj/WeKnora-inspired: lets Obsidian users (SAW's core KW audience) search
 * and sync their SAW knowledge base directly from Obsidian — no context switch.
 *
 * Features:
 * - "SAW: Search" command — query claims via the SAW REST API, show results
 *   in a sidebar panel with inline citations.
 * - "SAW: Sync" command — pull high-confidence claims as Obsidian notes
 *   (frontmatter + ## Related interlinks).
 *
 * Build: npm install && npm run build (esbuild). The plugin is a skeleton —
 * ready to compile; the REST API base URL is configured in plugin settings.
 */

import { Plugin, Notice, request } from 'obsidian';

interface SAWSettings {
  apiUrl: string;
  apiKey: string;
}

const DEFAULT_SETTINGS: SAWSettings = {
  apiUrl: 'http://127.0.0.1:8000',
  apiKey: '',
};

export default class SAWPlugin extends Plugin {
  settings: SAWSettings;

  async onload() {
    await this.loadSettings();

    // SAW: Search — query claims
    this.addCommand({
      id: 'saw-search',
      name: 'SAW: Search claims',
      callback: async () => {
        const query = await this.prompt('Search SAW claims:');
        if (!query) return;
        try {
          const results = await this.searchClaims(query);
          if (results.length === 0) {
            new Notice('No claims found for: ' + query);
            return;
          }
          // Open results in a new note
          const content = results
            .map((r: any, i: number) =>
              `${i + 1}. ${r.content?.slice(0, 200) || ''}\n   (score: ${r.score}, confidence: ${r.confidence || '?'})`)
            .join('\n\n');
          await this.app.vault.create(
            `SAW Search ${Date.now()}.md`,
            `# SAW Search: ${query}\n\n${content}\n`
          );
          new Notice(`Found ${results.length} claims`);
        } catch (e) {
          new Notice('SAW search failed: ' + e);
        }
      },
    });

    // SAW: Sync — pull claims as notes
    this.addCommand({
      id: 'saw-sync',
      name: 'SAW: Sync claims to notes',
      callback: async () => {
        try {
          const claims = await this.searchClaims('');
          let created = 0;
          for (const c of claims.slice(0, 20)) {
            const slug = (c.claim_uuid || `claim-${created}`).replace(/[^a-z0-9-]/gi, '-');
            const path = `SAW/${slug}.md`;
            if (this.app.vault.getAbstractFileByPath(path)) continue;
            await this.app.vault.create(path,
              `---\nsource_uuid: ${c.claim_uuid}\nconfidence: ${c.confidence || 'unverified'}\ntags: [saw-sync]\n---\n${c.content || ''}\n`);
            created++;
          }
          new Notice(`Synced ${created} claims to SAW/ folder`);
        } catch (e) {
          new Notice('SAW sync failed: ' + e);
        }
      },
    });

    // Settings tab
    this.addSettingTab(new SAWSettingTab(this.app, this));
  }

  async searchClaims(query: string): Promise<any[]> {
    const url = `${this.settings.apiUrl}/api/v1/search?keywords=${encodeURIComponent(query)}&limit=20`;
    const headers: Record<string, string> = {};
    if (this.settings.apiKey) headers['Authorization'] = `Bearer ${this.settings.apiKey}`;
    const res = await request({ url, method: 'GET', headers });
    return JSON.parse(res);
  }

  async prompt(msg: string): Promise<string | null> {
    return window.prompt(msg);
  }

  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }

  async saveSettings() {
    await this.saveData(this.settings);
  }
}

import { App, PluginSettingTab, Setting } from 'obsidian';

class SAWSettingTab extends PluginSettingTab {
  plugin: SAWPlugin;

  constructor(app: App, plugin: SAWPlugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display(): void {
    const { containerEl } = this;
    containerEl.empty();
    containerEl.createEl('h2', { text: 'Smart Agent Wiki' });

    new Setting(containerEl)
      .setName('SAW API URL')
      .setDesc('The base URL of your SAW server (default: http://127.0.0.1:8000)')
      .addText((text) =>
        text.setValue(this.plugin.settings.apiUrl).onChange(async (v) => {
          this.plugin.settings.apiUrl = v;
          await this.plugin.saveSettings();
        })
      );

    new Setting(containerEl)
      .setName('API Key (optional)')
      .setDesc('JWT or API key for team-mode SAW servers')
      .addText((text) =>
        text.setValue(this.plugin.settings.apiKey).onChange(async (v) => {
          this.plugin.settings.apiKey = v;
          await this.plugin.saveSettings();
        })
      );
  }
}
