import { TimelineEntry } from './TimelineEntry';

interface TimelineDayGroupProps {
  day: {
    date: string;
    day_name: string;
    entries: Array<{
      slug: string;
      title: string;
      entity_type: string;
      snippet: string;
      is_daily_note: boolean;
      tags: string[];
    }>;
    daily_note_slug: string | null;
  };
}

export function TimelineDayGroup({ day }: TimelineDayGroupProps) {
  // Format date for display
  const dateObj = new Date(day.date + 'T00:00:00');
  const formattedDate = dateObj.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  return (
    <div className="mb-8">
      {/* Date header */}
      <div className="flex items-center gap-3 mb-3">
        <div className="flex-shrink-0 w-12 h-12 rounded-full bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center">
          <span className="text-lg font-bold text-indigo-600 dark:text-indigo-400">
            {dateObj.getDate()}
          </span>
        </div>
        <div>
          <h3 className="font-semibold text-gray-900 dark:text-white">
            {day.day_name}
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">{formattedDate}</p>
        </div>
        {day.daily_note_slug && (
          <span className="ml-auto text-xs px-2 py-1 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 rounded">
            📅 Has daily note
          </span>
        )}
      </div>

      {/* Entries */}
      <div className="ml-6 pl-6 border-l-2 border-gray-200 dark:border-gray-700 space-y-3">
        {day.entries.map((entry) => (
          <TimelineEntry key={entry.slug} entry={entry} />
        ))}
      </div>
    </div>
  );
}
