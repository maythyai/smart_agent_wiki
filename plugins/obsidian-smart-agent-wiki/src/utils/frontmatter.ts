export interface Frontmatter {
  title?: string;
  confidence?: number;
  freshness?: number;
  tags?: string[];
  type?: string;
  saw_synced_at?: string;
  saw_path?: string;
  [key: string]: unknown;
}

const FRONTMATTER_REGEX = /^---\n([\s\S]*?)\n---\n/;

/**
 * Parse YAML frontmatter from markdown content.
 * Returns null if no frontmatter found.
 */
export function parseFrontmatter(content: string): Frontmatter | null {
  const match = content.match(FRONTMATTER_REGEX);
  if (!match) return null;

  const yaml = match[1];
  const result: Frontmatter = {};

  // Simple YAML parsing (key: value)
  const lines = yaml.split('\n');
  for (const line of lines) {
    const colonIndex = line.indexOf(':');
    if (colonIndex === -1) continue;

    const key = line.slice(0, colonIndex).trim();
    let value: unknown = line.slice(colonIndex + 1).trim();

    // Remove quotes
    if (typeof value === 'string') {
      if ((value.startsWith('"') && value.endsWith('"')) ||
          (value.startsWith("'") && value.endsWith("'"))) {
        value = value.slice(1, -1);
      }
    }

    // Parse arrays (simple format: [item1, item2])
    if (typeof value === 'string' && value.startsWith('[') && value.endsWith(']')) {
      value = value.slice(1, -1).split(',').map(s => s.trim());
    }

    // Parse numbers
    if (typeof value === 'string' && !isNaN(Number(value))) {
      value = Number(value);
    }

    // Parse booleans
    if (value === 'true') value = true;
    if (value === 'false') value = false;

    result[key] = value;
  }

  return result;
}

/**
 * Extract the body content without frontmatter.
 */
export function extractBody(content: string): string {
  const match = content.match(FRONTMATTER_REGEX);
  if (!match) return content;
  return content.slice(match[0].length);
}

/**
 * Extract frontmatter and body separately.
 */
export function extractFrontmatter(content: string): { frontmatter: Frontmatter | null; body: string } {
  return {
    frontmatter: parseFrontmatter(content),
    body: extractBody(content),
  };
}

/**
 * Serialize frontmatter back to YAML string.
 */
export function serializeFrontmatter(frontmatter: Frontmatter): string {
  const lines: string[] = ['---'];

  for (const [key, value] of Object.entries(frontmatter)) {
    if (value === undefined) continue;

    if (Array.isArray(value)) {
      lines.push(`${key}: [${value.join(', ')}]`);
    } else if (typeof value === 'string') {
      // Quote strings with special characters
      if (value.includes(':') || value.includes('#') || value.includes('"')) {
        lines.push(`${key}: "${value}"`);
      } else {
        lines.push(`${key}: ${value}`);
      }
    } else {
      lines.push(`${key}: ${value}`);
    }
  }

  lines.push('---');
  return lines.join('\n') + '\n';
}

/**
 * Update frontmatter in content, preserving body.
 */
export function updateFrontmatter(content: string, updates: Partial<Frontmatter>): string {
  const { frontmatter, body } = extractFrontmatter(content);
  const merged = { ...frontmatter, ...updates };
  return serializeFrontmatter(merged) + body;
}

/**
 * Get SAW metadata from frontmatter.
 */
export function getSAWMetadata(content: string): {
  syncedAt: string | null;
  path: string | null;
  confidence: number;
} {
  const frontmatter = parseFrontmatter(content);
  return {
    syncedAt: frontmatter?.saw_synced_at || null,
    path: frontmatter?.saw_path || null,
    confidence: frontmatter?.confidence || 1,
  };
}

/**
 * Set SAW metadata in frontmatter.
 */
export function setSAWMetadata(
  content: string,
  metadata: { syncedAt: string; path: string; confidence: number }
): string {
  return updateFrontmatter(content, {
    saw_synced_at: metadata.syncedAt,
    saw_path: metadata.path,
    confidence: metadata.confidence,
  });
}