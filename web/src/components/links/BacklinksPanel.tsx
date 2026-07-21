import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router';
import { api } from '../../lib/api';

interface Backlink {
  slug: string;
  title: string;
  context: string;
  link_count: number;
}

interface BacklinksPanelProps {
  slug: string;
}

/**
 * Displays pages that link TO the current page (backlinks).
 * Obsidian/Logseq-style panel showing reverse connections.
 */
export function BacklinksPanel({ slug }: BacklinksPanelProps) {
  const navigate = useNavigate();

  const { data: backlinks, isLoading } = useQuery<Backlink[]>({
    queryKey: ['backlinks', slug],
    queryFn: () => api.get<Backlink[]>(`/api/pages/${encodeURIComponent(slug)}/backlinks`),
    enabled: !!slug,
    staleTime: 60_000,
  });

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-2">
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3" />
        <div className="h-12 bg-gray-100 dark:bg-gray-800 rounded" />
      </div>
    );
  }

  if (!backlinks || backlinks.length === 0) {
    return null;
  }

  return (
    <div className="mt-8 border-t dark:border-gray-700 pt-6">
      <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">
        🔗 Backlinks ({backlinks.length})
      </h3>
      <div className="space-y-2">
        {backlinks.map((bl) => (
          <button
            key={bl.slug}
            onClick={() => navigate(`/page/${bl.slug}`)}
            className="w-full text-left p-3 rounded-lg border dark:border-gray-700
              hover:bg-gray-50 dark:hover:bg-gray-800 hover:border-blue-300
              dark:hover:border-blue-600 transition-colors group"
          >
            <div className="flex items-center gap-2 mb-1">
              <svg className="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
              <span className="font-medium text-gray-900 dark:text-white group-hover:text-blue-600">
                {bl.title}
              </span>
              {bl.link_count > 1 && (
                <span className="text-xs bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 px-1.5 py-0.5 rounded">
                  ×{bl.link_count}
                </span>
              )}
            </div>
            {bl.context && (
              <p className="text-sm text-gray-500 dark:text-gray-400 line-clamp-2 ml-6">
                {bl.context}
              </p>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
