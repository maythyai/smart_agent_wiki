import { App, PluginSettingTab, Setting, Notice } from 'obsidian';
import SmartAgentWikiPlugin from '../main';

export class SAWSettingsTab extends PluginSettingTab {
  plugin: SmartAgentWikiPlugin;

  constructor(app: App, plugin: SmartAgentWikiPlugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display(): void {
    const { containerEl } = this;
    containerEl.empty();

    containerEl.createEl('h2', { text: 'Smart Agent Wiki Settings' });

    // API URL setting
    new Setting(containerEl)
      .setName('API URL')
      .setDesc('Smart Agent Wiki server URL')
      .addText((text) =>
        text
          .setPlaceholder('http://localhost:8000')
          .setValue(this.plugin.settings.apiUrl)
          .onChange(async (value) => {
            this.plugin.settings.apiUrl = value;
            await this.plugin.saveSettings();
          })
      );

    // API Token setting
    new Setting(containerEl)
      .setName('API Token')
      .setDesc('JWT token for authentication')
      .addText((text) =>
        text
          .setPlaceholder('Enter your API token')
          .setValue(this.plugin.settings.apiToken)
          .onChange(async (value) => {
            this.plugin.settings.apiToken = value;
            await this.plugin.saveSettings();
          })
      );

    // Sync interval setting
    new Setting(containerEl)
      .setName('Sync Interval')
      .setDesc('Automatic sync interval in minutes (0 to disable)')
      .addText((text) =>
        text
          .setValue(String(this.plugin.settings.syncInterval / 60000))
          .onChange(async (value) => {
            const minutes = parseInt(value) || 0;
            this.plugin.settings.syncInterval = minutes * 60000;
            await this.plugin.saveSettings();
          })
      );

    // Auto-sync toggle
    new Setting(containerEl)
      .setName('Auto Sync')
      .setDesc('Automatically sync on file changes')
      .addToggle((toggle) =>
        toggle
          .setValue(this.plugin.settings.autoSync)
          .onChange(async (value) => {
            this.plugin.settings.autoSync = value;
            await this.plugin.saveSettings();
          })
      );

    // Conflict strategy setting
    new Setting(containerEl)
      .setName('Conflict Strategy')
      .setDesc('How to handle sync conflicts')
      .addDropdown((dropdown) =>
        dropdown
          .addOption('prefer-local', 'Prefer Local')
          .addOption('prefer-remote', 'Prefer Remote')
          .addOption('create-conflict', 'Create Conflict File')
          .setValue(this.plugin.settings.conflictStrategy)
          .onChange(async (value: string) => {
            this.plugin.settings.conflictStrategy = value as 'prefer-local' | 'prefer-remote' | 'create-conflict';
            await this.plugin.saveSettings();
          })
      );

    // Test connection button
    new Setting(containerEl)
      .setName('Test Connection')
      .setDesc('Verify API connectivity')
      .addButton((button) =>
        button.setButtonText('Test').onClick(async () => {
          const success = await this.testConnection();
          if (success) {
            new Notice('Connection successful!');
          } else {
            new Notice('Connection failed. Check URL and token.');
          }
        })
      );

    // Manual sync button
    new Setting(containerEl)
      .setName('Manual Sync')
      .setDesc('Trigger immediate sync')
      .addButton((button) =>
        button.setButtonText('Sync Now').onClick(async () => {
          new Notice('Starting sync...');
          await this.plugin.syncAllFiles();
        })
      );
  }

  async testConnection(): Promise<boolean> {
    try {
      const response = await fetch(`${this.plugin.settings.apiUrl}/api/health`, {
        headers: {
          Authorization: `Bearer ${this.plugin.settings.apiToken}`,
        },
      });
      return response.ok;
    } catch (error) {
      console.error('Connection test failed:', error);
      return false;
    }
  }
}