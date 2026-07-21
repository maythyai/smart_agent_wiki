import { useState } from 'react';
import { useTimeline } from '../hooks/useTimeline';
import { useEntityTypes } from '../hooks/useEntityTypes';
import { TimelineDayGroup } from '../components/timeline/TimelineDayGroup';
import { TimelineFilters } from '../components/timeline/TimelineFilters';
import { DailyNoteButton } from '../components/timeline/DailyNoteButton';

export default function Timeline() {
  const [entityType, setEntityType] = useState('');
  const [tag, setTag] = useState('');
  const [limit, setLimit] = useState(30);

  const { data, isLoading, error } = useTimeline({
    entity_type: entityType || undefined,
    tag: tag || undefined,
    limit,
  });

  const { data: entityTypes } = useEntityTypes();

  const handleLoadMore = () => {
    setLimit((prev) => prev + 30);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Timeline</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Chronological view of your knowledge base
          </p>
        </div>
        <DailyNoteButton />
      </div>

      {/* Stats */}
      {data && (
        <div className="mb-6 flex gap-4 text-sm text-gray-600 dark:text-gray-400">
          <span>
            <strong className="text-gray-900 dark:text-white">{data.total_entries}</strong> entries
          </span>
          <span>
            <strong className="text-gray-900 dark:text-white">{data.days.length}</strong> days
          </span>
          {data.date_range.start !== data.date_range.end && (
            <span>
              {data.date_range.start} → {data.date_range.end}
            </span>
          )}
        </div>
      )}

      {/* Filters */}
      {entityTypes && (
        <TimelineFilters
          entityType={entityType}
          tag={tag}
          onEntityTypeChange={setEntityType}
          onTagChange={setTag}
          entityTypes={entityTypes}
        />
      )}

      {/* Loading */}
      {isLoading && (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="h-12 bg-gray-200 dark:bg-gray-700 rounded mb-3 w-48" />
              <div className="ml-6 pl-6 border-l-2 border-gray-200 dark:border-gray-700 space-y-3">
                <div className="h-24 bg-gray-200 dark:bg-gray-700 rounded" />
                <div className="h-24 bg-gray-200 dark:bg-gray-700 rounded" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-600 dark:text-red-400">
            Failed to load timeline: {error.message}
          </p>
        </div>
      )}

      {/* Timeline */}
      {data && data.days.length === 0 && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">📅</div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            No entries yet
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Create your first page or daily note to start building your timeline.
          </p>
        </div>
      )}

      {data && data.days.length > 0 && (
        <>
          {data.days.map((day) => (
            <TimelineDayGroup key={day.date} day={day} />
          ))}

          {/* Load More */}
          {data.has_more && (
            <div className="text-center mt-8">
              <button
                onClick={handleLoadMore}
                className="px-6 py-2 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700
                  text-gray-900 dark:text-white rounded-lg font-medium transition-colors"
              >
                Load More
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
