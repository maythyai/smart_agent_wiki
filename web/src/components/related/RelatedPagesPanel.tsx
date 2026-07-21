import { Link } from 'react-router';
import { useRelatedPages } from '../../hooks/useRelated';

interface RelatedPagesPanelProps {
  slug: string;
}

export function RelatedPagesPanel({ slug }: RelatedPagesPanelProps) {
  const { data: related, isLoading } = useRelatedPages(slug);

  if (isLoading) {
    return (
      <div className="mt-6 bg-white dark:bg-gray-800 rounded-lg border dark:border-gray-700 p-4">
        <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">
          Related Pages
        </h3>
        <div className="space-y-2 animate-pulse">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
        </div>
      </div>
    );
  }

  if (!related || related.length === 0) return null;

  return (
    <div className="mt-6 bg-white dark:bg-gray-800 rounded-lg border dark:border-gray-700 p-4">
      <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">
        Related Pages
      </h3>
      <ul className="space-y-2">
        {related.map((page) => (
          <li key={page.slug}>
            <Link
              to={`/page/${page.slug}`}
              className="flex items-start gap-3 p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors group"
            >
              {/* Score indicator */}
              <div className="mt-1 flex-shrink-0">
                <div
                  className="w-2 h-2 rounded-full bg-blue-500"
                  style={{ opacity: Math.min(1, page.score / 3) }}
                  title={`Score: ${page.score}`}
                />
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 truncate">
                  {page.title}
                </div>
                {page.reasons.length > 0 && (
                  <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-1">
                    {page.reasons.join(' · ')}
                  </div>
                )}
              </div>

              {/* Score */}
              <span className="text-xs text-gray-400 dark:text-gray-500 font-mono flex-shrink-0">
                {page.score.toFixed(1)}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
