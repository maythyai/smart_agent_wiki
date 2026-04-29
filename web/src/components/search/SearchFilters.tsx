import { Input } from '../ui/Input';
import { Badge } from '../ui/Badge';

interface SearchFiltersProps {
  type: string | undefined;
  tag: string | undefined;
  minConfidence: number | undefined;
  onTypeChange: (type: string | undefined) => void;
  onTagChange: (tag: string | undefined) => void;
  onMinConfidenceChange: (level: number | undefined) => void;
}

const TYPE_OPTIONS = [
  { value: undefined, label: 'All Types' },
  { value: 'summary', label: 'Summary' },
  { value: 'entity', label: 'Entity' },
  { value: 'concept', label: 'Concept' },
  { value: 'document', label: 'Document' },
];

const CONFIDENCE_LEVELS = [
  { value: undefined, label: 'Any Confidence' },
  { value: 4, label: 'Human Verified' },
  { value: 3, label: 'Cross-Validated' },
  { value: 2, label: 'Single Source' },
  { value: 1, label: 'Unverified' },
];

export function SearchFilters({
  type,
  tag,
  minConfidence,
  onTypeChange,
  onTagChange,
  onMinConfidenceChange,
}: SearchFiltersProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
      <h3 className="font-medium text-gray-900">Filters</h3>

      {/* Type filter per D-08 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Type
        </label>
        <select
          value={type ?? ''}
          onChange={(e) => onTypeChange(e.target.value || undefined)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {TYPE_OPTIONS.map((opt) => (
            <option key={opt.label} value={opt.value ?? ''}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {/* Tag filter per D-08 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Tag
        </label>
        <Input
          type="text"
          value={tag ?? ''}
          onChange={(e) => onTagChange(e.target.value || undefined)}
          placeholder="Enter tag..."
        />
      </div>

      {/* Confidence filter per D-08 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Minimum Confidence
        </label>
        <div className="flex flex-wrap gap-2">
          {CONFIDENCE_LEVELS.map((level) => (
            <button
              key={level.label}
              type="button"
              onClick={() => onMinConfidenceChange(level.value)}
              className={`
                px-3 py-1.5 rounded-lg text-sm font-medium border
                ${minConfidence === level.value
                  ? 'bg-blue-100 border-blue-500 text-blue-700'
                  : 'bg-white border-gray-300 text-gray-600 hover:bg-gray-50'
                }
              `}
            >
              {level.label}
            </button>
          ))}
        </div>
        {minConfidence && (
          <div className="mt-2">
            <Badge variant="confidence" level={minConfidence} />
          </div>
        )}
      </div>

      {/* Clear filters */}
      {(type || tag || minConfidence) && (
        <button
          type="button"
          onClick={() => {
            onTypeChange(undefined);
            onTagChange(undefined);
            onMinConfidenceChange(undefined);
          }}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          Clear all filters
        </button>
      )}
    </div>
  );
}