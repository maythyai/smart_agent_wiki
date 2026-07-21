import { useNavigate } from 'react-router';
import EntityTypeBadge from '../entity/EntityTypeBadge';

interface TimelineEntryProps {
  entry: {
    slug: string;
    title: string;
    entity_type: string;
    snippet: string;
    is_daily_note: boolean;
    tags: string[];
  };
}

export function TimelineEntry({ entry }: TimelineEntryProps) {
  const navigate = useNavigate();

  return (
    <div
      onClick={() => navigate(`/page/${entry.slug}`)}
      className={`p-4 rounded-lg border-2 cursor-pointer transition-all hover:shadow-md ${
        entry.is_daily_note
          ? 'border-indigo-300 dark:border-indigo-600 bg-indigo-50 dark:bg-indigo-900/20'
          : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <EntityTypeBadge typeId={entry.entity_type} />
            {entry.is_daily_note && (
              <span className="text-xs font-medium text-indigo-600 dark:text-indigo-400">
                📅 Daily Note
              </span>
            )}
          </div>
          <h3 className="font-semibold text-gray-900 dark:text-white truncate mb-1">
            {entry.title}
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
            {entry.snippet}
          </p>
          {entry.tags.length > 0 && (
            <div className="flex gap-1 mt-2 flex-wrap">
              {entry.tags.slice(0, 3).map((tag) => (
                <span
                  key={tag}
                  className="text-xs px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded"
                >
                  #{tag}
                </span>
              ))}
            </div>
          )}
        </div>
        <svg
          className="w-5 h-5 text-gray-400 flex-shrink-0"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </div>
    </div>
  );
}
