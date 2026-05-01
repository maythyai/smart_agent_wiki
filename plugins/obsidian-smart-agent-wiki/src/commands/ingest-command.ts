import { Command, Notice, TFile, Editor, MarkdownView, MarkdownFileInfo, Modal, App, Setting } from 'obsidian';
import SmartAgentWikiPlugin from '../../main';
import { APIClient } from '../api/client';
import { convertToSAWLinks } from '../utils/wikilinks';
import { parseFrontmatter, updateFrontmatter } from '../utils/frontmatter';

export interface IngestOptions {
  tags?: string[];
  type?: string;
  forceReingest?: boolean;
}

/**
 * Create ingest current file command.
 */
export function createIngestCommand(plugin: SmartAgentWikiPlugin): Command {
  return {
    id: 'ingest-current-file',
    name: 'Ingest current file to SAW Vault',
    icon: 'upload',
    editorCallback: async (editor: Editor, ctx: MarkdownView | MarkdownFileInfo) => {
      const file = ctx instanceof MarkdownView ? ctx.file : null;
      if (!file) {
        new Notice('No file active');
        return;
      }
      await executeIngest(plugin, file);
    },
  };
}

/**
 * Create ingest with options command.
 */
export function createIngestWithOptionsCommand(plugin: SmartAgentWikiPlugin): Command {
  return {
    id: 'ingest-with-options',
    name: 'Ingest current file with options...',
    icon: 'upload-cloud',
    editorCallback: async (editor: Editor, ctx: MarkdownView | MarkdownFileInfo) => {
      const file = ctx instanceof MarkdownView ? ctx.file : null;
      if (!file) {
        new Notice('No file active');
        return;
      }
      new IngestOptionsModal(plugin.app, file, plugin).open();
    },
  };
}

/**
 * Execute file ingest.
 */
export async function executeIngest(
  plugin: SmartAgentWikiPlugin,
  file: TFile,
  options: IngestOptions = {}
): Promise<boolean> {
  if (!plugin.settings.apiToken) {
    new Notice('Please configure API token in settings');
    return false;
  }

  try {
    new Notice(`Ingesting ${file.basename}...`);

    // Read file content
    const content = await plugin.app.vault.read(file);
    const frontmatter = parseFrontmatter(content);

    // Convert to SAW link format
    const sawContent = convertToSAWLinks(content).content;

    // Create API client
    const client = new APIClient({
      apiUrl: plugin.settings.apiUrl,
      apiToken: plugin.settings.apiToken,
    });

    // Send to ingest endpoint using public method
    const result = await client.ingestFile({
      path: file.path,
      content: sawContent,
      title: frontmatter?.title || file.basename,
      tags: options.tags || (frontmatter?.tags as string[]) || [],
      type: options.type || (frontmatter?.type as string) || 'document',
      force: options.forceReingest || false,
    });

    if (result.status === 'queued') {
      new Notice(`${file.basename} queued for ingestion`);
    } else if (result.status === 'skipped') {
      new Notice(`${file.basename} already in vault (use --force to reingest)`);
    } else {
      new Notice(`${file.basename} ingested successfully`);
    }

    // Update frontmatter with ingest status
    const updatedContent = updateFrontmatter(content, {
      saw_ingested_at: new Date().toISOString(),
      saw_ingest_id: result.id,
    });

    // Use Vault.process for atomic update (per Pitfall 18)
    await plugin.app.vault.process(file, () => updatedContent);

    return true;
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    new Notice(`Ingest failed: ${message}`);
    console.error('Ingest failed:', error);
    return false;
  }
}

/**
 * Modal for ingest options.
 */
class IngestOptionsModal extends Modal {
  private file: TFile;
  private plugin: SmartAgentWikiPlugin;
  private options: IngestOptions = {};

  constructor(app: App, file: TFile, plugin: SmartAgentWikiPlugin) {
    super(app);
    this.file = file;
    this.plugin = plugin;
  }

  onOpen() {
    const { contentEl } = this;
    contentEl.createEl('h2', { text: 'Ingest Options' });

    // Read file content synchronously for frontmatter parsing
    // Note: cachedRead returns a promise but we use it as placeholder
    const frontmatter: Record<string, unknown> = {};

    new Setting(contentEl)
      .setName('Tags')
      .setDesc('Comma-separated tags')
      .addText((text) =>
        text
          .setPlaceholder('tag1, tag2')
          .setValue((frontmatter?.tags as string[] || []).join(', '))
          .onChange((value) => {
            this.options.tags = value
              .split(',')
              .map((t) => t.trim())
              .filter(Boolean);
          })
      );

    new Setting(contentEl)
      .setName('Type')
      .setDesc('Document type')
      .addDropdown((dropdown) =>
        dropdown
          .addOption('document', 'Document')
          .addOption('note', 'Note')
          .addOption('reference', 'Reference')
          .addOption('summary', 'Summary')
          .setValue((frontmatter?.type as string) || 'document')
          .onChange((value) => {
            this.options.type = value;
          })
      );

    new Setting(contentEl)
      .setName('Force Re-ingest')
      .setDesc('Re-process even if already in vault')
      .addToggle((toggle) =>
        toggle.setValue(false).onChange((value) => {
          this.options.forceReingest = value;
        })
      );

    new Setting(contentEl)
      .addButton((button) =>
        button
          .setButtonText('Cancel')
          .onClick(() => {
            this.close();
          })
      )
      .addButton((button) =>
        button
          .setButtonText('Ingest')
          .setCta()
          .onClick(async () => {
            this.close();
            await executeIngest(this.plugin, this.file, this.options);
          })
      );
  }

  onClose() {
    const { contentEl } = this;
    contentEl.empty();
  }
}