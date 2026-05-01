/**
 * SAW internal link formats:
 * - [[entity:Transformer]] - entity reference
 * - [[claim:ABC123]] - claim reference
 * - [[wiki:Page-Title]] - wiki page reference
 *
 * Obsidian format:
 * - [[Page Title]] - simple internal link
 * - [[Page Title|display text]] - link with alias
 */

// SAW link patterns
const SAW_ENTITY_LINK = /\[\[entity:([^\]]+)\]\]/g;
const SAW_CLAIM_LINK = /\[\[claim:([^\]]+)\]\]/g;
const SAW_WIKI_LINK = /\[\[wiki:([^\]]+)\]\]/g;

// Obsidian link pattern
const OBSIDIAN_LINK = /\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g;

export interface LinkConversionResult {
  content: string;
  links: Array<{
    original: string;
    converted: string;
    type: 'entity' | 'claim' | 'wiki';
  }>;
}

/**
 * Convert SAW links to Obsidian format.
 * [[entity:Transformer]] -> [[Transformer]]
 * [[wiki:Page-Title]] -> [[Page Title]]
 */
export function convertToObsidianLinks(content: string): LinkConversionResult {
  const links: LinkConversionResult['links'] = [];

  // Convert entity links
  content = content.replace(SAW_ENTITY_LINK, (match, name) => {
    const converted = `[[${name}]]`;
    links.push({ original: match, converted, type: 'entity' });
    return converted;
  });

  // Convert claim links (use claim ID as page name)
  content = content.replace(SAW_CLAIM_LINK, (match, id) => {
    const converted = `[[Claim ${id}]]`;
    links.push({ original: match, converted, type: 'claim' });
    return converted;
  });

  // Convert wiki links (replace hyphens with spaces)
  content = content.replace(SAW_WIKI_LINK, (match, title) => {
    const displayTitle = title.replace(/-/g, ' ');
    const converted = `[[${displayTitle}]]`;
    links.push({ original: match, converted, type: 'wiki' });
    return converted;
  });

  return { content, links };
}

/**
 * Convert Obsidian links to SAW format.
 * Uses frontmatter metadata to determine link type.
 *
 * If the file has a `type` in frontmatter, use that.
 * Otherwise, default to wiki type.
 */
export function convertToSAWLinks(
  content: string,
  linkTypes: Map<string, 'entity' | 'claim' | 'wiki'> = new Map()
): LinkConversionResult {
  const links: LinkConversionResult['links'] = [];

  content = content.replace(OBSIDIAN_LINK, (match, target, display) => {
    // Normalize target: spaces to hyphens for SAW
    const normalizedTarget = target.replace(/\s+/g, '-');

    // Determine link type from metadata
    const linkType = linkTypes.get(target) || 'wiki';

    let sawLink: string;
    switch (linkType) {
      case 'entity':
        sawLink = `[[entity:${normalizedTarget}]]`;
        break;
      case 'claim':
        sawLink = `[[claim:${normalizedTarget}]]`;
        break;
      case 'wiki':
      default:
        sawLink = `[[wiki:${normalizedTarget}]]`;
        break;
    }

    links.push({ original: match, converted: sawLink, type: linkType });

    // Preserve display text if present
    if (display) {
      // SAW doesn't support display text, but we preserve the link
      return sawLink;
    }

    return sawLink;
  });

  return { content, links };
}

/**
 * Extract all wikilinks from content.
 */
export function extractLinks(content: string): Array<{
  target: string;
  display?: string;
  position: { start: number; end: number };
}> {
  const links: Array<{
    target: string;
    display?: string;
    position: { start: number; end: number };
  }> = [];

  let match;
  const regex = new RegExp(OBSIDIAN_LINK.source, 'g');

  while ((match = regex.exec(content)) !== null) {
    links.push({
      target: match[1],
      display: match[2],
      position: { start: match.index, end: match.index + match[0].length },
    });
  }

  return links;
}

/**
 * Check if content contains SAW-style links.
 */
export function hasSAWLinks(content: string): boolean {
  return (
    SAW_ENTITY_LINK.test(content) ||
    SAW_CLAIM_LINK.test(content) ||
    SAW_WIKI_LINK.test(content)
  );
}

/**
 * Check if content contains Obsidian-style links.
 */
export function hasObsidianLinks(content: string): boolean {
  return OBSIDIAN_LINK.test(content);
}