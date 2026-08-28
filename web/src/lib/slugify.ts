// Frontend slugify — mirrors saw.drivers.web.routes.capture.slugify so that
// slugs derived on the client (graph node labels, search-bar suggestions)
// match the slugs the backend stores. Without this, navigating to a page
// whose title contains special characters 404'd (F-QS-06).
//
// Backend: lowercase -> replace [^a-z0-9一-鿿]+ with '-' -> strip leading/
// trailing hyphens -> 'untitled' if empty.

const CJK = '一-鿿';

export function slugify(text: string): string {
  const slug = text
    .trim()
    .toLowerCase()
    .replace(new RegExp(`[^a-z0-9${CJK}]+`, 'g'), '-')
    .replace(/^-+|-+$/g, '');
  return slug || 'untitled';
}
