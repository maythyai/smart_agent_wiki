import { ItemView, WorkspaceLeaf, Menu, Notice, TFile, Setting } from 'obsidian';
import cytoscape, { Core, NodeSingular } from 'cytoscape';
import type SmartAgentWikiPlugin from '../../main';
import { GraphResponse } from '../types';

export const GRAPH_VIEW_TYPE = 'saw-graph-view';

// Confidence tier colors (per CONTEXT.md Decision 3)
const CONFIDENCE_COLORS: Record<number, string> = {
  1: '#808080', // Unverified - Gray
  2: '#CD7F32', // Single Source - Bronze
  3: '#C0C0C0', // Cross-Validated - Silver
  4: '#FFD700', // Human Verified - Gold
};

// Node type colors (per web UI patterns)
const NODE_TYPE_COLORS: Record<string, string> = {
  concept: '#4CAF50',
  person: '#2196F3',
  organization: '#FF9800',
  location: '#9C27B0',
  claim: '#F44336',
  source: '#00BCD4',
  default: '#607D8B',
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type CytoscapeStylesheet = any;

export class SAWGraphView extends ItemView {
  private plugin: SmartAgentWikiPlugin;
  private cy: Core | null = null;
  private graphContainerEl: HTMLElement | null = null;

  constructor(leaf: WorkspaceLeaf, plugin: SmartAgentWikiPlugin) {
    super(leaf);
    this.plugin = plugin;
  }

  getViewType(): string {
    return GRAPH_VIEW_TYPE;
  }

  getDisplayText(): string {
    return 'SAW Knowledge Graph';
  }

  getIcon(): string {
    return 'brain';
  }

  async onOpen() {
    this.graphContainerEl = this.contentEl;
    this.graphContainerEl.empty();
    this.graphContainerEl.addClass('saw-graph-container');

    // Create controls
    this.createControls();

    // Create graph container
    const graphDiv = this.graphContainerEl.createDiv({ cls: 'saw-graph-canvas' });
    graphDiv.style.height = '100%';
    graphDiv.style.width = '100%';

    // Initialize Cytoscape
    this.initCytoscape(graphDiv);

    // Load graph data
    await this.loadGraph();
  }

  async onClose() {
    if (this.cy) {
      this.cy.destroy();
      this.cy = null;
    }
  }

  private createControls() {
    if (!this.graphContainerEl) return;
    const controlsDiv = this.graphContainerEl.createDiv({ cls: 'saw-graph-controls' });

    // Layout selector
    new Setting(controlsDiv)
      .setName('Layout')
      .addDropdown((dropdown) =>
        dropdown
          .addOption('fcose', 'Force-directed')
          .addOption('concentric', 'Concentric')
          .addOption('breadthfirst', 'Tree')
          .setValue('fcose')
          .onChange((value) => this.applyLayout(value as 'fcose' | 'concentric' | 'breadthfirst'))
      );

    // Confidence filter
    new Setting(controlsDiv)
      .setName('Min Confidence')
      .addSlider((slider) =>
        slider
          .setLimits(1, 4, 1)
          .setValue(1)
          .setDynamicTooltip()
          .onChange((value) => this.filterByConfidence(value))
      );

    // Node type filter
    new Setting(controlsDiv)
      .setName('Node Type')
      .addDropdown((dropdown) =>
        dropdown
          .addOption('', 'All Types')
          .addOption('concept', 'Concept')
          .addOption('person', 'Person')
          .addOption('organization', 'Organization')
          .addOption('claim', 'Claim')
          .setValue('')
          .onChange((value) => this.filterByType(value))
      );

    // Refresh button
    new Setting(controlsDiv)
      .setName('Refresh')
      .addButton((button) =>
        button.setButtonText('Refresh').onClick(() => this.loadGraph())
      );
  }

  private initCytoscape(container: HTMLElement) {
    const styles: CytoscapeStylesheet[] = [
      {
        selector: 'node',
        style: {
          'background-color': 'data(color)',
          'label': 'data(label)',
          'text-valign': 'center',
          'text-halign': 'center',
          'font-size': '12px',
          'width': 'data(size)',
          'height': 'data(size)',
          'text-outline-color': '#fff',
          'text-outline-width': '2px',
          'border-width': 'data(borderWidth)',
          'border-color': 'data(borderColor)',
        },
      },
      {
        selector: 'node:selected',
        style: {
          'border-width': '3px',
          'border-color': '#2196F3',
        },
      },
      {
        selector: 'edge',
        style: {
          'width': 'data(weight)',
          'line-color': '#999',
          'target-arrow-color': '#999',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          'opacity': 0.7,
        },
      },
      {
        selector: 'edge.conflict',
        style: {
          'line-color': '#F44336',
          'line-style': 'dashed',
          'width': 3,
        },
      },
    ];

    this.cy = cytoscape({
      container,
      elements: [],
      style: styles,
      minZoom: 0.2,
      maxZoom: 3,
    });

    // Event handlers
    this.cy.on('tap', 'node', (evt) => this.onNodeTap(evt.target));
    this.cy.on('cxttap', 'node', (evt) => this.onNodeContext(evt.target, evt.originalEvent));
    this.cy.on('mouseover', 'node', (evt) => this.onNodeHover(evt.target));
    this.cy.on('mouseout', 'node', () => this.hideTooltip());
  }

  async loadGraph() {
    try {
      if (!this.plugin.settings.apiToken) {
        new Notice('Please configure API token');
        return;
      }

      new Notice('Loading graph...');

      // Import APIClient dynamically to avoid circular dependencies
      const { APIClient } = await import('../api/client');
      const client = new APIClient({
        apiUrl: this.plugin.settings.apiUrl,
        apiToken: this.plugin.settings.apiToken,
      });

      const graph = await client.getGraph(2, 100);
      this.renderGraph(graph);

      new Notice('Graph loaded');
    } catch (error) {
      console.error('Failed to load graph:', error);
      new Notice('Failed to load graph');
    }
  }

  private renderGraph(graph: GraphResponse) {
    if (!this.cy) return;

    const nodes = graph.nodes.map((node) => ({
      data: {
        id: node.id,
        label: node.label,
        type: node.type,
        confidence: node.confidence,
        color: NODE_TYPE_COLORS[node.type] || NODE_TYPE_COLORS.default,
        size: 20 + node.confidence * 5,
        borderWidth: node.confidence >= 4 ? 3 : 1,
        borderColor: CONFIDENCE_COLORS[node.confidence],
        description: node.description,
      },
    }));

    const edges = graph.edges.map((edge) => ({
      data: {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: edge.type,
        weight: Math.max(1, edge.weight * 2),
      },
      classes: edge.type === 'conflicts' ? 'conflict' : '',
    }));

    this.cy.elements().remove();
    this.cy.add([...nodes, ...edges]);

    this.applyLayout('fcose');
  }

  private applyLayout(name: 'fcose' | 'concentric' | 'breadthfirst') {
    if (!this.cy) return;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const layoutOptions: Record<string, any> = {
      fcose: {
        name: 'fcose',
        animate: true,
        animationDuration: 500,
        fit: true,
        padding: 30,
        nodeDimensionsIncludeLabels: true,
      },
      concentric: {
        name: 'concentric',
        animate: true,
        fit: true,
        padding: 30,
        concentric: (node: NodeSingular) => node.data('confidence'),
      },
      breadthfirst: {
        name: 'breadthfirst',
        animate: true,
        fit: true,
        padding: 30,
        directed: true,
      },
    };

    this.cy.layout(layoutOptions[name] as cytoscape.LayoutOptions).run();
  }

  private filterByConfidence(minConfidence: number) {
    if (!this.cy) return;

    this.cy.nodes().forEach((node) => {
      const confidence = node.data('confidence');
      if (confidence < minConfidence) {
        node.style('display', 'none');
      } else {
        node.style('display', 'element');
      }
    });

    // Also hide orphaned edges
    this.cy.edges().forEach((edge) => {
      const source = edge.source();
      const target = edge.target();
      if (source.style('display') === 'none' || target.style('display') === 'none') {
        edge.style('display', 'none');
      } else {
        edge.style('display', 'element');
      }
    });
  }

  private filterByType(type: string) {
    if (!this.cy) return;

    this.cy.nodes().forEach((node) => {
      if (!type || node.data('type') === type) {
        node.style('display', 'element');
      } else {
        node.style('display', 'none');
      }
    });

    // Update edges
    this.cy.edges().forEach((edge) => {
      const source = edge.source();
      const target = edge.target();
      if (source.style('display') === 'none' || target.style('display') === 'none') {
        edge.style('display', 'none');
      } else {
        edge.style('display', 'element');
      }
    });
  }

  private onNodeTap(node: NodeSingular) {
    const id = node.data('id');
    const type = node.data('type');

    // Navigate to the file if it's a wiki page
    if (type === 'concept' || type === 'claim') {
      this.navigateToNode(id);
    }
  }

  private async navigateToNode(id: string) {
    // Try to find matching file
    const files = this.app.vault.getMarkdownFiles();
    const matchingFile = files.find((f) => {
      const slug = f.basename.toLowerCase().replace(/\s+/g, '-');
      return slug === id || f.basename === id;
    });

    if (matchingFile) {
      await this.app.workspace.openLinkText(matchingFile.path, '', true);
    } else {
      new Notice(`No matching file found for: ${id}`);
    }
  }

  private onNodeContext(node: NodeSingular, event: MouseEvent) {
    const menu = new Menu();

    menu.addItem((item) =>
      item
        .setTitle('Open in new pane')
        .setIcon('arrow-up-right')
        .onClick(() => {
          this.navigateToNode(node.data('id'));
        })
    );

    menu.addItem((item) =>
      item
        .setTitle('Copy ID')
        .setIcon('copy')
        .onClick(() => {
          navigator.clipboard.writeText(node.data('id'));
          new Notice('ID copied');
        })
    );

    menu.showAtMouseEvent(event);
  }

  private onNodeHover(node: NodeSingular) {
    const confidence = node.data('confidence');
    const type = node.data('type');
    const description = node.data('description');

    const tooltipContent = [
      `<strong>${node.data('label')}</strong>`,
      `Type: ${type}`,
      `Confidence: ${confidence} (${this.getConfidenceLabel(confidence)})`,
      description ? `<br><em>${description}</em>` : '',
    ].join('<br>');

    this.showTooltip(tooltipContent, node.renderedPosition());
  }

  private showTooltip(content: string, position: { x: number; y: number }) {
    this.hideTooltip();
    if (!this.graphContainerEl) return;

    const tooltip = this.graphContainerEl.createDiv({ cls: 'saw-tooltip' });
    tooltip.innerHTML = content;
    tooltip.style.left = `${position.x + 20}px`;
    tooltip.style.top = `${position.y}px`;
  }

  private hideTooltip() {
    this.graphContainerEl?.querySelectorAll('.saw-tooltip').forEach((el) => el.remove());
  }

  private getConfidenceLabel(tier: number): string {
    const labels: Record<number, string> = {
      1: 'Unverified',
      2: 'Single Source',
      3: 'Cross-Validated',
      4: 'Human Verified',
    };
    return labels[tier] || 'Unknown';
  }
}