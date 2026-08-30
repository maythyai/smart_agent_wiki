import { Link, useLocation } from 'react-router';

// F-WEB-08: breadcrumb navigation so users keep their place in the page
// hierarchy (was: no breadcrumbs → users lose context in deep pages).

const SEGMENT_LABELS: Record<string, string> = {
  pages: 'Pages',
  search: 'Search',
  graph: 'Graph',
  dashboard: 'Dashboard',
  import: 'Import',
  templates: 'Templates',
  timeline: 'Timeline',
  integrations: 'Integrations',
  page: 'Page',
  onboarding: 'Onboarding',
  settings: 'Settings',
};

export function Breadcrumbs() {
  const { pathname } = useLocation();
  const segments = pathname.split('/').filter(Boolean);
  if (segments.length === 0) return null; // home — no breadcrumb

  let path = '';
  const crumbs = segments.map((seg, idx) => {
    path += `/${seg}`;
    const isLast = idx === segments.length - 1;
    const label = SEGMENT_LABELS[seg] ?? decodeURIComponent(seg);
    return (
      <li key={path} className="flex items-center min-w-0">
        {idx > 0 && <span className="mx-1.5 text-gray-400 dark:text-gray-500">/</span>}
        {isLast ? (
          <span className="text-gray-700 dark:text-gray-200 font-medium truncate max-w-[40ch]">
            {label}
          </span>
        ) : (
          <Link
            to={path}
            className="text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 truncate"
          >
            {label}
          </Link>
        )}
      </li>
    );
  });

  return (
    <nav aria-label="Breadcrumb" className="text-sm py-2">
      <ol className="flex items-center flex-wrap">{crumbs}</ol>
    </nav>
  );
}
