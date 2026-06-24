interface TimelineFiltersProps {
  entityType: string;
  tag: string;
  onEntityTypeChange: (type: string) => void;
  onTagChange: (tag: string) => void;
  entityTypes: Array<{ id: string; name: string; icon: string }>;
}

export function TimelineFilters({
  entityType,
  tag,
  onEntityTypeChange,
  onTagChange,
  entityTypes,
}: TimelineFiltersProps) {
  return (
    <div className="flex flex-wrap gap-3 mb-6">
      {/* Entity Type Filter */}
      <select
        value={entityType}
        onChange={(e) => onEntityTypeChange(e.target.value)}
        className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
          bg-white dark:bg-gray-800 text-gray-900 dark:text-white
          focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
      >
        <option value="">All Types</option>
        {entityTypes.map((type) => (
          <option key={type.id} value={type.id}>
            {type.icon} {type.name}
          </option>
        ))}
      </select>

      {/* Tag Filter */}
      <input
        type="text"
        value={tag}
        onChange={(e) => onTagChange(e.target.value)}
        placeholder="Filter by tag..."
        className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
          bg-white dark:bg-gray-800 text-gray-900 dark:text-white
          placeholder-gray-400 dark:placeholder-gray-500
          focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
      />

      {/* Clear Filters */}
      {(entityType || tag) && (
        <button
          onClick={() => {
            onEntityTypeChange('');
            onTagChange('');
          }}
          className="px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
        >
          Clear filters
        </button>
      )}
    </div>
  );
}
